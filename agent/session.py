"""Per-session memory (docs/decisions.md D8): run state, conversation, the last plan, rules
learned in conversation and rejected picks.

Sessions live in memory on one Cloud Run instance, so the service needs session affinity.
Each session has its own DuckDB connection, where a loaded randomizer log's overlays live.
"""

import threading
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field

import duckdb

from agent.db import connect_session
from agent.state import RunState, Ruleset
from agent.schemas import RuleUpdate

MAX_SESSIONS = 200


@dataclass
class Session:
    id: str
    state: RunState = field(default_factory=RunState)
    con: duckdb.DuckDBPyConnection = field(default_factory=connect_session)
    history: list[dict] = field(default_factory=list)
    last_plan: dict | None = None
    excluded: set[str] = field(default_factory=set)
    learned_rules: list[RuleUpdate] = field(default_factory=list)
    randomizer: dict | None = None  # overlay.summary() of the loaded randomizer log


def apply_rules(rules: Ruleset, u: RuleUpdate) -> Ruleset:
    data = rules.model_dump()
    for key in ("nuzlocke", "encounter_scope", "gifts_count_as_encounter", "dupes_clause", "level_caps",
                "level_cap_offset", "allowed_types", "no_legendaries", "wild_only"):
        value = getattr(u, key)
        if value is not None:
            data[key] = value.lower() if isinstance(value, str) else value
    for key, add in (("banned_species", u.add_banned_species), ("banned_types", u.add_banned_types),
                     ("used_routes", u.add_used_routes), ("notes", u.add_notes)):
        data[key] = list(dict.fromkeys([*data[key], *add]))
    return Ruleset(**data)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, session_id: str | None) -> Session:
        with self._lock:
            if session_id and session_id in self._sessions:
                self._sessions.move_to_end(session_id)
                return self._sessions[session_id]
            session = Session(id=session_id or uuid.uuid4().hex)
            self._sessions[session.id] = session
            while len(self._sessions) > MAX_SESSIONS:
                _, old = self._sessions.popitem(last=False)
                old.con.close()
            return session

    def peek(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def clear(self, session_id: str) -> bool:
        with self._lock:
            old = self._sessions.pop(session_id, None)
        if old:
            old.con.close()
        return old is not None


SESSIONS = SessionStore()
