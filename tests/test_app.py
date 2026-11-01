"""HTTP surface: the /chat contract (PLAN.md section 8) and the health route."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_chat_contract_shape():
    body = client.post("/chat", json={"message": "hi"}).json()
    assert set(body) == {"response", "session_id", "tool_calls", "citations", "plan", "chart"}
    assert isinstance(body["response"], str) and body["session_id"]


def test_chat_keeps_session_id():
    body = client.post("/chat", json={"message": "hi", "session_id": "abc"}).json()
    assert body["session_id"] == "abc"


def test_chat_requires_message():
    assert client.post("/chat", json={}).status_code == 422
