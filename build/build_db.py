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

    sections = {r[0]: (r[3], r[4]) for r in rows}
    map_rows = [
        (map_id, m["folder"], m["region_map_section"], *sections.get(m["region_map_section"], (None, None)))
        for map_id, m in sorted(decomp.maps(DECOMP_DIR).items())
    ]
    con.execute("CREATE TABLE maps (map VARCHAR PRIMARY KEY, folder VARCHAR, mapsec VARCHAR, location VARCHAR, area VARCHAR)")
    con.executemany("INSERT INTO maps VALUES (?, ?, ?, ?, ?)", map_rows)


def build_wild_headers(con: duckdb.DuckDBPyConnection) -> None:
    """gWildMonHeaders in ROM order, one row per (header, method). Randomizer logs list wild
    sets in this order, which lets the log parser pin each set to an exact map."""
    rows, n = [], 0
    for i, header in enumerate(decomp.wild_headers(DECOMP_DIR)):
        for key, method in (("land_mons", "Grass/Cave"), ("water_mons", "Surfing"), ("rock_smash_mons", "Rock Smash"), ("fishing_mons", "Fishing")):
            if key in header:
                n += 1
                rows.append((n, i, header["map"], header["base_label"], method, header[key]["encounter_rate"], len(header[key]["mons"])))
    con.execute(
        "CREATE TABLE wild_headers (set_no INTEGER PRIMARY KEY, header_index INTEGER, map VARCHAR, base_label VARCHAR, "
        "method VARCHAR, rate INTEGER, slots INTEGER)"
    )
    con.executemany("INSERT INTO wild_headers VALUES (?, ?, ?, ?, ?, ?, ?)", rows)


def add_rom_names(con: duckdb.DuckDBPyConnection) -> None:
    """Names as the Emerald ROM spells them ("FAINT ATTACK", "NIDORAN♀"). Randomizer logs use these."""
    tables = [
        ("species", "species_id", decomp.national_dex(DECOMP_DIR), "src/data/text/species_names.h"),
        ("moves", "move_id", decomp.move_ids(DECOMP_DIR), "src/data/text/move_names.h"),
    ]
    for table, key, ids, rel in tables:
        con.execute(f"ALTER TABLE {table} ADD COLUMN rom_name VARCHAR")
        rows = [(name, ids[const]) for const, name in decomp.rom_names(DECOMP_DIR, rel).items() if const in ids]
        con.executemany(f"UPDATE {table} SET rom_name = ? WHERE {key} = ?", rows)
    con.execute("ALTER TABLE abilities ADD COLUMN rom_name VARCHAR")
    rows = [
        (name, decomp.ability_identifier(const))
        for const, name in decomp.rom_names(DECOMP_DIR, "src/data/text/abilities.h").items()
        if const.startswith("ABILITY_")
    ]
    con.executemany("UPDATE abilities SET rom_name = ? WHERE identifier = ?", rows)
    for table in ("species", "moves", "abilities"):
        (missing,) = con.execute(f"SELECT count(*) FROM {table} WHERE rom_name IS NULL").fetchone()
        assert missing == 0, f"{missing} {table} rows without a ROM name"


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
    gen3_corrections.reconcile_evolutions_with_rom(con, DECOMP_DIR)
    add_rom_names(con)
    build_wild_headers(con)
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
