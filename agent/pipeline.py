"""One /chat turn: Clarifier -> Lead (parallel researchers) -> Verifier -> Writer -> citation check.

The Verifier (code, no LLM) checks every pick and backup. A failing pick is replaced by a
passing backup at no model cost; only a pick with no valid backup sends the Lead back for one
targeted repair round (the gap loop, capped at PLAN's 3 research rounds in total). The Writer's
citations are then checked, with one retry.
"""

import asyncio
import json

from pydantic import ValidationError

from agent import overlay, runtime
from agent.brief import state_brief
from agent.chart import coverage_chart
from agent.clarifier import make_clarifier, missing_question
from agent.context import RequestContext, shared_index
from agent.lead import make_lead
from agent.randomizer_log import load_overlay, parse_log
from agent.schemas import ClarifierDecision, LeadDraft, StateUpdate
from agent.session import SESSIONS, Session, apply_rules
from agent.state import RunState
from agent.verifier import ERROR, WARNING, Violation, promote_backups, verify
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


def sanitize_citations(ctx: RequestContext, draft: LeadDraft) -> LeadDraft:
    """Strip ids no tool returned from steps and battle notes (picks with bad ids go through repair)."""
    def clean(items):
        return [i.model_copy(update={"source_ids": [s for s in i.source_ids if s in ctx.ledger]}) for i in items]
    return draft.model_copy(update={"steps": clean(draft.steps), "battle_notes": clean(draft.battle_notes)})


async def verify_and_repair(ctx: RequestContext, draft: LeadDraft, lead_input: str) -> tuple[LeadDraft, list[Violation]]:
    """The gap loop: verify, promote passing backups, send the Lead back once for picks that
    still fail, then drop whatever can't be fixed. Returns the draft and the remaining warnings."""
    violations = verify(ctx, draft)
    record(ctx, "verifier", "verify", {"picks": [r.species for r in draft.recommendations]}, [v.to_dict() for v in violations] or "all checks passed")
    draft, actions, unfixed = promote_backups(draft, violations)
    if actions:
        record(ctx, "verifier", "promote_backups", {}, actions)
    if unfixed:
        failing = [v for v in violations if v.severity == ERROR and v.alt is None and v.rec is not None
                   and draft.recommendations[v.rec].species == v.species]
        ctx.round_cap = ctx.research_round + 1
        repair_input = (
            f"{lead_input}\n\nYOUR DRAFT (JSON)\n{draft.model_dump_json()}\n\nVERIFIER ERRORS (code: detail)\n"
            + "\n".join(f"- {v.species}: {v.code}: {v.detail}" for v in failing)
            + "\n\nFix only these. For each failing pick, find a replacement that passes these checks (one targeted "
            "dispatch_researchers round if you need new data), keep every pick that passed, and return the full corrected draft."
        )
        draft = await runtime.run(make_lead(), repair_input, ctx, max_turns=LEAD_MAX_TURNS)
        violations = verify(ctx, draft)
        record(ctx, "verifier", "verify", {"picks": [r.species for r in draft.recommendations], "after": "repair"},
               [v.to_dict() for v in violations] or "all checks passed")
        draft, actions, unfixed = promote_backups(draft, violations)
        if unfixed:
            dropped = [draft.recommendations[i] for i in unfixed]
            reasons = {i: next(v.detail for v in violations if v.rec == i and v.alt is None and v.severity == ERROR) for i in unfixed}
            draft = draft.model_copy(update={
                "recommendations": [r for i, r in enumerate(draft.recommendations) if i not in unfixed],
                "unresolved": draft.unresolved + [f"Dropped {d.species}: {reasons[i]}" for i, d in zip(unfixed, dropped)],
            })
            actions.append("dropped " + ", ".join(d.species for d in dropped) + " after the repair round")
        if actions:
            record(ctx, "verifier", "promote_backups", {"after": "repair"}, actions)
    return sanitize_citations(ctx, draft), [v for v in violations if v.severity == WARNING]


def picks_changed(before: LeadDraft, after: LeadDraft) -> LeadDraft:
    """The Lead's headline names its own picks; once the Verifier swaps or drops one, the
    Writer writes the opening line from the final picks instead."""
    if [r.species for r in before.recommendations] == [r.species for r in after.recommendations]:
        return after
    return after.model_copy(update={"headline": ""})


def citation_problems(ctx: RequestContext, markdown: str, draft: LeadDraft) -> list[str]:
    """Ids the ledger doesn't have, and picks whose part of the answer cites nothing."""
    _, _, unknown = ctx.ledger.cite(markdown)
    problems = [f"[[{u}]] isn't a source any tool returned" for u in sorted(set(unknown))]
    lines = markdown.splitlines()
    names = [r.species for r in draft.recommendations]
    starts = {n: next((i for i, l in enumerate(lines) if n.lower() in l.lower()), None) for n in names}
    marks = sorted(i for i in starts.values() if i is not None)
    for n, i in starts.items():
        if i is None:
            problems.append(f"the pick {n} is missing from the answer")
            continue
        end = next((s for s in marks if s > i), len(lines))
        if "[[" not in "\n".join(lines[i:end]):
            problems.append(f"the section for {n} has no citation")
    return problems


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
    lead_draft: LeadDraft = await runtime.run(make_lead(), lead_input, ctx, max_turns=LEAD_MAX_TURNS)
    draft, warnings = await verify_and_repair(ctx, lead_draft, lead_input)
    draft = picks_changed(lead_draft, draft)

    writer_input = (
        f"PLAYER QUESTION\n{message}\n\nRUN STATE\n{state_brief(ctx)}\n\n"
        f"PLAYER RULES\n{json.dumps(session.state.ruleset.describe())}\n\n"
        f"REVISION FEEDBACK: {decision.revision_feedback or 'none'}\n\n"
        f"VERIFIER WARNINGS (mention briefly where they matter)\n{json.dumps([f'{w.species}: {w.detail}' for w in warnings])}\n\n"
        f"DRAFT (JSON)\n{draft.model_dump_json()}"
    )
    markdown = await runtime.run(make_writer(), writer_input, ctx, max_turns=2)
    problems = citation_problems(ctx, markdown, draft)
    record(ctx, "verifier", "citation_check", {}, problems or "all citations resolve")
    if problems:
        retry_input = (
            f"{writer_input}\n\nYOUR PREVIOUS ANSWER\n{markdown}\n\nCITATION PROBLEMS\n" + "\n".join(f"- {p}" for p in problems)
            + "\n\nRewrite the answer fixing only these: cite only ids that appear in the draft, and cite every pick."
        )
        markdown = await runtime.run(make_writer(), retry_input, ctx, max_turns=2)
        problems = citation_problems(ctx, markdown, draft)
        record(ctx, "verifier", "citation_check", {"after": "retry"}, problems or "all citations resolve")
    text, citations, _ = ctx.ledger.cite(markdown)
    plan = draft.model_dump()
    if problems:
        plan["citation_warnings"] = problems
    session.last_plan = plan
    return {"response": text, "citations": citations, "plan": plan, "chart": chart_or_none(ctx, plan)}


def chart_or_none(ctx: RequestContext, plan: dict) -> dict | None:
    try:
        return coverage_chart(ctx, plan)
    except Exception as e:  # noqa: BLE001 - a broken chart shouldn't cost the player their answer
        record(ctx, "pipeline", "chart_error", {}, f"{type(e).__name__}: {e}")
        return None


def apply_form_state(session: Session, run_state: RunState) -> None:
    """The form's state wins; rules learned in conversation and the loaded log still apply on top of it."""
    state = run_state
    for u in session.learned_rules:
        state = state.model_copy(update={"ruleset": apply_rules(state.ruleset, u)})
    if session.randomizer:
        state = state.model_copy(update={"randomizer_log_id": session.randomizer["log_id"]})
    session.state = state


def clear_log(session_id: str) -> bool:
    session = SESSIONS.peek(session_id)
    if session is None or session.randomizer is None:
        return False
    overlay.uninstall(session.con)
    session.randomizer = None
    session.state = session.state.model_copy(update={"randomizer_log_id": None})
    return True


def load_log(text: str, name: str | None = None, session_id: str | None = None) -> dict:
    """Parse a UPR ZX log into the session: overlay tables, then views that shadow the vanilla
    tables it changed (agent/overlay.py). Replaces any log the session had."""
    session = SESSIONS.get(session_id)
    log = parse_log(text, session.con, shared_index())
    if not (log.sections or log.statuses):
        raise ValueError("that doesn't look like a Universal Pokemon Randomizer log (no --Section-- headers)")
    log_id = (name or "log").strip()[:80] or "log"
    load_overlay(session.con, log, log_id)
    overlay.uninstall(session.con)
    session.randomizer = overlay.summary(log, log_id, overlay.install(session.con, log, log_id))
    session.state = session.state.model_copy(update={"randomizer_log_id": log_id})
    return {"session_id": session.id, **session.randomizer}


async def chat(message: str, session_id: str | None = None, run_state: RunState | None = None,
               listener=None) -> dict:
    """One /chat turn. `listener`, if given, gets progress events as agents start and tools run."""
    session = SESSIONS.get(session_id)
    if run_state is not None:
        apply_form_state(session, run_state)
    ctx = RequestContext(state=session.state, con=session.con, excluded_species=set(session.excluded),
                         randomizer=session.randomizer, listener=listener)
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
        "chart": result.get("chart"),
        "usage": ctx.usage,  # per-LLM-call tokens and timing; not part of the /chat contract
    }
