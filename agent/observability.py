"""LangFuse tracing (PLAN.md §11): each /chat turn becomes one LangFuse trace holding every
agent run, model call (with tokens) and tool call, grouped by session.

Off unless LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set (locally in .env, on Cloud Run
as environment variables; LANGFUSE_BASE_URL picks the region). When on, the Agents SDK's
tracing is switched on with OpenInference's processor as its only processor: the instrumentor
replaces the SDK's default exporter, so spans go to LangFuse and never to OpenAI.
"""

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager

_enabled = False


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

    get_client()  # sets the global OpenTelemetry provider the instrumentor's spans export through
    OpenAIAgentsInstrumentor().instrument()  # exclusive by default: the SDK's OpenAI exporter is dropped
    set_tracing_disabled(False)
    _enabled = True
    return True


def enabled() -> bool:
    return _enabled


@contextmanager
def chat_trace(session_id: str, message: str) -> Iterator[Callable[[dict], None]]:
    """Wrap one /chat turn; yields a function that records the turn's output on the trace."""
    if not _enabled:
        yield lambda output: None
        return
    from agents import trace
    from langfuse import get_client, propagate_attributes

    with get_client().start_as_current_observation(as_type="span", name="chat", input={"message": message}) as root:
        with propagate_attributes(session_id=session_id, trace_name="lockesmith chat"):
            with trace("lockesmith chat", group_id=session_id):
                yield lambda output: root.update(output=output)


def flush() -> None:
    """Send buffered spans now: on Cloud Run the CPU may idle as soon as the response is out."""
    if _enabled:
        from langfuse import get_client

        get_client().flush()
