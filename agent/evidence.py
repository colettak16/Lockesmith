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


# What a cited database row says, for the citations list (the ids alone are opaque to a reader).
ROW_LABELS = {
    "species": ("SELECT name FROM species WHERE source_id = ?", "PokeAPI: {0} (species data)"),
    "moves": ("SELECT name FROM moves WHERE source_id = ?", "PokeAPI: {0} (move data)"),
    "encounters": (
        "SELECT s.name, coalesce(l.name, e.location), e.method FROM encounters e JOIN species s USING (species_id) "
        "LEFT JOIN locations l ON l.identifier = e.location WHERE e.source_id = ? LIMIT 1",
        "PokeAPI: {0} at {1} ({2})",
    ),
    "evolutions": (
        "SELECT f.name, t.name FROM evolutions e JOIN species f ON f.species_id = e.from_species_id "
        "JOIN species t ON t.species_id = e.to_species_id WHERE e.source_id = ? LIMIT 1",
        "PokeAPI: {0} evolves into {1}",
    ),
    "learnsets": (
        "SELECT s.name, m.name, l.method FROM learnsets l JOIN species s USING (species_id) JOIN moves m USING (move_id) "
        "WHERE l.source_id = ? LIMIT 1",
        "PokeAPI: {0} learns {1} ({2})",
    ),
    "machines": ("SELECT mc.label, m.name FROM machines mc JOIN moves m USING (move_id) WHERE mc.source_id = ?", "PokeAPI: {0} is {1}"),
}


@cache
def _vanilla():
    from agent.db import connect_readonly  # here, not at import: evidence is imported by the build too

    return connect_readonly()


@cache
def readable(source_id: str) -> str | None:
    """A plain-words label for a cited row, or None to keep `describe`'s."""
    kind, _, rest = source_id.partition(":")
    try:
        if kind == "pokeapi":
            for sql, template in ROW_LABELS.values():
                row = _vanilla().cursor().execute(sql, [source_id]).fetchone()
                if row:
                    return template.format(*row)
        if kind == "progression":
            from agent.progression import load

            return f"Story progression (data/progression.yaml): {load().get(rest).label}"
        if kind == "log" and rest.startswith("trainers#"):
            row = _vanilla().cursor().execute(
                "SELECT class_name, name FROM trainers WHERE trainer_id = ?", [int(rest.split("#")[1])]).fetchone()
            if row:
                return f"Your randomizer log: {row[0]} {row[1].title()}'s team"
    except Exception:  # noqa: BLE001 - a label is a nicety; fall back to the generic one
        return None
    return None


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

        def split_ids(group: str) -> list[str]:
            # Ids can contain commas (guide anchors like "#Stop,_Thief!"), so join comma-separated
            # pieces back together whenever the joined text is a known id.
            pieces, out, i = group.split(","), [], 0
            while i < len(pieces):
                for j in range(len(pieces), i, -1):
                    candidate = ",".join(pieces[i:j]).strip()
                    if candidate in self.entries or j == i + 1:
                        out.append(candidate)
                        i = j
                        break
            return [s for s in out if s]

        def sub(m):
            ids = split_ids(m.group(1))
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
            {"n": n, "source_id": sid, "label": readable(sid) or self.entries[sid]["label"], "url": self.entries[sid]["url"]}
            for sid, n in numbers.items()
        ]
        return text, citations, unknown
