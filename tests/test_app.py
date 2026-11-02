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
    async def fake_chat(message, session_id=None, run_state=None, listener=None, user=None):
        if listener:
            listener({"type": "agent_start", "agent": "clarifier", "round": 0, "t": 0.1})
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


def test_chat_stream_sends_progress_then_the_chat_body():
    import json

    with client.stream("POST", "/chat/stream", json={"message": "hi", "session_id": "st1"}) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        events = [json.loads(line[6:]) for line in r.iter_lines() if line.startswith("data: ")]
    assert [e["type"] for e in events] == ["agent_start", "done"]
    assert set(events[-1]["body"]) == {"response", "session_id", "tool_calls", "citations", "plan", "chart"}


def test_catalog_and_examples():
    cat = client.get("/catalog").json()
    assert len(cat["species"]) == 386 and cat["species"][0]["name"] == "Bulbasaur"
    assert [b["id"] for b in cat["badges"]][:2] == ["stone", "knuckle"]
    assert cat["places"][0]["name"] in ("Route 101", "Route 102", "Route 103", "Route 104", "Petalburg City", "Petalburg Woods")
    examples = client.get("/examples").json()
    assert len(examples) >= 3 and sum(e.get("readme", False) for e in examples) == 3
    for e in examples:  # every example's run state is valid
        assert client.post("/run_state", json={"session_id": f"ex-{e['id']}", "run_state": e["run_state"]}).status_code == 200


def test_examples_sample_logs_exist():
    from app import STATIC
    from agent.examples import EXAMPLES

    for e in EXAMPLES:
        if "sample_log" in e:
            assert (STATIC / "samples" / e["sample_log"]).exists()


def test_post_run_state_and_clear_log():
    from test_log_parser import SAMPLE

    body = client.post("/run_state", json={"session_id": "rs1", "run_state": {"starter": "torchic", "badges": []}}).json()
    assert body["run_state"]["starter"] == "torchic"
    client.post("/upload_log", json={"log_text": SAMPLE, "name": "x.log", "session_id": "rs1"})
    assert client.get("/run_state", params={"session_id": "rs1"}).json()["run_state"]["randomizer_log_id"] == "x.log"
    assert client.post("/clear_log", json={"session_id": "rs1"}).json()["cleared"] is True
    after = client.get("/run_state", params={"session_id": "rs1"}).json()
    assert after["randomizer"] is None and after["run_state"]["randomizer_log_id"] is None


def test_index_page_is_served():
    r = client.get("/")
    assert r.status_code == 200 and "LockeSmith" in r.text


def test_fastapi_telemetry_is_off():
    """FastAPI's built-in tracing would parent every turn on the request's traceparent header,
    which Cloud Run sends marked "not sampled", so LangFuse got nothing for most turns (D12)."""
    assert app_module.app._telemetry["tracing"] is False
