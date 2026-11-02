"""DuckDB connections for the agent.

The shipped data/emerald.duckdb is opened read-only. A session connection is an
in-memory database with the shipped one attached as `base` and on the search
path, so per-session tables (randomizer overlays) live in memory while plain
table names still resolve to the vanilla data.
"""

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "emerald.duckdb"


def connect_readonly() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=True)


SEARCH_PATH = "SET search_path = 'memory.main,base.main'"


def connect_session() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"ATTACH '{DB_PATH.as_posix()}' AS base (READ_ONLY)")
    con.execute(SEARCH_PATH)
    return con


def session_cursor(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """A cursor on a session connection. Cursors share the database (and its overlays)
    but not settings, so the search path is set again."""
    cur = con.cursor()
    cur.execute(SEARCH_PATH)
    return cur
