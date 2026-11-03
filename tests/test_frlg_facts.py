"""FireRed and LeafGreen facts the built databases must get right (docs/decisions.md D16).

The first group is game facts: Kanto's bosses, what differs between the two versions, and the
TM and tutor sources. The second cross-checks each database against the pokefirered
decompilation for that version and skips when build/.cache/pokefirered hasn't been fetched.
"""

from pathlib import Path

import duckdb
import pytest

from agent.games import GAMES

ROOT = Path(__file__).resolve().parent.parent
DECOMP = ROOT / "build" / ".cache" / "pokefirered"
needs_decomp = pytest.mark.skipif(not DECOMP.exists(), reason="pokefirered not fetched (run build/fetch_sources.py)")

# Wild species only one version has (Kanto's #1-151; the Sevii Islands add no more)
EXCLUSIVE = {
    "firered": {"ekans", "arbok", "oddish", "gloom", "psyduck", "golduck", "growlithe", "shellder", "seadra",
                "scyther", "electabuzz", "weezing"},
    "leafgreen": {"sandshrew", "sandslash", "vulpix", "bellsprout", "weepinbell", "slowpoke", "slowbro", "staryu",
                  "kingler", "magmar", "pinsir", "muk"},
}


@pytest.fixture(scope="module", params=["firered", "leafgreen"])
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
    return rows(db, "SELECT species, level FROM trainer_mons WHERE trainer_const = ? ORDER BY slot", const)


# --- the same Gen 3 engine ----------------------------------------------------------------


def test_gen3_basics(db):
    assert rows(db, "SELECT damage_class FROM moves WHERE identifier = 'crunch'") == [("special",)]
    assert rows(db, "SELECT type1, type2 FROM species WHERE identifier = 'clefairy'") == [("normal", None)]
    assert rows(db, "SELECT count(*) FROM types WHERE identifier = 'fairy'") == [(0,)]


def test_friendship_threshold_is_220(db):
    assert rows(db, "SELECT DISTINCT min_happiness FROM evolutions WHERE min_happiness IS NOT NULL") == [(220,)]


# --- Kanto's bosses ---------------------------------------------------------------------


def test_gym_leaders(db):
    assert team(db, "TRAINER_LEADER_BROCK") == [("geodude", 12), ("onix", 14)]
    assert team(db, "TRAINER_LEADER_MISTY") == [("staryu", 18), ("starmie", 21)]
    assert max(level for _, level in team(db, "TRAINER_LEADER_GIOVANNI")) == 50


def test_champion_team_follows_the_players_starter(db):
    """The rival takes the starter strong against yours: TRAINER_CHAMPION_FIRST_<your starter>."""
    aces = {const: team(db, const)[-1] for const in (
        "TRAINER_CHAMPION_FIRST_BULBASAUR", "TRAINER_CHAMPION_FIRST_CHARMANDER", "TRAINER_CHAMPION_FIRST_SQUIRTLE")}
    assert aces == {"TRAINER_CHAMPION_FIRST_BULBASAUR": ("venusaur", 63),
                    "TRAINER_CHAMPION_FIRST_CHARMANDER": ("charizard", 63),
                    "TRAINER_CHAMPION_FIRST_SQUIRTLE": ("blastoise", 63)}


def test_elite_four_first_round(db):
    assert [team(db, f"TRAINER_ELITE_FOUR_{n}")[-1] for n in ("LORELEI", "BRUNO", "AGATHA", "LANCE")] == [
        ("lapras", 54), ("machamp", 56), ("gengar", 58), ("dragonite", 60)]


# --- what differs between the versions -------------------------------------------------------


def test_version_exclusives(db, game):
    wild = {s for (s,) in rows(db, "SELECT DISTINCT s.identifier FROM encounters e JOIN species s USING (species_id) "
                                   "WHERE method IN ('walk', 'surf', 'rock-smash', 'old-rod', 'good-rod', 'super-rod')")}
    other = "leafgreen" if game.id == "firered" else "firered"
    assert EXCLUSIVE[game.id] <= wild and not (EXCLUSIVE[other] & wild)


def test_in_game_trades_differ_by_version(db, game):
    route11 = rows(db, "SELECT s.identifier, e.conditions FROM encounters e JOIN species s USING (species_id) "
                       "WHERE method = 'npc-trade' AND location = 'kanto-route-11'")
    assert route11 == ([("nidorina", ["trade-nidorino"])] if game.id == "firered" else [("nidorino", ["trade-nidorina"])])


def test_game_corner_prizes_differ_by_version(db, game):
    prizes = {s for (s,) in rows(db, "SELECT s.identifier FROM encounters e JOIN species s USING (species_id) "
                                     "WHERE location = 'celadon-city' AND area = 'prize-corner'")}
    assert prizes == ({"abra", "clefairy", "dratini", "scyther", "porygon"} if game.id == "firered"
                      else {"abra", "clefairy", "dratini", "pinsir", "porygon"})


# --- TMs and tutors ----------------------------------------------------------------------


def test_every_tm_and_hm_has_a_source_but_dive_and_tm10(db):
    """FireRed/LeafGreen have no Dive, and no script, mart or map in pokefirered gives TM10."""
    missing = rows(db, "SELECT label FROM machines WHERE label NOT IN (SELECT label FROM tm_locations) ORDER BY label")
    assert missing == [("HM08",), ("TM10",)]


def test_gym_tms_name_their_leader(db):
    gyms = dict(rows(db, "SELECT label, detail FROM tm_locations WHERE method = 'gift' AND map_folder LIKE '%_Gym'"))
    assert gyms["TM39"] == "after defeating TRAINER_LEADER_BROCK" and gyms["TM26"] == "after defeating TRAINER_LEADER_GIOVANNI"
    assert len(gyms) == 8


def test_roof_drinks_buy_three_tms(db):
    roof = rows(db, "SELECT label, detail FROM tm_locations WHERE map_folder = 'CeladonCity_DepartmentStore_Roof' "
                    "AND requires IS NOT NULL ORDER BY label")
    assert roof == [("TM16", "for Fresh Water"), ("TM20", "for Soda Pop"), ("TM33", "for Lemonade")]


def test_tutors_and_cape_brink(db):
    tutors = rows(db, "SELECT m.identifier, t.map_folder, t.requires FROM move_tutors t JOIN moves m USING (move_id) ORDER BY 1")
    assert len(tutors) == 18 and all(one for (one,) in rows(db, "SELECT one_time FROM move_tutors"))
    brink = {move: req for move, folder, req in tutors if folder == "TwoIsland_CapeBrink_House"}
    assert set(brink) == {"frenzy-plant", "blast-burn", "hydro-cannon"}
    assert all("friendship 255" in req for req in brink.values())


# --- Cross-checks against pokefirered ---------------------------------------------------


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
    for location, method, sid in rows(db, "SELECT location, method, species_id FROM encounters WHERE method IN ('walk', 'surf', 'rock-smash', 'old-rod', 'good-rod', 'super-rod')"):
        ours.setdefault((location, method), set()).add(sid)
    assert ours == ref


@needs_decomp
def test_statics_match_rom_scripts(db, game):
    from build import gen3_corrections

    mapsec_to_location = dict(rows(db, "SELECT mapsec, location FROM map_sections"))
    rom = gen3_corrections.rom_static_locations(DECOMP, game, mapsec_to_location)
    ours = set(rows(db, "SELECT location, species_id FROM encounters WHERE method IN ('static', 'pokeflute')"))
    # Pokemon Tower's Marowak is the ghost battle (StartMarowakBattle), not a catchable static
    assert rom - ours == {("pokemon-tower", 105)}
    # Navel Rock and Birth Island are event-ticket islands no story script sets up
    assert {loc for loc, _ in ours - rom} == {"navel-rock", "birth-island"}
