"""Agent tools against facts already verified in Phase 1 (no model calls)."""

import json

import pytest

from agent.context import RequestContext
from agent.db import connect_session
from agent.evidence import Ledger
from agent.progression import load
from agent.state import PartyMember, RunState, Ruleset, progress
from agent.tools import battles, encounters, guide, moves, sql, story
from agent.tools.common import ToolError, guarded


@pytest.fixture(scope="module")
def con():
    c = connect_session()
    yield c
    c.close()


def ctx_for(con, **state) -> RequestContext:
    return RequestContext(state=RunState(**state), con=con)


# --- run state ---------------------------------------------------------------------------------


def test_badges_accept_leaders_and_badge_names():
    assert RunState(badges=["Roxanne", "Knuckle Badge", "gym3_wattson"]).badges == ["stone", "knuckle", "dynamo"]
    assert RunState().missing_required() == ["starter", "badges"]
    assert RunState(starter="Mudkip", badges=[]).missing_required() == []


def test_progress_handles_a_deferred_gym():
    p = progress(RunState(starter="mudkip", badges=["stone", "dynamo", "heat"]), load())
    assert [b.id for b in p.deferred] == ["gym2_brawly"]
    assert p.next_battle.id == "gym5_norman"
    assert p.remaining[0].id == "gym2_brawly"


def test_progress_from_scratch_and_from_last_battle():
    assert progress(RunState(starter="treecko", badges=[]), load()).next_battle.id == "rival1_route103"
    p = progress(RunState(starter="treecko", badges=["stone"], last_battle="grunt_rusturf_tunnel"), load())
    assert p.next_battle.id == "rival2_rustboro"


# --- battles -----------------------------------------------------------------------------------


def test_trainer_team_juan(con):
    t = battles.trainer_team(ctx_for(con, starter="mudkip", badges=[]), "Juan")
    mons = t["teams"][0]["pokemon"]
    assert [(m["species"], m["level"]) for m in mons][-1] == ("Kingdra", 46)
    assert mons[-1]["ability"] == "swift-swim" and mons[-1]["held_item"] == "chesto-berry"


def test_rival_team_lists_both_rivals_when_they_differ(con):
    t = battles.trainer_team(ctx_for(con, starter="torchic", badges=["stone"]), "rival2_rustboro")
    assert len(t["teams"]) == 2 and t["rival_note"]
    one = battles.trainer_team(ctx_for(con, starter="torchic", badges=["stone"], rival="may"), "rival2_rustboro")
    assert len(one["teams"]) == 1


def test_rival_needs_starter(con):
    with pytest.raises(ToolError):
        battles.trainer_team(ctx_for(con, badges=[]), "rival1_route103")


def test_remaining_battles_from_seven_badges(con):
    ctx = ctx_for(con, starter="mudkip", badges=["stone", "knuckle", "dynamo", "heat", "balance", "feather", "mind"])
    r = battles.remaining_battles(ctx)
    assert r["next_battle"] == "space_center"
    assert r["battles"][-1]["battle_id"] == "champion_wallace"


def test_threat_matrix_ground_type_ignores_electric(con):
    ctx = ctx_for(con, starter="mudkip", badges=["stone", "knuckle"], party=[PartyMember(species="Marshtomp", level=24)])
    m = battles.threat_matrix(ctx, "gym3_wattson")
    assert all(not row["threatens"] or all(t["member"] != "Marshtomp" or "Electric" not in t["move"] for t in row["threatens"]) for row in m["matchups"])
    assert m["assumptions"]  # moves weren't given, so the default moveset was used


def test_threat_matrix_needs_a_party(con):
    with pytest.raises(ToolError):
        battles.threat_matrix(ctx_for(con, starter="mudkip", badges=[]), "gym1_roxanne")


# --- encounters --------------------------------------------------------------------------------


def names(result) -> set[str]:
    return {s["species"] for s in result["species"]}


def test_catchable_before_roxanne(con):
    r = encounters.catchable(ctx_for(con, starter="mudkip", badges=[]), "gym1_roxanne")
    assert {"Whismur", "Nincada"} <= names(r)  # Rusturf Tunnel and Route 116 open before her
    assert not any(p["method"] == "surf" for s in r["species"] for p in s["places"])


def test_starters_and_fossils_are_not_early_catches(con):
    r = encounters.catchable(ctx_for(con, starter="mudkip", badges=["stone", "knuckle"]), "gym3_wattson")
    assert not {"Treecko", "Torchic", "Mudkip", "Anorith", "Lileep"} & names(r)
    assert r["species"][0]["wild"]  # wild catches sort before gifts and trades
    for fossil in ("Anorith", "Lileep"):
        later = encounters.catchable(ctx_for(con, starter="mudkip", badges=["stone", "knuckle"]), "shelly_weather_institute", species=fossil)
        assert names(later) == {fossil} and "Mirage Tower" in later["species"][0]["places"][0]["note"]


def test_bagon_needs_waterfall(con):
    ctx = ctx_for(con, starter="mudkip", badges=["stone", "knuckle", "dynamo", "heat", "balance", "feather", "mind"])
    before_juan = encounters.catchable(ctx, "gym8_juan", species="Bagon")
    assert before_juan["species"] == [] and before_juan["why_not"]
    assert names(encounters.catchable(ctx, "wally_victory_road", species="Bagon")) == {"Bagon"}


def test_rules_filter_candidates(con):
    rules = Ruleset(monotype="grass", no_legendaries=True, banned_species=["Lotad"])
    ctx = ctx_for(con, starter="treecko", badges=["stone", "knuckle", "dynamo", "heat", "balance"], ruleset=rules)
    r = encounters.catchable(ctx, "gym6_winona")
    assert r["species"] and all("grass" in s["types"] for s in r["species"])
    assert "Lotad" not in names(r) and r["excluded_by_rules"]


def test_session_rejections_filter_candidates(con):
    ctx = ctx_for(con, starter="treecko", badges=[])
    ctx.excluded_species = {"whismur"}
    assert "Whismur" not in names(encounters.catchable(ctx, "gym1_roxanne"))


def test_encounter_odds_route_119_feebas(con):
    r = encounters.encounter_odds(ctx_for(con, starter="mudkip", badges=[]), "Route 119")
    assert any(e["species"] == "Feebas" and e["method"] == "feebas-tile-fishing" for e in r["encounters"])


# --- moves and TMs -----------------------------------------------------------------------------


def test_brawly_tm_only_after_brawly(con):
    ctx = ctx_for(con, starter="mudkip", badges=["stone"])
    before = {r["label"] for r in moves.tm_availability(ctx, "gym2_brawly")["available"]}
    after = {r["label"] for r in moves.tm_availability(ctx, "gym3_wattson")["available"]}
    assert "TM08" not in before and "TM08" in after


def test_learnset_and_varies_category(con):
    ctx = ctx_for(con, starter="mudkip", badges=[])
    ls = moves.learnset(ctx, "Mudkip", 16)
    assert ls["default_moveset_at_level"] and ls["tm_hm"]
    assert "varies" in moves.move_info(ctx, "Hidden Power")["damage_class"]
    assert moves.species_info(ctx, "Gardevoir")["types"] == ["psychic"]


# --- story, guide, sql -------------------------------------------------------------------------


def test_next_steps_from_scratch(con):
    s = story.next_steps(ctx_for(con, starter="treecko", badges=[]))
    assert s["next"]["battle_id"] == "rival1_route103" and len(s["then"]) == 2


def test_story_outline_ends_at_champion(con):
    o = story.story_outline(ctx_for(con, starter="treecko", badges=["stone"]))
    assert o["remaining"][-1]["battle_id"] == "champion_wallace"


def test_search_guide_finds_feebas():
    hits = guide.search("Feebas fishing Route 119")
    assert hits and any("Feebas" in h["text"] for h in hits)


def test_query_db_is_read_only(con):
    ctx = ctx_for(con, starter="treecko", badges=[])
    assert sql.query_db(ctx, "select count(*) as n from species")["rows"] == [[386]]
    for bad in ("drop table species", "select 1; drop table species", "with x as (select 1) insert into t select * from x"):
        with pytest.raises(ToolError):
            sql.query_db(ctx, bad)


# --- ledger ------------------------------------------------------------------------------------


def test_tool_output_feeds_the_ledger(con):
    ctx = ctx_for(con, starter="mudkip", badges=[])
    text = guarded(battles.trainer_team)(ctx, "Juan")
    assert json.loads(text)["teams"]
    assert "progression:gym8_juan" in ctx.ledger and any(k.startswith("decomp:") for k in ctx.ledger.entries)
    err = json.loads(guarded(battles.trainer_team)(ctx, "Professor Oak"))
    assert "error" in err


def test_cite_numbers_known_ids_and_drops_unknown():
    ledger = Ledger()
    ledger.add("progression:gym8_juan")
    ledger.add("guide:Walkthrough:Pokemon_Emerald/Part_17#Sootopolis_Gym")
    text, citations, unknown = ledger.cite(
        "Juan is next [[progression:gym8_juan]]. Gym puzzle [[guide:Walkthrough:Pokemon_Emerald/Part_17#Sootopolis_Gym, made:up]]."
    )
    assert text == "Juan is next [1]. Gym puzzle [2]."
    assert [c["n"] for c in citations] == [1, 2] and citations[1]["url"].startswith("https://bulbapedia")
    assert unknown == ["made:up"]


def test_cite_handles_ids_with_commas():
    ledger = Ledger()
    ledger.add("guide:Walkthrough:Pokemon_Emerald/Part_2#Stop,_Thief!")
    ledger.add("progression:gym1_roxanne")
    text, citations, unknown = ledger.cite(
        "Chase the grunt [[guide:Walkthrough:Pokemon_Emerald/Part_2#Stop,_Thief!, progression:gym1_roxanne]]."
    )
    assert text == "Chase the grunt [1][2]." and unknown == []
