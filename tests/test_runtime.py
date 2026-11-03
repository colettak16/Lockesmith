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
    assert fast.model.hedge_after == runtime.HEDGE_AFTER_S["fast"] and strong.model.hedge_after is None
    assert strong.model.retry_waits == runtime.RETRY_PRIMARY_S["strong"] and fast.model.retry_waits == ()


def scripted(monkeypatch, outcomes: dict[str, list]):
    """Fake models that raise or answer in the order given per model; returns the calls made."""
    calls = []

    class Response:
        pass

    async def fake_get_response(self, *args, **kwargs):
        calls.append(self.model)
        out = outcomes[self.model].pop(0) if len(outcomes[self.model]) > 1 else outcomes[self.model][0]
        if isinstance(out, Exception):
            raise out
        return Response()

    monkeypatch.setattr(LitellmModel, "get_response", fake_get_response)
    return calls


RATE_LIMITED = litellm.RateLimitError("429", llm_provider="vertex_ai", model="vertex_ai/gemini-3.1-pro-preview")
STALLED = litellm.Timeout("timed out", model="vertex_ai/gemini-3.1-pro-preview", llm_provider="vertex_ai")


def test_the_lead_stays_on_pro_through_brief_rate_limits(monkeypatch):
    """Live Ruby run: one 429 on Pro sent a Lead call to Flash."""
    calls = scripted(monkeypatch, {"pro": [RATE_LIMITED, RATE_LIMITED, "ok"], "flash": ["ok"]})
    response = asyncio.run(runtime.FallbackModel("pro", "flash", retry_waits=(0.01, 0.01, 0.01)).get_response())
    assert calls == ["pro", "pro", "pro"] and not hasattr(response, "lockesmith_fallback")


def test_the_lead_goes_to_flash_only_when_pro_stays_unavailable(monkeypatch):
    calls = scripted(monkeypatch, {"pro": [RATE_LIMITED], "flash": ["ok"]})
    response = asyncio.run(runtime.FallbackModel("pro", "flash", retry_waits=(0.01, 0.01)).get_response())
    assert calls == ["pro", "pro", "pro", "flash"] and response.lockesmith_fallback == "flash"


def test_a_stalled_pro_call_is_retried_once(monkeypatch):
    calls = scripted(monkeypatch, {"pro": [STALLED, "ok"], "flash": ["ok"]})
    asyncio.run(runtime.FallbackModel("pro", "flash", retry_waits=(0.01,)).get_response())
    assert calls == ["pro", "pro"]
    calls = scripted(monkeypatch, {"pro": [STALLED, STALLED, "ok"], "flash": ["ok"]})
    asyncio.run(runtime.FallbackModel("pro", "flash", retry_waits=(0.01,)).get_response())
    assert calls == ["pro", "pro", "flash"]


@pytest.fixture
def timed_models(monkeypatch):
    """Fake models that answer after a set delay (or raise); records starts, finishes and cancellations."""
    delays, events = {}, []

    class Response:
        pass

    async def fake_get_response(self, *args, **kwargs):
        events.append(("start", self.model))
        try:
            await asyncio.sleep(delays[self.model])
        except asyncio.CancelledError:
            events.append(("cancelled", self.model))
            raise
        if self.model.startswith("broken"):
            raise litellm.Timeout("timed out", model=self.model, llm_provider="vertex_ai")
        events.append(("answered", self.model))
        return Response()

    monkeypatch.setattr(LitellmModel, "get_response", fake_get_response)
    return delays, events


def test_a_stalled_call_races_the_fallback_and_the_loser_is_cancelled(timed_models):
    delays, events = timed_models
    delays.update(primary=5, backup=0.05)
    response = asyncio.run(runtime.FallbackModel("primary", "backup", hedge_after=0.05).get_response())
    assert response.lockesmith_fallback == "backup"
    assert events == [("start", "primary"), ("start", "backup"), ("answered", "backup"), ("cancelled", "primary")]


def test_a_slow_call_that_finishes_first_still_wins(timed_models):
    """A long answer that was nearly done when the hedge started isn't thrown away."""
    delays, events = timed_models
    delays.update(primary=0.1, backup=5)
    response = asyncio.run(runtime.FallbackModel("primary", "backup", hedge_after=0.05).get_response())
    assert not hasattr(response, "lockesmith_fallback")
    assert events[-2:] == [("answered", "primary"), ("cancelled", "backup")]


def test_no_hedge_when_the_call_answers_in_time(timed_models):
    delays, events = timed_models
    delays.update(primary=0.01, backup=0.01)
    asyncio.run(runtime.FallbackModel("primary", "backup", hedge_after=1).get_response())
    assert events == [("start", "primary"), ("answered", "primary")]


def test_a_failed_racer_leaves_the_other_to_answer(timed_models):
    delays, events = timed_models
    delays.update(broken=0.1, backup=0.2)
    response = asyncio.run(runtime.FallbackModel("broken", "backup", hedge_after=0.05).get_response())
    assert response.lockesmith_fallback == "backup"
    delays.update({"broken-too": 0.2})
    with pytest.raises(litellm.Timeout):
        asyncio.run(runtime.FallbackModel("broken", "broken-too", hedge_after=0.05).get_response())
