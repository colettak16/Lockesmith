"""Lockesmith FastAPI entry point.

Phase 0: a hello-world service that proves the Cloud Run deploy path. The
/chat endpoint already returns the response shape fixed in PLAN.md section 8,
so the deploy can be smoke-tested against the real contract.
"""

import os
import uuid

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Lockesmith")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    run_state: dict | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list[dict] = []
    citations: list[dict] = []
    plan: dict | None = None
    chart: dict | None = None


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lockesmith</title></head>
<body style="font-family: system-ui, sans-serif; max-width: 40rem; margin: 3rem auto; padding: 0 1rem;">
<h1>Lockesmith</h1>
<p>A research agent for Pok&eacute;mon Emerald runs (normal, Nuzlocke and randomized):
it tells you what to catch next, and where, to beat the rest of the game.</p>
<p>Under construction. The agent is not wired up yet.</p>
</body></html>"""


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "revision": os.environ.get("K_REVISION", "local")}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return ChatResponse(
        response="Lockesmith is deployed but the agent isn't wired up yet.",
        session_id=req.session_id or uuid.uuid4().hex,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
