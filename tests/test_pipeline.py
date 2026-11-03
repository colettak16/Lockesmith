"""The /chat pipeline's control flow with the models stubbed (scripts/phase2_acceptance.py runs
the real ones): asking, declining, the Verifier's gap loop, citation checks, rules learned in
conversation, rejected picks."""

import asyncio

import pytest

from agent import pipeline, runtime
from agent.schemas import Alternative, ClarifierDecision, LeadDraft, Recommendation, RuleUpdate, StateUpdate
from agent.session import SESSIONS
from agent.state import RunState

NO_STATE = StateUpdate(game=None, starter=None, badges=None, rival=None, last_battle=None, party=None)
NO_RULES = RuleUpdate(nuzlocke=None, encounter_scope=None, gifts_count_as_encounter=None, dupes_clause=None,
                      level_caps=None, level_cap_offset=None, allowed_types=None, no_legendaries=None, wild_only=None,
                      add_banned_species=[], add_banned_types=[], add_used_routes=[], add_notes=[])
CITED = ["progression:gym7_tate_liza"]
STATE = RunState(starter="mudkip", badges=["stone", "knuckle", "dynamo", "heat", "balance", "feather"])


def decision(**kw) -> ClarifierDecision:
    base = dict(action="proceed", intent="catch", reply="", research_brief="", state_updates=NO_STATE,
                rule_updates=NO_RULES, reject_species=[], revision_feedback="")
    return ClarifierDecision(**{**base, **kw})


def rec(species, alts=()) -> Recommendation:
    return Recommendation(species=species, role="answer to Psychic", horizon="core", before_battle="gym7_tate_liza",
                          where="w", when="before Tate & Liza", why="fits", long_term="lt", evolve_to="", key_moves=[],
                          source_ids=CITED, alternatives=list(alts))


def backup(species) -> Alternative:
    return Alternative(species=species, horizon="core", where="w", why="fits", long_term="lt", evolve_to="",
                       key_moves=[], source_ids=CITED)


def draft(*recs) -> LeadDraft:
    return LeadDraft(intent="catch", headline="h", recommendations=list(recs), steps=[], battle_notes=[],
                     assumptions=[], follow_up_questions=[], unresolved=[])


DRAFT = draft(rec("Sharpedo"))


@pytest.fixture
def models(monkeypatch):
    """Stub runtime.run per agent name (a list scripts successive calls); returns the agents that ran."""
    calls, script = [], {}

    async def fake_run(agent, input, context, max_turns=8):
        calls.append(agent.name)
        if agent.name == "lead":
            context.ledger.add(CITED[0])
            context.research_round += 1
        out = script[agent.name]
        if isinstance(out, list):
            out = out.pop(0) if len(out) > 1 else out[0]
        return out(context) if callable(out) else out

    monkeypatch.setattr(runtime, "run", fake_run)
    return calls, script


def chat(message, session_id, state=None):
    return asyncio.run(pipeline.chat(message, session_id, state))


def test_missing_required_state_asks_without_research(models):
    calls, script = models
    script["clarifier"] = decision()
    body = chat("what should I catch?", "p-vague")
    assert "starter" in body["response"] and calls == ["clarifier"]
    assert body["tool_calls"][0]["agent"] == "clarifier"


def test_decline_returns_the_reply(models):
    calls, script = models
    script["clarifier"] = decision(action="decline", intent="lookup", reply="I only cover Emerald.")
    assert chat("EVs for Garchomp?", "p-decline")["response"] == "I only cover Emerald."
    assert calls == ["clarifier"]


def test_full_turn_cites_ledger_ids_and_flags_unknown(models):
    calls, script = models
    script["clarifier"] = decision()
    script["lead"] = DRAFT
    script["writer"] = "Catch Sharpedo [[progression:gym7_tate_liza]]. It's great [[made:up]]."
    body = chat("what for Tate & Liza?", "p-full", STATE)
    assert calls == ["clarifier", "lead", "writer", "writer"]  # one retry for the unknown id
    assert body["response"] == "Catch Sharpedo [1]. It's great ."
    assert body["citations"][0]["source_id"] == "progression:gym7_tate_liza"
    assert body["plan"]["citation_warnings"] == ["[[made:up]] isn't a source any tool returned"]


def test_rules_lookup_cites_the_game_line(models):
    # A rules question answered from the brief's game line (round-4 live run: Synchronize/Pickup in Ruby)
    calls, script = models
    script["clarifier"] = decision(intent="lookup")
    script["lead"] = LeadDraft(intent="lookup", headline="h", recommendations=[], battle_notes=[], assumptions=[],
                               follow_up_questions=[], unresolved=[],
                               steps=[{"title": "No Synchronize effect", "detail": "Emerald-only", "source_ids": ["rules:game"]}])
    script["writer"] = "Synchronize does nothing outside battle in Ruby [[rules:game]]."
    body = chat("does synchronize work?", "p-rules", RunState(game="ruby", starter="mudkip", badges=["stone"]))
    assert calls == ["clarifier", "lead", "writer"]
    assert [c for c in body["tool_calls"] if c["name"] == "verify"][0]["result"] == "all checks passed"
    assert body["response"].endswith("[1].") and body["citations"][0]["source_id"] == "rules:game"
    assert body["citations"][0]["label"].startswith("LockeSmith's Ruby rules") and body["citations"][0]["url"].endswith("engine.txt")


def test_citation_retry_fixes_an_uncited_pick(models):
    calls, script = models
    script["clarifier"] = decision()
    script["lead"] = DRAFT
    script["writer"] = ["Catch Sharpedo, it's great.", "Catch Sharpedo [[progression:gym7_tate_liza]]."]
    body = chat("what for Tate & Liza?", "p-cite-retry", STATE)
    assert calls.count("writer") == 2 and "citation_warnings" not in body["plan"]
    checks = [c for c in body["tool_calls"] if c["name"] == "citation_check"]
    assert "no citation" in checks[0]["result"] and "all citations resolve" in checks[1]["result"]


def test_seeded_bad_pick_is_replaced_by_its_backup(models):
    """PLAN's Phase 3 acceptance: a bad candidate is rejected and replaced in the gap loop."""
    calls, script = models
    script["clarifier"] = decision()
    script["lead"] = draft(rec("Bagon", alts=[backup("Absol")]))  # Bagon needs Waterfall: not before Tate & Liza
    script["writer"] = "Catch Absol [[progression:gym7_tate_liza]]."
    body = chat("what for Tate & Liza?", "p-seeded", STATE)
    assert [r["species"] for r in body["plan"]["recommendations"]] == ["Absol"]
    assert body["plan"]["headline"] == ""  # it named Bagon; the Writer opens from the final picks
    assert calls.count("lead") == 1  # the backup was promoted without a repair round
    verifier = [c for c in body["tool_calls"] if c["agent"] == "verifier"]
    assert "NOT_OBTAINABLE_BEFORE" in verifier[0]["result"] and "replaced Bagon" in verifier[1]["result"]


def test_pick_without_a_backup_sends_the_lead_back(models):
    calls, script = models
    script["clarifier"] = decision()
    script["lead"] = [draft(rec("Bagon")), draft(rec("Absol"))]
    script["writer"] = "Catch Absol [[progression:gym7_tate_liza]]."
    body = chat("what for Tate & Liza?", "p-repair", STATE)
    assert calls.count("lead") == 2
    assert [r["species"] for r in body["plan"]["recommendations"]] == ["Absol"]


def test_unfixable_pick_is_dropped_with_a_reason(models):
    calls, script = models
    script["clarifier"] = decision()
    script["lead"] = draft(rec("Absol"), rec("Bagon"))  # the repair returns the same draft
    script["writer"] = "Catch Absol [[progression:gym7_tate_liza]]."
    body = chat("what for Tate & Liza?", "p-drop", STATE)
    plan = body["plan"]
    assert [r["species"] for r in plan["recommendations"]] == ["Absol"]
    assert any(u.startswith("Dropped Bagon") for u in plan["unresolved"])


def test_rules_and_rejections_persist_across_turns(models):
    calls, script = models
    script["clarifier"] = decision(
        intent="revision", rule_updates=NO_RULES.model_copy(update={"allowed_types": ["Grass"], "add_banned_types": ["Poison"],
                                                 "add_notes": ["no items in battle"]}),
        reject_species=["Sharpedo"], revision_feedback="wants grass types",
    )
    script["lead"] = DRAFT
    script["writer"] = "ok"
    form = RunState(starter="treecko", badges=["stone"])
    chat("only grass types, and not Sharpedo", "p-rules", form)
    script["clarifier"] = decision()
    chat("and now?", "p-rules", form)  # the form doesn't know the rule; the session does
    session = SESSIONS.get("p-rules")
    rules = session.state.ruleset
    assert rules.allowed_types == ["grass"] and rules.banned_types == ["poison"] and "no items in battle" in rules.notes
    answer = SESSIONS.get("p-rules").history[-1]["content"]
    assert "- only Grass types (checked by the Verifier)" in answer and "- no Poison types (checked by the Verifier)" in answer
    assert "- no items in battle (followed, not checked automatically)" in answer
    assert "sharpedo" in session.excluded


def test_stated_progress_updates_the_session(models):
    calls, script = models
    script["clarifier"] = decision(
        state_updates=NO_STATE.model_copy(update={"starter": "torchic", "badges": ["stone", "knuckle"], "last_battle": "not-a-battle"})
    )
    script["lead"] = DRAFT
    script["writer"] = "ok"
    chat("I picked Torchic and beat Brawly", "p-state")
    state = SESSIONS.get("p-state").state
    assert state.starter == "torchic" and state.badges == ["stone", "knuckle"] and state.last_battle is None


def test_trace_tags_and_pseudonymous_users():
    from agent import observability
    from agent.state import Ruleset

    session = SESSIONS.get("p-tags")
    session.state = RunState(starter="mudkip", badges=[], ruleset=Ruleset(nuzlocke=True, allowed_types=["water"]))
    assert pipeline.trace_tags(session) == ["emerald", "vanilla", "nuzlocke", "custom-rules"]
    session.state = RunState(game="sapphire", starter="mudkip", badges=[])
    assert pipeline.trace_tags(session) == ["sapphire", "vanilla"]
    uid = observability.user_id("accounts.google.com:1234567890")
    assert uid == observability.user_id("accounts.google.com:1234567890") and "1234567890" not in uid
    assert observability.user_id(None) is None
    assert observability.workflow_name("catch_researcher") == "research-catches"
