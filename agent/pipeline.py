"""One /chat turn: Clarifier -> Lead (with parallel researchers) -> Writer -> citations.

The Verifier and the gap loop it drives come in Phase 3; for now the Lead's own coverage
check decides whether to run another research round.
"""

import asyncio
import json

from pydantic import ValidationError

from agent import runtime
from agent.brief import state_brief
from agent.clarifier import make_clarifier, missing_question
from agent.context import RequestContext
from agent.lead import make_lead
from agent.schemas import ClarifierDecision, LeadDraft, StateUpdate
from agent.session import SESSIONS, Session, apply_rules
from agent.state import RunState
from agent.writer import make_writer

REQUEST_BUDGET_S = 270  # graders wait up to 5 minutes; Cloud Run's timeout is 600 s
LEAD_MAX_TURNS = 12
HISTORY_TURNS = 3


def apply_state(state: RunState, u: StateUpdate, ctx: RequestContext) -> RunState:
    data = state.model_dump()
    for key in ("starter", "badges", "rival"):
        if getattr(u, key) is not None:
            data[key] = getattr(u, key)
    if u.last_battle:
        ids = {b.id for b in ctx.prog.battles}
        if u.last_battle in ids:
            data["last_battle"] = u.last_battle
    if u.party is not None:
        data["party"] = [p.model_dump() for p in u.party]
    try:
        return RunState(**data)
    except ValidationError:
        return state


def clarifier_input(message: str, session: Session) -> str:
    recent = session.history[-2 * HISTORY_TURNS:]
    convo = "\n".join(f"{t['role']}: {t['content'][:400]}" for t in recent) or "(none)"
    previous = "(none)"
    if session.last_plan:
        picks = ", ".join(r["species"] for r in session.last_plan.get("recommendations", []))
        previous = session.last_plan.get("headline", "") + (f" Picks: {picks}." if picks else "")
    return (
        f"CURRENT RUN STATE (JSON)\n{session.state.model_dump_json(exclude_defaults=True)}\n\n"
        f"PREVIOUS ANSWER\n{previous}\n\nRECENT CONVERSATION\n{convo}\n\nPLAYER MESSAGE\n{message}"
    )


def record(ctx: RequestContext, agent: str, name: str, args: dict, result) -> None:
    ctx.tool_calls.append(
        {"agent": agent, "name": name, "args": args, "result": runtime.preview(result), "round": ctx.research_round, "t": ctx.elapsed()}
    )


async def answer(message: str, session: Session, ctx: RequestContext) -> dict:
    decision: ClarifierDecision = await runtime.run(make_clarifier(), clarifier_input(message, session), ctx, max_turns=2)
    record(ctx, "clarifier", "decide", {"message": message}, decision.model_dump())

    session.state = apply_state(session.state, decision.state_updates, ctx)
    session.state = session.state.model_copy(update={"ruleset": apply_rules(session.state.ruleset, decision.rule_updates)})
    session.learned_rules.append(decision.rule_updates)
    for name in decision.reject_species:
        match = ctx.index.resolve(name, "species", cutoff=80)
        if match:
            session.excluded.add(match.id)
    ctx.state, ctx.excluded_species = session.state, set(session.excluded)

    if decision.action == "decline":
        return {"response": decision.reply, "plan": None}
    missing = session.state.missing_required()
    if decision.action == "ask" or (missing and decision.intent != "lookup"):
        return {"response": decision.reply if decision.action == "ask" and decision.reply else missing_question(missing), "plan": None}

    lead_input = (
        f"PLAYER QUESTION\n{message}\n\nINTENT: {decision.intent}\nGATEKEEPER BRIEF: {decision.research_brief}\n\n"
        f"RUN STATE\n{state_brief(ctx)}"
    )
    if decision.intent == "revision" and session.last_plan:
        lead_input += (
            f"\n\nPREVIOUS PLAN (the player wants something different)\n{json.dumps(session.last_plan)[:3000]}"
            f"\nPLAYER FEEDBACK: {decision.revision_feedback or 'vague'}"
        )
    draft: LeadDraft = await runtime.run(make_lead(), lead_input, ctx, max_turns=LEAD_MAX_TURNS)

    writer_input = (
        f"PLAYER QUESTION\n{message}\n\nRUN STATE\n{state_brief(ctx)}\n\n"
        f"PLAYER RULES\n{json.dumps(session.state.ruleset.describe())}\n\n"
        f"REVISION FEEDBACK: {decision.revision_feedback or 'none'}\n\nDRAFT (JSON)\n{draft.model_dump_json()}"
    )
    markdown = await runtime.run(make_writer(), writer_input, ctx, max_turns=2)
    text, citations, unknown = ctx.ledger.cite(markdown)
    plan = draft.model_dump()
    if unknown:
        plan["unverified_source_ids"] = sorted(set(unknown))
    session.last_plan = plan
    return {"response": text, "citations": citations, "plan": plan}


async def chat(message: str, session_id: str | None = None, run_state: RunState | None = None) -> dict:
    session = SESSIONS.get(session_id)
    if run_state is not None:
        # The form's state wins; rules learned in conversation still apply on top of it.
        state = run_state
        for u in session.learned_rules:
            state = state.model_copy(update={"ruleset": apply_rules(state.ruleset, u)})
        session.state = state
    ctx = RequestContext(state=session.state, con=session.con, excluded_species=set(session.excluded))
    try:
        result = await asyncio.wait_for(answer(message, session, ctx), REQUEST_BUDGET_S)
    except TimeoutError:
        result = {"response": "Sorry, that took longer than my time budget. Try a narrower question.", "plan": None}
    except Exception as e:  # noqa: BLE001 - the player gets a message, the trace keeps the details
        record(ctx, "pipeline", "error", {}, f"{type(e).__name__}: {e}")
        result = {"response": "Sorry, something went wrong while researching that. Please try again.", "plan": None}
    session.history += [{"role": "user", "content": message}, {"role": "assistant", "content": result["response"]}]
    return {
        "response": result["response"],
        "session_id": session.id,
        "tool_calls": ctx.tool_calls,
        "citations": result.get("citations", []),
        "plan": result.get("plan"),
        "chart": None,
        "usage": ctx.usage,  # per-LLM-call tokens and timing; not part of the /chat contract
    }
