"""Randomizer overlays as session views: once a log is loaded, the session's own database
shadows the vanilla tables it changed, so every tool and the Verifier read the randomized
game unchanged (PLAN.md §4.5, docs/decisions.md D11).

The session connection's search path is `memory.main, base.main`, so a view or table named
`encounters` in memory.main hides base.encounters for that session only (views also resolve
unqualified names in memory.main first). Kinds of data the log changed but the parser can't
read (level-up movesets, TM compatibility, move data) aren't shadowed: `RandomizerLog.vanilla_ok`
is false for them, and the tools refuse rather than answer from vanilla.
"""

import duckdb

from agent.randomizer_log import RandomizerLog

WILD_METHODS = ("walk", "surf", "old-rod", "good-rod", "super-rod", "rock-smash", "seaweed")
# Rows UPR's "Static Pokemon" can change (legendaries, gifts, the egg, Kecleon, Sudowoodo, roamers);
# in-game trades are their own section, and the Feebas tiles and JP bonus disc aren't randomized.
STATIC_METHODS = ("static", "gift", "gift-egg", "devon-scope", "wailmer-pail", "roaming-grass", "roaming-water", "pokeflute")
VANILLA_STARTERS = ("treecko", "torchic", "mudkip")  # gStarterMons order, which UPR's "Set starter N" follows
# Overlay slots are 0-based over the whole set (fishing is one 10-slot table: Old 0-1, Good 2-4,
# Super 5-9); the vanilla table numbers slots from 1 within each method.
SLOT_SQL = "CASE o.method WHEN 'good-rod' THEN o.slot - 1 WHEN 'super-rod' THEN o.slot - 4 ELSE o.slot + 1 END"
RARITY_SQL = f"""CASE o.method
    WHEN 'walk' THEN [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1][{SLOT_SQL}]
    WHEN 'old-rod' THEN [70, 30][{SLOT_SQL}]
    WHEN 'good-rod' THEN [60, 20, 20][{SLOT_SQL}]
    WHEN 'super-rod' THEN [40, 40, 15, 4, 1][{SLOT_SQL}]
    ELSE [60, 30, 5, 4, 1][{SLOT_SQL}] END"""
# The log's targets for a multi-evolution species come in evolution.h order, which is dex order
# except for these two (src/data/pokemon/evolution.h at the pinned decomp sha).
ROM_EVOLUTION_ORDER = {
    "eevee": ["jolteon", "vaporeon", "flareon", "espeon", "umbreon"],
    "tyrogue": ["hitmonchan", "hitmonlee", "hitmontop"],
}
UNKNOWN_PLACE = "log-static-place-unknown"  # one vanilla species, several randomized ones: which is where is unknown


def ident(text: str | None) -> str | None:
    """UPR's display names ("Oran Berry", "SWIFT SWIM") as table identifiers (oran-berry, swift-swim)."""
    return text.strip().lower().replace(" ", "-") if text else None


def install(con: duckdb.DuckDBPyConnection, log: RandomizerLog, log_id: str) -> list[str]:
    """Create the session views for what the log changed and the parser read; returns the tables shadowed.
    Expects `load_overlay(con, log, log_id)` to have run."""
    q = log_id.replace("'", "''")
    changes = log.changes
    shadowed = []

    if changes.get("evolutions") == "parsed" or log.evolution_updates or log.friendship_threshold:
        install_evolutions(con, log)
        shadowed.append("evolutions")
    # Chains decide the dupes clause; random evolutions regroup them
    chains = "memory.main.log_chains" if changes.get("evolutions") == "parsed" else "(SELECT NULL::INTEGER AS species_id, NULL::INTEGER AS chain_id, NULL::INTEGER AS evolves_from)"
    if changes.get("base_stats") == "parsed" or changes.get("evolutions") == "parsed":
        con.execute("CREATE OR REPLACE TABLE memory.main.log_species AS SELECT * FROM overlay_species WHERE log_id = ?", [log_id])
        con.execute("UPDATE memory.main.log_species SET ability1 = lower(replace(trim(ability1), ' ', '-')), "
                    "ability2 = lower(replace(trim(ability2), ' ', '-'))")
        stats = ("hp", "attack", "defense", "sp_attack", "sp_defense", "speed")
        con.execute(f"""
            CREATE OR REPLACE VIEW memory.main.species AS
            SELECT b.species_id, b.identifier, b.name, b.generation,
                   coalesce(o.type1, b.type1) AS type1, CASE WHEN o.type1 IS NULL THEN b.type2 ELSE o.type2 END AS type2,
                   {", ".join(f"coalesce(o.{c}, b.{c}) AS {c}" for c in stats)},
                   {" + ".join(f"coalesce(o.{c}, b.{c})" for c in stats)} AS bst,
                   coalesce(o.ability1, b.ability1) AS ability1,
                   CASE WHEN o.ability1 IS NULL THEN b.ability2 ELSE o.ability2 END AS ability2,
                   b.capture_rate, b.gender_rate, b.growth_rate, b.egg_groups,
                   CASE WHEN c.species_id IS NULL THEN b.evolves_from_species_id ELSE c.evolves_from END AS evolves_from_species_id,
                   coalesce(c.chain_id, b.evolution_chain_id) AS evolution_chain_id,
                   b.is_legendary, b.is_mythical, coalesce(o.source_id, b.source_id) AS source_id, b.rom_name
            FROM base.species b LEFT JOIN memory.main.log_species o USING (species_id)
            LEFT JOIN {chains} c ON c.species_id = b.species_id
        """)
        shadowed.append("species")
    species = "memory.main.species" if "species" in shadowed else "base.species"

    wild = changes.get("wild") == "parsed"
    trades = changes.get("trades", "unchanged") != "unchanged"
    if wild or log.statics or log.starters or trades:
        install_remaps(con, log, log_id)
        con.execute(f"""
            CREATE OR REPLACE VIEW memory.main.encounters AS
            SELECT NULL::INTEGER AS encounter_id, o.location, o.area, o.method, {SLOT_SQL} AS slot, {RARITY_SQL} AS rarity,
                   o.species_id, o.min_level, o.max_level, []::VARCHAR[] AS conditions, o.source_id
            FROM overlay_encounters o WHERE {str(wild).upper()} AND o.log_id = '{q}' AND o.location IS NOT NULL
            UNION ALL
            SELECT e.encounter_id, e.location, e.area, e.method, e.slot, e.rarity, coalesce(r.species_id, e.species_id),
                   e.min_level, e.max_level, CASE WHEN r.ambiguous THEN list_append(e.conditions, '{UNKNOWN_PLACE}') ELSE e.conditions END,
                   coalesce(r.source_id, e.source_id)
            FROM base.encounters e
            LEFT JOIN memory.main.log_remap r ON r.vanilla_species_id = e.species_id AND (
                (r.kind = 'starter' AND e.method = 'gift' AND e.location = 'hoenn-route-101')
                OR (r.kind = 'static' AND e.method IN {STATIC_METHODS} AND NOT (e.method = 'gift' AND e.location = 'hoenn-route-101')))
            WHERE NOT ({str(wild).upper()} AND e.method IN {WILD_METHODS}) AND NOT ({str(trades).upper()} AND e.method = 'npc-trade')
        """)
        shadowed.append("encounters")

    if changes.get("trainers") == "parsed":
        con.execute(f"""
            CREATE OR REPLACE VIEW memory.main.trainer_mons AS
            SELECT o.trainer_id, o.trainer_const, o.slot, o.species_id, s.identifier AS species, o.level,
                   lower(replace(trim(o.held_item), ' ', '-')) AS held_item, coalesce(o.moves, []::VARCHAR[]) AS moves,
                   CASE WHEN o.moves IS NULL THEN 'unknown (the log has no movesets)' ELSE 'log' END AS moves_source,
                   b.iv, b.iv_value, o.source_id, coalesce(lower(replace(trim(o.ability), ' ', '-')), s.ability1) AS ability
            FROM overlay_trainer_mons o JOIN {species} s USING (species_id)
            LEFT JOIN base.trainer_mons b ON b.trainer_const = o.trainer_const AND b.slot = o.slot
            WHERE o.log_id = '{q}' AND o.trainer_const IS NOT NULL
            UNION ALL
            SELECT * FROM base.trainer_mons
            WHERE trainer_const NOT IN (SELECT trainer_const FROM overlay_trainer_mons WHERE log_id = '{q}' AND trainer_const IS NOT NULL)
        """)
        shadowed.append("trainer_mons")

    tms, tutors = changes.get("tm_moves") == "parsed", changes.get("move_tutors") == "parsed"
    if tms or tutors:
        install_move_remap(con, log, log_id)
        if tms:
            con.execute("""
                CREATE OR REPLACE VIEW memory.main.machines AS
                SELECT b.label, b.machine_number, coalesce(r.new_move_id, b.move_id) AS move_id, b.item,
                       coalesce(r.source_id, b.source_id) AS source_id
                FROM base.machines b LEFT JOIN memory.main.log_move_remap r ON r.kind = 'machine' AND r.old_move_id = b.move_id
            """)
            shadowed.append("machines")
        if tutors:
            con.execute("""
                CREATE OR REPLACE VIEW memory.main.move_tutors AS
                SELECT coalesce(r.new_move_id, t.move_id) AS move_id, t.map, t.map_folder, t.mapsec, t.location, t.one_time,
                       coalesce(r.source_id, t.source_id) AS source_id
                FROM base.move_tutors t LEFT JOIN memory.main.log_move_remap r ON r.kind = 'tutor' AND r.old_move_id = t.move_id
            """)
            shadowed.append("move_tutors")
        # UPR keeps compatibility with the TM or tutor slot, so a species that could learn TM01
        # learns its new move (if compatibility was randomized too, that section is unread and refused).
        con.execute("""
            CREATE OR REPLACE VIEW memory.main.learnsets AS
            SELECT l.species_id, coalesce(r.new_move_id, l.move_id) AS move_id, l.method, l.level, l.level_order,
                   coalesce(r.source_id, l.source_id) AS source_id
            FROM base.learnsets l LEFT JOIN memory.main.log_move_remap r ON r.kind = l.method AND r.old_move_id = l.move_id
        """)
        shadowed.append("learnsets")
    return shadowed


def install_move_remap(con: duckdb.DuckDBPyConnection, log: RandomizerLog, log_id: str) -> None:
    """Vanilla move -> randomized move for each TM and Hoenn tutor the log changed."""
    move_ids = dict(con.execute("SELECT identifier, move_id FROM base.moves").fetchall())
    tm_moves = dict(con.execute("SELECT label, move_id FROM base.machines").fetchall())
    rows = [("machine", tm_moves[label], move_ids[new], f"log:tm#{label}") for label, new in log.tm_moves.items()
            if label in tm_moves and new in move_ids]
    rows += [("tutor", move_ids[old], move_ids[new], f"log:tutors#{old}") for old, new in log.move_tutors
             if old in move_ids and new in move_ids]
    con.execute("CREATE OR REPLACE TABLE memory.main.log_move_remap (kind VARCHAR, old_move_id INTEGER, "
                "new_move_id INTEGER, source_id VARCHAR)")
    if rows:
        con.executemany("INSERT INTO memory.main.log_move_remap VALUES (?, ?, ?, ?)", rows)


def install_remaps(con: duckdb.DuckDBPyConnection, log: RandomizerLog, log_id: str) -> None:
    """Vanilla species -> randomized species for the starters and the static encounters."""
    ids = dict(con.execute("SELECT identifier, species_id FROM base.species").fetchall())
    counts = dict(con.execute(
        f"SELECT species_id, count(*) FROM base.encounters WHERE method IN {STATIC_METHODS} GROUP BY 1"
    ).fetchall())
    rows = [("starter", ids[old], ids[new], f"log:starters#{i}", False)
            for i, (old, new) in enumerate(zip(VANILLA_STARTERS, log.starters), 1)]
    options: dict[str, list[str]] = {}
    for old, new in log.statics:
        if new not in options.setdefault(old, []):
            options[old].append(new)
    for old, news in options.items():
        ambiguous = len(news) > 1 and counts.get(ids[old], 0) > 1
        rows += [("static", ids[old], ids[new], f"log:statics#{old}", ambiguous) for new in news]
    con.execute("CREATE OR REPLACE TABLE memory.main.log_remap (kind VARCHAR, vanilla_species_id INTEGER, "
                "species_id INTEGER, source_id VARCHAR, ambiguous BOOLEAN)")
    if rows:
        con.executemany("INSERT INTO memory.main.log_remap VALUES (?, ?, ?, ?, ?)", rows)


CONDITION_COLUMNS = ("min_level", "item", "held_item", "min_happiness", "min_beauty", "time_of_day", "relative_physical_stats")


def install_evolutions(con: duckdb.DuckDBPyConnection, log: RandomizerLog) -> None:
    """A session copy of the evolution table. UPR's random evolutions change each evolution's
    target and keep its method, so the log's targets take the vanilla methods by position;
    UPR's method changes ("Making Evolutions Easier" and friends) are applied on top."""
    cols = [r[0] for r in con.execute("DESCRIBE base.evolutions").fetchall()]
    ids = dict(con.execute("SELECT identifier, species_id FROM base.species").fetchall())
    names = {v: k for k, v in ids.items()}
    rows = [dict(zip(cols, r)) for r in con.execute("SELECT * FROM base.evolutions ORDER BY from_species_id, to_species_id").fetchall()]
    if log.evolutions:
        by_from: dict[int, list[dict]] = {}
        for r in rows:
            by_from.setdefault(r["from_species_id"], []).append(r)
        for src, order in ROM_EVOLUTION_ORDER.items():
            by_from[ids[src]].sort(key=lambda r: order.index(names[r["to_species_id"]]))
        out = []
        for src, targets in log.evolutions.items():
            vanilla = by_from.pop(ids[src], [])
            for i, dst in enumerate(targets):
                row = dict(vanilla[min(i, len(vanilla) - 1)]) if vanilla else {c: None for c in cols} | {"trigger": "level-up", "needs_trade": False}
                row.update(from_species_id=ids[src], to_species_id=ids[dst], source_id=f"log:evolutions#{src}")
                out.append(row)
        rows = out + [r for rs in by_from.values() for r in rs]
    threshold = log.friendship_threshold
    for u in log.evolution_updates:
        if not (u.src and u.dst) or u.overwritten:
            continue
        for r in rows:
            if (r["from_species_id"], r["to_species_id"]) != (ids[u.src], ids[u.dst]):
                continue
            how = u.how.lower()
            if how.startswith(("at level", "at minimum level", "using a", "by reaching high happiness")):
                r.update({c: None for c in CONDITION_COLUMNS}, trigger="level-up", needs_trade=False)
                if how.startswith("using a"):
                    r.update(trigger="use-item", item=ident(u.how.split(" ", 2)[2]))
                elif how.startswith("by reaching"):
                    r["min_happiness"] = threshold or 220
                else:
                    r["min_level"] = int(how.split()[-1])
            r["source_id"] = f"log:evolution_updates#{u.src}"
            r["note"] = f"changed by the randomizer: {u.how}"
    if threshold:
        for r in rows:
            if r["min_happiness"] is not None:
                r["min_happiness"] = threshold
    con.execute("CREATE OR REPLACE TABLE memory.main.evolutions AS SELECT * FROM base.evolutions LIMIT 0")
    if rows:
        con.executemany(f"INSERT INTO memory.main.evolutions VALUES ({', '.join('?' * len(cols))})",
                        [[r[c] for c in cols] for r in rows])
    if log.evolutions:
        install_chains(con, rows, list(ids.values()))


def install_chains(con: duckdb.DuckDBPyConnection, evolutions: list[dict], species_ids: list[int]) -> None:
    """Evolution families from the randomized evolutions (a union-find over its edges): the chain
    id is the family's lowest species id, which only has to be equal within a family."""
    parent = {s: s for s in species_ids}

    def root(s: int) -> int:
        while parent[s] != s:
            parent[s] = parent[parent[s]]
            s = parent[s]
        return s

    evolves_from = {}
    for r in evolutions:
        a, b = root(r["from_species_id"]), root(r["to_species_id"])
        parent[max(a, b)] = min(a, b)
        evolves_from.setdefault(r["to_species_id"], r["from_species_id"])
    con.execute("CREATE OR REPLACE TABLE memory.main.log_chains (species_id INTEGER, chain_id INTEGER, evolves_from INTEGER)")
    con.executemany("INSERT INTO memory.main.log_chains VALUES (?, ?, ?)",
                    [(s, root(s), evolves_from.get(s)) for s in species_ids])


SHADOW_NAMES = ("encounters", "trainer_mons", "species", "machines", "move_tutors", "learnsets", "evolutions",
                "log_species", "log_chains", "log_remap", "log_move_remap")
# What a log can change that LockeSmith doesn't read; tools refuse these (agent/tools/common.py `unread`)
UNREAD_KINDS = {
    "movesets": "level-up movesets",
    "tm_compatibility": "TM/HM compatibility",
    "tutor_compatibility": "move tutor compatibility",
    "move_data": "move data (power, type, accuracy)",
    "trades": "in-game trades",
    "shops": "shop items",
    "pickup_items": "Pickup items",
}


def summary(log: RandomizerLog, log_id: str, shadowed: list[str]) -> dict:
    """What the session now knows about the run, for the brief, the tools and the upload's reply."""
    changes = log.changes
    unread = {k: v for k, v in changes.items() if v in ("unparsed", "metronome-only")}
    return {
        "log_id": log_id,
        "seed": log.header.get("Random Seed"),
        "randomizer_version": log.header.get("Randomizer Version"),
        "changes": changes,
        "shadowed": shadowed,
        "unread": {k: UNREAD_KINDS.get(k, k) + (" (Metronome only)" if v == "metronome-only" else "") for k, v in unread.items()},
        "starters": dict(zip(VANILLA_STARTERS, log.starters)),
        "friendship_threshold": log.friendship_threshold,
        "warnings": log.warnings[:20],
        "warning_count": len(log.warnings),
    }


def uninstall(con: duckdb.DuckDBPyConnection) -> None:
    """Drop a previous log's views and tables, so the session reads vanilla again."""
    for name, kind in con.execute(
        "SELECT view_name, 'VIEW' FROM duckdb_views() WHERE database_name = 'memory' AND NOT internal "
        "UNION ALL SELECT table_name, 'TABLE' FROM duckdb_tables() WHERE database_name = 'memory'"
    ).fetchall():
        if name in SHADOW_NAMES:
            con.execute(f"DROP {kind} IF EXISTS memory.main.{name}")
