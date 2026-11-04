"""One /chat turn: Clarifier -> Lead (parallel researchers) -> Verifier -> Writer -> citation check.

The Verifier (code, no LLM) checks every pick and backup. A failing pick is replaced by a
passing backup at no model cost; only a pick with no valid backup sends the Lead back for one
targeted repair round (the gap loop, capped at PLAN's 3 research rounds in total). The Writer's
citations are then checked, with one retry.
"""

import asyncio
import json
import logging

from pydantic import ValidationError

from agent import observability, overlay, runtime
from agent.brief import GAME_LINES, GAME_SOURCE, state_brief
from agent.chart import coverage_chart
from agent.clarifier import make_clarifier, missing_question
from agent.context import RequestContext, shared_index
from agent.games import get as get_game
from agent.lead import make_lead
from agent.progression import load_game
from agent.randomizer_log import detect_game, load_overlay, parse_log
from agent.schemas import ClarifierDecision, LeadDraft, StateUpdate
from agent.session import SESSIONS, Session, apply_rules
from agent.state import RunState
from agent.verifier import ERROR, WARNING, Violation, correct_places, promote_backups, verify
from agent.writer import make_writer

log = logging.getLogger("lockesmith.pipeline")
REQUEST_BUDGET_S = 270  # graders wait up to 5 minutes; Cloud Run's timeout is 600 s
LEAD_MAX_TURNS = 12
HISTORY_TURNS = 3
RESEARCH_TURNS = 3  # earlier turns whose researcher findings a follow-up's Lead sees
RESEARCH_CHARS = 16_000  # newest first; a turn's findings run 3-7k characters


def apply_state(state: RunState, u: StateUpdate, ctx: RequestContext) -> RunState:
    data = state.model_dump()
    if getattr(u, "game", None) and u.game != state.game:
        # A different game: progress and party were for the other one unless restated now. In
        # another region (Sapphire -> FireRed) the starter, badges and rival don't carry over either.
        data.update(game=u.game, last_battle=None)
        new, old = get_game(u.game).cast, get_game(state.game).cast
        if (new.starters, new.badges) != (old.starters, old.badges):
            data.update(starter=None, badges=None, rival=None, party=[])
    for key in ("starter", "badges", "rival"):
        if getattr(u, key) is not None:
            data[key] = getattr(u, key)
    if u.last_battle:
        ids = {b.id for b in load_game(get_game(data["game"])).battles}
        if u.last_battle in ids:
            data["last_battle"] = u.last_battle
    if u.party is not None:
        data["party"] = [p.model_dump() for p in u.party]
    if getattr(u, "owned", None):  # added to, not replaced: players mention their PC a few at a time
        names = [o.strip() for o in u.owned if o.strip()]
        if ctx is not None:  # "Growlith" -> "Growlithe"; names that match no species are dropped
            names = [m.name for m in (ctx.index.resolve(n, "species", cutoff=80) for n in names) if m]
        data["owned"] = list(dict.fromkeys([*data.get("owned", []), *names]))
    try:
        return RunState(**data)
    except ValidationError:
        return state


# Verifier findings the Writer fixes in the text rather than mentions: wrong matchups, and moves a party
# Pokémon already knows offered as new
CORRECTION_CODES = {"TYPE_CLAIM_WRONG", "MOVE_ALREADY_KNOWN"}


def conversation_context(session: Session) -> str:
    """What the Lead needs from earlier turns on a follow-up: what the player said (Pokémon they have,
    plans) and what was already recommended, so an answer builds on it instead of starting over."""
    said = [t["content"][:600] for t in session.history[-2 * HISTORY_TURNS:] if t["role"] == "user"]
    lines = [f"- The player said: {s}" for s in said]
    if session.last_plan:
        picks = ", ".join(r["species"] for r in session.last_plan.get("recommendations", []))
        lines.append(f"- Your previous answer: {session.last_plan.get('headline', '')}" + (f" Picks: {picks}." if picks else ""))
    return "\n".join(lines)


def research_key(state: RunState) -> tuple:
    """Findings hold for the game (and randomizer log) they were researched on."""
    return (state.game, state.randomizer_log_id)


def keep_research(session: Session, ctx: RequestContext, message: str) -> None:
    """Save this turn's findings for follow-ups, keeping only source ids a tool returned. A live
    FireRed follow-up ("I have Dig, Fire Blast, Aerial Ace and Overheat for Arcanine") re-scouted
    the whole Elite Four the previous turn had just scouted: 26 of its 67 s."""
    def known(ids: list[str]) -> list[str]:
        return [s for s in ids if s in ctx.ledger]
    findings = [{"researcher": r["researcher"], "task": r["task"], "summary": r["finding"]["summary"],
                 "claims": [{**c, "source_ids": known(c["source_ids"])} for c in r["finding"]["claims"]],
                 "candidates": [{**c, "source_ids": known(c["source_ids"])} for c in r["finding"]["candidates"]]}
                for r in ctx.findings]
    if findings:
        turn = {"key": research_key(session.state), "question": message[:200], "findings": findings}
        session.research = [*session.research, turn][-RESEARCH_TURNS:]


def earlier_research(session: Session) -> tuple[str, set[str]]:
    """The findings of earlier turns on this game, newest turn first, up to RESEARCH_CHARS, and the
    source ids they cite (put back in the ledger, so the Lead can cite them without asking again)."""
    blocks, ids, size = [], set(), 0
    for turn in reversed(session.research):
        if turn["key"] != research_key(session.state):
            continue
        header = f'For "{turn["question"]}":'
        for f in turn["findings"]:
            lines = [f"- {f['researcher']} researcher, asked: {f['task']}", f"  {f['summary']}"]
            lines += [f"  - {c['text']} {c['source_ids']}" for c in f["claims"]]
            lines += [f"  - candidate {c['species']}: {c['where']}; {c['when']}. {c['why']} Long term: {c['long_term']} "
                      f"{c['source_ids']}" for c in f["candidates"]]
            block = "\n".join(lines)
            if size + len(block) > RESEARCH_CHARS:
                return "\n".join(blocks), ids
            if header:
                blocks.append(header)
                header = ""
            blocks.append(block)
            size += len(block)
            ids.update(s for c in [*f["claims"], *f["candidates"]] for s in c["source_ids"])
    return "\n".join(blocks), ids


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
    observability.step(name, args, result)


def sanitize_citations(ctx: RequestContext, draft: LeadDraft) -> tuple[LeadDraft, list[str]]:
    """Strip ids no tool returned from picks, backups, steps and battle notes. (A pick citing only
    such ids failed the Verifier and went through repair.) Returns the draft and the ids dropped."""
    dropped: list[str] = []

    def keep(ids: list[str]) -> list[str]:
        dropped.extend(s for s in ids if s not in ctx.ledger)
        return [s for s in ids if s in ctx.ledger]

    def clean(items):
        return [i.model_copy(update={"source_ids": keep(i.source_ids)}) for i in items]
    recs = [r.model_copy(update={"source_ids": keep(r.source_ids), "alternatives": clean(r.alternatives)})
            for r in draft.recommendations]
    return draft.model_copy(update={"recommendations": recs, "steps": clean(draft.steps),
                                    "battle_notes": clean(draft.battle_notes)}), dropped


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
    draft, fixes = correct_places(ctx, draft)
    if fixes:
        record(ctx, "verifier", "correct_where", {}, fixes)
    draft, dropped = sanitize_citations(ctx, draft)
    if dropped:
        record(ctx, "verifier", "drop_unknown_citations", {}, sorted(set(dropped)))
    return draft, [v for v in violations if v.severity == WARNING]


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
    if session.sync_game():  # the player said which game they're playing ("I'm on Sapphire")
        ctx.state = session.state
        ctx.randomizer = session.randomizer
        ctx.refresh_game(session.con)
    session.learned_rules.append(decision.rule_updates)
    for name in decision.reject_species:
        match = ctx.index.resolve(name, "species", cutoff=80)
        if match:
            session.excluded.add(match.id)
    ctx.state, ctx.excluded_species = session.state, set(session.excluded)

    if decision.action == "decline":
        return {"response": decision.reply, "plan": None, "intent": "declined"}
    missing = session.state.missing_required()
    if decision.action == "ask" and not missing and session.state.party:
        # The Clarifier may only ask for the starter, badges or party, and all three are here. A live
        # Sapphire run had it ask where the player was and which routes they'd used, with no Nuzlocke on.
        record(ctx, "clarifier", "ask_overridden", {"reply": decision.reply}, "starter, badges and party are known; researching")
        decision = decision.model_copy(update={"action": "proceed", "reply": "", "research_brief": decision.research_brief or message})
    if decision.action == "ask" or (missing and decision.intent != "lookup"):
        return {"response": decision.reply if decision.action == "ask" and decision.reply else missing_question(missing, ctx.game.cast.starters),
                "plan": None, "intent": "clarify"}

    # The game line of the brief is a source in its own right: rules questions can be answered from it
    ctx.ledger.add(GAME_SOURCE, GAME_LINES[ctx.state.game])
    lead_input = (
        f"PLAYER QUESTION\n{message}\n\nINTENT: {decision.intent}\nGATEKEEPER BRIEF: {decision.research_brief}\n\n"
        f"RUN STATE\n{state_brief(ctx)}"
    )
    if decision.intent == "revision" and session.last_plan:
        lead_input += (
            f"\n\nPREVIOUS PLAN (the player wants something different)\n{json.dumps(session.last_plan)[:3000]}"
            f"\nPLAYER FEEDBACK: {decision.revision_feedback or 'vague'}"
        )
    if session.history:
        lead_input += f"\n\nEARLIER IN THIS CONVERSATION\n{conversation_context(session)}"
    research, cited = earlier_research(session)
    if research:
        for sid in cited:
            ctx.ledger.add(sid)
        lead_input += f"\n\nRESEARCH FROM EARLIER TURNS (game data; source ids still valid)\n{research}"
    lead_draft: LeadDraft = await runtime.run(make_lead(), lead_input, ctx, max_turns=LEAD_MAX_TURNS)
    draft, warnings = await verify_and_repair(ctx, lead_draft, lead_input)
    draft = picks_changed(lead_draft, draft)
    corrections = [f"{w.species}: {w.detail}" for w in warnings if w.code in CORRECTION_CODES]
    warnings = [w for w in warnings if w.code not in CORRECTION_CODES]

    writer_input = (
        f"PLAYER QUESTION\n{message}\n\nRUN STATE\n{state_brief(ctx)}\n\n"
        f"PLAYER RULES\n{json.dumps(session.state.ruleset.describe())}\n\n"
        f"REVISION FEEDBACK: {decision.revision_feedback or 'none'}\n\n"
        f"VERIFIER WARNINGS (mention briefly where they matter)\n{json.dumps([f'{w.species}: {w.detail}' for w in warnings])}\n\n"
        f"VERIFIER CORRECTIONS (the draft gets these wrong: write the correct version, or leave the claim out)\n"
        f"{json.dumps(corrections)}\n\n"
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
    rules = session.state.ruleset.describe()
    if rules:  # written in code, so "checked by the Verifier" vs "not checked" is always right
        markdown += "\n\n### Rules I followed\n" + "\n".join(
            f"- {r}" + ("" if "not checked" in r else " (checked by the Verifier)") for r in rules)
    text, citations, _ = ctx.ledger.cite(markdown)
    plan = draft.model_dump()
    if problems:
        plan["citation_warnings"] = problems
    session.last_plan = plan
    keep_research(session, ctx, message)
    return {"response": text, "citations": citations, "plan": plan, "chart": chart_or_none(ctx, plan), "intent": decision.intent}


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
    if session.randomizer and state.game == session.con_game:
        state = state.model_copy(update={"randomizer_log_id": session.randomizer["log_id"]})
    session.state = state
    session.sync_game()


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
    game = detect_game(text)
    if game and game != session.state.game:  # a Sapphire log makes this a Sapphire run
        session.state = session.state.model_copy(update={"game": game, "last_battle": None})
        session.sync_game()
    log = parse_log(text, session.con, shared_index(session.con_game))
    if not (log.sections or log.statuses):
        raise ValueError("that doesn't look like a Universal Pokemon Randomizer log (no --Section-- headers)")
    log_id = (name or "log").strip()[:80] or "log"
    load_overlay(session.con, log, log_id)
    overlay.uninstall(session.con)
    session.randomizer = overlay.summary(log, log_id, overlay.install(session.con, log, log_id))
    session.state = session.state.model_copy(update={"randomizer_log_id": log_id})
    return {"session_id": session.id, "game": session.state.game, **session.randomizer}


def trace_tags(session: Session) -> list[str]:
    """What kind of run this is, known before the turn starts (LangFuse tags are fixed at creation,
    so a game named in the message shows in the trace's `game` metadata instead)."""
    rules = session.state.ruleset
    tags = [session.state.game, "randomized" if session.randomizer else "vanilla"]
    if rules.nuzlocke:
        tags.append("nuzlocke")
    if rules.allowed_types or rules.banned_types or rules.no_legendaries or rules.wild_only or rules.banned_species or rules.notes:
        tags.append("custom-rules")
    return tags


async def chat(message: str, session_id: str | None = None, run_state: RunState | None = None,
               listener=None, user: str | None = None) -> dict:
    """One /chat turn. `listener`, if given, gets progress events as agents start and tools run;
    `user` is a pseudonymous id for tracing."""
    session = SESSIONS.get(session_id)
    if run_state is not None:
        apply_form_state(session, run_state)
    ctx = RequestContext(state=session.state, con=session.con, excluded_species=set(session.excluded),
                         randomizer=session.randomizer, listener=listener)
    with observability.chat_trace(session.id, message, user=user, tags=trace_tags(session)) as finish:
        trace_id = observability.current_trace_id()
        try:
            result = await asyncio.wait_for(answer(message, session, ctx), REQUEST_BUDGET_S)
        except TimeoutError:
            result = {"response": "Sorry, that took longer than my time budget. Try a narrower question.", "plan": None}
        except Exception as e:  # noqa: BLE001 - the player gets a message, the trace keeps the details
            record(ctx, "pipeline", "error", {}, f"{type(e).__name__}: {e}")
            result = {"response": "Sorry, something went wrong while researching that. Please try again.", "plan": None}
        finish(result["response"], {
            "game": session.state.game,
            "intent": result.get("intent"),
            "picks": [r["species"] for r in (result.get("plan") or {}).get("recommendations", [])],
            "seconds": ctx.elapsed(), "model_calls": len(ctx.usage),
            "cost_usd": round(sum(u.get("cost_usd") or 0 for u in ctx.usage), 4),
            "citations": len(result.get("citations", [])),
            "randomizer_log": session.randomizer["log_id"] if session.randomizer else None,
            "rules": session.state.ruleset.describe(),
        })
    await asyncio.to_thread(observability.flush)
    # One line per turn in the service logs, to match against LangFuse
    log.info("chat session=%s trace=%s intent=%s seconds=%.1f model_calls=%d fallbacks=%d cost_usd=%.3f "
             "spans_exported(accepted,failed)=%s",
             session.id, trace_id, result.get("intent"), ctx.elapsed(), len(ctx.usage),
             sum(1 for u in ctx.usage if u.get("fallback")), sum(u.get("cost_usd") or 0 for u in ctx.usage),
             observability.exported(trace_id))
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
