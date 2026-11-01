"""Gen 3 facts the built database must get right (PLAN.md section 4.2).

PokeAPI stores modern data, so every test here is a place where an uncorrected
build gives the wrong answer for Emerald. The last group cross-checks the whole
correction layer against the pokeemerald decompilation (the ROM's own tables) and
skips when build/.cache/pokeemerald hasn't been fetched.
"""

from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "emerald.duckdb"
DECOMP = ROOT / "build" / ".cache" / "pokeemerald"

needs_decomp = pytest.mark.skipif(not DECOMP.exists(), reason="pokeemerald not fetched (run build/fetch_sources.py)")


@pytest.fixture(scope="module")
def db():
    if not DB_PATH.exists():
        pytest.fail(f"{DB_PATH} missing; run `uv run python build/build_db.py`")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    yield con
    con.close()


def one(db, sql, *params):
    row = db.execute(sql, params).fetchone()
    assert row is not None, f"no row for: {sql} {params}"
    return row


def species_types(db, identifier):
    t1, t2 = one(db, "SELECT type1, type2 FROM species WHERE identifier = ?", identifier)
    return (t1, t2)


# --- The five facts PLAN.md requires -------------------------------------------------


def test_crunch_is_special(db):
    type_, damage_class = one(db, "SELECT type, damage_class FROM moves WHERE identifier = 'crunch'")
    assert type_ == "dark"
    assert damage_class == "special"


def test_gardevoir_is_pure_psychic(db):
    assert species_types(db, "gardevoir") == ("psychic", None)


def test_steel_resists_dark_and_ghost(db):
    for attacker in ("dark", "ghost"):
        (mult,) = one(
            db,
            "SELECT multiplier FROM type_efficacy WHERE attacking_type = ? AND defending_type = 'steel'",
            attacker,
        )
        assert mult == 0.5, attacker


def test_route_119_has_feebas_via_tile_fishing(db):
    rows = db.execute(
        """
        SELECT e.method, e.min_level, e.max_level
        FROM encounters e JOIN species s USING (species_id)
        WHERE s.identifier = 'feebas' AND e.location = 'hoenn-route-119'
        """
    ).fetchall()
    assert ("feebas-tile-fishing", 20, 25) in rows


def test_juan_1_team_is_exact(db):
    rows = db.execute(
        """
        SELECT species, level FROM trainer_mons
        WHERE trainer_const = 'TRAINER_JUAN_1' ORDER BY slot
        """
    ).fetchall()
    assert rows == [("luvdisc", 41), ("whiscash", 41), ("sealeo", 43), ("crawdaunt", 43), ("kingdra", 46)]


# --- Types and the type chart ---------------------------------------------------------


@pytest.mark.parametrize(
    "species, expected",
    [
        ("azumarill", ("water", None)),
        ("marill", ("water", None)),
        ("clefairy", ("normal", None)),
        ("clefable", ("normal", None)),
        ("jigglypuff", ("normal", None)),
        ("togetic", ("normal", "flying")),
        ("snubbull", ("normal", None)),
        ("mawile", ("steel", None)),
        ("ralts", ("psychic", None)),
        ("mr-mime", ("psychic", None)),
        ("magnemite", ("electric", "steel")),  # past-types row for Gen 1 must not apply
    ],
)
def test_fairy_era_types_reverted(db, species, expected):
    assert species_types(db, species) == expected


def test_no_fairy_anywhere(db):
    assert one(db, "SELECT count(*) FROM types WHERE identifier = 'fairy'") == (0,)
    assert one(db, "SELECT count(*) FROM species WHERE 'fairy' IN (type1, type2)") == (0,)
    assert one(db, "SELECT count(*) FROM moves WHERE type = 'fairy'") == (0,)
    assert one(db, "SELECT count(*) FROM type_efficacy WHERE 'fairy' IN (attacking_type, defending_type)") == (0,)


def test_type_chart_is_17_by_17(db):
    assert one(db, "SELECT count(*) FROM types") == (17,)
    assert one(db, "SELECT count(*) FROM type_efficacy") == (17 * 17,)


# --- Moves ----------------------------------------------------------------------------

PHYSICAL_TYPES = {"normal", "fighting", "flying", "poison", "ground", "rock", "bug", "ghost", "steel"}
SPECIAL_TYPES = {"fire", "water", "grass", "electric", "psychic", "ice", "dragon", "dark"}


def test_damage_class_follows_move_type(db):
    rows = db.execute("SELECT identifier, type, damage_class FROM moves WHERE damage_class <> 'status'").fetchall()
    assert len(rows) > 200
    for identifier, type_, damage_class in rows:
        if type_ in PHYSICAL_TYPES:
            assert damage_class == "physical", identifier
        elif type_ in SPECIAL_TYPES:
            assert damage_class == "special", identifier
        else:
            pytest.fail(f"{identifier} is a damaging move of type {type_}")


@pytest.mark.parametrize(
    "move, field, value",
    [
        ("shadow-ball", "damage_class", "physical"),  # Ghost is physical in Gen 3
        ("hidden-power", "damage_class", "physical"),  # listed as Normal; real type varies
        ("high-jump-kick", "power", 85),  # 100 in Gen 4, 130 in Gen 5+
        ("high-jump-kick", "pp", 20),
        ("dig", "power", 60),  # 80 from Gen 4
        ("tackle", "power", 35),  # 50 from Gen 5, 40 from Gen 7
        ("tackle", "accuracy", 95),
        ("curse", "type", "???"),  # Ghost from Gen 5
        # PokeAPI's move_changelog misses these later changes; the ROM reconciliation fixes them.
        ("rest", "pp", 10),  # 5 in Scarlet/Violet
        ("soft-boiled", "pp", 10),
        ("slack-off", "pp", 10),
        ("luster-purge", "power", 70),  # 95 in Scarlet/Violet
        ("mind-reader", "pp", 5),
    ],
)
def test_gen3_move_values(db, move, field, value):
    (actual,) = one(db, f"SELECT {field} FROM moves WHERE identifier = ?", move)
    assert actual == value


def test_only_gen1_to_3_moves(db):
    assert one(db, "SELECT count(*), max(move_id) FROM moves") == (354, 354)


# --- Species, abilities, evolutions ---------------------------------------------------


def test_only_national_dex_1_to_386(db):
    assert one(db, "SELECT count(*), min(species_id), max(species_id) FROM species") == (386, 1, 386)


def test_no_hidden_abilities_and_no_later_abilities(db):
    assert one(db, "SELECT ability1, ability2 FROM species WHERE identifier = 'gengar'") == ("levitate", None)
    assert one(db, "SELECT ability1, ability2 FROM species WHERE identifier = 'pidgey'") == ("keen-eye", None)
    later = db.execute(
        """
        SELECT s.identifier FROM species s
        WHERE s.ability1 NOT IN (SELECT identifier FROM abilities)
           OR (s.ability2 IS NOT NULL AND s.ability2 NOT IN (SELECT identifier FROM abilities))
        """
    ).fetchall()
    assert later == []
    assert one(db, "SELECT max(ability_id) <= 77 FROM abilities") == (True,)


@pytest.mark.parametrize("species", ["snorlax", "chansey", "roselia", "mr-mime", "sudowoodo", "mantine", "chimecho"])
def test_gen4_baby_pre_evolutions_removed(db, species):
    assert one(db, "SELECT evolves_from_species_id FROM species WHERE identifier = ?", species) == (None,)
    assert one(
        db,
        "SELECT count(*) FROM evolutions e JOIN species s ON s.species_id = e.to_species_id WHERE s.identifier = ?",
        species,
    ) == (0,)


def test_no_evolutions_into_later_generations(db):
    assert one(db, "SELECT count(*) FROM evolutions WHERE to_species_id > 386 OR from_species_id > 386") == (0,)
    targets = db.execute(
        """
        SELECT t.identifier FROM evolutions e
        JOIN species f ON f.species_id = e.from_species_id
        JOIN species t ON t.species_id = e.to_species_id
        WHERE f.identifier = 'kirlia'
        """
    ).fetchall()
    assert targets == [("gardevoir",)]


def test_no_regional_form_evolution_methods(db):
    rows = db.execute(
        """
        SELECT e.trigger, e.min_level, e.time_of_day, e.item FROM evolutions e
        JOIN species t ON t.species_id = e.to_species_id WHERE t.identifier = 'raticate'
        """
    ).fetchall()
    assert rows == [("level-up", 20, None, None)]
    (n,) = one(
        db,
        "SELECT count(*) FROM evolutions e JOIN species t ON t.species_id = e.to_species_id "
        "WHERE t.identifier IN ('sandslash', 'ninetales', 'marowak', 'typhlosion')",
    )
    assert n == 4


def test_feebas_evolves_by_beauty(db):
    rows = db.execute(
        """
        SELECT e.trigger, e.min_beauty, e.held_item FROM evolutions e
        JOIN species f ON f.species_id = e.from_species_id WHERE f.identifier = 'feebas'
        """
    ).fetchall()
    assert rows == [("level-up", 170, None)]


# --- Learnsets and TMs ----------------------------------------------------------------


def test_learnsets_are_emerald_only(db):
    assert one(db, "SELECT max(move_id) FROM learnsets") == (354,)
    assert one(db, "SELECT max(species_id) FROM learnsets") == (386,)
    (level,) = one(
        db,
        """
        SELECT l.level FROM learnsets l JOIN species s USING (species_id) JOIN moves m USING (move_id)
        WHERE s.identifier = 'kirlia' AND m.identifier = 'calm-mind' AND l.method = 'level-up'
        """,
    )
    assert level == 21


def test_tm_and_hm_list(db):
    assert one(db, "SELECT count(*) FROM machines") == (58,)
    assert one(db, "SELECT m.identifier FROM machines x JOIN moves m USING (move_id) WHERE label = 'TM26'") == (
        "earthquake",
    )
    assert one(db, "SELECT m.identifier FROM machines x JOIN moves m USING (move_id) WHERE label = 'HM03'") == ("surf",)
    assert one(db, "SELECT m.identifier FROM machines x JOIN moves m USING (move_id) WHERE label = 'TM50'") == (
        "overheat",
    )


# --- Trainers and the default-moves rule ----------------------------------------------


def test_default_moves_rule_unit():
    from build.parse_decomp_trainers import default_moves

    learnset = [(1, "a"), (1, "b"), (5, "c"), (5, "a"), (9, "d"), (13, "e"), (20, "f")]
    assert default_moves(learnset, 4) == ["a", "b"]
    assert default_moves(learnset, 9) == ["a", "b", "c", "d"]  # re-learning "a" at 5 is a no-op
    assert default_moves(learnset, 13) == ["b", "c", "d", "e"]  # oldest move drops off
    assert default_moves(learnset, 100) == ["c", "d", "e", "f"]


def test_every_party_parsed(db):
    assert one(db, "SELECT count(*) FROM trainers WHERE party_size > 0") == (854,)
    assert one(
        db,
        "SELECT count(*) FROM trainers t WHERE party_size <> (SELECT count(*) FROM trainer_mons m WHERE m.trainer_id = t.trainer_id)",
    ) == (0,)


def test_trainer_ids_match_opponents_h(db):
    assert one(db, "SELECT trainer_id FROM trainers WHERE trainer_const = 'TRAINER_ROXANNE_1'") == (265,)


def test_default_move_mons_have_legal_moves(db):
    bad = db.execute(
        """
        SELECT m.trainer_const, m.species, m.level, mv.move FROM trainer_mons m, unnest(m.moves) AS mv(move)
        WHERE m.moves_source = 'default' AND NOT EXISTS (
            SELECT 1 FROM learnsets l JOIN moves x USING (move_id)
            WHERE l.species_id = m.species_id AND l.method = 'level-up' AND x.identifier = mv.move AND l.level <= m.level
        )
        """
    ).fetchall()
    assert bad == []
    assert one(db, "SELECT max(len(moves)) FROM trainer_mons") == (4,)
    assert one(db, "SELECT count(*) FROM trainer_mons WHERE moves_source = 'default' AND len(moves) = 0") == (0,)


def test_tate_and_liza_is_a_double_battle(db):
    assert one(db, "SELECT is_double FROM trainers WHERE trainer_const = 'TRAINER_TATE_AND_LIZA_1'") == (True,)


# --- Cross-checks against the decompilation -------------------------------------------


@needs_decomp
def test_species_match_decomp(db):
    from build import decomp

    ref = decomp.species_info(DECOMP)
    rows = db.execute(
        "SELECT species_id, type1, type2, hp, attack, defense, sp_attack, sp_defense, speed, ability1, ability2 FROM species"
    ).fetchall()
    mismatches = [r for r in rows if ref[r[0]] != tuple(r[1:])]
    assert mismatches == [], [(m, ref[m[0]]) for m in mismatches[:10]]


@needs_decomp
def test_moves_match_decomp(db):
    from build import decomp

    ref = decomp.battle_moves(DECOMP)
    rows = db.execute("SELECT move_id, type, power, accuracy, pp FROM moves").fetchall()
    mismatches = [r for r in rows if ref[r[0]] != tuple(r[1:])]
    assert mismatches == [], [(m, ref[m[0]]) for m in mismatches[:10]]


@needs_decomp
def test_type_chart_matches_decomp(db):
    from build import decomp

    ref = decomp.type_chart(DECOMP)
    rows = db.execute("SELECT attacking_type, defending_type, multiplier FROM type_efficacy WHERE multiplier <> 1").fetchall()
    assert {(a, d): m for a, d, m in rows} == ref


@needs_decomp
def test_level_up_learnsets_match_decomp(db):
    from build import decomp

    ref = decomp.level_up_learnsets(DECOMP)
    rows = db.execute(
        "SELECT species_id, level, move_id FROM learnsets WHERE method = 'level-up' ORDER BY species_id, level, move_id"
    ).fetchall()
    ours: dict[int, set] = {}
    for species_id, level, move_id in rows:
        ours.setdefault(species_id, set()).add((level, move_id))
    theirs = {sid: {(lvl, mid) for lvl, mid in moves} for sid, moves in ref.items()}
    diff = {sid for sid in theirs if ours.get(sid, set()) != theirs[sid]}
    assert diff == set(), sorted(diff)[:10]


@needs_decomp
def test_evolutions_match_decomp(db):
    from build import decomp

    ref = decomp.evolution_pairs(DECOMP)
    ours = set(db.execute("SELECT from_species_id, to_species_id FROM evolutions").fetchall())
    assert ours == ref


@needs_decomp
def test_wild_species_match_decomp(db):
    from build import decomp

    mapsec_to_location = dict(db.execute("SELECT mapsec, location FROM map_sections").fetchall())
    ref = decomp.wild_species_by_location(DECOMP, mapsec_to_location)
    rows = db.execute(
        """
        SELECT location, method, species_id FROM encounters
        WHERE method IN ('walk', 'surf', 'rock-smash', 'old-rod', 'good-rod', 'super-rod', 'seaweed')
        """
    ).fetchall()
    ours: dict[tuple, set] = {}
    for location, method, species_id in rows:
        ours.setdefault((location, method), set()).add(species_id)
    # Mirage Island is part of the Route 130 map in the ROM, so it has no header of its own.
    ours.pop(("mirage-island", "walk"), None)
    assert ours == ref
