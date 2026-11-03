"""LockeSmith FastAPI entry point.

/chat runs the agent pipeline (agent/pipeline.py) and returns the response shape fixed in
PLAN.md §8; /chat/stream is the same turn as server-sent events, so the front end (static/)
can show progress while researchers work. /history, /clear and /run_state follow the course's
chatbot conventions.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent import observability, pipeline
from agent.catalog import catalog as build_catalog
from agent.examples import EXAMPLES
from agent.games import get as get_game
from agent.session import SESSIONS
from agent.state import RunState

STATIC = Path(__file__).resolve().parent / "static"
KEEPALIVE_S = 15  # a comment line this often keeps proxies from closing a quiet stream

# Warnings and errors from every library (the LangFuse exporter included) reach Cloud Run's logs,
# plus LockeSmith's own per-turn and fallback lines
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("lockesmith").setLevel(logging.INFO)

# FastAPI's built-in OpenTelemetry switches itself on once LangFuse configures a tracer, and makes
# each request's `traceparent` header the parent of everything the request does. Cloud Run's front
# end sends that header, usually marked "not sampled", so most turns recorded nothing at all
# (docs/decisions.md D12). LangFuse traces the agents; HTTP spans aren't wanted.
app = FastAPI(title="LockeSmith", telemetry={"tracing": False, "metrics": False, "logs": False})

# Cloud Run's build dates every file 1980, so without this a browser would treat its cached copy of
# the page, banner, CSS and JS as fresh for years and never pick up a deploy. no-cache makes it ask
# each time (a quick 304 when nothing changed).
NO_CACHE = {"Cache-Control": "no-cache"}


class FreshStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers.update(NO_CACHE)
        return response


app.mount("/static", FreshStaticFiles(directory=STATIC), name="static")


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


class RunStateRequest(BaseModel):
    session_id: str
    run_state: RunState


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html", headers=NO_CACHE)


@app.get("/health")  # not /healthz: Cloud Run reserves paths ending in "z"
def health() -> dict:
    return {"status": "ok", "revision": os.environ.get("K_REVISION", "local")}


def traced_user(request: Request) -> str | None:
    """IAP's id for the signed-in user, pseudonymized for tracing (agent/observability.py)."""
    return observability.user_id(request.headers.get("x-goog-authenticated-user-id"))


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    return ChatResponse(**await pipeline.chat(req.message, req.session_id, req.run_state, user=traced_user(request)))


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request) -> StreamingResponse:
    """The /chat turn as server-sent events: `agent_start`, `tool_start` and `tool_call` events
    while it runs, then `done` with the /chat response as `body` (and per-call `usage`)."""
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def listener(event: dict) -> None:
        try:
            asyncio.get_running_loop()  # on the loop's thread: keep the order exact
            queue.put_nowait(event)
        except RuntimeError:  # a tool running in a worker thread
            loop.call_soon_threadsafe(queue.put_nowait, event)

    async def work() -> None:
        try:
            body = await pipeline.chat(req.message, req.session_id, req.run_state, listener=listener, user=traced_user(request))
            await asyncio.sleep(0)  # let events scheduled from worker threads land before `done`
            await queue.put({"type": "done", "body": ChatResponse(**body).model_dump(), "usage": body.get("usage", [])})
        except Exception as e:  # noqa: BLE001 - pipeline.chat already turns agent failures into a reply
            await queue.put({"type": "error", "detail": f"{type(e).__name__}: {e}"})

    task = asyncio.create_task(work())

    async def events():
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), KEEPALIVE_S)
            except TimeoutError:
                yield ": keepalive\n\n"
                continue
            yield f"data: {json.dumps(event, default=str, ensure_ascii=False)}\n\n"
            if event["type"] in ("done", "error"):
                break
        await task

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/catalog")
def catalog(game: str = "emerald") -> dict:
    """Species, moves, battles, badges, types and Nuzlocke places for one game's run-state form,
    and whether a banner video (static/media/banner.mp4) is there to replace the still banner art."""
    try:
        data = build_catalog(get_game(game).id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return {**data, "banner_video": (STATIC / "media" / "banner.mp4").exists()}


@app.get("/examples")
def examples() -> list[dict]:
    """One-click example questions with the run state each needs (agent/examples.py)."""
    return EXAMPLES


@app.post("/upload_log")
def upload_log(req: UploadLogRequest) -> dict:
    """Load a Universal Pokemon Randomizer ZX log into the session (PLAN.md §4.5): from then on
    the session's answers use the randomized game. Returns what was read and what wasn't."""
    try:
        return pipeline.load_log(req.log_text, req.name, req.session_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post("/clear_log")
def clear_log(req: SessionRequest) -> dict:
    """Unload the session's randomizer log: answers use the vanilla game again."""
    return {"session_id": req.session_id, "cleared": pipeline.clear_log(req.session_id)}


@app.get("/history")
def history(session_id: str) -> dict:
    session = SESSIONS.peek(session_id)
    return {"session_id": session_id, "history": session.history if session else []}


@app.post("/clear")
def clear(req: SessionRequest) -> dict:
    return {"session_id": req.session_id, "cleared": SESSIONS.clear(req.session_id)}


@app.post("/run_state")
def set_run_state(req: RunStateRequest) -> dict:
    """Save the form's run state to the session without asking anything (PLAN.md §8)."""
    session = SESSIONS.get(req.session_id)
    pipeline.apply_form_state(session, req.run_state)
    return run_state(session.id)


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
