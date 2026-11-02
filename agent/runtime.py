"""The only module that knows which agent framework and models Lockesmith uses (PLAN.md §0).

Agents are built with `make_agent` and run with `run`. Swapping the OpenAI Agents SDK
for another framework touches this file only; swapping Gemini for Claude is an env var
(docs/decisions.md D8):

    LOCKESMITH_FAST_MODEL      Clarifier, researchers, Writer  (default vertex_ai/gemini-3.5-flash)
    LOCKESMITH_STRONG_MODEL    Lead                            (default vertex_ai/gemini-3.1-pro-preview)
    LOCKESMITH_FALLBACK_MODEL  used when either is rate-limited (default vertex_ai/gemini-3.8-flash)

Any LiteLLM model string works. Vertex calls use Application Default Credentials and
VERTEXAI_PROJECT / VERTEXAI_LOCATION (defaults: lockesmith, global).

Rate limits: Vertex serves these models from shared capacity, so bursts of parallel
researchers get "429 Resource exhausted". Rather than wait that out, a rate-limited call
goes straight to the fallback model, which has its own capacity (docs/decisions.md D10).
"""

import json
import logging
import os
from typing import Any

import litellm

from agents import Agent, ModelSettings, RunHooks, Runner, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from agents.retry import ModelRetrySettings, retry_policies
from agents.run_error_handlers import RunErrorHandlerInput, RunErrorHandlerResult
from openai.types.shared import Reasoning

os.environ.setdefault("VERTEXAI_PROJECT", "lockesmith")
os.environ.setdefault("VERTEXAI_LOCATION", "global")
# The SDK's built-in tracer exports to OpenAI's servers; Lockesmith never sends data there.
set_tracing_disabled(True)

RESULT_PREVIEW_CHARS = 1200
log = logging.getLogger("lockesmith.runtime")
# Last resort after the fallback model: short retries for 429s, server and network errors.
RETRY = ModelRetrySettings(
    max_retries=2,
    backoff={"initial_delay": 1.0, "multiplier": 2.0, "max_delay": 4.0, "jitter": True},
    policy=retry_policies.any(retry_policies.http_status([429, 500, 503]), retry_policies.network_error()),
)


def model_name(tier: str) -> str:
    if tier == "fast":
        return os.environ.get("LOCKESMITH_FAST_MODEL", "vertex_ai/gemini-3.5-flash")
    if tier == "fallback":
        return os.environ.get("LOCKESMITH_FALLBACK_MODEL", "vertex_ai/gemini-3.8-flash")
    return os.environ.get("LOCKESMITH_STRONG_MODEL", "vertex_ai/gemini-3.1-pro-preview")


class FallbackModel(LitellmModel):
    """A LiteLLM model that sends a rate-limited call to a second model instead of waiting."""

    def __init__(self, model: str, fallback: str | None):
        super().__init__(model=model)
        self.fallback = LitellmModel(model=fallback) if fallback and fallback != model else None

    async def get_response(self, *args, **kwargs):
        try:
            return await super().get_response(*args, **kwargs)
        except litellm.RateLimitError:
            if self.fallback is None:
                raise
            log.info("rate-limited on %s; using %s", self.model, self.fallback.model)
            response = await self.fallback.get_response(*args, **kwargs)
            response.lockesmith_fallback = self.fallback.model  # surfaced by ToolCallRecorder.on_llm_end
            return response


def make_agent(name: str, instructions: str, tier: str, tools=(), output_type=None, effort: str | None = None) -> Agent:
    """`effort` ("low", "medium", "high") caps the model's thinking; LiteLLM maps it to each
    provider's setting (Gemini thinking level, Claude thinking budget)."""
    return Agent(
        name=name,
        instructions=instructions,
        model=FallbackModel(model_name(tier), model_name("fallback")),
        model_settings=ModelSettings(reasoning=Reasoning(effort=effort) if effort else None, retry=RETRY),
        tools=list(tools),
        output_type=output_type,
    )


def preview(result: Any) -> str:
    text = result if isinstance(result, str) else json.dumps(result, default=str)
    if len(text) <= RESULT_PREVIEW_CHARS:
        return text
    return text[:RESULT_PREVIEW_CHARS] + f"... [{len(text) - RESULT_PREVIEW_CHARS} more characters]"


class ToolCallRecorder(RunHooks):
    """Appends {agent, name, args, result, round} to the request context for every tool call,
    including those made by researchers running inside the Lead's dispatch tool."""

    async def on_agent_start(self, context, agent) -> None:
        context.context.emit({"type": "agent_start", "agent": agent.name})

    async def on_tool_start(self, context, agent, tool) -> None:
        raw = getattr(context, "tool_arguments", None)
        try:
            args = json.loads(raw) if raw else {}
        except ValueError:
            args = {}
        context.context.emit({"type": "tool_start", "agent": agent.name, "name": tool.name, "args": args})

    async def on_tool_end(self, context, agent, tool, result) -> None:
        raw = getattr(context, "tool_arguments", None)
        try:
            args = json.loads(raw) if raw else {}
        except ValueError:
            args = {"raw": raw}
        ctx = context.context
        ctx.tool_calls.append(
            {"agent": agent.name, "name": tool.name, "args": args, "result": preview(result),
             "round": ctx.research_round, "t": ctx.elapsed()}
        )

    async def on_llm_end(self, context, agent, response) -> None:
        usage = getattr(response, "usage", None)
        if usage is not None:
            context.context.usage.append(
                {"agent": agent.name, "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
                 "t": context.context.elapsed(), "fallback": getattr(response, "lockesmith_fallback", None)}
            )


RECORDER = ToolCallRecorder()
WRAP_UP = "You've used your tool budget. Give your final answer now, using only the tool results above."


async def finish_at_turn_limit(data: RunErrorHandlerInput):
    """When an agent hits max_turns still calling tools, give it one more turn with tools
    switched off so it reports what it found instead of failing."""
    agent = data.run_data.last_agent
    ctx = data.context.context
    ctx.tool_calls.append(
        {"agent": agent.name, "name": "turn_limit_wrap_up", "args": {}, "result": "tool budget used; asked for the final answer",
         "round": ctx.research_round, "t": ctx.elapsed()}
    )
    closer = agent.clone(model_settings=agent.model_settings.resolve(ModelSettings(tool_choice="none")))
    history = list(data.run_data.history) + [{"role": "user", "content": WRAP_UP}]
    result = await Runner.run(closer, history, context=ctx, hooks=RECORDER, max_turns=1)
    return RunErrorHandlerResult(final_output=result.final_output, include_in_history=False)


async def run(agent: Agent, input: str, context, max_turns: int = 8):
    """Run one agent to completion and return its final output (a pydantic model when the
    agent has an output_type, else text). An agent that runs out of turns while still
    calling tools is asked to wrap up rather than failing."""
    result = await Runner.run(
        agent, input, context=context, hooks=RECORDER, max_turns=max_turns,
        error_handlers={"max_turns": finish_at_turn_limit},
    )
    return result.final_output
