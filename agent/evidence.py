"""Evidence ledger (PLAN.md §7): every source_id a tool returned during one request.

Writers cite ledger ids as `[[source_id]]`; `cite` swaps those for `[n]` markers and
builds the response's `citations` list with a human-readable label and, where there is
one, a link.
"""

import json
import re
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "data" / "guide" / "chunks.jsonl"
LOCK = ROOT / "data" / "sources.lock.json"
DECOMP_FILES = {
    "trainer_parties.h": "src/data/trainer_parties.h",
    "trainers.h": "src/data/trainers.h",
}
CITE_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")


@cache
def guide_urls() -> dict[str, tuple[str, str]]:
    out = {}
    for line in CHUNKS.read_text(encoding="utf-8").splitlines():
        c = json.loads(line)
        out[c["source_id"]] = (f"Bulbapedia: {c['page']} § {c['section']}", c["url"])
    return out


@cache
def decomp_sha() -> str:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    entry = next(v for k, v in lock.items() if "emerald" in k.lower())
    return entry["sha"] if isinstance(entry, dict) else entry


def describe(source_id: str) -> tuple[str, str | None]:
    """(label, url) for a source id."""
    kind, _, rest = source_id.partition(":")
    if kind == "guide" and source_id in guide_urls():
        return guide_urls()[source_id]
    if kind == "decomp":
        path, _, anchor = rest.partition("#")
        path = DECOMP_FILES.get(path, path)
        url = f"https://github.com/pret/pokeemerald/blob/{decomp_sha()}/{path}" if "/" in path else None
        return f"pokeemerald {path}" + (f" ({anchor})" if anchor else ""), url
    if kind == "pokeapi":
        table, _, row = rest.partition("#")
        return f"PokeAPI {table}" + (f" row {row}" if row else ""), None
    if kind == "progression":
        return f"data/progression.yaml: {rest}", None
    if kind == "rules":
        return {"gen3_type_chart": "Gen 3 type chart (pokeemerald gTypeEffectiveness)"}.get(rest, f"rules: {rest}"), None
    if kind == "log":
        return f"your randomizer log: {rest}", None
    if kind == "sql":
        return f"database query {rest}", None
    return source_id, None


class Ledger:
    def __init__(self) -> None:
        self.entries: dict[str, dict] = {}

    def add(self, source_id: str, detail: str | None = None) -> None:
        if source_id and source_id not in self.entries:
            label, url = describe(source_id)
            self.entries[source_id] = {"label": label, "url": url, "detail": detail}

    def __contains__(self, source_id: str) -> bool:
        return source_id in self.entries

    def cite(self, markdown: str) -> tuple[str, list[dict], list[str]]:
        """Replace `[[id]]` markers with `[n]`; return the text, the citations list and any ids
        that weren't in the ledger (dropped from the text)."""
        numbers: dict[str, int] = {}
        unknown: list[str] = []

        def sub(m):
            ids = [s.strip() for s in m.group(1).split(",")]
            marks = []
            for sid in ids:
                if sid not in self.entries:
                    unknown.append(sid)
                    continue
                numbers.setdefault(sid, len(numbers) + 1)
                marks.append(f"[{numbers[sid]}]")
            return "".join(marks)

        text = CITE_RE.sub(sub, markdown)
        citations = [
            {"n": n, "source_id": sid, "label": self.entries[sid]["label"], "url": self.entries[sid]["url"]}
            for sid, n in numbers.items()
        ]
        return text, citations, unknown
