"""LangFuse tracing (PLAN.md §11): each /chat turn becomes one LangFuse trace holding every
agent run, model call (with tokens and cost) and tool call, plus the Verifier's checks, grouped
by session (docs/decisions.md D12).

Off unless LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set (locally in .env, on Cloud Run
as environment variables; LANGFUSE_BASE_URL picks the region). When on, the Agents SDK's
tracing is switched on with OpenInference's processor as its only processor: the instrumentor
replaces the SDK's default exporter, so spans go to LangFuse and never to OpenAI.

Trace shape, following LangFuse's best practices (names verb-first and stable, the player's
question and the answer as the trace's input and output):

    answer-question (chain)          input: the question, output: the answer, metadata: intent, picks, cost
      run-agents (agent)             the Agents SDK workflow
        classify-request > clarifier > turn > generation
        lead-research > lead > turn > generation, dispatch_researchers (tool)
          research-battles > battle_researcher > turn > generation, scout_battle (tool), ...
        write-answer > writer > ...
      verify-picks, correct-places, check-citations (evaluator); promote-backups (span)
"""

import hashlib
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager

_enabled = False

# Agent -> the step its run performs (the Agents SDK's workflow name for that run)
WORKFLOW_NAMES = {
    "clarifier": "classify-request",
    "lead": "lead-research",
    "battle_researcher": "research-battles",
    "catch_researcher": "research-catches",
    "moves_researcher": "research-moves",
    "story_researcher": "research-story",
    "writer": "write-answer",
}
# Pipeline steps done in code (pipeline.record) -> observation name and type; others aren't traced
STEPS = {
    "verify": ("verify-picks", "evaluator"),
    "correct_where": ("correct-places", "evaluator"),
    "citation_check": ("check-citations", "evaluator"),
    "promote_backups": ("promote-backups", "span"),
    "error": ("handle-error", "span"),
    "chart_error": ("draw-chart", "span"),
}
ERROR_STEPS = {"error", "chart_error"}


def setup() -> bool:
    """Start tracing if LangFuse keys are configured; safe to call more than once."""
    global _enabled
    if _enabled:
        return True
    if not (os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")):
        return False
    from agents import set_tracing_disabled
    from langfuse import get_client
    from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor

    # Cloud Run sets K_SERVICE; keeps local test runs out of the deployed service's dashboards
    os.environ.setdefault("LANGFUSE_TRACING_ENVIRONMENT", "production" if os.environ.get("K_SERVICE") else "development")
    get_client()  # sets the global OpenTelemetry provider the instrumentor's spans export through
    OpenAIAgentsInstrumentor().instrument()  # exclusive by default: the SDK's OpenAI exporter is dropped
    set_tracing_disabled(False)
    _enabled = True
    return True


def enabled() -> bool:
    return _enabled


def workflow_name(agent_name: str) -> str:
    return WORKFLOW_NAMES.get(agent_name, agent_name)


def user_id(iap_header: str | None) -> str | None:
    """A stable pseudonymous id from IAP's X-Goog-Authenticated-User-Id, so LangFuse can group
    a person's traces without storing who they are."""
    if not iap_header:
        return None
    return "u-" + hashlib.sha256(iap_header.encode()).hexdigest()[:12]


@contextmanager
def chat_trace(session_id: str, message: str, *, user: str | None = None,
               tags: list[str] | None = None) -> Iterator[Callable[[str, dict], None]]:
    """Wrap one /chat turn; yields finish(answer, metadata), which sets the trace's output."""
    if not _enabled:
        yield lambda answer, metadata: None
        return
    from agents import trace
    from langfuse import get_client, propagate_attributes

    with get_client().start_as_current_observation(as_type="chain", name="answer-question", input=message) as root:
        with propagate_attributes(session_id=session_id, user_id=user, tags=tags or [], trace_name="lockesmith-chat"):
            with trace("run-agents", group_id=session_id):
                yield lambda answer, metadata: root.update(output=answer, metadata=metadata)


def step(name: str, args: dict, result) -> None:
    """A pipeline step done in code (the Verifier's checks, errors) as its own observation."""
    if not _enabled or name not in STEPS:
        return
    from langfuse import get_client

    label, kind = STEPS[name]
    get_client().start_observation(
        name=label, as_type=kind, input=args or None, output=result,
        level="ERROR" if name in ERROR_STEPS else None,
    ).end()


def flush() -> None:
    """Send buffered spans now: on Cloud Run the CPU may idle as soon as the response is out."""
    if _enabled:
        from langfuse import get_client

        get_client().flush()
