"""The Verifier: every violation code, and backups replacing failed picks (PLAN.md §13 Phase 3)."""

import pytest

from agent.context import RequestContext
from agent.db import connect_session, session_cursor
from agent.schemas import Alternative, LeadDraft, Recommendation
from agent.state import PartyMember, RunState, Ruleset
from agent.verifier import CODES, ERROR, WARNING, check_pick, promote_backups, verify

SIX_BADGES = ["stone", "knuckle", "dynamo", "heat", "balance", "feather"]
CITED = ["progression:gym7_tate_liza"]
covered: set[str] = set()


@pytest.fixture(scope="module")
def con():
    c = connect_session()
    yield c
    c.close()


def ctx_for(con, **kw) -> RequestContext:
    state = {"starter": "mudkip", "badges": SIX_BADGES, **kw}
    ctx = RequestContext(state=RunState(**state), con=con)
    ctx.ledger.add(CITED[0])
    return ctx


def pick(species, battle="gym7_tate_liza", evolve_to="", key_moves=(), why="fits", source_ids=CITED, alts=()):
    return Recommendation(species=species, role="r", horizon="core", before_battle=battle, where="w", when="w",
                          why=why, long_term="lt", evolve_to=evolve_to, key_moves=list(key_moves),
                          source_ids=list(source_ids), alternatives=list(alts))


def alt(species, **kw):
    return Alternative(species=species, horizon="core", where="w", why="fits", long_term="lt",
                       evolve_to=kw.get("evolve_to", ""), key_moves=list(kw.get("key_moves", ())), source_ids=CITED)


def found(ctx, p, severity=None) -> set[str]:
    vs = check_pick(ctx, p, p.before_battle, 0, None)
    covered.update(v.code for v in vs)
    return {v.code for v in vs if severity is None or v.severity == severity}


def test_a_sound_pick_passes(con):
    ctx = ctx_for(con)
    move = session_cursor(con).execute(
        "SELECT m.name FROM learnsets l JOIN moves m USING (move_id) JOIN species s USING (species_id) "
        "WHERE s.identifier = 'absol' AND l.method = 'level-up' AND l.level <= 30 AND m.power > 0 LIMIT 1"
    ).fetchone()[0]
    assert found(ctx, pick("Absol", key_moves=[move]), ERROR) == set()


def test_not_obtainable_before(con):
    assert "NOT_OBTAINABLE_BEFORE" in found(ctx_for(con), pick("Bagon", "gym8_juan"))  # needs Waterfall


def test_evolution_not_reachable(con):
    assert "EVOLUTION_NOT_REACHABLE" in found(ctx_for(con), pick("Machop", "champion_wallace", evolve_to="Machamp"))
    assert "EVOLUTION_NOT_REACHABLE" in found(ctx_for(con), pick("Shuppet", evolve_to="Dusclops"))


def test_evolution_item_is_flagged_not_failed(con):
    assert "EVOLUTION_ITEM_UNVERIFIED" in found(ctx_for(con), pick("Pikachu", evolve_to="Raichu"), WARNING)


def test_move_not_learnable(con):
    assert "MOVE_NOT_LEARNABLE" in found(ctx_for(con), pick("Shuppet", key_moves=["Surf"]))


def test_tm_from_a_town_without_wild_pokemon(con):
    """TM24 Thunderbolt is sold and given in Mauville City, which has no encounter table."""
    ctx = ctx_for(con, badges=SIX_BADGES + ["mind"])
    assert "MOVE_NOT_LEARNABLE" not in found(ctx, pick("Chinchou", "gym8_juan", evolve_to="Lanturn", key_moves=["Thunderbolt"]))


def test_split_mismatch_is_a_warning(con):
    assert "GEN3_SPLIT_MISMATCH" in found(ctx_for(con), pick("Absol", key_moves=["Crunch"]), WARNING)


def test_gen3_anachronisms(con):
    ctx = ctx_for(con)
    assert "GEN3_ANACHRONISM" in found(ctx, pick("Lucario"))
    assert "GEN3_ANACHRONISM" in found(ctx, pick("Absol", key_moves=["Dazzling Gleam"]))
    assert "GEN3_ANACHRONISM" in found(ctx, pick("Absol", why="It resists Fairy moves"))


def test_nuzlocke_used_area_and_dupes(con):
    used = ctx_for(con, ruleset=Ruleset(nuzlocke=True, used_routes=["Route 120"]))
    assert "NUZLOCKE_ROUTE_USED" in found(used, pick("Absol"))  # Absol is only on Route 120
    dupes = ctx_for(con, party=[PartyMember(species="Lombre", level=30)], ruleset=Ruleset(nuzlocke=True, dupes_clause=True))
    assert "NUZLOCKE_DUPE" in found(dupes, pick("Lotad"))


def test_single_type_rule(con):
    assert "RULESET_TYPE_VIOLATION" in found(ctx_for(con, ruleset=Ruleset(monotype="grass")), pick("Absol"))
    # Nincada is Bug/Ground; Ninjask drops Ground
    assert "RULESET_TYPE_VIOLATION" in found(ctx_for(con, ruleset=Ruleset(monotype="ground")), pick("Nincada", evolve_to="Ninjask"))


def test_bans_rejections_legendaries_wild_only(con):
    assert "RULESET_BANNED" in found(ctx_for(con, ruleset=Ruleset(banned_species=["absol"])), pick("Absol"))
    rejected = ctx_for(con)
    rejected.excluded_species = {"absol"}
    assert "RULESET_REJECTED" in found(rejected, pick("Absol"))
    assert "RULESET_NO_LEGENDARIES" in found(ctx_for(con, ruleset=Ruleset(no_legendaries=True)), pick("Regirock", "champion_wallace"))
    assert "RULESET_WILD_ONLY" in found(ctx_for(con, ruleset=Ruleset(wild_only=True)), pick("Castform", "gym6_winona"))


def test_level_cap(con):
    capped = ctx_for(con, badges=SIX_BADGES[:5], ruleset=Ruleset(level_caps=True))
    assert "OVER_LEVEL_CAP" in found(capped, pick("Trapinch", "gym6_winona", evolve_to="Vibrava"))  # Vibrava is Lv35


def test_citations(con):
    ctx = ctx_for(con)
    assert "UNCITED_CLAIM" in found(ctx, pick("Absol", source_ids=[]))
    assert "CITATION_NOT_IN_EVIDENCE" in found(ctx, pick("Absol", source_ids=["made:up"]))


def test_move_unverifiable_when_the_log_hides_movesets(con):
    """A randomized run whose movesets the log changed unreadably: warn, don't reject (D11)."""
    ctx = ctx_for(con)
    ctx.randomizer = {"changes": {"movesets": "metronome-only"}}
    codes = found(ctx, pick("Shuppet", key_moves=["Surf"]))
    assert "MOVE_UNVERIFIABLE" in codes and "MOVE_NOT_LEARNABLE" not in codes


def test_every_code_is_exercised():
    """Runs last in this module: each code in CODES came up in at least one test above."""
    assert set(CODES) - covered == set()


# --- backups ---------------------------------------------------------------------------------


def draft_with(*recs) -> LeadDraft:
    return LeadDraft(intent="catch", headline="h", recommendations=list(recs), steps=[], battle_notes=[],
                     assumptions=[], follow_up_questions=[], unresolved=[])


def test_failed_pick_is_replaced_by_its_passing_backup(con):
    ctx = ctx_for(con)
    draft = draft_with(pick("Bagon", "gym7_tate_liza", alts=[alt("Lucario"), alt("Absol")]))
    new, actions, unfixed = promote_backups(draft, verify(ctx, draft))
    assert [r.species for r in new.recommendations] == ["Absol"] and unfixed == []
    assert any("replaced Bagon with its backup Absol" in a for a in actions)
    assert any("dropped backup(s) Lucario" in a for a in actions)


def test_failed_pick_without_a_backup_is_left_for_repair(con):
    ctx = ctx_for(con)
    draft = draft_with(pick("Absol"), pick("Bagon", "gym7_tate_liza"))
    new, _, unfixed = promote_backups(draft, verify(ctx, draft))
    assert unfixed == [1] and [r.species for r in new.recommendations] == ["Absol", "Bagon"]
