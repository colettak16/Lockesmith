"""Run the agent on the README's sample queries and save full traces (PLAN.md §11).

    uv run python scripts/run_samples.py            # the three README samples
    uv run python scripts/run_samples.py tate-liza  # one by id

Each sample runs exactly as its example button does on the site: a fresh session, the form's
run state and, for the randomizer sample, the sample log uploaded first. Writes
docs/samples/<id>.json (the full /chat body plus per-call usage and cost) and <id>.md (the
answer, its sources, time and cost).
"""

import asyncio
import json
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import pipeline  # noqa: E402
from agent.examples import EXAMPLES  # noqa: E402
from agent.session import SESSIONS  # noqa: E402
from agent.state import RunState  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "samples"


async def run(ex: dict) -> dict:
    session_id = f"sample-{ex['id']}"
    SESSIONS.clear(session_id)
    if ex.get("sample_log"):
        text = (ROOT / "static" / "samples" / ex["sample_log"]).read_text(encoding="utf-8")
        pipeline.load_log(text, ex["sample_log"], session_id)
    t = time.time()
    body = await pipeline.chat(ex["message"], session_id, RunState(**ex["run_state"]))
    body["seconds"] = round(time.time() - t, 1)
    return body


def save(ex: dict, body: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{ex['id']}.json").write_text(json.dumps(body, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    usage = body["usage"]
    cost = sum(u["cost_usd"] or 0 for u in usage)
    researchers = sorted({c["agent"] for c in body["tool_calls"] if c["agent"].endswith("_researcher")})
    sources = "\n".join(f"{c['n']}. {c['label']} (`{c['source_id']}`)" for c in body["citations"])
    (OUT / f"{ex['id']}.md").write_text(
        f"# Agent: {ex['id']}\n\n"
        f"**Question:** {ex['message']}\n\n"
        f"{body['seconds']} s · {len(usage)} model calls · {sum(u['input_tokens'] + u['output_tokens'] for u in usage):,} tokens · "
        f"about ${cost:.3f} · researchers: {', '.join(researchers) or 'none'} · {len(body['tool_calls'])} trace steps "
        f"(full trace in `{ex['id']}.json`)\n\n## Answer\n\n{body['response']}\n\n## Sources\n\n{sources or '(none)'}\n",
        encoding="utf-8",
    )
    print(f"{ex['id']}: {body['seconds']} s, {len(usage)} model calls, about ${cost:.3f}")


async def main(ids: list[str]) -> int:
    for ex in [e for e in EXAMPLES if (e["id"] in ids if ids else e.get("readme"))]:
        save(ex, await run(ex))  # one at a time, as a grader would ask them
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
