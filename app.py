"""Lockesmith FastAPI entry point.

/chat runs the agent pipeline (agent/pipeline.py) and returns the response shape fixed in
PLAN.md §8. /history, /clear and /run_state follow the course's chatbot conventions; the
front end that uses them comes in Phase 4.
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from agent import pipeline
from agent.session import SESSIONS
from agent.state import RunState

app = FastAPI(title="Lockesmith")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    run_state: RunState | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list[dict] = []
    citations: list[dict] = []
    plan: dict | None = None
    chart: dict | None = None


class SessionRequest(BaseModel):
    session_id: str


MAX_LOG_CHARS = 4_000_000  # a full UPR ZX Emerald log with every section is about 1-2 MB


class UploadLogRequest(BaseModel):
    log_text: str = Field(max_length=MAX_LOG_CHARS)
    name: str | None = None
    session_id: str | None = None


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lockesmith</title></head>
<body style="font-family: system-ui, sans-serif; max-width: 40rem; margin: 3rem auto; padding: 0 1rem;">
<h1>Lockesmith</h1>
<p>A research agent for Pok&eacute;mon Emerald runs (normal, Nuzlocke and randomized):
what to catch, what to do next, and how to beat the rest of the game.</p>
<p>The agent answers on <code>POST /chat</code>; the full front end is coming.</p>
</body></html>"""


@app.get("/health")  # not /healthz: Cloud Run reserves paths ending in "z"
def health() -> dict:
    return {"status": "ok", "revision": os.environ.get("K_REVISION", "local")}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    return ChatResponse(**await pipeline.chat(req.message, req.session_id, req.run_state))


@app.post("/upload_log")
def upload_log(req: UploadLogRequest) -> dict:
    """Load a Universal Pokemon Randomizer ZX log into the session (PLAN.md §4.5): from then on
    the session's answers use the randomized game. Returns what was read and what wasn't."""
    try:
        return pipeline.load_log(req.log_text, req.name, req.session_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.get("/history")
def history(session_id: str) -> dict:
    session = SESSIONS.peek(session_id)
    return {"session_id": session_id, "history": session.history if session else []}


@app.post("/clear")
def clear(req: SessionRequest) -> dict:
    return {"session_id": req.session_id, "cleared": SESSIONS.clear(req.session_id)}


@app.get("/run_state")
def run_state(session_id: str) -> dict:
    """The session's current run state, including rules and facts learned in conversation."""
    session = SESSIONS.peek(session_id)
    return {
        "session_id": session_id,
        "run_state": session.state.model_dump() if session else None,
        "rejected_species": sorted(session.excluded) if session else [],
        "randomizer": session.randomizer if session else None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
