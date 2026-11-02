"""HTTP surface: the /chat contract (PLAN.md §8) and the session endpoints.

The pipeline is stubbed here so the tests don't call a model; scripts/phase2_acceptance.py
runs the real thing.
"""

import pytest
from fastapi.testclient import TestClient

import app as app_module
from agent.session import SESSIONS

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def stub_pipeline(monkeypatch):
    async def fake_chat(message, session_id=None, run_state=None):
        session = SESSIONS.get(session_id)
        if run_state is not None:
            session.state = run_state
        session.history += [{"role": "user", "content": message}, {"role": "assistant", "content": "ok"}]
        return {
            "response": "ok", "session_id": session.id,
            "tool_calls": [{"agent": "lead", "name": "dispatch_researchers", "args": {}, "result": "{}"}],
            "citations": [], "plan": None, "chart": None,
        }

    monkeypatch.setattr(app_module.pipeline, "chat", fake_chat)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_chat_contract_shape():
    body = client.post("/chat", json={"message": "hi"}).json()
    assert set(body) == {"response", "session_id", "tool_calls", "citations", "plan", "chart"}
    assert isinstance(body["response"], str) and body["session_id"]
    assert body["tool_calls"][0]["agent"] == "lead"


def test_chat_keeps_session_id():
    body = client.post("/chat", json={"message": "hi", "session_id": "abc"}).json()
    assert body["session_id"] == "abc"


def test_chat_requires_message():
    assert client.post("/chat", json={}).status_code == 422


def test_run_state_is_validated():
    bad = client.post("/chat", json={"message": "hi", "run_state": {"starter": "pikachu"}})
    assert bad.status_code == 422
    ok = client.post("/chat", json={"message": "hi", "session_id": "s1", "run_state": {"starter": "Mudkip", "badges": ["Roxanne"]}})
    assert ok.status_code == 200
    state = client.get("/run_state", params={"session_id": "s1"}).json()["run_state"]
    assert state["starter"] == "mudkip" and state["badges"] == ["stone"]


def test_history_and_clear():
    client.post("/chat", json={"message": "first", "session_id": "h1"})
    assert [t["content"] for t in client.get("/history", params={"session_id": "h1"}).json()["history"]] == ["first", "ok"]
    assert client.post("/clear", json={"session_id": "h1"}).json()["cleared"] is True
    assert client.get("/history", params={"session_id": "h1"}).json()["history"] == []
