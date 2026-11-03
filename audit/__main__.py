"""Run every audit check and write the reports to docs/audit/.

    uv run python -m audit

Downloads the two decomps at their pinned commits on first use (audit.sources). The
version-dependent checks run once as Ruby and once as Sapphire; the summary says whether the
two reports are identical (review packet V-13). Takes about a minute.
"""

import sys
import time
from pathlib import Path

from audit import chokepoints, core_data, encounter_scripts, engine, layouts, map_changes, reach, story_gates
from audit.sources import ROOT, pinned

OUT = ROOT / "docs" / "audit"
ONCE = {"core_data": core_data.main, "engine": engine.main, "layouts": layouts.main, "reach": lambda: reach.main([])}
PER_VERSION = {"story_gates": story_gates.main, "map_changes": map_changes.main,
               "chokepoints": chokepoints.main, "encounter_scripts": encounter_scripts.main}


def header(name: str) -> str:
    (rr, rs), (er, es) = pinned("pokeruby"), pinned("pokeemerald")
    return (f"# audit.{name}: {rr}@{rs[:12]} vs {er}@{es[:12]}\n"
            f"# regenerate with `uv run python -m audit` (see audit/README.md)\n")


def write(name: str, lines: list[str]) -> str:
    text = "\n".join(lines).rstrip() + "\n"
    (OUT / f"{name}.txt").write_text(header(name.removesuffix("_ruby").removesuffix("_sapphire")) + text, encoding="utf-8")
    return text


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in ONCE.items():
        t = time.time()
        write(name, fn())
        print(f"{name}: {time.time() - t:.0f}s", file=sys.stderr)
    same = {}
    for name, fn in PER_VERSION.items():
        t = time.time()
        ruby, sapphire = write(f"{name}_ruby", fn("RUBY")), write(f"{name}_sapphire", fn("SAPPHIRE"))
        same[name] = ruby == sapphire
        print(f"{name}: {time.time() - t:.0f}s, Ruby and Sapphire {'identical' if same[name] else 'DIFFER'}", file=sys.stderr)
    print(f"wrote {len(list(OUT.glob('*.txt')))} reports to {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
