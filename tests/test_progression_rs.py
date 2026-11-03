"""Consistency checks for data/progression_rs.yaml, loaded for Ruby and for Sapphire, against
each version's database and the Ruby/Sapphire walkthrough corpus (the same checks
test_progression.py runs for Emerald, plus the Ruby/Sapphire-specific steps)."""

import json

import duckdb
import pytest

from agent.games import GAMES
from agent.progression import ALL, RIVALS, STARTERS, load_game, resolve_versions

HMS = ("cut", "flash", "rock-smash", "strength", "surf", "fly", "dive", "waterfall")


@pytest.fixture(scope="module", params=["ruby", "sapphire"])
def game(request):
    return GAMES[request.param]


@pytest.fixture(scope="module")
def prog(game):
    return load_game(game)


@pytest.fixture(scope="module")
def db(game):
    con = duckdb.connect(str(game.db_path), read_only=True)
    yield con
    con.close()


def all_consts(battle):
    if battle.trainer_consts is not None:
        return list(battle.trainer_consts)
    return [c for v in battle.starter_variants.values() for c in v.values()]


def test_version_values_resolve():
    assert resolve_versions({"label": {"ruby": "R", "sapphire": "S"}, "n": [1, {"ruby": 2, "sapphire": 3}]}, "sapphire") == {"label": "S", "n": [1, 3]}
    with pytest.raises(ValueError):
        resolve_versions({"ruby": 1}, "sapphire")


def test_order_and_ids(prog):
    assert [b.order for b in prog.battles] == list(range(1, 30))
    assert len({b.id for b in prog.battles}) == len(prog.battles)
    badges = [b.badges_before for b in prog.battles]
    assert badges == sorted(badges)
    assert prog.battles[-1].id == "champion_steven"


def test_gyms_e4_and_champion(prog):
    gyms = [b for b in prog.battles if b.id.startswith("gym")]
    expected = ["ROXANNE", "BRAWLY", "WATTSON", "FLANNERY", "NORMAN", "WINONA", "TATE_AND_LIZA", "WALLACE"]
    assert [b.trainer_consts[0] for b in gyms] == [f"TRAINER_{n}" for n in expected]
    assert [b.badges_before for b in gyms] == list(range(8))
    tail = [b.trainer_consts[0] for b in prog.battles[-5:]]
    assert tail == ["TRAINER_SIDNEY", "TRAINER_PHOEBE", "TRAINER_GLACIA", "TRAINER_DRAKE", "TRAINER_STEVEN"]


def test_trainer_consts_exist(prog, db):
    known = {c for (c,) in db.execute("SELECT trainer_const FROM trainers WHERE party_size > 0").fetchall()}
    assert [(b.id, c) for b in prog.battles for c in all_consts(b) if c not in known] == []


def test_villain_fights_are_the_versions_team(prog, db, game):
    """Ruby fights only Team Magma ("Team Magma", "Magma Admin", "Magma Leader"), Sapphire only Team Aqua."""
    team = {"ruby": "Magma", "sapphire": "Aqua"}[game.id]
    villain = [b for b in prog.battles if b.id.startswith(("grunt", "admin", "leader"))]
    assert len(villain) == 9
    classes = {name for b in villain for c in all_consts(b)
               for (name,) in db.execute("SELECT class_name FROM trainers WHERE trainer_const = ?", [c]).fetchall()}
    assert classes and all(team in name for name in classes), classes


def test_starter_variants_complete(prog):
    for b in prog.battles:
        if b.trainer_consts is None:
            assert set(b.starter_variants) == set(STARTERS), b.id
            for starter in STARTERS:
                assert set(b.starter_variants[starter]) == set(RIVALS), (b.id, starter)


def test_rival_starters_have_the_advantage(prog, db):
    beats = {"treecko": "torchic", "torchic": "mudkip", "mudkip": "treecko"}
    lines = {"torchic": ("torchic", "combusken"), "mudkip": ("mudkip", "marshtomp"), "treecko": ("treecko", "grovyle")}
    for b in prog.battles:
        if b.trainer_consts is None:
            for starter, v in b.starter_variants.items():
                species = {s for (s,) in db.execute("SELECT species FROM trainer_mons WHERE trainer_const = ?", [v["may"]]).fetchall()}
                assert species & set(lines[beats[starter]]), (b.id, starter, species)


def test_rivals_differ_only_in_one_lead(prog, db):
    """May and Brendan have the same species everywhere; only the Route 110 Mudkip lead differs."""
    teams = {c: list(t) for c, t in db.execute("SELECT trainer_const, list(species ORDER BY slot) FROM trainer_mons GROUP BY 1").fetchall()}
    same_set = [(b.id, s) for b in prog.battles if b.trainer_consts is None for s, v in b.starter_variants.items()
                if sorted(teams[v["may"]]) != sorted(teams[v["brendan"]])]
    order = [(b.id, s) for b in prog.battles if b.trainer_consts is None for s, v in b.starter_variants.items()
             if teams[v["may"]] != teams[v["brendan"]]]
    assert same_set == [] and order == [("rival2_route110", "mudkip")]


def test_battle_format_agrees_with_trainer_structs(prog, db):
    doubles = {c for (c,) in db.execute("SELECT trainer_const FROM trainers WHERE is_double").fetchall()}
    for b in prog.battles:
        assert b.battle_format in ("single", "double"), b.id
        assert (b.battle_format == "double") == any(c in doubles for c in all_consts(b)), b.id


def test_legendary_step(prog, db, game):
    b = prog.get("legendary_cave_of_origin")
    species = {"ruby": "groudon", "sapphire": "kyogre"}[game.id]
    assert b.wild == {"species": species, "level": 45} and b.trainers_for() == []
    assert prog.battles[b.order].id == "gym8_wallace"
    assert prog.is_reachable(b.id, "cave-of-origin", "b4f", "static")
    assert not prog.is_reachable("leader_seafloor_cavern", "cave-of-origin", "1f", "walk")
    row = db.execute("SELECT min_level FROM encounters e JOIN species s USING (species_id) WHERE s.identifier = ? AND e.method = 'static'", [species]).fetchall()
    assert row == [(45,)]


def test_hideout_is_the_versions(prog, game):
    hideout = {"ruby": "team-magma-hideout", "sapphire": "team-aqua-hideout"}[game.id]
    assert prog.get("admin_hideout").location == hideout
    assert prog.is_reachable("gym6_winona", hideout, None, "static")


def test_locations_exist(prog, db):
    known = {l for (l,) in db.execute("SELECT identifier FROM locations").fetchall()}
    assert [b.location for b in prog.battles if b.location not in known] == []


def test_area_specs_exist(prog, db):
    areas = set(db.execute("SELECT location, area FROM location_areas").fetchall())
    methods = {m for (m,) in db.execute("SELECT DISTINCT method FROM encounters").fetchall()}
    locations = {l for (l,) in db.execute("SELECT identifier FROM locations").fetchall()}
    specs = [(b.id, s) for b in prog.battles for s in b.areas_new] + [("never", s) for s, _ in prog.never_reachable]
    assert [(who, s) for who, s in specs if (s[0] not in locations if s[1] == ALL else (s[0], s[1]) not in areas)] == []
    assert [(who, s) for who, s in specs if s[2] and not set(s[2]) <= methods] == []


def test_each_area_opens_once(prog):
    seen = []
    for b in prog.battles:
        for spec in b.areas_new:
            for other, where in seen:
                same_area = other[:2] == spec[:2] or ALL in (other[1], spec[1]) and other[0] == spec[0]
                same_methods = other[2] is None or spec[2] is None or set(other[2]) & set(spec[2])
                assert not (same_area and same_methods), (spec, where, b.id)
            seen.append((spec, b.id))


def test_every_encounter_area_is_placed(prog, db):
    rows = db.execute("SELECT DISTINCT location, area, method FROM encounters").fetchall()
    unplaced = [r for r in rows if not prog.is_reachable("champion_steven", *r) and prog.never_reason(*r) is None]
    overlap = [r for r in rows if prog.is_reachable("champion_steven", *r) and prog.never_reason(*r)]
    assert unplaced == [] and overlap == []


def test_gates_only_grow(prog):
    prev_hm, prev_items = set(), set()
    for b in prog.battles:
        assert set(b.hm_gates_open) <= set(HMS), b.id
        assert prev_hm <= set(b.hm_gates_open) and prev_items <= set(b.key_items), b.id
        prev_hm, prev_items = set(b.hm_gates_open), set(b.key_items)


def test_sources_cite_existing_guide_chunks(prog, game):
    chunks = [json.loads(line) for line in (game.guide_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    versions = {c["source_id"]: c["versions"] for c in chunks}
    assert [(b.id, b.source) for b in prog.battles if b.source not in versions] == []
    # A version-marked section is only cited for its own version.
    assert [(b.id, b.source) for b in prog.battles if game.id not in versions[b.source]] == []


def test_events_follow_real_battles(prog):
    ids = {b.id for b in prog.battles}
    assert len(prog.events) == 9 and all(e["after"] in ids for e in prog.events)


def test_tm_places_open(prog, db):
    places = {l for (l,) in db.execute("SELECT location FROM tm_locations").fetchall() if l}
    never_ok = {"ss-tidal"}  # TM49, after the Hall of Fame
    assert sorted(l for l in places - never_ok if not any(s[0] == l for b in prog.battles for s in b.areas_new)) == []
