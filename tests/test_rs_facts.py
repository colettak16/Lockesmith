"""Ruby and Sapphire facts the built databases must get right (docs/review_packet_rs.md).

The first group is game facts that differ from Emerald, or that PokeAPI gets wrong for
Ruby/Sapphire. The second cross-checks each database against the pokeruby decompilation
for that version and skips when build/.cache/pokeruby hasn't been fetched.
"""

from pathlib import Path

import duckdb
import pytest

from agent.games import GAMES

ROOT = Path(__file__).resolve().parent.parent
DECOMP = ROOT / "build" / ".cache" / "pokeruby"
needs_decomp = pytest.mark.skipif(not DECOMP.exists(), reason="pokeruby not fetched (run build/fetch_sources.py)")

LEGENDARY = {"ruby": "groudon", "sapphire": "kyogre"}
HIDEOUT = {"ruby": "team-magma-hideout", "sapphire": "team-aqua-hideout"}
ROAMER = {"ruby": "latios", "sapphire": "latias"}
EXCLUSIVE = {"ruby": ("zangoose", "seviper"), "sapphire": ("seviper", "zangoose")}  # (has, lacks)


@pytest.fixture(scope="module", params=["ruby", "sapphire"])
def game(request):
    return GAMES[request.param]


@pytest.fixture(scope="module")
def db(game):
    if not game.db_path.exists():
        pytest.fail(f"{game.db_path} missing; run `uv run python build/build_db.py`")
    con = duckdb.connect(str(game.db_path), read_only=True)
    yield con
    con.close()


def rows(db, sql, *params):
    return db.execute(sql, params).fetchall()


def team(db, const):
    return rows(db, "SELECT species, level, held_item FROM trainer_mons WHERE trainer_const = ? ORDER BY slot", const)


# --- Gen 3 rules are the same engine as Emerald's ---------------------------------------


def test_gen3_basics(db):
    assert rows(db, "SELECT damage_class FROM moves WHERE identifier = 'crunch'") == [("special",)]
    assert rows(db, "SELECT type1, type2 FROM species WHERE identifier = 'gardevoir'") == [("psychic", None)]
    assert rows(db, "SELECT count(*) FROM types WHERE identifier = 'fairy'") == [(0,)]
    steel = dict(rows(db, "SELECT attacking_type, multiplier FROM type_efficacy WHERE defending_type = 'steel' AND attacking_type IN ('dark', 'ghost')"))
    assert steel == {"dark": 0.5, "ghost": 0.5}


def test_friendship_threshold_is_220(db):
    assert rows(db, "SELECT DISTINCT min_happiness FROM evolutions WHERE min_happiness IS NOT NULL") == [(220,)]


def test_deoxys_is_normal_forme(db):
    """Ruby/Sapphire's Deoxys learns Hyper Beam at 50 (Emerald's Speed Forme: Extreme Speed)."""
    assert rows(db, "SELECT m.identifier FROM learnsets l JOIN moves m USING (move_id) WHERE l.species_id = 386 AND l.method = 'level-up' AND l.level = 50") == [("hyper-beam",)]


# --- Trainers ---------------------------------------------------------------------------


def test_roxanne_team(db):
    assert team(db, "TRAINER_ROXANNE") == [("geodude", 14, None), ("nosepass", 15, None)]


def test_tate_and_liza_is_a_two_pokemon_double(db):
    assert rows(db, "SELECT is_double FROM trainers WHERE trainer_const = 'TRAINER_TATE_AND_LIZA'") == [(True,)]
    assert team(db, "TRAINER_TATE_AND_LIZA") == [("lunatone", 42, None), ("solrock", 42, None)]


def test_wallace_is_eighth_leader_and_steven_champion(db):
    assert team(db, "TRAINER_WALLACE")[-1] == ("milotic", 43, None)
    assert team(db, "TRAINER_STEVEN")[-1] == ("metagross", 58, "sitrus-berry")
    assert rows(db, "SELECT class_name FROM trainers WHERE trainer_const IN ('TRAINER_WALLACE', 'TRAINER_STEVEN') ORDER BY trainer_id") == [("Leader",), ("Champion",)]


def test_no_gym_leader_rematch_parties(db):
    assert rows(db, "SELECT count(*) FROM trainers WHERE trainer_const LIKE 'TRAINER_ROXANNE_%'") == [(0,)]
    assert rows(db, "SELECT count(*), max(trainer_id) FROM trainers WHERE party_size > 0") == [(693, 693)]


def test_villain_leaders_differ_by_team(db):
    assert team(db, "TRAINER_MAXIE_3")[-1][:2] == ("camerupt", 25)
    assert team(db, "TRAINER_ARCHIE_3")[-1][:2] == ("sharpedo", 25)


# --- Encounters --------------------------------------------------------------------------


def test_version_exclusives(db, game):
    has, lacks = EXCLUSIVE[game.id]
    wild = {s for (s,) in rows(db, "SELECT DISTINCT s.identifier FROM encounters e JOIN species s USING (species_id) WHERE e.method = 'walk'")}
    assert has in wild and lacks not in wild


def test_legendary_is_a_one_time_story_battle(db, game):
    got = rows(db, "SELECT s.identifier, e.area, e.min_level, e.conditions FROM encounters e JOIN species s USING (species_id) WHERE e.location = 'cave-of-origin' AND e.method = 'static'")
    assert got == [(LEGENDARY[game.id], "b4f", 45, ["legendary-story-battle"])]


def test_electrode_only_in_the_versions_hideout(db, game):
    """PokeAPI also files the hideout Electrode under New Mauville (Ruby) or the other team's hideout (Sapphire)."""
    assert rows(db, "SELECT DISTINCT e.location FROM encounters e JOIN species s USING (species_id) WHERE s.identifier = 'electrode' AND e.method = 'static'") == [(HIDEOUT[game.id],)]
    assert rows(db, "SELECT location FROM map_sections WHERE mapsec = 'MAPSEC_EVIL_TEAM_HIDEOUT'") == [(HIDEOUT[game.id],)]


def test_new_mauville_voltorb_not_duplicated(db):
    assert rows(db, "SELECT count(*) FROM encounters e JOIN species s USING (species_id) WHERE s.identifier = 'voltorb' AND e.method = 'static'") == [(1,)]


def test_rayquaza_is_postgame(db):
    assert rows(db, "SELECT conditions FROM encounters e JOIN species s USING (species_id) WHERE s.identifier = 'rayquaza'") == [(["sky-pillar-postgame"],)]


def test_roamer_needs_the_hall_of_fame_and_the_tv_report(db, game):
    # E-10: the Hall of Fame only turns the news on; checking the home TV starts the roamer
    got = rows(db, "SELECT DISTINCT s.identifier, e.conditions FROM encounters e JOIN species s USING (species_id) WHERE e.method LIKE 'roaming-%'")
    assert got == [(ROAMER[game.id], ["story-progress-hall-of-fame", "lati-tv-report"])]
    (desc,) = db.execute("SELECT description FROM rom_conditions WHERE condition = 'lati-tv-report'").fetchone()
    assert "check the TV" in desc and "InitRoamer" in desc


def test_regi_puzzles_are_ruby_sapphire_ones(db):
    desc = dict(rows(db, "SELECT condition, description FROM rom_conditions"))
    assert "Strength" in desc["regirock-puzzle"] and "Fly" in desc["registeel-puzzle"] and "wait" in desc["regice-puzzle"]
    assert "Relicanth first and Wailord last" in desc["sealed-chamber-opened"]


def test_in_game_trades(db):
    got = rows(db, "SELECT s.identifier, e.location FROM encounters e JOIN species s USING (species_id) WHERE e.method = 'npc-trade' ORDER BY 1")
    assert got == [("corsola", "pacifidlog-town"), ("makuhita", "rustboro-city"), ("skitty", "fortree-city")]


def test_cave_of_origin_has_four_wild_floors(db):
    floors = {a for (a,) in rows(db, "SELECT DISTINCT area FROM encounters WHERE location = 'cave-of-origin' AND method = 'walk'")}
    assert {"1f", "b1f", "b2f", "b3f"} <= floors


# --- TMs and tutors ----------------------------------------------------------------------


def test_no_move_tutors(db):
    assert rows(db, "SELECT count(*) FROM move_tutors") == [(0,)]
    assert rows(db, "SELECT count(*) FROM learnsets WHERE method = 'tutor'") == [(0,)]


def test_every_tm_and_hm_has_a_source(db):
    assert rows(db, "SELECT count(DISTINCT label) FROM tm_locations") == [(58,)]


def test_waterfall_and_dive_sources(db):
    assert rows(db, "SELECT method, location FROM tm_locations WHERE label = 'HM07'") == [("item-ball", "cave-of-origin")]
    # Steven's gift only: the house's item ball is a postgame fallback and the extractor ignores it.
    assert rows(db, "SELECT method, map_folder FROM tm_locations WHERE label = 'HM08'") == [("gift", "MossdeepCity_StevensHouse")]


def test_gym_tms_name_their_leader(db):
    got = dict(rows(db, "SELECT label, detail FROM tm_locations WHERE map_folder LIKE '%Gym%' AND method = 'gift'"))
    assert got["TM39"] == "after defeating TRAINER_ROXANNE" and got["TM03"] == "after defeating TRAINER_WALLACE"


def test_sootopolis_tm_waits_for_the_legendary(db):
    (req,) = rows(db, "SELECT requires FROM tm_locations WHERE label = 'TM31'")[0]
    assert "FLAG_LEGENDARY_BATTLE_COMPLETED" in req


@pytest.mark.parametrize("game_id", ["emerald", "ruby", "sapphire"])
def test_lilycove_store_tms_need_the_rival_battle(game_id):
    # All three games: the rival stands on the only tile below the store's door until battled;
    # declining leaves them there (docs/review_packet_rs.md V-14).
    con = duckdb.connect(str(GAMES[game_id].db_path), read_only=True)
    got = dict(con.execute("SELECT label, requires FROM tm_locations WHERE map_folder = 'LilycoveCity_DepartmentStore_4F'").fetchall())
    con.close()
    assert sorted(got) == ["TM14", "TM15", "TM16", "TM17", "TM20", "TM25", "TM33", "TM38"]
    assert all(req and "Lilycove rival battle" in req for req in got.values())


# --- Cross-checks against pokeruby ------------------------------------------------------


@needs_decomp
def test_species_moves_chart_match_decomp(db):
    from build import decomp

    species = {r[0]: tuple(r[1:]) for r in rows(db, "SELECT species_id, type1, type2, hp, attack, defense, sp_attack, sp_defense, speed, ability1, ability2 FROM species")}
    assert species == decomp.species_info(DECOMP)
    moves = {r[0]: tuple(r[1:]) for r in rows(db, "SELECT move_id, type, power, accuracy, pp FROM moves")}
    assert moves == decomp.battle_moves(DECOMP)
    chart = {(a, d): m for a, d, m in rows(db, "SELECT attacking_type, defending_type, multiplier FROM type_efficacy WHERE multiplier <> 1")}
    assert chart == decomp.type_chart(DECOMP)


@needs_decomp
def test_learnsets_and_evolutions_match_decomp(db):
    from build import decomp

    ours: dict[int, set] = {}
    for sid, level, mid in rows(db, "SELECT species_id, level, move_id FROM learnsets WHERE method = 'level-up'"):
        ours.setdefault(sid, set()).add((level, mid))
    theirs = {sid: set(moves) for sid, moves in decomp.level_up_learnsets(DECOMP).items()}
    assert {sid for sid in theirs if ours.get(sid, set()) != theirs[sid]} == set()
    assert set(rows(db, "SELECT from_species_id, to_species_id FROM evolutions")) == decomp.evolution_pairs(DECOMP)


@needs_decomp
def test_wild_species_match_decomp(db, game):
    from build import decomp

    mapsec_to_location = dict(rows(db, "SELECT mapsec, location FROM map_sections"))
    ref = decomp.wild_species_by_location(DECOMP, mapsec_to_location, game.rom_version)
    ours: dict[tuple, set] = {}
    for location, method, sid in rows(db, "SELECT location, method, species_id FROM encounters WHERE method IN ('walk', 'surf', 'rock-smash', 'old-rod', 'good-rod', 'super-rod', 'seaweed')"):
        ours.setdefault((location, method), set()).add(sid)
    ours.pop(("mirage-island", "walk"), None)  # inside the Route 130 map in the ROM
    assert ours == ref


@needs_decomp
def test_statics_match_rom_scripts(db, game):
    from build import gen3_corrections

    mapsec_to_location = dict(rows(db, "SELECT mapsec, location FROM map_sections"))
    rom = gen3_corrections.rom_static_locations(DECOMP, game, mapsec_to_location)
    # The ROM's Kecleon battles are setwildbattle scripts too; PokeAPI files them as 'devon-scope'.
    ours = set(rows(db, "SELECT location, species_id FROM encounters WHERE method IN ('static', 'devon-scope')"))
    # Event-only Southern Island isn't set up by a map script in the decomp's story files.
    assert rom <= ours and {r for r in ours - rom if r[0] != "southern-island"} == set()
