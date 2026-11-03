"""Consistency checks for data/progression.yaml against the database and guide corpus.

These catch typos and drift (a trainer const that doesn't exist, an area PokeAPI
doesn't have, a citation to a missing guide section), not judgement calls about
story order; those are for human review.
"""

import json
from pathlib import Path

import duckdb
import pytest

from agent.progression import ALL, RIVALS, STARTERS, load

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "data" / "guide" / "chunks.jsonl"
HMS = ("cut", "flash", "rock-smash", "strength", "surf", "fly", "dive", "waterfall")


@pytest.fixture(scope="module")
def prog():
    return load()


@pytest.fixture(scope="module")
def db():
    con = duckdb.connect(str(ROOT / "data" / "emerald.duckdb"), read_only=True)
    yield con
    con.close()


def all_consts(battle):
    if battle.trainer_consts is not None:
        return list(battle.trainer_consts)
    return [c for v in battle.starter_variants.values() for c in v.values()]


def test_order_and_ids(prog):
    assert [b.order for b in prog.battles] == list(range(1, len(prog.battles) + 1))
    assert len({b.id for b in prog.battles}) == len(prog.battles)
    badges = [b.badges_before for b in prog.battles]
    assert badges == sorted(badges)
    assert prog.battles[-1].id == "champion_wallace"


def test_gyms_e4_and_champion(prog):
    gyms = [b for b in prog.battles if b.id.startswith("gym")]
    expected = ["ROXANNE", "BRAWLY", "WATTSON", "FLANNERY", "NORMAN", "WINONA", "TATE_AND_LIZA", "JUAN"]
    assert [b.trainer_consts[0] for b in gyms] == [f"TRAINER_{n}_1" for n in expected]
    assert [b.badges_before for b in gyms] == list(range(8))
    tail = [b.trainer_consts[0] for b in prog.battles[-5:]]
    assert tail == ["TRAINER_SIDNEY", "TRAINER_PHOEBE", "TRAINER_GLACIA", "TRAINER_DRAKE", "TRAINER_WALLACE"]


def test_trainer_consts_exist(prog, db):
    known = {c for (c,) in db.execute("SELECT trainer_const FROM trainers WHERE party_size > 0").fetchall()}
    missing = [(b.id, c) for b in prog.battles for c in all_consts(b) if c not in known]
    assert missing == []


def test_starter_variants_complete(prog):
    for b in prog.battles:
        if b.trainer_consts is None:
            assert set(b.starter_variants) == set(STARTERS), b.id
            for starter in STARTERS:
                assert set(b.starter_variants[starter]) == set(RIVALS), (b.id, starter)
            assert b.trainers_for("torchic", "may")
            with pytest.raises(ValueError):
                b.trainers_for(None)


def test_rival_fights_that_differ_by_rival(prog, db):
    """Only list rival variants where May's and Brendan's teams really differ in species."""
    teams = {
        c: sorted(t)
        for c, t in db.execute(
            "SELECT trainer_const, list(species) FROM trainer_mons GROUP BY 1"
        ).fetchall()
    }
    differing = []
    for b in prog.battles:
        if b.trainer_consts is None:
            for starter, v in b.starter_variants.items():
                if teams[v["may"]] != teams[v["brendan"]]:
                    differing.append((b.id, starter))
    assert differing == [("rival2_rustboro", "torchic"), ("rival4_route119", "mudkip")]


def test_battle_format_agrees_with_trainer_structs(prog, db):
    doubles = {c for (c,) in db.execute("SELECT trainer_const FROM trainers WHERE is_double").fetchall()}
    for b in prog.battles:
        assert b.battle_format in ("single", "double", "multi"), b.id
        if any(c in doubles for c in all_consts(b)):
            assert b.battle_format == "double", b.id
    assert prog.get("gym7_tate_liza").battle_format == "double"
    assert prog.get("space_center").battle_format == "multi"


def test_locations_exist(prog, db):
    known = {l for (l,) in db.execute("SELECT identifier FROM locations").fetchall()}
    assert [b.location for b in prog.battles if b.location not in known] == []


def test_area_specs_exist(prog, db):
    areas = set(db.execute("SELECT location, area FROM location_areas").fetchall())
    methods = {m for (m,) in db.execute("SELECT DISTINCT method FROM encounters").fetchall()}
    # A whole-location spec may name a place with no encounter areas (Mauville City has TMs and tutors)
    locations = {l for (l,) in db.execute("SELECT identifier FROM locations").fetchall()}
    specs = [(b.id, s) for b in prog.battles for s in b.areas_new] + [("never", s) for s, _ in prog.never_reachable]
    bad = [(who, s) for who, s in specs if (s[0] not in locations if s[1] == ALL else (s[0], s[1]) not in areas)]
    assert bad == []
    assert [(who, s) for who, s in specs if s[2] and not set(s[2]) <= methods] == []


def test_each_area_opens_once(prog):
    """No area and method opens at two battles (method-limited specs may split an area)."""
    seen = []
    for b in prog.battles:
        for spec in b.areas_new:
            for other, where in seen:
                same_area = other[:2] == spec[:2] or ALL in (other[1], spec[1]) and other[0] == spec[0]
                same_methods = other[2] is None or spec[2] is None or set(other[2]) & set(spec[2])
                assert not (same_area and same_methods), (spec, where, b.id)
            seen.append((spec, b.id))


def test_every_encounter_area_is_placed(prog, db):
    """Every area and method with Emerald encounters is reachable by the Champion or listed as never reachable."""
    rows = db.execute("SELECT DISTINCT location, area, method FROM encounters").fetchall()
    unplaced = [
        (loc, area, method) for loc, area, method in rows
        if not prog.opened("champion_wallace", loc, area, method) and prog.never_reason(loc, area, method) is None
    ]
    assert unplaced == []
    overlap = [
        (loc, area, method) for loc, area, method in rows
        if prog.opened("champion_wallace", loc, area, method) and prog.never_reason(loc, area, method)
    ]
    assert overlap == []


def test_gates_only_grow(prog):
    prev_hm, prev_items = set(), set()
    for b in prog.battles:
        assert set(b.hm_gates_open) <= set(HMS), b.id
        assert prev_hm <= set(b.hm_gates_open), b.id
        assert prev_items <= set(b.key_items), b.id
        prev_hm, prev_items = set(b.hm_gates_open), set(b.key_items)
    assert set(prog.get("gym7_tate_liza").hm_gates_open) == {"cut", "flash", "rock-smash", "strength", "surf", "fly"}


def test_sources_cite_existing_guide_chunks(prog):
    ids = {json.loads(line)["source_id"] for line in CHUNKS.read_text(encoding="utf-8").splitlines()}
    missing = [(b.id, b.source) for b in prog.battles if b.source not in ids]
    if prog.get("space_center").partner:
        assert prog.get("space_center").partner["source"] in ids
    assert missing == []


def test_reachability_examples(prog):
    assert not prog.is_reachable("gym1_roxanne", "granite-cave", "1f")
    assert prog.is_reachable("gym2_brawly", "granite-cave", "b2f")
    assert prog.is_reachable("gym6_winona", "hoenn-route-119", None)  # Feebas tiles
    assert not prog.is_reachable("gym5_norman", "hoenn-route-119", None)
    assert not prog.is_reachable("gym8_juan", "meteor-falls", "backsmall-room")  # Bagon needs Waterfall
    assert prog.is_reachable("e4_sidney", "meteor-falls", "backsmall-room")
    assert prog.never_reason("mossdeep-city", "stevens-house")  # Beldum is postgame
    assert prog.is_reachable("gym7_tate_liza", "mossdeep-city", None)


def test_resolved_review_placements(prog):
    """The draft's review flags, as settled from decomp scripts and Bulbapedia (see each battle's notes)."""
    assert all(b.review is None for b in prog.battles)
    # Route 116 and Rusturf Tunnel's west end: open before Roxanne
    assert prog.is_reachable("gym1_roxanne", "hoenn-route-116", None)
    assert prog.is_reachable("gym1_roxanne", "rusturf-tunnel", None)
    # Briney sails to Slateport once Steven has the letter; Aqua grunts hold Route 110 until the museum
    assert prog.is_reachable("gym2_brawly", "slateport-city", None)
    assert not prog.is_reachable("grunts_oceanic_museum", "hoenn-route-110", None, "surf")  # north of the line
    # Mauville's side routes are open before Wally; Route 115's grass isn't reached via Meteor Falls
    assert prog.is_reachable("wally_mauville", "hoenn-route-117", None)
    assert not prog.is_reachable("maxie_mt_chimney", "hoenn-route-115", None, "walk")
    # The Devon Scope opens Lilycove before Winona; the rival waits there from the first visit
    assert prog.is_reachable("gym6_winona", "lilycove-city", None)
    assert prog.get("rival5_lilycove").order == prog.get("gym6_winona").order + 1
    # Rayquaza returns to Sky Pillar before Juan; Meteor Falls past 1F 1R needs Waterfall (Rain Badge)
    assert prog.is_reachable("gym8_juan", "sky-pillar", "apex")
    assert not prog.is_reachable("gym8_juan", "meteor-falls", "b1f")


def test_cross_check_placements(prog):
    """Corrections from the second-model review, each re-verified (see the battles' notes)."""
    # Open-water routes need Surf; the boat ride across them is a cutscene
    for route in ("hoenn-route-105", "hoenn-route-107", "hoenn-route-108"):
        assert not prog.is_reachable("gym5_norman", route, None)
        assert prog.is_reachable("shelly_weather_institute", route, None)
    # Route 115: beach fishing from Rustboro early, grass only in the Surf-only north
    assert prog.is_reachable("gym1_roxanne", "hoenn-route-115", None, "old-rod")
    assert not prog.is_reachable("gym5_norman", "hoenn-route-115", None, "walk")
    assert prog.is_reachable("shelly_weather_institute", "hoenn-route-115", None, "walk")
    # The eastern sea opens by Surf once Team Aqua leaves Lilycove, before Tate & Liza
    for loc in ("hoenn-route-128", "hoenn-route-131", "pacifidlog-town", "hoenn-route-134", "mirage-island"):
        assert prog.is_reachable("gym7_tate_liza", loc, None)
    assert not prog.is_reachable("matt_aqua_hideout", "hoenn-route-126", None)
    # Dive opens Sootopolis and the Regi caves before Shelly at Seafloor Cavern
    for loc in ("sootopolis-city", "desert-ruins", "island-cave", "ancient-tomb"):
        assert prog.is_reachable("shelly_seafloor_cavern", loc, None)
        assert not prog.is_reachable("space_center", loc, None)


def test_second_cross_check_placements(prog):
    """Round two: routes with several unlock points, and postgame gifts in reachable places."""
    # Route 110's first grass is south of the Team Aqua line, so it opens with Slateport
    assert prog.is_reachable("gym2_brawly", "hoenn-route-110", None, "walk")
    assert not prog.is_reachable("grunts_oceanic_museum", "hoenn-route-110", None, "super-rod")
    assert prog.is_reachable("rival3_route110", "hoenn-route-110", None, "super-rod")
    # Route 111: pond fishing and Rock Smash from Mauville, desert grass after the Go-Goggles
    assert prog.is_reachable("wally_mauville", "hoenn-route-111", None, "old-rod")
    assert prog.is_reachable("wally_mauville", "hoenn-route-111", None, "rock-smash")
    assert not prog.is_reachable("gym4_flannery", "hoenn-route-111", None, "walk")
    assert prog.is_reachable("gym5_norman", "hoenn-route-111", None, "walk")
    # Postgame gifts don't make their places unreachable
    assert prog.never_reason("littleroot-town", None, "gift")
    assert prog.never_reason("mossdeep-city", "stevens-house", "gift")
    assert "pokeblock-case" in prog.get("gym6_winona").key_items


def test_tm_and_tutor_places_open(prog, db):
    """Every TM or tutor location opens at some step (towns with no wild Pokémon included)."""
    opened = {s[0] for b in prog.battles for s in b.areas_new}
    places = {l for (l,) in db.execute("SELECT location FROM tm_locations UNION SELECT location FROM move_tutors").fetchall() if l}
    assert places - opened == {"ss-tidal"}  # the S.S. Ticket comes after the Hall of Fame


def test_cave_of_origin_is_open_only_during_the_crisis(prog):
    assert not prog.is_reachable("archie_seafloor_cavern", "cave-of-origin", "1f")
    assert prog.is_reachable("gym8_juan", "cave-of-origin", "1f")
    assert prog.missable_reason("gym8_juan", "cave-of-origin", "1f")
    assert not prog.is_reachable("wally_victory_road", "cave-of-origin", "1f")
    assert "crisis" in prog.closed_reason("champion_wallace", "cave-of-origin", "b1f")


def test_mirage_tower_is_flagged_not_removed(prog):
    assert prog.is_reachable("champion_wallace", "mirage-tower", None)  # falls on the player's action, not a battle
    assert "fossil" in prog.missable_reason("champion_wallace", "mirage-tower", None)
