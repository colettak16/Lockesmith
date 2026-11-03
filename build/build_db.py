"""Build one database per game (data/emerald.duckdb, data/ruby.duckdb, data/sapphire.duckdb).

    uv run python build/fetch_sources.py              # once, or after changing data/sources.lock.json
    uv run python build/build_db.py                   # all three games
    uv run python build/build_db.py --game ruby       # one game

Steps: load PokeAPI CSVs into `raw`, apply the Gen 3 correction layer for the game's
PokeAPI version, add the decomp-derived tables (map sections, trainers, TM locations,
tutors), drop `raw` and write the file. Every table a tool reads carries a `source_id`
per row. Emerald comes from pokeemerald; Ruby and Sapphire from pokeruby, each with its
own wild tables, script branches and aliases (agent/games.py, docs/decisions.md D13).
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb

from agent.games import GAMES, Game
from build import decomp, gen3_corrections, parse_decomp_trainers, tm_locations
from build.fetch_sources import CACHE, LOCK, POKEAPI_CSVS

ROOT = Path(__file__).resolve().parent.parent
POKEAPI_DIR = CACHE / "pokeapi"

# Sections PokeAPI's Gen 3 location indices don't cover, or cover ambiguously. Underwater
# areas are filed under the route above them. Emerald's Aqua Hideout uses a new section (the
# old index points at Ruby's Magma Hideout). In Ruby/Sapphire one section holds whichever
# hideout the version has; pokeruby's UNDERWATER_125 is the map under Route 126 (its dive
# connection, and how PokeAPI files it); index 58 is the Battle Tower, not the Frontier.
MAPSEC_OVERRIDES = {
    "emerald": {
        "MAPSEC_UNDERWATER_124": ("hoenn-route-124", "underwater"),
        "MAPSEC_UNDERWATER_126": ("hoenn-route-126", "underwater"),
        "MAPSEC_AQUA_HIDEOUT": ("team-aqua-hideout", None),
    },
    "ruby": {
        "MAPSEC_UNDERWATER_124": ("hoenn-route-124", "underwater"),
        "MAPSEC_UNDERWATER_125": ("hoenn-route-126", "underwater"),
        "MAPSEC_EVIL_TEAM_HIDEOUT": ("team-magma-hideout", None),
        "MAPSEC_BATTLE_TOWER": ("hoenn-battle-tower", None),
    },
    "sapphire": {
        "MAPSEC_UNDERWATER_124": ("hoenn-route-124", "underwater"),
        "MAPSEC_UNDERWATER_125": ("hoenn-route-126", "underwater"),
        "MAPSEC_EVIL_TEAM_HIDEOUT": ("team-aqua-hideout", None),
        "MAPSEC_BATTLE_TOWER": ("hoenn-battle-tower", None),
    },
}


def decomp_dir(game: Game) -> Path:
    return CACHE / game.decomp


def load_raw(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("CREATE SCHEMA raw")
    for name in POKEAPI_CSVS:
        path = (POKEAPI_DIR / f"{name}.csv").as_posix()
        con.execute(f"CREATE TABLE raw.{name} AS SELECT * FROM read_csv('{path}', header = true, sample_size = -1)")


def build_map_sections(con: duckdb.DuckDBPyConnection, game: Game) -> None:
    """MAPSEC -> PokeAPI location. MAPSEC names are also the map names in randomizer logs."""
    gen3 = dict(
        con.execute(
            "SELECT g.game_index, l.identifier FROM raw.location_game_indices g "
            "JOIN raw.locations l ON l.id = g.location_id WHERE g.generation_id = 3"
        ).fetchall()
    )
    overrides = MAPSEC_OVERRIDES[game.id]
    # pokeruby's hideout section is "{EVIL_TEAM} HIDEOUT", filled in with the version's team.
    team = {"RUBY": "MAGMA", "SAPPHIRE": "AQUA"}.get(game.rom_version, "")
    rows = []
    for sec in decomp.map_sections(decomp_dir(game)):
        location, area = overrides.get(sec["id"], (gen3.get(sec["index"]), None))
        rows.append((sec["id"], sec["index"], sec["name"].replace("{EVIL_TEAM}", team), location, area))
    con.execute(
        "CREATE TABLE map_sections (mapsec VARCHAR PRIMARY KEY, mapsec_index INTEGER, name VARCHAR, location VARCHAR, area VARCHAR)"
    )
    con.executemany("INSERT INTO map_sections VALUES (?, ?, ?, ?, ?)", rows)

    sections = {r[0]: (r[3], r[4]) for r in rows}
    map_rows = [
        (map_id, m["folder"], m["region_map_section"], *sections.get(m["region_map_section"], (None, None)))
        for map_id, m in sorted(decomp.maps(decomp_dir(game), game.rom_version).items())
    ]
    con.execute("CREATE TABLE maps (map VARCHAR PRIMARY KEY, folder VARCHAR, mapsec VARCHAR, location VARCHAR, area VARCHAR)")
    con.executemany("INSERT INTO maps VALUES (?, ?, ?, ?, ?)", map_rows)


def build_wild_headers(con: duckdb.DuckDBPyConnection, game: Game) -> None:
    """gWildMonHeaders in ROM order, one row per (header, method). Randomizer logs list wild
    sets in this order, which lets the log parser pin each set to an exact map."""
    rows, n = [], 0
    for i, header in enumerate(decomp.wild_headers(decomp_dir(game), game.rom_version)):
        for key, method in (("land_mons", "Grass/Cave"), ("water_mons", "Surfing"), ("rock_smash_mons", "Rock Smash"), ("fishing_mons", "Fishing")):
            if key in header:
                n += 1
                rows.append((n, i, header["map"], header["base_label"], method, header[key]["encounter_rate"], len(header[key]["mons"])))
    con.execute(
        "CREATE TABLE wild_headers (set_no INTEGER PRIMARY KEY, header_index INTEGER, map VARCHAR, base_label VARCHAR, "
        "method VARCHAR, rate INTEGER, slots INTEGER)"
    )
    con.executemany("INSERT INTO wild_headers VALUES (?, ?, ?, ?, ?, ?, ?)", rows)


def add_rom_names(con: duckdb.DuckDBPyConnection, game: Game) -> None:
    """Names as the ROM spells them ("FAINT ATTACK", "NIDORAN♀"). Randomizer logs use these."""
    d = decomp_dir(game)
    names = decomp.rom_name_tables(d)
    tables = [
        ("species", "species_id", decomp.national_dex(d), names["species"]),
        ("moves", "move_id", decomp.move_ids(d), names["moves"]),
    ]
    for table, key, ids, rom in tables:
        con.execute(f"ALTER TABLE {table} ADD COLUMN rom_name VARCHAR")
        rows = [(name, ids[const]) for const, name in rom.items() if const in ids]
        con.executemany(f"UPDATE {table} SET rom_name = ? WHERE {key} = ?", rows)
    con.execute("ALTER TABLE abilities ADD COLUMN rom_name VARCHAR")
    rows = [(name, decomp.ability_identifier(const)) for const, name in names["abilities"].items() if const.startswith("ABILITY_")]
    con.executemany("UPDATE abilities SET rom_name = ? WHERE identifier = ?", rows)
    for table in ("species", "moves", "abilities"):
        (missing,) = con.execute(f"SELECT count(*) FROM {table} WHERE rom_name IS NULL").fetchone()
        assert missing == 0, f"{missing} {table} rows without a ROM name"


def check_items(con: duckdb.DuckDBPyConnection) -> None:
    """Every held or bag item the decomp names must be a PokeAPI item (catches constant renames)."""
    known = {i for (i,) in con.execute("SELECT identifier FROM raw.items").fetchall()}
    used = {i for (i,) in con.execute("SELECT DISTINCT held_item FROM trainer_mons WHERE held_item IS NOT NULL").fetchall()}
    used |= {i for (items,) in con.execute("SELECT items FROM trainers").fetchall() for i in items}
    unknown = sorted(used - known)
    assert not unknown, f"trainer items with no PokeAPI identifier: {unknown}"


def build_meta(con: duckdb.DuckDBPyConnection, game: Game) -> None:
    lock = json.loads(LOCK.read_text())
    con.execute("CREATE TABLE build_info (key VARCHAR PRIMARY KEY, value VARCHAR)")
    con.executemany(
        "INSERT INTO build_info VALUES (?, ?)",
        [
            ("built_at", datetime.now(timezone.utc).isoformat(timespec="seconds")),
            ("game", game.id),
            ("pokeapi_sha", lock["pokeapi"]["sha"]),
            (f"{game.decomp}_sha", lock[game.decomp]["sha"]),
        ],
    )


def build(game: Game) -> None:
    d = decomp_dir(game)
    if not (POKEAPI_DIR / ".sha").exists() or not (d / ".git").exists():
        sys.exit("raw sources missing; run `uv run python build/fetch_sources.py` first")

    # Build in memory and copy out only the final tables, so the file doesn't keep raw's pages.
    con = duckdb.connect()
    load_raw(con)
    gen3_corrections.apply(con, game)
    gen3_corrections.reconcile_moves_with_rom(con, d)
    build_map_sections(con, game)
    gen3_corrections.reconcile_statics_with_rom(con, d, game)
    gen3_corrections.reconcile_evolutions_with_rom(con, d)
    gen3_corrections.add_rom_conditions(con, d, game)
    add_rom_names(con, game)
    build_wild_headers(con, game)
    parse_decomp_trainers.build(con, d)
    check_items(con)
    tm_locations.build(con, d, game.rom_version)
    build_meta(con, game)
    con.execute("DROP SCHEMA raw CASCADE")

    tables = [t for (t,) in con.execute(
        "SELECT table_name FROM duckdb_tables() WHERE database_name = 'memory' AND schema_name = 'main' ORDER BY 1"
    ).fetchall()]
    print(f"== {game.name}")
    for table in tables:
        (n,) = con.execute(f"SELECT count(*) FROM {table}").fetchone()
        print(f"{table:16s} {n:6d}")

    out = game.db_path
    tmp = out.with_suffix(".tmp.duckdb")
    tmp.unlink(missing_ok=True)
    con.execute(f"ATTACH '{tmp.as_posix()}' AS out")
    con.execute("COPY FROM DATABASE memory TO out")
    con.execute("DETACH out")
    con.close()
    tmp.replace(out)
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", choices=[*GAMES, "all"], default="all")
    args = ap.parse_args()
    for game in GAMES.values() if args.game == "all" else [GAMES[args.game]]:
        build(game)


if __name__ == "__main__":
    main()
