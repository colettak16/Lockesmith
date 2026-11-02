"""Randomizer log parser (PLAN.md section 4.5).

Two groups:
- Fixture tests run against a real UPR ZX log in tests/fixtures/ (*.log or *.txt)
  and are skipped until one is added. These are the ones that matter: no real
  Emerald log has been through the parser yet.
- Format tests use a small hand-written log in the format UPR ZX's logging code
  prints (Randomizer.java log* methods, TrainerPokemon/StaticEncounter.toString,
  Gen3RomHandler set names). They pin the parser's logic (ROM-order set alignment,
  the fishing split, trainer id join, overlays) but can't replace a real log.
"""

from pathlib import Path

import pytest

from agent.db import connect_session
from agent.entities import EntityIndex
from agent.randomizer_log import load_overlay, parse_log

FIXTURES = sorted(p for p in (Path(__file__).parent / "fixtures").glob("*") if p.suffix in (".log", ".txt"))
needs_fixture = pytest.mark.skipif(not FIXTURES, reason="no UPR ZX log in tests/fixtures/ yet")


@pytest.fixture(scope="module")
def con():
    c = connect_session()
    yield c
    c.close()


@pytest.fixture(scope="module")
def index(con):
    return EntityIndex(con)


# --- Real-log fixture tests -----------------------------------------------------------


@pytest.fixture(scope="module")
def fixture_logs(con, index):
    return [(p.name, parse_log(p.read_text(encoding="utf-8", errors="replace"), con, index)) for p in FIXTURES]


@needs_fixture
def test_fixture_names_all_resolve(fixture_logs):
    for name, log in fixture_logs:
        unknown = [w for w in log.warnings if w.startswith(("unknown species", "unknown move"))]
        assert unknown == [], (name, unknown[:10])


@needs_fixture
def test_fixture_trainer_ids_join_decomp(fixture_logs, con):
    for name, log in fixture_logs:
        if not log.trainers:
            continue
        trainers = [t for t in log.trainers.values() if not t.is_partner]  # Steven's Space Center team
        assert all(t.trainer_const for t in trainers), name
        # PLAN.md: TRAINER_ROXANNE_1 = 265 <-> "#265 (ROXANNE)"
        assert "ROXANNE" in log.trainers[265].name.upper(), name
        sizes = dict(con.execute("SELECT trainer_id, party_size FROM trainers").fetchall())
        wrong = [t.index for t in trainers if len(t.mons) != sizes[t.index]]
        assert wrong == [], (name, wrong[:10])


@needs_fixture
def test_fixture_wild_sets_line_up_with_rom_order(fixture_logs, con):
    (expected,) = con.execute("SELECT count(*) FROM wild_headers").fetchone()
    for name, log in fixture_logs:
        if not log.wild_sets:
            continue
        assert len(log.wild_sets) == expected, name
        assert [ws.set_no for ws in log.wild_sets if not ws.aligned] == [], name
        assert all(ws.location for ws in log.wild_sets), name


@needs_fixture
def test_fixture_unrandomized_wild_matches_vanilla(fixture_logs, con):
    """The fishing-split check PLAN.md asks for: a log with wild Pokemon left unchanged
    should reproduce the vanilla tables slot for slot, rods included."""
    vanilla = {}
    for location, method, species_id in con.execute(
        "SELECT location, method, species_id FROM encounters WHERE method IN ('walk','surf','seaweed','rock-smash','old-rod','good-rod','super-rod')"
    ).fetchall():
        vanilla.setdefault((location, method), set()).add(species_id)
    ids = dict(con.execute("SELECT identifier, species_id FROM species").fetchall())
    checked = 0
    for name, log in fixture_logs:
        ours = {}
        for ws in log.wild_sets:
            if ws.rom_map == "MAP_ALTERING_CAVE" and ws.set_no != min(
                w.set_no for w in log.wild_sets if w.rom_map == "MAP_ALTERING_CAVE"
            ):
                continue
            for mon in ws.mons:
                ours.setdefault((ws.location, mon.method), set()).add(ids[mon.species])
        same = sum(ours.get(k) == v for k, v in vanilla.items())
        if not ours or same < 0.9 * len(vanilla):
            continue  # this log randomizes wild Pokemon; nothing to compare
        checked += 1
        ours.pop(("mirage-island", "walk"), None)
        vanilla_cmp = {k: v for k, v in vanilla.items() if k != ("mirage-island", "walk")}
        assert ours == vanilla_cmp, name
    if not checked:
        pytest.skip("no fixture log with unrandomized wild Pokemon")


@needs_fixture
def test_fixture_overlay_loads(fixture_logs, con):
    for name, log in fixture_logs:
        load_overlay(con, log, name)
        (n,) = con.execute("SELECT count(*) FROM overlay_sections WHERE log_id = ?", [name]).fetchone()
        assert n == len(log.sections)


# --- Format tests on a hand-written log ------------------------------------------------

ROUTE_101 = """\
Set #1 - ROUTE 101 Grass/Cave (rate=20)
Treecko        Lv2       HP 40  ATK 45  DEF 35  SPATK 65  SPDEF 55  SPEED 70
Mudkip         Lv2       HP 50  ATK 70  DEF 50  SPATK 50  SPDEF 50  SPEED 40
Torchic        Lv2
Treecko        Lv3
Mudkip         Lv3
Torchic        Lv3
Treecko        Lv3
Mudkip         Lv3
Torchic        Lv2
Treecko        Lv2
Mudkip         Lv3
Torchic        Lv3
"""

ROUTE_102_FISHING = """\
Set #4 - ROUTE 102 Fishing (rate=30)
Magikarp Lvs 5-10        HP 20  ATK 10  DEF 55  SPATK 15  SPDEF 20  SPEED 80
Goldeen Lvs 5-10         HP 45  ATK 67  DEF 60  SPATK 35  SPDEF 50  SPEED 63
Magikarp Lvs 10-30       HP 20  ATK 10  DEF 55  SPATK 15  SPDEF 20  SPEED 80
Goldeen Lvs 10-30        HP 45  ATK 67  DEF 60  SPATK 35  SPDEF 50  SPEED 63
Corphish Lvs 10-30       HP 43  ATK 80  DEF 65  SPATK 50  SPDEF 35  SPEED 35
Feebas Lvs 20-25         HP 20  ATK 15  DEF 20  SPATK 10  SPDEF 55  SPEED 80
Corphish Lvs 20-30       HP 43  ATK 80  DEF 65  SPATK 50  SPDEF 35  SPEED 35
Corphish Lvs 20-30       HP 43  ATK 80  DEF 65  SPATK 50  SPDEF 35  SPEED 35
Barboach Lvs 20-25       HP 50  ATK 48  DEF 43  SPATK 46  SPDEF 41  SPEED 60
Whiscash Lvs 35-40       HP 110 ATK 78  DEF 73  SPATK 76  SPDEF 71  SPEED 60
"""

SAMPLE = f"""\
Randomizer Version: 4.6.1
Random Seed: 12345
Settings String: 461ABC

--Wild Pokemon--
{ROUTE_101}
{ROUTE_102_FISHING}
Set #210 - NOWHERE Grass/Cave (rate=10)
Zigzagoon      Lv2

--Trainers Pokemon--
#265 (ROXANNE)@31F0C8 - Geodude Lv12, Geodude Lv12, Nosepass@Oran Berry Lv15
#266 (BRAWLY)@31F0F0 - Machop Lv16, Meditite Lv16, Makuhita@Sitrus Berry Lv19
#855 (STEVEN)@5DD6D0 - Metang Lv42, Skarmory Lv43, Aggron Lv44

--Static Pokemon--
VOLTORB Lv25 => PIKACHU Lv25
VOLTORB Lv25(2) => ELECTRODE Lv25

--TM Moves--
TM01 THUNDERBOLT
TM26 FAINT ATTACK

--Randomized Evolutions--
RALTS          -> KIRLIA
KIRLIA         -> GARDEVOIR
WURMPLE        -> SILCOON and CASCOON

--Random Starters--
Set starter 1 to BAGON
Set starter 2 to BELDUM
Set starter 3 to LARVITAR

--Some Future Section--
whatever
"""


@pytest.fixture(scope="module")
def sample(con, index):
    return parse_log(SAMPLE, con, index)


def test_sections_and_header(sample):
    assert sample.header["Random Seed"] == "12345"
    assert sample.randomized("wild") and sample.randomized("trainers")
    assert not sample.randomized("base_stats")
    assert sample.unparsed_sections == ["Some Future Section"]


def test_wild_set_aligned_to_rom_map(sample):
    route_101 = sample.wild_sets[0]
    assert (route_101.rom_map, route_101.location, route_101.method, route_101.aligned) == (
        "MAP_ROUTE101", "hoenn-route-101", "walk", True
    )
    assert [m.species for m in route_101.mons[:3]] == ["treecko", "mudkip", "torchic"]
    assert len(route_101.mons) == 12


def test_fishing_set_split_by_rod(sample):
    fishing = sample.wild_sets[1]
    assert fishing.location == "hoenn-route-102" and fishing.aligned
    rods = [m.method for m in fishing.mons]
    assert rods == ["old-rod"] * 2 + ["good-rod"] * 3 + ["super-rod"] * 5
    assert (fishing.mons[0].min_level, fishing.mons[0].max_level) == (5, 10)


def test_unaligned_set_is_flagged(sample):
    stray = sample.wild_sets[2]
    assert not stray.aligned and stray.location is None
    assert any("#210" in w for w in sample.warnings)


def test_trainers_join_on_decomp_id(sample):
    roxanne = sample.trainers[265]
    assert roxanne.trainer_const == "TRAINER_ROXANNE_1"
    assert [(m.species, m.level) for m in roxanne.mons] == [("geodude", 12), ("geodude", 12), ("nosepass", 15)]
    assert roxanne.mons[2].held_item == "Oran Berry"  # TrainerPokemon.toString: Name@Item LvN
    assert roxanne.mons[0].moves is None  # compact form carries no movesets


def test_steven_partner_entry(sample):
    """Gen3RomHandler appends Steven's Space Center team after the last real trainer."""
    steven = sample.trainers[855]
    assert steven.is_partner and steven.trainer_const is None
    assert [m.species for m in steven.mons] == ["metang", "skarmory", "aggron"]
    assert not any("#855" in w for w in sample.warnings)


def test_statics_strip_levels_and_repeat_counts(sample):
    assert sample.statics == [("voltorb", "pikachu"), ("voltorb", "electrode")]


def test_tm_moves_use_rom_names(sample):
    assert sample.tm_moves == {"TM01": "thunderbolt", "TM26": "feint-attack"}


def test_evolutions_and_starters(sample):
    assert sample.evolutions["wurmple"] == ["silcoon", "cascoon"]
    assert sample.starters == ["bagon", "beldum", "larvitar"]


def test_moveset_logging_form(con, index):
    """With moveset logging the header stands alone and each Pokemon gets a line."""
    log = parse_log(
        "--Trainers Pokemon--\n"
        "#265 (ROXANNE)@31F0C8\n"
        "Geodude@Oran Berry Lv12, Ability: STURDY - TACKLE, DEFENSE CURL, ROCK THROW, ROCK TOMB\n"
        "Nosepass Lv15, Ability: STURDY - TACKLE, HARDEN, ROCK TOMB, BLOCK\n",
        con,
        index,
    )
    first, second = log.trainers[265].mons
    assert (first.species, first.level, first.held_item, first.ability) == ("geodude", 12, "Oran Berry", "STURDY")
    assert first.moves == ["tackle", "defense-curl", "rock-throw", "rock-tomb"]
    assert (second.species, second.held_item, second.moves[-1]) == ("nosepass", None, "block")
    assert log.warnings == []


def test_overlay_tables(con, sample):
    load_overlay(con, sample, "sample")
    rows = con.execute(
        "SELECT method, count(*) FROM overlay_encounters WHERE log_id = 'sample' AND set_no = 4 GROUP BY 1 ORDER BY 1"
    ).fetchall()
    assert rows == [("good-rod", 3), ("old-rod", 2), ("super-rod", 5)]
    (n,) = con.execute("SELECT count(*) FROM overlay_trainer_mons WHERE log_id = 'sample' AND trainer_id = 265").fetchone()
    assert n == 3
    # reloading the same log replaces, not duplicates
    load_overlay(con, sample, "sample")
    (n,) = con.execute("SELECT count(*) FROM overlay_starters WHERE log_id = 'sample'").fetchone()
    assert n == 3
