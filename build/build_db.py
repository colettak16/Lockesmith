"""Build data/emerald.duckdb from the raw sources.

    uv run python build/fetch_sources.py   # once, or after changing data/sources.lock.json
    uv run python build/build_db.py

Steps: load PokeAPI CSVs into `raw`, apply the Gen 3 correction layer, add the
decomp-derived tables (map sections, trainers, TM locations, tutors), drop `raw`
and write the file. Every table a tool reads carries a `source_id` per row.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb

from build import decomp, gen3_corrections, parse_decomp_trainers, tm_locations
from build.fetch_sources import CACHE, LOCK, POKEAPI_CSVS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "emerald.duckdb"
POKEAPI_DIR = CACHE / "pokeapi"
DECOMP_DIR = CACHE / "pokeemerald"

# Sections PokeAPI's Gen 3 location indices don't cover. Underwater areas are filed under the route
# above them; Emerald's Aqua Hideout uses a new section (the old index points at Ruby's Magma Hideout).
MAPSEC_OVERRIDES = {
    "MAPSEC_UNDERWATER_124": ("hoenn-route-124", "underwater"),
    "MAPSEC_UNDERWATER_126": ("hoenn-route-126", "underwater"),
    "MAPSEC_AQUA_HIDEOUT": ("team-aqua-hideout", None),
}


def load_raw(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("CREATE SCHEMA raw")
    for name in POKEAPI_CSVS:
        path = (POKEAPI_DIR / f"{name}.csv").as_posix()
        con.execute(f"CREATE TABLE raw.{name} AS SELECT * FROM read_csv('{path}', header = true, sample_size = -1)")


def build_map_sections(con: duckdb.DuckDBPyConnection) -> None:
    """MAPSEC -> PokeAPI location. MAPSEC names are also the map names in randomizer logs."""
    gen3 = dict(
        con.execute(
            "SELECT g.game_index, l.identifier FROM raw.location_game_indices g "
            "JOIN raw.locations l ON l.id = g.location_id WHERE g.generation_id = 3"
        ).fetchall()
    )
    rows = []
    for sec in decomp.map_sections(DECOMP_DIR):
        location, area = MAPSEC_OVERRIDES.get(sec["id"], (gen3.get(sec["index"]), None))
        rows.append((sec["id"], sec["index"], sec["name"], location, area))
    con.execute(
        "CREATE TABLE map_sections (mapsec VARCHAR PRIMARY KEY, mapsec_index INTEGER, name VARCHAR, location VARCHAR, area VARCHAR)"
    )
    con.executemany("INSERT INTO map_sections VALUES (?, ?, ?, ?, ?)", rows)


def build_meta(con: duckdb.DuckDBPyConnection) -> None:
    lock = json.loads(LOCK.read_text())
    con.execute("CREATE TABLE build_info (key VARCHAR PRIMARY KEY, value VARCHAR)")
    con.executemany(
        "INSERT INTO build_info VALUES (?, ?)",
        [
            ("built_at", datetime.now(timezone.utc).isoformat(timespec="seconds")),
            ("pokeapi_sha", lock["pokeapi"]["sha"]),
            ("pokeemerald_sha", lock["pokeemerald"]["sha"]),
        ],
    )


def main() -> None:
    if not (POKEAPI_DIR / ".sha").exists() or not (DECOMP_DIR / ".git").exists():
        sys.exit("raw sources missing; run `uv run python build/fetch_sources.py` first")

    # Build in memory and copy out only the final tables, so the file doesn't keep raw's pages.
    con = duckdb.connect()
    load_raw(con)
    gen3_corrections.apply(con)
    gen3_corrections.reconcile_moves_with_rom(con, DECOMP_DIR)
    build_map_sections(con)
    gen3_corrections.reconcile_statics_with_rom(con, DECOMP_DIR)
    parse_decomp_trainers.build(con, DECOMP_DIR)
    tm_locations.build(con, DECOMP_DIR)
    build_meta(con)
    con.execute("DROP SCHEMA raw CASCADE")

    tables = [t for (t,) in con.execute(
        "SELECT table_name FROM duckdb_tables() WHERE database_name = 'memory' AND schema_name = 'main' ORDER BY 1"
    ).fetchall()]
    for table in tables:
        (n,) = con.execute(f"SELECT count(*) FROM {table}").fetchone()
        print(f"{table:16s} {n:6d}")

    tmp = OUT.with_suffix(".tmp.duckdb")
    tmp.unlink(missing_ok=True)
    con.execute(f"ATTACH '{tmp.as_posix()}' AS out")
    con.execute("COPY FROM DATABASE memory TO out")
    con.execute("DETACH out")
    con.close()
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
