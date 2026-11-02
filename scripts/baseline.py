"""The no-tools baseline for the README (assignment: "the answer from the same model with no
tools and no system prompt, next to your agent's answer").

    uv run python scripts/baseline.py            # the three README samples
    uv run python scripts/baseline.py tate-liza  # one by id

Each sample's question goes to the Lead's model (the strongest in the pipeline, Gemini 3.1
Pro) with no system prompt and no tools. The run state the agent gets from the form is
written out in words, as a player would type it; for the randomizer sample the log itself is
pasted in. Answers go to docs/baseline/<id>.md.
"""

import asyncio
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import litellm  # noqa: E402

from agent import runtime  # noqa: E402,F401  (loads .env and the Vertex settings)
from agent.examples import EXAMPLES  # noqa: E402
from agent.pricing import cost_usd  # noqa: E402
from agent.runtime import model_name  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "baseline"


def state_in_words(ex: dict) -> str:
    """The run state as a player would type it."""
    rs, parts = ex["run_state"], ["I'm playing Pokémon Emerald."]
    if rs.get("starter"):
        parts.append(f"My starter was {rs['starter'].title()}" + (f" and my rival is {rs['rival'].title()}." if rs.get("rival") else "."))
    if rs.get("badges") is not None:
        badges = rs["badges"]
        parts.append(f"I have {len(badges)} badge{'s' if len(badges) != 1 else ''}"
                     + (f": {', '.join(b.title() for b in badges)}." if badges else "."))
    if rs.get("party"):
        parts.append("My party: " + ", ".join(f"{m['species']} Lv{m['level']}" for m in rs["party"]) + ".")
    r = rs.get("ruleset", {})
    if r.get("nuzlocke"):
        rules = ["Nuzlocke (first encounter per area only)"]
        rules += ["dupes clause"] if r.get("dupes_clause") else []
        rules += ["level caps at the next gym leader's highest level"] if r.get("level_caps") else []
        parts.append("Rules: " + ", ".join(rules) + ".")
        if r.get("used_routes"):
            parts.append("Areas whose encounter I've already used: " + ", ".join(r["used_routes"]) + ".")
    if ex.get("sample_log"):
        log = (ROOT / "static" / "samples" / ex["sample_log"]).read_text(encoding="utf-8")
        parts.append("It's a randomized run (Universal Pokémon Randomizer ZX). Here's my spoiler log:\n\n" + log)
    return " ".join(parts)


def prompt_for(ex: dict) -> str:
    return f"{state_in_words(ex)}\n\n{ex['message']}"


async def ask(ex: dict) -> dict:
    model = model_name("strong")
    prompt = prompt_for(ex)
    t = time.time()
    r = await litellm.acompletion(model=model, messages=[{"role": "user", "content": prompt}])
    took = time.time() - t
    usage = r.usage
    return {"id": ex["id"], "model": model, "prompt": prompt, "answer": r.choices[0].message.content, "seconds": round(took, 1),
            "input_tokens": usage.prompt_tokens, "output_tokens": usage.completion_tokens,
            "cost_usd": cost_usd(model, usage.prompt_tokens, usage.completion_tokens)}


def save(res: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{res['id']}.md"
    path.write_text(
        f"# Baseline: {res['id']}\n\n"
        f"{res['model']}, no tools, no system prompt. {res['seconds']} s, {res['input_tokens']} input / "
        f"{res['output_tokens']} output tokens, about ${res['cost_usd']:.4f}.\n\n"
        f"## Prompt\n\n```text\n{res['prompt']}\n```\n\n## Answer\n\n{res['answer']}\n",
        encoding="utf-8",
    )
    return path


async def main(ids: list[str]) -> int:
    samples = [e for e in EXAMPLES if (e["id"] in ids if ids else e.get("readme"))]
    for res in await asyncio.gather(*(ask(e) for e in samples)):
        print(f"{res['id']}: {res['seconds']} s -> {save(res).relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
