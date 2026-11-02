"""The model wrapper: a rate-limited or stalled call goes to the fallback model (no model calls)."""

import asyncio

import litellm
import pytest
from agents.extensions.models.litellm_model import LitellmModel

from agent import runtime


@pytest.mark.parametrize("error", [
    litellm.RateLimitError("429", llm_provider="vertex_ai", model="vertex_ai/gemini-3.5-flash"),
    litellm.Timeout("timed out", model="vertex_ai/gemini-3.5-flash", llm_provider="vertex_ai"),
])
def test_rate_limits_and_stalls_go_to_the_fallback(monkeypatch, error):
    calls = []

    class Response:
        pass

    async def fake_get_response(self, *args, **kwargs):
        calls.append(self.model)
        if self.model == "primary":
            raise error
        return Response()

    monkeypatch.setattr(LitellmModel, "get_response", fake_get_response)
    response = asyncio.run(runtime.FallbackModel("primary", "backup").get_response())
    assert calls == ["primary", "backup"] and response.lockesmith_fallback == "backup"


def test_agents_get_a_per_call_timeout():
    fast = runtime.make_agent("x", "be brief", "fast")
    strong = runtime.make_agent("y", "be brief", "strong")
    assert fast.model_settings.extra_args == {"timeout": runtime.CALL_TIMEOUT_S["fast"]}
    assert strong.model_settings.extra_args == {"timeout": runtime.CALL_TIMEOUT_S["strong"]}
