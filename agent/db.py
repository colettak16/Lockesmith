"""DuckDB connections for the agent.

Each game's shipped database (data/emerald.duckdb, ruby.duckdb, sapphire.duckdb) is
opened read-only. A session connection is an in-memory database with the game's one
attached as `base` and on the search path, so per-session tables (randomizer
overlays) live in memory while plain table names still resolve to the vanilla data.
"""

import duckdb

from agent.games import EMERALD, Game

DB_PATH = EMERALD.db_path


def connect_readonly(game: Game = EMERALD) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(game.db_path), read_only=True)


SEARCH_PATH = "SET search_path = 'memory.main,base.main'"


def connect_session(game: Game = EMERALD) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"ATTACH '{game.db_path.as_posix()}' AS base (READ_ONLY)")
    con.execute(SEARCH_PATH)
    return con


def session_cursor(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """A cursor on a session connection. Cursors share the database (and its overlays)
    but not settings, so the search path is set again."""
    cur = con.cursor()
    cur.execute(SEARCH_PATH)
    return cur
