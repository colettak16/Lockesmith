"""Gen 3 correction layer: PokeAPI's modern tables -> Emerald-accurate tables.

Expects the PokeAPI CSVs loaded into schema `raw` (see build_db.load_raw) and
creates the corrected tables in `main`. PLAN.md section 4.2 lists the rules; each
function below says which one it implements.

PokeAPI's *_past tables record a value together with the last generation it
applied in. So for Gen 3 we take, per key, the row with the smallest
generation_id >= 3, and fall back to the current value when there isn't one.
"""

import re
from pathlib import Path

import duckdb

from build import decomp

GEN = 3
EMERALD_VERSION_ID = 9
EMERALD_VERSION_GROUP_ID = 6
ENGLISH = 9
MAX_SPECIES = 386

# Before Gen 4 a move's damage class came from its type (PLAN.md 4.2).
PHYSICAL_TYPES = ("normal", "fighting", "flying", "poison", "ground", "rock", "bug", "ghost", "steel")
# Moves whose type is set in battle (dynamicMoveType), so their category varies too.
DYNAMIC_TYPE_MOVES = {"hidden-power": "type from the user's IVs", "weather-ball": "type from the weather"}
# Conditions from pokemon.c (GetEvolutionTargetSpecies) and evolution_scene.c.
EVOLUTION_NOTES = {
    ("wurmple", "silcoon"): "only if (personality >> 16) % 10 <= 4",
    ("wurmple", "cascoon"): "only if (personality >> 16) % 10 > 4",
    ("nincada", "shedinja"): "appears when Nincada evolves into Ninjask with an empty party slot (no Poke Ball needed in Gen 3)",
}
SPECIAL_TYPES = ("fire", "water", "grass", "electric", "psychic", "ice", "dragon", "dark")
GEN3_TYPES = PHYSICAL_TYPES + SPECIAL_TYPES


def apply(con: duckdb.DuckDBPyConnection) -> None:
    for step in (types, type_efficacy, abilities, species, moves, learnsets, machines, evolutions, locations, encounters):
        step(con)


def types(con):
    """17 types, no Fairy. Gen 3 damage class is a property of the type."""
    con.execute(
        f"""
        CREATE TABLE types AS
        SELECT t.id AS type_id, t.identifier, n.name,
               CASE WHEN t.identifier IN {PHYSICAL_TYPES} THEN 'physical' ELSE 'special' END AS damage_class
        FROM raw.types t
        JOIN raw.type_names n ON n.type_id = t.id AND n.local_language_id = {ENGLISH}
        WHERE t.identifier IN {GEN3_TYPES}
        ORDER BY t.id
        """
    )
    # PokeAPI's own per-type damage class agrees with the rule; fail loudly if that ever changes.
    (disagree,) = con.execute(
        """
        SELECT count(*) FROM types t JOIN raw.types r ON r.id = t.type_id
        JOIN raw.move_damage_classes d ON d.id = r.damage_class_id
        WHERE d.identifier <> t.damage_class
        """
    ).fetchone()
    assert disagree == 0, "PokeAPI types.damage_class_id disagrees with the Gen 3 type split"


def type_efficacy(con):
    """Modern chart minus Fairy, with Gen 2-5 values restored (Steel resists Ghost and Dark)."""
    con.execute(
        f"""
        CREATE TABLE type_efficacy AS
        WITH past AS (
            SELECT damage_type_id, target_type_id, damage_factor,
                   row_number() OVER (PARTITION BY damage_type_id, target_type_id ORDER BY generation_id) AS rn
            FROM raw.type_efficacy_past WHERE generation_id >= {GEN}
        )
        SELECT a.identifier AS attacking_type, d.identifier AS defending_type,
               coalesce(p.damage_factor, e.damage_factor) / 100.0 AS multiplier,
               'rules:gen3_type_chart' AS source_id
        FROM raw.type_efficacy e
        JOIN types a ON a.type_id = e.damage_type_id
        JOIN types d ON d.type_id = e.target_type_id
        LEFT JOIN past p ON p.rn = 1 AND p.damage_type_id = e.damage_type_id AND p.target_type_id = e.target_type_id
        ORDER BY a.type_id, d.type_id
        """
    )


def abilities(con):
    """Abilities introduced in Gen 3 or earlier, with Emerald's in-game description."""
    con.execute(
        f"""
        CREATE TABLE abilities AS
        SELECT a.id AS ability_id, a.identifier, n.name, f.flavor_text AS description
        FROM raw.abilities a
        JOIN raw.ability_names n ON n.ability_id = a.id AND n.local_language_id = {ENGLISH}
        LEFT JOIN raw.ability_flavor_text f
               ON f.ability_id = a.id AND f.version_group_id = {EMERALD_VERSION_GROUP_ID} AND f.language_id = {ENGLISH}
        WHERE a.generation_id <= {GEN} AND a.is_main_series = 1
        ORDER BY a.id
        """
    )


def species(con):
    """National Dex #1-386 with Gen 3 types, base stats and abilities.

    - Types: the whole typing is replaced by the applicable pokemon_types_past rows.
    - Stats: replaced per stat from pokemon_stats_past.
    - Abilities: replaced per slot from pokemon_abilities_past (an empty ability_id
      means the slot was empty), then hidden abilities (slot 3) are dropped.
    - Pre-evolutions added in Gen 4 (Munchlax, Happiny, ...) are cut off.
    """
    con.execute(
        f"""
        CREATE TEMP TABLE gen3_types AS
        WITH past AS (
            SELECT pokemon_id, generation_id, type_id, slot,
                   min(generation_id) OVER (PARTITION BY pokemon_id) AS g
            FROM raw.pokemon_types_past WHERE generation_id >= {GEN}
        )
        SELECT pokemon_id, type_id, slot FROM past WHERE generation_id = g
        UNION ALL
        SELECT pokemon_id, type_id, slot FROM raw.pokemon_types
        WHERE pokemon_id NOT IN (SELECT pokemon_id FROM past)
        """
    )
    con.execute(
        f"""
        CREATE TEMP TABLE gen3_stats AS
        WITH past AS (
            SELECT pokemon_id, stat_id, base_stat,
                   row_number() OVER (PARTITION BY pokemon_id, stat_id ORDER BY generation_id) AS rn
            FROM raw.pokemon_stats_past WHERE generation_id >= {GEN}
        )
        SELECT s.pokemon_id, st.identifier AS stat, coalesce(p.base_stat, s.base_stat) AS base_stat
        FROM raw.pokemon_stats s
        JOIN raw.stats st ON st.id = s.stat_id
        LEFT JOIN past p ON p.rn = 1 AND p.pokemon_id = s.pokemon_id AND p.stat_id = s.stat_id
        """
    )
    con.execute(
        f"""
        CREATE TEMP TABLE gen3_abilities AS
        WITH past AS (
            SELECT pokemon_id, slot, ability_id,
                   row_number() OVER (PARTITION BY pokemon_id, slot ORDER BY generation_id) AS rn
            FROM raw.pokemon_abilities_past WHERE generation_id >= {GEN}
        ),
        slots AS (
            SELECT pokemon_id, slot FROM raw.pokemon_abilities
            UNION SELECT pokemon_id, slot FROM past WHERE rn = 1
        )
        SELECT s.pokemon_id, s.slot,
               CASE WHEN p.pokemon_id IS NOT NULL THEN p.ability_id ELSE c.ability_id END AS ability_id
        FROM slots s
        LEFT JOIN past p ON p.rn = 1 AND p.pokemon_id = s.pokemon_id AND p.slot = s.slot
        LEFT JOIN raw.pokemon_abilities c ON c.pokemon_id = s.pokemon_id AND c.slot = s.slot
        WHERE s.slot IN (1, 2)
        """
    )
    con.execute(
        f"""
        CREATE TABLE species AS
        WITH forms AS (
            SELECT id AS pokemon_id, species_id FROM raw.pokemon WHERE is_default = 1 AND species_id <= {MAX_SPECIES}
        ),
        typ AS (
            SELECT g.pokemon_id,
                   max(t.identifier) FILTER (WHERE g.slot = 1) AS type1,
                   max(t.identifier) FILTER (WHERE g.slot = 2) AS type2
            FROM gen3_types g JOIN types t ON t.type_id = g.type_id GROUP BY 1
        ),
        st AS (
            SELECT pokemon_id,
                   max(base_stat) FILTER (WHERE stat = 'hp') AS hp,
                   max(base_stat) FILTER (WHERE stat = 'attack') AS attack,
                   max(base_stat) FILTER (WHERE stat = 'defense') AS defense,
                   max(base_stat) FILTER (WHERE stat = 'special-attack') AS sp_attack,
                   max(base_stat) FILTER (WHERE stat = 'special-defense') AS sp_defense,
                   max(base_stat) FILTER (WHERE stat = 'speed') AS speed
            FROM gen3_stats GROUP BY 1
        ),
        ab AS (
            SELECT g.pokemon_id,
                   max(a.identifier) FILTER (WHERE g.slot = 1) AS ability1,
                   max(a.identifier) FILTER (WHERE g.slot = 2) AS ability2
            FROM gen3_abilities g JOIN raw.abilities a ON a.id = g.ability_id GROUP BY 1
        ),
        eggs AS (
            SELECT pe.species_id, list(eg.identifier ORDER BY eg.id) AS egg_groups
            FROM raw.pokemon_egg_groups pe JOIN raw.egg_groups eg ON eg.id = pe.egg_group_id GROUP BY 1
        )
        SELECT s.id AS species_id, s.identifier, n.name, s.generation_id AS generation,
               typ.type1, typ.type2,
               st.hp, st.attack, st.defense, st.sp_attack, st.sp_defense, st.speed,
               st.hp + st.attack + st.defense + st.sp_attack + st.sp_defense + st.speed AS bst,
               ab.ability1, ab.ability2,
               s.capture_rate, s.gender_rate, gr.identifier AS growth_rate, eggs.egg_groups,
               CASE WHEN s.evolves_from_species_id <= {MAX_SPECIES} THEN s.evolves_from_species_id END
                   AS evolves_from_species_id,
               s.evolution_chain_id, s.is_legendary = 1 AS is_legendary, s.is_mythical = 1 AS is_mythical,
               'pokeapi:pokemon_species#' || s.id AS source_id
        FROM raw.pokemon_species s
        JOIN forms f ON f.species_id = s.id
        JOIN raw.pokemon_species_names n ON n.pokemon_species_id = s.id AND n.local_language_id = {ENGLISH}
        JOIN typ ON typ.pokemon_id = f.pokemon_id
        JOIN st ON st.pokemon_id = f.pokemon_id
        JOIN ab ON ab.pokemon_id = f.pokemon_id
        LEFT JOIN eggs ON eggs.species_id = s.id
        LEFT JOIN raw.growth_rates gr ON gr.id = s.growth_rate_id
        ORDER BY s.id
        """
    )


def moves(con):
    """Moves #1-354 with post-Gen-3 changes reverted and the type-based damage class.

    move_changelog rows hold the values a move had *before* the version group in
    changed_in_version_group_id. Per field, the earliest change made after Gen 3
    holds the Gen 3 value. Power 1 is PokeAPI's placeholder for variable power.
    """
    fields = ("type_id", "power", "pp", "accuracy", "priority", "target_id", "effect_chance")
    picks = ",\n".join(
        f"arg_min(c.{f}, vg.\"order\") FILTER (WHERE c.{f} IS NOT NULL) AS {f}" for f in fields
    )
    con.execute(
        f"""
        CREATE TEMP TABLE gen3_move_changes AS
        SELECT c.move_id, {picks}
        FROM raw.move_changelog c
        JOIN raw.version_groups vg ON vg.id = c.changed_in_version_group_id
        WHERE vg.generation_id > {GEN}
        GROUP BY c.move_id
        """
    )
    con.execute(
        f"""
        CREATE TABLE moves AS
        WITH m AS (
            SELECT mv.id AS move_id, mv.identifier,
                   coalesce(ch.type_id, mv.type_id) AS type_id,
                   coalesce(ch.power, mv.power) AS power,
                   coalesce(ch.pp, mv.pp) AS pp,
                   coalesce(ch.accuracy, mv.accuracy) AS accuracy,
                   coalesce(ch.priority, mv.priority) AS priority,
                   coalesce(ch.target_id, mv.target_id) AS target_id,
                   coalesce(ch.effect_chance, mv.effect_chance) AS effect_chance,
                   dc.identifier AS modern_class
            FROM raw.moves mv
            JOIN raw.move_damage_classes dc ON dc.id = mv.damage_class_id
            LEFT JOIN gen3_move_changes ch ON ch.move_id = mv.id
            WHERE mv.generation_id <= {GEN} AND mv.id < 10000
        )
        SELECT m.move_id, m.identifier, n.name,
               coalesce(t.identifier, '???') AS type,
               CASE WHEN m.modern_class = 'status' THEN 'status' ELSE t.damage_class END AS damage_class,
               CASE WHEN m.power > 1 THEN m.power END AS power,
               m.accuracy, m.pp, m.priority, m.effect_chance, tg.identifier AS target,
               f.flavor_text AS description,
               'pokeapi:moves#' || m.move_id AS source_id
        FROM m
        JOIN raw.move_names n ON n.move_id = m.move_id AND n.local_language_id = {ENGLISH}
        LEFT JOIN types t ON t.type_id = m.type_id
        LEFT JOIN raw.move_targets tg ON tg.id = m.target_id
        LEFT JOIN raw.move_flavor_text f
               ON f.move_id = m.move_id AND f.version_group_id = {EMERALD_VERSION_GROUP_ID} AND f.language_id = {ENGLISH}
        ORDER BY m.move_id
        """
    )


def learnsets(con):
    """Emerald (version group 6) learnsets: level-up, machine, tutor, egg.

    Normally the default form holds them, but Emerald's Deoxys is the Speed Forme and
    PokeAPI files its Emerald learnset under that form, so take whichever form of each
    species has the most Emerald rows.
    """
    con.execute(
        f"""
        CREATE TABLE learnsets AS
        WITH form_rows AS (
            SELECT p.id AS pokemon_id, p.species_id, p.is_default, count(*) AS n
            FROM raw.pokemon_moves pm JOIN raw.pokemon p ON p.id = pm.pokemon_id
            WHERE pm.version_group_id = {EMERALD_VERSION_GROUP_ID} AND p.species_id <= {MAX_SPECIES}
            GROUP BY 1, 2, 3
        ),
        form AS (
            SELECT species_id, arg_max(pokemon_id, (n, is_default)) AS pokemon_id FROM form_rows GROUP BY 1
        )
        SELECT p.species_id, pm.move_id, mm.identifier AS method,
               CASE WHEN mm.identifier = 'level-up' THEN pm.level END AS level,
               pm."order" AS level_order,
               'pokeapi:pokemon_moves#' || p.species_id || '/' || pm.move_id || '/' || mm.identifier
                   || coalesce('/' || CASE WHEN mm.identifier = 'level-up' THEN pm.level END, '') AS source_id
        FROM raw.pokemon_moves pm
        JOIN form f ON f.pokemon_id = pm.pokemon_id
        JOIN raw.pokemon p ON p.id = pm.pokemon_id
        JOIN raw.pokemon_move_methods mm ON mm.id = pm.pokemon_move_method_id
        WHERE pm.version_group_id = {EMERALD_VERSION_GROUP_ID}
          AND pm.move_id IN (SELECT move_id FROM moves)
        ORDER BY p.species_id, mm.id, level, pm."order", pm.move_id
        """
    )


def machines(con):
    """TM01-TM50 and HM01-HM08 as they are in Emerald."""
    con.execute(
        f"""
        CREATE TABLE machines AS
        SELECT CASE WHEN x.machine_number > 100 THEN 'HM' || lpad(CAST(x.machine_number - 100 AS VARCHAR), 2, '0')
                    ELSE 'TM' || lpad(CAST(x.machine_number AS VARCHAR), 2, '0') END AS label,
               x.machine_number, x.move_id, i.identifier AS item,
               'pokeapi:machines#' || x.machine_number || '/{EMERALD_VERSION_GROUP_ID}' AS source_id
        FROM raw.machines x JOIN raw.items i ON i.id = x.item_id
        WHERE x.version_group_id = {EMERALD_VERSION_GROUP_ID}
        ORDER BY x.machine_number
        """
    )


def evolutions(con):
    """Evolution methods that existed in Gen 3, between Gen 1-3 species.

    pokemon_evolution also carries rows for later games (Alolan Raticate at night,
    Ice Stone Sandslash, Prism Scale Feebas, ...) on the same species ids, so keep
    only rows whose version group is Gen 3 or earlier.
    """
    con.execute(
        f"""
        CREATE TABLE evolutions AS
        SELECT s.evolves_from_species_id AS from_species_id, e.evolved_species_id AS to_species_id,
               tr.identifier AS trigger, e.minimum_level AS min_level,
               ti.identifier AS item, hi.identifier AS held_item,
               e.minimum_happiness AS min_happiness, e.minimum_beauty AS min_beauty,
               nullif(e.time_of_day, '') AS time_of_day, e.relative_physical_stats,
               tr.identifier = 'trade' AS needs_trade,
               'pokeapi:pokemon_evolution#' || e.id AS source_id
        FROM raw.pokemon_evolution e
        JOIN species s ON s.species_id = e.evolved_species_id
        JOIN raw.evolution_triggers tr ON tr.id = e.evolution_trigger_id
        JOIN raw.version_groups vg ON vg.id = e.version_group_id
        LEFT JOIN raw.items ti ON ti.id = e.trigger_item_id
        LEFT JOIN raw.items hi ON hi.id = e.held_item_id
        WHERE s.evolves_from_species_id IS NOT NULL AND vg.generation_id <= {GEN}
        ORDER BY from_species_id, to_species_id
        """
    )


def locations(con):
    """Locations and areas that have Emerald encounters."""
    con.execute(
        f"""
        CREATE TABLE location_areas AS
        SELECT DISTINCT a.id AS area_id, l.identifier AS location, nullif(a.identifier, '') AS area,
               ln.name AS location_name, ap.name AS area_name
        FROM raw.encounters e
        JOIN raw.location_areas a ON a.id = e.location_area_id
        JOIN raw.locations l ON l.id = a.location_id
        LEFT JOIN raw.location_names ln ON ln.location_id = l.id AND ln.local_language_id = {ENGLISH}
        LEFT JOIN raw.location_area_prose ap ON ap.location_area_id = a.id AND ap.local_language_id = {ENGLISH}
        WHERE e.version_id = {EMERALD_VERSION_ID}
        ORDER BY location, area
        """
    )
    con.execute(
        f"""
        CREATE TABLE locations AS
        SELECT DISTINCT l.id AS location_id, l.identifier, ln.name
        FROM raw.locations l
        LEFT JOIN raw.location_names ln ON ln.location_id = l.id AND ln.local_language_id = {ENGLISH}
        WHERE l.identifier IN (SELECT location FROM location_areas)
           OR l.id IN (SELECT location_id FROM raw.location_game_indices WHERE generation_id = {GEN})
        ORDER BY l.identifier
        """
    )


def encounters(con):
    """Every Emerald encounter row (version 9) with its slot rarity and method."""
    con.execute(
        f"""
        CREATE TABLE encounters AS
        WITH cond AS (
            SELECT m.encounter_id, list(v.identifier ORDER BY v.identifier) AS conditions
            FROM raw.encounter_condition_value_map m
            JOIN raw.encounter_condition_values v ON v.id = m.encounter_condition_value_id
            GROUP BY 1
        )
        SELECT e.id AS encounter_id, la.location, la.area, em.identifier AS method,
               es.slot, es.rarity, e.pokemon_id AS species_id, e.min_level, e.max_level,
               coalesce(cond.conditions, []) AS conditions,
               'pokeapi:encounters#' || e.id AS source_id
        FROM raw.encounters e
        JOIN location_areas la ON la.area_id = e.location_area_id
        JOIN raw.encounter_slots es ON es.id = e.encounter_slot_id
        JOIN raw.encounter_methods em ON em.id = es.encounter_method_id
        LEFT JOIN cond ON cond.encounter_id = e.id
        WHERE e.version_id = {EMERALD_VERSION_ID} AND e.pokemon_id <= {MAX_SPECIES}
        ORDER BY la.location, la.area, em.id, es.slot, e.id
        """
    )
    # PokeAPI puts the Hall of Fame and TV-choice conditions only on the roaming-grass rows.
    # The roaming-water rows are the same roaming Latias/Latios, so they share them.
    con.execute(
        """
        UPDATE encounters SET conditions = g.conditions
        FROM (SELECT DISTINCT species_id, conditions FROM encounters WHERE method = 'roaming-grass') g
        WHERE encounters.method = 'roaming-water' AND encounters.species_id = g.species_id
          AND len(encounters.conditions) = 0
        """
    )


def reconcile_moves_with_rom(con, decomp_dir: Path) -> None:
    """Patch move type, power, accuracy and PP to the ROM's battle_moves.h values.

    move_changelog misses some post-Gen-3 changes (the Scarlet/Violet PP cuts to
    Rest, Soft-Boiled, Milk Drink and Slack-Off, Luster Purge's power buff), and it
    stores "can't miss" as NULL where the ROM stores an accuracy. The ROM is the
    ground truth for Emerald, so it wins; `rom_patched` lists what changed.
    """
    con.execute("ALTER TABLE moves ADD COLUMN rom_patched VARCHAR[] DEFAULT []")
    names = ("type", "power", "accuracy", "pp")
    current = {r[0]: r[1:] for r in con.execute("SELECT move_id, type, power, accuracy, pp FROM moves").fetchall()}
    for move_id, rom in decomp.battle_moves(decomp_dir).items():
        changed = [n for n, ours, theirs in zip(names, current[move_id], rom) if ours != theirs]
        if changed:
            sets = ", ".join(f"{n} = ?" for n in changed)
            values = [rom[names.index(n)] for n in changed]
            con.execute(f"UPDATE moves SET {sets}, rom_patched = ? WHERE move_id = ?", [*values, changed, move_id])
    # The type-based damage class must follow any type the ROM corrected.
    con.execute(
        "UPDATE moves SET damage_class = t.damage_class FROM types t "
        "WHERE moves.type = t.identifier AND moves.damage_class <> 'status' AND moves.damage_class <> t.damage_class"
    )
    # Damage calculation (pokemon.c) takes the category from the move's effective type
    # (typeOverride), which these two moves change in battle, so neither has a fixed one.
    con.execute(f"UPDATE moves SET damage_class = 'varies' WHERE identifier IN {tuple(DYNAMIC_TYPE_MOVES)}")


def reconcile_evolutions_with_rom(con, decomp_dir: Path) -> None:
    """Friendship thresholds and the evolution conditions PokeAPI's columns can't express.

    PokeAPI stores the Gen 8+ friendship threshold (160) for most friendship evolutions;
    Emerald's EVO_FRIENDSHIP* checks use FRIENDSHIP_EVO_THRESHOLD from pokemon.c (220).
    """
    threshold = int(re.search(r"#define FRIENDSHIP_EVO_THRESHOLD (\d+)", decomp.read(decomp_dir, "src/pokemon.c")).group(1))
    con.execute("UPDATE evolutions SET min_happiness = ? WHERE min_happiness IS NOT NULL", [threshold])
    con.execute("ALTER TABLE evolutions ADD COLUMN note VARCHAR")
    for (frm, to), note in EVOLUTION_NOTES.items():
        con.execute(
            "UPDATE evolutions SET note = ? FROM species f, species t WHERE evolutions.from_species_id = f.species_id "
            "AND evolutions.to_species_id = t.species_id AND f.identifier = ? AND t.identifier = ?",
            [note, frm, to],
        )


def reconcile_statics_with_rom(con, decomp_dir: Path) -> None:
    """Fix PokeAPI's Emerald static encounters against the ROM's `setwildbattle` scripts.

    PokeAPI lists New Mauville's three Voltorb twice, and puts the Aqua Hideout's two
    Electrode in New Mauville and team-magma-hideout as well. For every species the ROM
    sets up with `setwildbattle`, keep a static row only where the ROM has one, and drop
    exact duplicates. Legendaries placed some other way (event islands) are untouched.
    Needs `map_sections`.
    """
    dex = decomp.national_dex(decomp_dir)
    mapsec_location = dict(con.execute("SELECT mapsec, location FROM map_sections").fetchall())
    rom = set()
    for map_id, m in decomp.maps(decomp_dir).items():
        path = Path(decomp_dir) / "data" / "maps" / m["folder"] / "scripts.inc"
        if not path.exists():
            continue
        for species in re.findall(r"setwildbattle\s+(SPECIES_\w+)", path.read_text(encoding="utf-8")):
            location = mapsec_location.get(m["region_map_section"])
            if location and species in dex:
                rom.add((location, dex[species]))
    rom_species = {sid for _, sid in rom}
    con.execute("CREATE TEMP TABLE rom_statics (location VARCHAR, species_id INTEGER)")
    con.executemany("INSERT INTO rom_statics VALUES (?, ?)", sorted(rom))
    con.execute(
        f"""
        DELETE FROM encounters e
        WHERE e.method = 'static' AND e.species_id IN {tuple(sorted(rom_species))}
          AND NOT EXISTS (SELECT 1 FROM rom_statics r WHERE r.location = e.location AND r.species_id = e.species_id)
        """
    )
    con.execute(
        """
        DELETE FROM encounters WHERE method = 'static' AND encounter_id NOT IN (
            SELECT min(encounter_id) FROM encounters WHERE method = 'static'
            GROUP BY location, area, species_id, min_level, max_level
        )
        """
    )
