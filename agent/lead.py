"""Lead: plans the research, fans out to researchers in parallel, drafts the answer (PLAN.md §6)."""

import asyncio
import json

from agents import RunContextWrapper, function_tool

from agent import runtime
from agent.brief import state_brief
from agent.context import RequestContext
from agent.researchers import make_researcher
from agent.schemas import LeadDraft, ResearchTask

MAX_RESEARCH_ROUNDS = 2  # Phase 3's Verifier-driven gap loop may raise this to PLAN's 3
MAX_TASKS_PER_ROUND = 4
RESEARCHER_MAX_TURNS = 8


async def run_researcher(ctx: RequestContext, task: ResearchTask) -> dict:
    agent = make_researcher(task.researcher)
    prompt = f"RUN STATE\n{state_brief(ctx)}\n\nTASK\n{task.task}"
    try:
        finding = await runtime.run(agent, prompt, ctx, max_turns=RESEARCHER_MAX_TURNS)
        return {"researcher": task.researcher, "task": task.task, "finding": finding.model_dump()}
    except Exception as e:  # noqa: BLE001 - one failed researcher shouldn't sink the round
        error = f"{type(e).__name__}: {str(e)[:200]}"
        ctx.tool_calls.append(
            {"agent": agent.name, "name": "error", "args": {"task": task.task}, "result": error,
             "round": ctx.research_round, "t": ctx.elapsed()}
        )
        return {"researcher": task.researcher, "task": task.task, "error": error}


@function_tool
async def dispatch_researchers(ctx: RunContextWrapper[RequestContext], tasks: list[ResearchTask]) -> str:
    """Run researchers in parallel, each in a fresh context, and return their findings. Put every
    task for this round in ONE call (up to 4). Researchers: battle (opposing teams, threats, levels),
    catch (Pokémon obtainable in time, where and odds), moves (learnsets, TMs, evolution timing),
    story (next steps, route to the Champion, guide passages).

    Args:
        tasks: One entry per researcher job, each a specific, self-contained instruction.
    """
    c = ctx.context
    if c.research_round >= MAX_RESEARCH_ROUNDS:
        return json.dumps({"error": f"research round limit ({MAX_RESEARCH_ROUNDS}) reached; draft the answer now and list what's unresolved"})
    c.research_round += 1
    results = await asyncio.gather(*(run_researcher(c, t) for t in tasks[:MAX_TASKS_PER_ROUND]))
    return json.dumps({"round": c.research_round, "results": results}, ensure_ascii=False)


INSTRUCTIONS = f"""\
You lead Lockesmith's research for a player partway through Pokémon Emerald (Gen III). You plan the
research, send it to researchers, then draft the answer as structured data for the writer. You
never state facts from memory: every fact in your draft must come from a researcher finding, with
its source ids copied exactly.

RESEARCH. Call dispatch_researchers with all of this round's tasks in ONE call, so they run in
parallel. Name the target battle by id in every task (e.g. "before gym7_tate_liza"). Pick
researchers by intent (and no others):
- catch: battle (what's coming and what threatens the party), catch (candidates obtainable before
  the target battle that fit the need, by type), moves (evolution timing and key moves for the
  party and the likely candidate types).
- next_steps: story (the next battle and what opens on the way); add battle if a party is known.
- plan: story (the road to the Champion), battle (the toughest fights ahead), catch (key catches
  along the way).
- lookup: only the one researcher that fits.
- revision: the original kind of research, telling researchers what the player rejected and what
  to change (a genuinely different plan, not a reshuffle).
Write each task as a specific, self-contained instruction (the researcher sees only the run state
and your task). One round is usually enough. Run a second round (the maximum is {MAX_RESEARCH_ROUNDS})
only to fill a specific gap a finding left open, and never repeat a task that was already answered.

DRAFT. Fill LeadDraft:
- recommendations: for catch/plan/revision, 2-4 picks, each with role, where (exact location,
  method and levels from the catch finding, e.g. "Route 119, Super Rod, Lv25-30"), when (the
  battle it should be caught before), why, source_ids, and 1-2 `alternatives` (with exact where)
  taken from other candidates the researchers found. Never recommend a species the player
  rejected or that breaks their rules.
- steps: for next_steps/plan, ordered steps with detail and source_ids. For lookups, put the answer
  in steps.
- battle_notes: per relevant battle, the threat and how to handle it, with source_ids.
- assumptions: what you assumed (from researcher findings and the run state).
- follow_up_questions: at most 3, from researchers' open questions, that would sharpen the answer.
- unresolved: anything the data couldn't answer, or out-of-scope parts of the question.
- headline: one sentence answering the question.
"""


def make_lead():
    # Low thinking: at default effort the Lead spent ~8k tokens (and a minute or more) per request
    # deliberating; the researchers' findings carry the substance.
    return runtime.make_agent("lead", INSTRUCTIONS, "strong", tools=[dispatch_researchers], output_type=LeadDraft, effort="low")
