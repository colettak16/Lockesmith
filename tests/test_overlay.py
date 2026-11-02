"""A loaded randomizer log as session views (agent/overlay.py, D11): the unchanged tools read
the randomized game, other sessions keep vanilla, and what the log changed but Lockesmith
can't read is refused rather than answered from vanilla. Uses the hand-written logs in
test_log_parser.py (no real UPR log is in tests/fixtures/ yet)."""

import pytest
from fastapi.testclient import TestClient

import app as app_module
from agent import pipeline
from agent.brief import state_brief
from agent.context import RequestContext
from agent.db import connect_session, session_cursor
from agent.session import SESSIONS
from agent.state import RunState
from agent.tools import battles, encounters, guide, moves
from agent.tools.common import ToolError
from test_log_parser import CHANGES_LOG, SAMPLE

EVOLUTIONS_LOG = """\
Randomizer Version: 4.6.1

--Randomized Evolutions--
ZIGZAGOON      -> GARDEVOIR
EEVEE          -> PIKACHU, RAICHU, BULBASAUR, IVYSAUR and VENUSAUR
"""


def loaded(text: str, session_id: str, **state) -> RequestContext:
    pipeline.load_log(text, f"{session_id}.log", session_id)
    s = SESSIONS.get(session_id)
    return RequestContext(state=RunState(**({"starter": "mudkip", "badges": []} | state)), con=s.con, randomizer=s.randomizer)


@pytest.fixture(scope="module")
def sample():
    return loaded(SAMPLE, "ov-sample")


@pytest.fixture(scope="module")
def changes():
    return loaded(CHANGES_LOG, "ov-changes")


def q(ctx, sql, params=()):
    return session_cursor(ctx.con).execute(sql, list(params)).fetchall()


def test_wild_slots_match_the_vanilla_numbering(sample):
    rods = q(sample, "SELECT method, slot, rarity FROM encounters WHERE location = 'hoenn-route-102' "
                     "AND method LIKE '%rod' ORDER BY method, slot")
    assert rods == [("good-rod", 1, 60), ("good-rod", 2, 20), ("good-rod", 3, 20), ("old-rod", 1, 70), ("old-rod", 2, 30),
                    ("super-rod", 1, 40), ("super-rod", 2, 40), ("super-rod", 3, 15), ("super-rod", 4, 4), ("super-rod", 5, 1)]
    (total,) = q(sample, "SELECT sum(rarity) FROM encounters WHERE location = 'hoenn-route-101' AND method = 'walk'")[0]
    assert total == 100


def test_catch_tool_reads_the_log(sample):
    """Treecko isn't wild in vanilla Emerald; in this log it's on Route 101."""
    found = encounters.catchable(sample, "gym1_roxanne", "treecko")["species"]
    assert found[0]["places"][0]["where"] == "Route 101" and found[0]["places"][0]["source_id"] == "log:wild#Set1"


def test_other_sessions_keep_vanilla(sample):
    vanilla = RequestContext(state=RunState(starter="mudkip", badges=[]), con=connect_session())
    assert encounters.catchable(vanilla, "gym1_roxanne", "treecko")["species"] == []


def test_starters_and_statics_are_remapped(sample):
    gifts = q(sample, "SELECT s.identifier FROM encounters e JOIN species s USING (species_id) "
                      "WHERE e.location = 'hoenn-route-101' AND e.method = 'gift' ORDER BY 1")
    assert [g for (g,) in gifts] == ["bagon", "beldum", "larvitar"]
    mauville = q(sample, "SELECT s.identifier FROM encounters e JOIN species s USING (species_id) "
                         "WHERE e.location = 'new-mauville' AND e.method = 'static' ORDER BY 1")
    assert [m for (m,) in mauville] == ["electrode", "pikachu"]
    assert "starter slot (mudkip) is larvitar" in state_brief(sample)


def test_randomized_trainer_gets_its_new_species_default_moves(sample):
    roxanne = battles.trainer_team(sample, "gym1_roxanne")["teams"][0]["pokemon"]
    assert [(m["species"], m["level"]) for m in roxanne] == [("Geodude", 12), ("Geodude", 12), ("Nosepass", 15)]
    assert roxanne[2]["held_item"] == "oran-berry" and roxanne[0]["moves"] and roxanne[0]["source_id"] == "log:trainers#265"
    assert roxanne[0]["moves_source"].startswith("default")


def test_tm_moves_follow_the_tm_number(sample):
    tm01 = next(t for t in moves.tm_availability(sample, "gym8_juan")["available"] if t["label"] == "TM01")
    assert tm01["move"] == "Thunderbolt"
    # Machop can use TM01 (Focus Punch in vanilla), so in this run it learns Thunderbolt from it
    assert ("TM01", "Thunderbolt") in {(t["label"], t["name"]) for t in moves.learnset(sample, "machop")["tm_hm"]}


def test_evolution_updates_and_friendship(changes):
    evos = {e["to"]: e["how"] for e in moves.species_info(changes, "eevee")["evolutions"] if e["from"] == "Eevee"}
    assert "sun-stone" in evos["Espeon"] and "friendship >= 160" in evos["Umbreon"]
    feebas = moves.species_info(changes, "feebas")["evolutions"][0]
    assert "level 25" in feebas["how"] and "beauty" not in feebas["how"]  # the overwritten Lv30 change is skipped


def test_random_evolutions_keep_methods_and_regroup_families():
    ctx = loaded(EVOLUTIONS_LOG, "ov-evos")
    evos = {e["to"]: e["how"] for e in moves.species_info(ctx, "eevee")["evolutions"] if e["from"] == "Eevee"}
    # evolution.h order is Jolteon, Vaporeon, Flareon, Espeon, Umbreon: Thunder Stone first
    assert "thunder-stone" in evos["Pikachu"] and "water-stone" in evos["Raichu"] and "night" in evos["Venusaur"]
    chains = dict(q(ctx, "SELECT identifier, evolution_chain_id FROM species WHERE identifier IN ('zigzagoon', 'ralts', 'linoone')"))
    assert chains["zigzagoon"] == chains["ralts"] != chains["linoone"]  # the dupes clause sees the new family


def test_unreadable_changes_are_refused(changes):
    ls = moves.learnset(changes, "machop", 20)
    assert ls["level_up"] == [] and ls["tm_hm"] == [] and set(ls["unknown"]) == {"movesets", "tm_compatibility"}
    roxanne = battles.trainer_team(changes, "gym1_roxanne")["teams"][0]["pokemon"]
    assert roxanne[0]["moves_source"].startswith("Metronome only")
    assert "unknown" in moves.tm_availability(changes, "gym8_juan", "machop")


def test_unreadable_move_data_blocks_move_info():
    ctx = loaded("--Move Data--\nwhatever\n", "ov-movedata")
    with pytest.raises(ToolError, match="move data"):
        moves.move_info(ctx, "surf")


def test_guide_warns_in_a_randomized_run(sample):
    assert "vanilla game" in guide.search_guide(sample, "Route 104")["note"]


def test_a_new_log_replaces_the_old_one():
    first = loaded(SAMPLE, "ov-replace")
    assert encounters.catchable(first, "gym1_roxanne", "treecko")["species"]
    second = loaded(CHANGES_LOG, "ov-replace")
    assert second.randomizer["shadowed"] == ["evolutions"]
    assert encounters.catchable(second, "gym1_roxanne", "treecko")["species"] == []


def test_upload_endpoint():
    client = TestClient(app_module.app)
    body = client.post("/upload_log", json={"log_text": SAMPLE, "name": "mine.log"}).json()
    assert body["session_id"] and body["log_id"] == "mine.log" and "encounters" in body["shadowed"]
    assert body["unread"] == {"some future section": "some future section"}
    state = client.get("/run_state", params={"session_id": body["session_id"]}).json()
    assert state["run_state"]["randomizer_log_id"] == "mine.log" and state["randomizer"]["seed"] == "12345"
    assert client.post("/upload_log", json={"log_text": "just some text"}).status_code == 422
