"""What every tool and agent sees during one /chat request."""

from dataclasses import dataclass, field
from functools import cache

import duckdb

from agent.db import connect_readonly, session_cursor
from agent.entities import EntityIndex
from agent.evidence import Ledger
from agent.progression import Progression, load
from agent.state import Progress, RunState, progress


@cache
def shared_index() -> EntityIndex:
    """Name matching over the vanilla tables, built once per process."""
    return EntityIndex(connect_readonly())


@dataclass
class RequestContext:
    state: RunState
    con: duckdb.DuckDBPyConnection  # the session connection (vanilla attached read-only + overlays)
    prog: Progression = field(default_factory=load)
    index: EntityIndex = field(default_factory=shared_index)
    ledger: Ledger = field(default_factory=Ledger)
    excluded_species: set[str] = field(default_factory=set)  # picks the user rejected this session
    tool_calls: list[dict] = field(default_factory=list)
    usage: list[dict] = field(default_factory=list)
    research_round: int = 0

    def cursor(self) -> duckdb.DuckDBPyConnection:
        """A cursor per tool call: researchers run in parallel, and DuckDB connections
        aren't safe to share across threads, while cursors on the same database are."""
        return session_cursor(self.con)

    @property
    def progress(self) -> Progress:
        return progress(self.state, self.prog)
