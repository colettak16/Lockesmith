"""The only module that knows which agent framework and models LockeSmith uses (PLAN.md §0).

Agents are built with `make_agent` and run with `run`. Swapping the OpenAI Agents SDK
for another framework touches this file only; swapping Gemini for Claude is an env var
(docs/decisions.md D8):

    LOCKESMITH_FAST_MODEL      Clarifier, researchers, Writer  (default vertex_ai/gemini-3.5-flash)
    LOCKESMITH_STRONG_MODEL    Lead                            (default vertex_ai/gemini-3.1-pro-preview)
    LOCKESMITH_FALLBACK_MODEL  used when either is rate-limited (default vertex_ai/gemini-3.8-flash)

Any LiteLLM model string works. Vertex calls use Application Default Credentials and
VERTEXAI_PROJECT / VERTEXAI_LOCATION (defaults: lockesmith, global).

Rate limits: Vertex serves these models from shared capacity, so bursts of parallel
researchers get "429 Resource exhausted". Rather than wait that out, a rate-limited Flash call
goes straight to the fallback model, which has its own capacity (docs/decisions.md D10). The
Lead's Pro calls are retried first (RETRY_PRIMARY_S), since their fallback is a weaker model.
Stalls: a fast-tier call with no answer after HEDGE_AFTER_S is also sent to the fallback
model, and whichever answers first is used (docs/decisions.md D15).
"""

import asyncio
import json
import logging
import os
from typing import Any

from litellm.exceptions import RateLimitError, Timeout
from dotenv import load_dotenv

from agents import Agent, ModelSettings, RunConfig, RunHooks, Runner, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from agents.retry import ModelRetrySettings, retry_policies
from agents.run_error_handlers import RunErrorHandlerInput, RunErrorHandlerResult
from openai.types.shared import Reasoning

from agent import observability
from agent.pricing import cost_usd

load_dotenv()  # local settings and keys (.env is gitignored); Cloud Run sets real environment variables
os.environ.setdefault("VERTEXAI_PROJECT", "lockesmith")
os.environ.setdefault("VERTEXAI_LOCATION", "global")
# The SDK's built-in tracer exports to OpenAI's servers; LockeSmith never sends data there.
set_tracing_disabled(True)
observability.setup()  # with LangFuse keys set, tracing comes back on, exporting to LangFuse only

RESULT_PREVIEW_CHARS = 1200
log = logging.getLogger("lockesmith.runtime")
# Last resort after the fallback model: short retries for 429s, server and network errors.
RETRY = ModelRetrySettings(
    max_retries=2,
    backoff={"initial_delay": 1.0, "multiplier": 2.0, "max_delay": 4.0, "jitter": True},
    policy=retry_policies.any(retry_policies.http_status([429, 500, 503]), retry_policies.network_error()),
)
# Per-call limits. In LangFuse traces a normal Flash call finished within 15 s even writing 2,800
# tokens, and Pro within 35 s; slower ones had stalled (68 s for a 76-token reply), holding up the
# whole parallel round. A call past its limit goes to the fallback model instead (docs/decisions.md D12).
CALL_TIMEOUT_S = {"fast": 25, "strong": 60}
# Hedging. In 185 LangFuse Flash calls, every answer of 1,000+ tokens came within 14.6 s, and the
# slower ones were short replies that had stalled (68 s for 76 tokens). Past 12 s (13% of calls), the
# same request also goes to the fallback model; the first answer wins and the other is cancelled.
# The original keeps running, so a long answer that's nearly done still finishes. Pro isn't hedged:
# it hasn't stalled, and its fallback is a weaker model.
HEDGE_AFTER_S = {"fast": 12}
# The Lead plans the research and drafts the picks, so it should stay on Pro: a rate-limited Pro call
# is retried after each of these waits (a 429 comes back in under a second, and the shared capacity
# frees up quickly), and a stalled one is retried once, before either goes to Flash.
RETRY_PRIMARY_S = {"strong": (1, 2, 4, 8)}


def model_name(tier: str) -> str:
    if tier == "fast":
        return os.environ.get("LOCKESMITH_FAST_MODEL", "vertex_ai/gemini-3.5-flash")
    if tier == "fallback":
        return os.environ.get("LOCKESMITH_FALLBACK_MODEL", "vertex_ai/gemini-3.8-flash")
    return os.environ.get("LOCKESMITH_STRONG_MODEL", "vertex_ai/gemini-3.1-pro-preview")


class FallbackModel(LitellmModel):
    """A LiteLLM model that sends a rate-limited or stalled call to a second model instead of
    waiting. With `hedge_after`, a call still unanswered by then races the second model too.
    With `retry_waits`, the first model is retried while rate-limited (and once after a stall)
    before the second is used."""

    def __init__(self, model: str, fallback: str | None, hedge_after: float | None = None,
                 retry_waits: tuple[float, ...] = ()):
        super().__init__(model=model)
        self.fallback = LitellmModel(model=fallback) if fallback and fallback != model else None
        self.hedge_after = hedge_after
        self.retry_waits = retry_waits

    async def _primary_response(self, *args, **kwargs):
        waits, stalled = list(self.retry_waits), False
        while True:
            try:
                return await super().get_response(*args, **kwargs)
            except RateLimitError:
                if not waits:
                    raise
                wait = waits.pop(0)
            except Timeout:
                if not self.retry_waits or stalled:
                    raise
                stalled, wait = True, 0
            log.warning("no answer from %s; trying it again in %ss", self.model, wait)
            await asyncio.sleep(wait)

    async def _fallback_response(self, *args, **kwargs):
        response = await self.fallback.get_response(*args, **kwargs)
        response.lockesmith_fallback = self.fallback.model  # surfaced by ToolCallRecorder.on_llm_end
        return response

    async def get_response(self, *args, **kwargs):
        if self.fallback is None:
            return await self._primary_response(*args, **kwargs)
        primary = asyncio.ensure_future(self._primary_response(*args, **kwargs))
        running = {primary}
        try:
            done, _ = await asyncio.wait(running, timeout=self.hedge_after)
            if done:
                try:
                    return primary.result()
                except (RateLimitError, Timeout) as e:
                    log.warning("%s on %s; using %s", type(e).__name__, self.model, self.fallback.model)
                    return await self._fallback_response(*args, **kwargs)
            log.warning("no answer from %s after %ss; racing %s", self.model, self.hedge_after, self.fallback.model)
            running.add(asyncio.ensure_future(self._fallback_response(*args, **kwargs)))
            error = None
            while running:
                done, running = await asyncio.wait(running, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    if task.exception() is None:
                        return task.result()
                    error = error or task.exception()  # the other may still answer
            raise error
        finally:
            for task in running:  # the race's loser, or both if the turn itself was cancelled
                task.cancel()


def make_agent(name: str, instructions: str, tier: str, tools=(), output_type=None, effort: str | None = None) -> Agent:
    """`effort` ("low", "medium", "high") caps the model's thinking; LiteLLM maps it to each
    provider's setting (Gemini thinking level, Claude thinking budget)."""
    return Agent(
        name=name,
        instructions=instructions,
        model=FallbackModel(model_name(tier), model_name("fallback"), HEDGE_AFTER_S.get(tier), RETRY_PRIMARY_S.get(tier, ())),
        model_settings=ModelSettings(reasoning=Reasoning(effort=effort) if effort else None, retry=RETRY,
                                     extra_args={"timeout": CALL_TIMEOUT_S.get(tier, 60)}),
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
            fallback = getattr(response, "lockesmith_fallback", None)
            model = fallback or getattr(agent.model, "model", str(agent.model))
            context.context.usage.append(
                {"agent": agent.name, "model": model, "input_tokens": usage.input_tokens,
                 "output_tokens": usage.output_tokens, "cost_usd": cost_usd(model, usage.input_tokens, usage.output_tokens),
                 "t": context.context.elapsed(), "fallback": fallback}
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
    result = await Runner.run(closer, history, context=ctx, hooks=RECORDER, max_turns=1,
                              run_config=RunConfig(workflow_name="wrap-up"))
    return RunErrorHandlerResult(final_output=result.final_output, include_in_history=False)


async def run(agent: Agent, input: str, context, max_turns: int = 8):
    """Run one agent to completion and return its final output (a pydantic model when the
    agent has an output_type, else text). An agent that runs out of turns while still
    calling tools is asked to wrap up rather than failing."""
    result = await Runner.run(
        agent, input, context=context, hooks=RECORDER, max_turns=max_turns,
        error_handlers={"max_turns": finish_at_turn_limit},
        run_config=RunConfig(workflow_name=observability.workflow_name(agent.name)),  # the step's name in traces
    )
    return result.final_output
