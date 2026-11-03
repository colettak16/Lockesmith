"""What every tool and agent sees during one /chat request."""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cache

import duckdb

from agent.db import connect_readonly, session_cursor
from agent.entities import EntityIndex
from agent.evidence import Ledger
from agent.games import DEFAULT, Game
from agent.games import get as get_game
from agent.progression import Progression, load_game
from agent.state import Progress, RunState, progress


@cache
def shared_index(game_id: str = DEFAULT) -> EntityIndex:
    """Name matching over one game's vanilla tables, built once per process."""
    return EntityIndex(connect_readonly(get_game(game_id)))


class CallLog(list):
    """`tool_calls` that also reports each entry to a listener (the streaming endpoint)."""

    listener: Callable[[dict], None] | None = None

    def append(self, call: dict) -> None:
        super().append(call)
        if self.listener:
            self.listener({"type": "tool_call", **call})


@dataclass
class RequestContext:
    state: RunState
    con: duckdb.DuckDBPyConnection  # the session connection (vanilla attached read-only + overlays)
    prog: Progression | None = None  # the game's progression, from state.game unless given
    index: EntityIndex | None = None
    ledger: Ledger | None = None
    excluded_species: set[str] = field(default_factory=set)  # picks the user rejected this session
    tool_calls: list[dict] = field(default_factory=CallLog)
    usage: list[dict] = field(default_factory=list)
    research_round: int = 0
    round_cap: int = 2  # the Verifier's repair pass allows one more round (PLAN's cap of 3)
    randomizer: dict | None = None  # overlay.summary() of the session's loaded log, if any
    started: float = field(default_factory=time.monotonic)
    listener: Callable[[dict], None] | None = None  # progress events for POST /chat/stream

    def __post_init__(self) -> None:
        if isinstance(self.tool_calls, CallLog):
            self.tool_calls.listener = self.listener
        self.prog = self.prog or load_game(self.game)
        self.index = self.index or shared_index(self.game.id)
        self.ledger = self.ledger or Ledger(self.game)

    @property
    def game(self) -> Game:
        return get_game(self.state.game)

    def refresh_game(self, con: duckdb.DuckDBPyConnection) -> None:
        """After the run state's game changed mid-turn: the game's connection, progression and names.
        The ledger keeps its entries (none are cited across a game switch) but labels for the new game."""
        self.con = con
        self.prog = load_game(self.game)
        self.index = shared_index(self.game.id)
        self.ledger.game = self.game

    def emit(self, event: dict) -> None:
        if self.listener:
            self.listener({**event, "round": self.research_round, "t": self.elapsed()})

    @property
    def log_changes(self) -> dict[str, str]:
        return self.randomizer["changes"] if self.randomizer else {}

    def elapsed(self) -> float:
        return round(time.monotonic() - self.started, 2)

    def cursor(self) -> duckdb.DuckDBPyConnection:
        """A cursor per tool call: researchers run in parallel, and DuckDB connections
        aren't safe to share across threads, while cursors on the same database are."""
        return session_cursor(self.con)

    @property
    def progress(self) -> Progress:
        return progress(self.state, self.prog)
