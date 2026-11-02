"""Phase 3 acceptance (PLAN.md §13) against the live models: the Verifier and gap loop on a
Nuzlocke, custom rules learned in chat, and a randomized run from an uploaded log.

    uv run python scripts/phase3_acceptance.py              # all scenarios
    uv run python scripts/phase3_acceptance.py randomizer   # one by name

Each final plan is checked again with the Verifier (citation codes aside, since that needs
the request's own evidence ledger), so a pick that slipped through shows up here. Full
responses are written to docs/phase3_runs/<scenario>.json.
"""

import asyncio
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import pipeline  # noqa: E402
from agent.context import RequestContext  # noqa: E402
from agent.schemas import LeadDraft  # noqa: E402
from agent.session import SESSIONS  # noqa: E402
from agent.state import PartyMember, RunState, Ruleset  # noqa: E402
from agent.verifier import ERROR, verify  # noqa: E402
from scripts.phase2_acceptance import MID_GAME, report  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "phase3_runs"
SEVEN_BADGES = ["stone", "knuckle", "dynamo", "heat", "balance", "feather", "mind"]
LATE_PARTY = [PartyMember(species="Swampert", level=42), PartyMember(species="Breloom", level=40),
              PartyMember(species="Swellow", level=40), PartyMember(species="Manectric", level=39)]
USED = ["Route 101", "Route 102", "Route 103", "Route 104", "Petalburg Woods", "Route 116", "Rusturf Tunnel",
        "Granite Cave", "Route 110", "Route 117", "Route 111", "Route 112", "Fiery Path", "Route 113", "Route 114",
        "Meteor Falls", "Route 115", "Route 118", "Route 119", "Route 120", "Route 121", "Safari Zone", "Mt. Pyre"]
NUZLOCKE = RunState(starter="mudkip", rival="may", badges=SEVEN_BADGES, party=LATE_PARTY,
                    ruleset=Ruleset(nuzlocke=True, dupes_clause=True, level_caps=True, used_routes=USED))
# A hand-made log in UPR ZX's format (Randomizer.java, TrainerPokemon.toString): Tate & Liza
# randomized to Fire types. UPR prints sections only for what it randomized, so the rest is vanilla.
FIRE_TATE_LIZA = (Path(__file__).resolve().parent.parent / "static" / "samples" / "fire-tate-liza.log").read_text(encoding="utf-8")
FIRE_TEAM = ("camerupt", "torkoal", "magcargo", "houndoom")

SCENARIOS = {
    "nuzlocke": ("Nuzlocke with the dupes clause and level caps. Juan is next; what should I catch?", NUZLOCKE, "p3-nuzlocke"),
    "custom_rules": ("I'm doing a Water monotype run with no legendaries. What should I catch before Juan?",
                     RunState(starter="mudkip", rival="may", badges=SEVEN_BADGES,
                              party=[PartyMember(species="Swampert", level=42), PartyMember(species="Pelipper", level=38)]),
                     "p3-custom"),
    "randomizer": ("What should I catch to get through Tate & Liza?", MID_GAME, "p3-randomizer"),
}


def recheck(session_id: str, body: dict) -> list[str]:
    """Errors the Verifier still finds in the final plan (citation codes aside)."""
    if not body["plan"]:
        return ["no plan"]
    session = SESSIONS.get(session_id)
    ctx = RequestContext(state=session.state, con=session.con, excluded_species=set(session.excluded),
                         randomizer=session.randomizer)
    draft = LeadDraft(**{k: v for k, v in body["plan"].items() if k in LeadDraft.model_fields})
    return [f"{v.species}: {v.code}" for v in verify(ctx, draft)
            if v.severity == ERROR and not v.code.startswith(("UNCITED", "CITATION"))]


def check(name: str, session_id: str, body: dict) -> list[str]:
    calls = body["tool_calls"]
    problems = [f"still failing: {p}" for p in recheck(session_id, body)]
    if not any(c["agent"] == "verifier" and c["name"] == "verify" for c in calls):
        problems.append("the Verifier never ran")
    if not body["citations"]:
        problems.append("no citations")
    if failed := sum(1 for c in calls if c["name"] == "error"):
        problems.append(f"{failed} agent run(s) failed")
    if name == "custom_rules":
        rules = SESSIONS.get(session_id).state.ruleset
        if rules.monotype != "water" or not rules.no_legendaries:
            problems.append(f"rules not learned from the message: {rules.describe()}")
    if name == "randomizer":
        scouted = " ".join(str(c["result"]) for c in calls if c["name"] in ("scout_battle", "get_trainer_team", "threat_matrix"))
        if not any(s in scouted.lower() for s in FIRE_TEAM):
            problems.append("no battle tool returned the log's Tate & Liza team")
        if not any(s in body["response"].lower() for s in FIRE_TEAM):
            problems.append("the answer doesn't mention the randomized team")
        if not any(c["source_id"].startswith("log:") for c in body["citations"]):
            problems.append("nothing cited from the log")
    return problems


def gap_loop(body: dict) -> str:
    calls = body["tool_calls"]
    verifies = [c for c in calls if c["agent"] == "verifier" and c["name"] == "verify"]
    promoted = [c["result"] for c in calls if c["name"] == "promote_backups"]
    repaired = any(c["args"].get("after") == "repair" for c in verifies)
    return (f"verify runs: {len(verifies)}; backups promoted: {promoted or 'none'}; repair round: {'yes' if repaired else 'no'}; "
            f"first verify: {str(verifies[0]['result'])[:300] if verifies else '-'}")


async def run(name: str) -> bool:
    message, state, session_id = SCENARIOS[name]
    SESSIONS.clear(session_id)
    if name == "randomizer":
        loaded = pipeline.load_log(FIRE_TATE_LIZA, "fire-tate-liza.log", session_id)
        print(f"loaded log: shadowed {loaded['shadowed']}, unread {loaded['unread']}, warnings {loaded['warnings']}")
    t = time.time()
    body = await pipeline.chat(message, session_id, state)
    problems = check(name, session_id, body)
    report(name, body, time.time() - t, problems, OUT)
    print(gap_loop(body))
    return not problems


async def main(names: list[str]) -> int:
    ok = True
    for name in names:
        ok &= await run(name)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:] or list(SCENARIOS))))
