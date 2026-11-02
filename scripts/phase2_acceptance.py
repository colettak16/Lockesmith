"""Phase 2 acceptance (PLAN.md §13) against the live models, plus the D8 additions.

    uv run python scripts/phase2_acceptance.py            # all scenarios
    uv run python scripts/phase2_acceptance.py vague      # one by name

Checks: a vanilla catch question runs end to end with researchers running in parallel in
one round; a vague question is answered with a clarifying question; an out-of-scope one
is declined; plus a next-steps question and a revision of the first answer. Full
responses are written to docs/phase2_runs/<scenario>.json.
"""

import asyncio
import json
import sys
import time
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import pipeline  # noqa: E402
from agent.state import PartyMember, RunState  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "phase2_runs"

MID_GAME = RunState(
    starter="mudkip", rival="may", badges=["stone", "knuckle", "dynamo", "heat", "balance", "feather"],
    party=[PartyMember(species="Marshtomp", level=33), PartyMember(species="Breloom", level=30),
           PartyMember(species="Swellow", level=31), PartyMember(species="Manectric", level=30)],
)
SCENARIOS = {
    "vanilla": ("What should I catch to get through Tate & Liza?", MID_GAME, "session-vanilla"),
    "revision": ("I don't like those picks, give me something else.", None, "session-vanilla"),
    "next_steps": ("What should I do next?", RunState(starter="treecko", badges=["stone"]), "session-next"),
    "vague": ("what should I catch?", None, "session-vague"),
    "out_of_scope": ("What's the best EV spread for Garchomp in Pokémon Sword?", None, "session-oos"),
}


def check(name: str, body: dict) -> list[str]:
    calls = body["tool_calls"]
    agents = [c["agent"] for c in calls]
    problems = []
    if name in ("vanilla", "revision", "next_steps"):
        if not body["citations"]:
            problems.append("no citations")
        rounds = Counter((c["round"], c["agent"]) for c in calls if c["agent"].endswith("_researcher"))
        first = {a for (r, a) in rounds if r == 1}
        if name != "next_steps" and len(first) < 2:
            problems.append(f"expected 2+ researchers in round 1, got {sorted(first)}")
        if "lead" not in agents:
            problems.append("lead never dispatched")
        failed = sum(1 for c in calls if c["name"] == "error")
        wrapped = sum(1 for c in calls if c["name"] == "turn_limit_wrap_up")
        if wrapped:
            print(f"  ({wrapped} agent run(s) hit the turn limit and wrapped up)")
        if failed:
            problems.append(f"{failed} researcher run(s) failed")
    if name == "vague" and any(a.endswith("_researcher") for a in agents):
        problems.append("researchers ran on a vague question")
    if name == "out_of_scope" and any(a.endswith("_researcher") for a in agents):
        problems.append("researchers ran on an out-of-scope question")
    return problems


async def run(name: str) -> bool:
    message, state, session_id = SCENARIOS[name]
    t = time.time()
    body = await pipeline.chat(message, session_id, state)
    problems = check(name, body)
    report(name, body, time.time() - t, problems, OUT)
    return not problems


def report(name: str, body: dict, took: float, problems: list[str], out_dir: Path) -> None:
    """Save the full response and print timings, model calls and the start of the answer."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(body, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    calls = body["tool_calls"]
    by_round = Counter((c["round"], c["agent"]) for c in calls)
    print(f"\n=== {name} ({took:.0f}s) {'OK' if not problems else 'PROBLEMS: ' + '; '.join(problems)}")
    print("tool calls by (round, agent):", dict(sorted(by_round.items())))
    researcher_spans = {}
    for c in calls:
        if c["agent"].endswith("_researcher"):
            lo, hi = researcher_spans.get((c["round"], c["agent"]), (c["t"], c["t"]))
            researcher_spans[(c["round"], c["agent"])] = (min(lo, c["t"]), max(hi, c["t"]))
    if researcher_spans:
        print("researcher tool-call windows (s):", {f"r{r} {a}": f"{lo}-{hi}" for (r, a), (lo, hi) in sorted(researcher_spans.items())})
    llm = {}
    for u in body.get("usage", []):
        n, lo, hi, out = llm.get(u["agent"], (0, u["t"], u["t"], 0))
        llm[u["agent"]] = (n + 1, min(lo, u["t"]), max(hi, u["t"]), out + u["output_tokens"])
    print("LLM calls (n, first-last s, output tokens):", {a: f"{n}, {lo}-{hi}, {out}" for a, (n, lo, hi, out) in llm.items()})
    usage = body.get("usage", [])
    print(f"model calls: {len(usage)}; served by the fallback model after a 429: {sum(1 for u in usage if u.get('fallback'))}")
    print(f"citations: {len(body['citations'])}; unverified: {(body['plan'] or {}).get('unverified_source_ids', [])}")
    print(body["response"][:900] + ("..." if len(body["response"]) > 900 else ""))


async def main(names: list[str]) -> int:
    ok = True
    for name in names:
        ok &= await run(name)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:] or list(SCENARIOS))))
