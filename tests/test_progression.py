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
    locations = {l for l, _ in areas}
    specs = [(b.id, s) for b in prog.battles for s in b.areas_new] + [("never", s) for s, _ in prog.never_reachable]
    bad = [(who, s) for who, s in specs if (s[0] not in locations if s[1] == ALL else s not in areas)]
    assert bad == []


def test_each_area_opens_once(prog):
    seen = {}
    for b in prog.battles:
        for spec in b.areas_new:
            assert spec not in seen, (spec, seen.get(spec), b.id)
            seen[spec] = b.id


def test_every_encounter_area_is_placed(prog, db):
    """Every area with Emerald encounters is either reachable by the Champion or listed as never reachable."""
    areas = db.execute("SELECT DISTINCT location, area FROM encounters").fetchall()
    unplaced = [
        (loc, area) for loc, area in areas
        if not prog.is_reachable("champion_wallace", loc, area) and prog.never_reason(loc, area) is None
    ]
    assert unplaced == []
    overlap = [(loc, area) for loc, area in areas if prog.is_reachable("champion_wallace", loc, area) and prog.never_reason(loc, area)]
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
    assert not prog.is_reachable("grunts_oceanic_museum", "hoenn-route-110", None)
    # Mauville's side routes are open before Wally; Route 115's grass only via Meteor Falls
    assert prog.is_reachable("wally_mauville", "hoenn-route-117", None)
    assert not prog.is_reachable("gym3_wattson", "hoenn-route-115", None)
    # The Devon Scope opens Lilycove before Winona; the rival waits there from the first visit
    assert prog.is_reachable("gym6_winona", "lilycove-city", None)
    assert prog.get("rival5_lilycove").order == prog.get("gym6_winona").order + 1
    # Rayquaza returns to Sky Pillar before Juan; Meteor Falls past 1F 1R needs Waterfall (Rain Badge)
    assert prog.is_reachable("gym8_juan", "sky-pillar", "apex")
    assert not prog.is_reachable("gym8_juan", "meteor-falls", "b1f")
