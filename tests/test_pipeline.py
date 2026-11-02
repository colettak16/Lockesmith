"""The /chat pipeline's control flow with the models stubbed (scripts/phase2_acceptance.py runs
the real ones): asking, declining, citations, rules learned in conversation, rejected picks."""

import asyncio

import pytest

from agent import pipeline, runtime
from agent.schemas import ClarifierDecision, LeadDraft, Recommendation, RuleUpdate, StateUpdate
from agent.session import SESSIONS
from agent.state import RunState

NO_STATE = StateUpdate(starter=None, badges=None, rival=None, last_battle=None, party=None)
NO_RULES = RuleUpdate(nuzlocke=None, dupes_clause=None, level_caps=None, monotype=None, no_legendaries=None,
                      wild_only=None, add_banned_species=[], add_used_routes=[], add_notes=[])


def decision(**kw) -> ClarifierDecision:
    base = dict(action="proceed", intent="catch", reply="", research_brief="", state_updates=NO_STATE,
                rule_updates=NO_RULES, reject_species=[], revision_feedback="")
    return ClarifierDecision(**{**base, **kw})


DRAFT = LeadDraft(
    intent="catch", headline="Catch Sharpedo.",
    recommendations=[Recommendation(species="Sharpedo", role="special attacker", where="Route 118, Super Rod",
                                    when="before gym7_tate_liza", why="Dark beats Psychic",
                                    source_ids=["progression:gym7_tate_liza"], alternatives=[])],
    steps=[], battle_notes=[], assumptions=[], follow_up_questions=[], unresolved=[],
)


@pytest.fixture
def models(monkeypatch):
    """Stub runtime.run per agent name; returns the list of agents that ran."""
    calls, script = [], {}

    async def fake_run(agent, input, context, max_turns=8):
        calls.append(agent.name)
        if agent.name == "lead":
            context.ledger.add("progression:gym7_tate_liza")
            context.research_round = 1
        out = script[agent.name]
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
    body = chat("what for Tate & Liza?", "p-full", RunState(starter="mudkip", badges=["stone"]))
    assert calls == ["clarifier", "lead", "writer"]
    assert body["response"] == "Catch Sharpedo [1]. It's great ."
    assert body["citations"][0]["source_id"] == "progression:gym7_tate_liza"
    assert body["plan"]["unverified_source_ids"] == ["made:up"]


def test_rules_and_rejections_persist_across_turns(models):
    calls, script = models
    script["clarifier"] = decision(
        intent="revision", rule_updates=NO_RULES.model_copy(update={"monotype": "Grass", "add_notes": ["no items in battle"]}),
        reject_species=["Sharpedo"], revision_feedback="wants grass types",
    )
    script["lead"] = DRAFT
    script["writer"] = "ok"
    form = RunState(starter="treecko", badges=["stone"])
    chat("only grass types, and not Sharpedo", "p-rules", form)
    script["clarifier"] = decision()
    chat("and now?", "p-rules", form)  # the form doesn't know the rule; the session does
    session = SESSIONS.get("p-rules")
    assert session.state.ruleset.monotype == "grass" and "no items in battle" in session.state.ruleset.notes
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
