"""The only module that knows which agent framework and models Lockesmith uses (PLAN.md §0).

Agents are built with `make_agent` and run with `run`. Swapping the OpenAI Agents SDK
for another framework touches this file only; swapping Gemini for Claude is an env var
(docs/decisions.md D8):

    LOCKESMITH_FAST_MODEL    Clarifier and researchers   (default vertex_ai/gemini-3.5-flash)
    LOCKESMITH_STRONG_MODEL  Lead and Writer             (default vertex_ai/gemini-3.1-pro-preview)

Any LiteLLM model string works. Vertex calls use Application Default Credentials and
VERTEXAI_PROJECT / VERTEXAI_LOCATION (defaults: lockesmith, global).
"""

import json
import os
from typing import Any

from agents import Agent, RunHooks, Runner, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

os.environ.setdefault("VERTEXAI_PROJECT", "lockesmith")
os.environ.setdefault("VERTEXAI_LOCATION", "global")
# The SDK's built-in tracer exports to OpenAI's servers; Lockesmith never sends data there.
set_tracing_disabled(True)

RESULT_PREVIEW_CHARS = 1200


def model_name(tier: str) -> str:
    if tier == "fast":
        return os.environ.get("LOCKESMITH_FAST_MODEL", "vertex_ai/gemini-3.5-flash")
    return os.environ.get("LOCKESMITH_STRONG_MODEL", "vertex_ai/gemini-3.1-pro-preview")


def make_agent(name: str, instructions: str, tier: str, tools=(), output_type=None) -> Agent:
    return Agent(
        name=name,
        instructions=instructions,
        model=LitellmModel(model=model_name(tier)),
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

    async def on_tool_end(self, context, agent, tool, result) -> None:
        raw = getattr(context, "tool_arguments", None)
        try:
            args = json.loads(raw) if raw else {}
        except ValueError:
            args = {"raw": raw}
        ctx = context.context
        ctx.tool_calls.append(
            {"agent": agent.name, "name": tool.name, "args": args, "result": preview(result), "round": ctx.research_round}
        )

    async def on_llm_end(self, context, agent, response) -> None:
        usage = getattr(response, "usage", None)
        if usage is not None:
            context.context.usage.append(
                {"agent": agent.name, "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}
            )


RECORDER = ToolCallRecorder()


async def run(agent: Agent, input: str, context, max_turns: int = 8):
    """Run one agent to completion and return its final output (a pydantic model when the
    agent has an output_type, else text)."""
    result = await Runner.run(agent, input, context=context, hooks=RECORDER, max_turns=max_turns)
    return result.final_output
