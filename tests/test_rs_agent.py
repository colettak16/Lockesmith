"""The agent layer on Ruby and Sapphire: run state, sessions, tools, search and citations read
the right game's data (no model calls)."""

import pytest

from agent.catalog import catalog
from agent.context import RequestContext
from agent.db import connect_session
from agent.games import GAMES
from agent.session import Session
from agent.state import RunState, normalize_badge, progress
from agent.progression import load_game
from agent.tools import battles, encounters, guide, moves, outlook, story

ALL_BADGES = ["stone", "knuckle", "dynamo", "heat", "balance", "feather", "mind"]


@pytest.fixture(scope="module", params=["ruby", "sapphire"])
def game(request):
    return GAMES[request.param]


@pytest.fixture(scope="module")
def con(game):
    c = connect_session(game)
    yield c
    c.close()


def ctx_for(con, game, **state) -> RequestContext:
    return RequestContext(state=RunState(game=game.id, **state), con=con)


def test_wallace_is_a_leader_only_in_ruby_and_sapphire():
    assert normalize_badge("Wallace", "ruby") == "rain" and normalize_badge("Juan", "emerald") == "rain"
    with pytest.raises(ValueError):
        normalize_badge("Wallace", "emerald")  # Emerald's Champion, not a gym
    assert RunState(game="Pokémon Sapphire", badges=["Wallace"]).badges == ["rain"]


def test_progress_uses_the_games_gyms(game):
    p = progress(RunState(game=game.id, starter="mudkip", badges=ALL_BADGES), load_game(game))
    assert p.next_battle.id == "admin_seafloor_cavern"
    assert [b.id for b in p.remaining][:4] == ["admin_seafloor_cavern", "leader_seafloor_cavern", "legendary_cave_of_origin", "gym8_wallace"]


def test_context_reads_the_games_data(con, game):
    ctx = ctx_for(con, game, starter="mudkip", badges=ALL_BADGES)
    assert ctx.prog.battles[-1].id == "champion_steven"
    assert ctx.cursor().execute("SELECT value FROM build_info WHERE key = 'game'").fetchone() == (game.id,)


def test_scout_wallace(con, game):
    s = battles.scout_battle(ctx_for(con, game, starter="mudkip", badges=ALL_BADGES), "Wallace")
    assert s["battle_id"] == "gym8_wallace"
    assert [m["species"] for m in s["teams"][0]["pokemon"]][-1] == "Milotic"


def test_villain_and_legendary_by_version(con, game):
    ctx = ctx_for(con, game, starter="mudkip", badges=ALL_BADGES)
    leader = battles.trainer_team(ctx, "leader_seafloor_cavern")
    ace = {"ruby": "Camerupt", "sapphire": "Sharpedo"}[game.id]
    assert leader["teams"][0]["pokemon"][-1]["species"] == ace
    legend = battles.trainer_team(ctx, "legendary_cave_of_origin")["teams"][0]["pokemon"]
    assert [(m["species"], m["level"]) for m in legend] == [({"ruby": "Groudon", "sapphire": "Kyogre"}[game.id], 45)]
    assert len(legend[0]["moves"]) == 4 and legend[0]["source_id"].startswith("pokeapi:encounters#")


def test_waterfall_is_available_before_wallace(con, game):
    tms = moves.tm_availability(ctx_for(con, game, starter="mudkip", badges=ALL_BADGES), "gym8_wallace")
    assert any(t["label"] == "HM07" for t in tms["available"])


def test_version_ghosts_before_tate_and_liza(con, game):
    ctx = ctx_for(con, game, starter="mudkip", badges=ALL_BADGES[:6])
    found = {r["species"] for r in encounters.catchable(ctx, "gym7_tate_liza", types=["ghost"])["species"]}
    has = {"ruby": "Duskull", "sapphire": "Shuppet"}[game.id]
    assert has in found


def test_gauntlet_and_outline_cover_the_legendary(con, game):
    ctx = ctx_for(con, game, starter="mudkip", badges=ALL_BADGES)
    ids = [b["battle_id"] for b in story.story_outline(ctx)["remaining"]]
    assert "legendary_cave_of_origin" in ids and ids[-1] == "champion_steven"
    assert outlook.gauntlet_overview(ctx)["battles"]


def test_search_skips_the_other_versions_sections(game):
    hits = [p["source_id"] for p in guide.search("VS Maxie VS Archie Mt. Chimney", k=6, game_id=game.id)]
    other = {"ruby": "Archie_(Sapphire)", "sapphire": "Maxie_(Ruby)"}[game.id]
    assert hits and not any(other in h for h in hits)


def test_citations_point_at_pokeruby(con, game):
    ctx = ctx_for(con, game, starter="mudkip", badges=[])
    ctx.ledger.add("decomp:trainer_parties.h#gTrainerParty_Roxanne/1")
    _, cites, _ = ctx.ledger.cite("Roxanne [[decomp:trainer_parties.h#gTrainerParty_Roxanne/1]]")
    assert cites[0]["url"].startswith("https://github.com/pret/pokeruby/blob/")


def test_catalog_badges_follow_the_game(game):
    c = catalog(game.id)
    assert c["game"] == game.id and {b["id"]: b["gym"] for b in c["badges"]}["rain"] == "gym8_wallace"
    assert catalog("emerald")["badges"][-1]["gym"] == "gym8_juan"


def test_session_switches_database_with_the_game():
    s = Session(id="t")
    s.randomizer = {"log_id": "x"}
    s.state = RunState(game="sapphire", starter="mudkip", badges=[])
    assert s.sync_game() and s.randomizer is None
    assert s.con.execute("SELECT value FROM base.build_info WHERE key = 'game'").fetchone() == ("sapphire",)
    assert not s.sync_game()
    s.con.close()


def test_hideout_electrode_until_the_mind_badge(con, game):
    before = encounters.catchable(ctx_for(con, game, starter="mudkip", badges=ALL_BADGES[:6]), "gym7_tate_liza", species="electrode")
    hideout = [p for p in before["species"][0]["places"] if p["method"] == "static"]
    assert hideout and "Mind Badge" in hideout[0]["missable"]
    after = encounters.catchable(ctx_for(con, game, starter="mudkip", badges=ALL_BADGES), "admin_seafloor_cavern", species="electrode")
    assert [(p["where"], p["method"]) for sp in after["species"] for p in sp["places"]] == [("New Mauville", "walk")]


def test_next_steps_warn_before_an_area_closes(con, game):
    steps = story.next_steps(ctx_for(con, game, starter="mudkip", badges=ALL_BADGES[:6]))
    last_chance = {s["battle_id"]: s.get("closes_for_good_after_it") for s in [steps["next"], *steps["then"]]}
    assert "Mind Badge" in last_chance["gym7_tate_liza"][0]


def test_legendary_not_offered_after_its_battle(con, game):
    legend = {"ruby": "groudon", "sapphire": "kyogre"}[game.id]
    out = encounters.catchable(ctx_for(con, game, starter="mudkip", badges=ALL_BADGES), "gym8_wallace", species=legend)
    assert out["species"] == [] and "closed for good" in out["why_not"][0]


def test_brief_rules_out_emerald_field_abilities(con, game):
    from agent.brief import state_brief
    text = state_brief(ctx_for(con, game, starter="mudkip"))
    assert "Synchronize" in text and "Compound Eyes" in text and "Stench" in text
    assert "Pickup does work" in text and "King's Rock 1%" in text  # review round 4: Pickup is Ruby/Sapphire too


def test_hideout_electrode_needs_the_slateport_scene_until_the_hideout(con, game):
    # Reaching Lilycove isn't enough: E-03 then E-04 must have happened, which the run state can't show
    early = encounters.catchable(ctx_for(con, game, starter="mudkip", badges=ALL_BADGES[:6]), "gym6_winona", species="electrode")
    hideout = [p for p in early["species"][0]["places"] if p["method"] == "static"]
    assert hideout and hideout[0]["only_after_story_events"][0].startswith("slateport_submarine_theft")
    later = encounters.catchable(ctx_for(con, game, starter="mudkip", badges=ALL_BADGES[:6]), "gym7_tate_liza", species="electrode")
    assert "only_after_story_events" not in [p for p in later["species"][0]["places"] if p["method"] == "static"][0]
