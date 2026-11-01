"""Fuzzy entity matching: user-typed names -> canonical ids (PLAN.md section 4.6).

Every lookup tool resolves names through here first, so "mr mime", "farfetchd",
"rt 119", "tate and liza" and ROM spellings from randomizer logs ("FAINT ATTACK",
"NIDORAN♀") all land on the same rows.

Matching is two-stage: an exact hit on a normalised, space-free alias wins outright;
otherwise RapidFuzz WRatio ranks aliases above a cutoff. Callers get every candidate
with its score, so a tool can ask the user when the top two are close.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
from rapidfuzz import fuzz, process

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "emerald.duckdb"
KINDS = ("species", "move", "location", "trainer")
AMBIGUITY_MARGIN = 3.0


@dataclass(frozen=True)
class Match:
    kind: str
    id: str  # species/move identifier, location slug or trainer const
    name: str
    score: float
    alias: str
    rank: int = field(default=0, compare=False)  # tie-break: lower is the likelier referent


def normalize(text: str) -> str:
    text = text.replace("♀", " f").replace("♂", " m").replace("é", "e").replace("&", " and ")
    text = text.lower()
    text = re.sub(r"['’`]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\b(?:rt|rte|r)\s*(\d{3})\b", r"route \1", text)
    text = re.sub(r"\broute(\d{3})\b", r"route \1", text)
    text = re.sub(r"\bmt\b", "mount", text)
    return " ".join(text.split())


def compact(text: str) -> str:
    return normalize(text).replace(" ", "")


class EntityIndex:
    def __init__(self, con: duckdb.DuckDBPyConnection | None = None):
        own = con is None
        con = con or duckdb.connect(str(DB_PATH), read_only=True)
        self._entries: dict[str, list[Match]] = {}  # normalised alias -> candidates
        self._by_compact: dict[str, list[Match]] = {}
        self._load(con)
        if own:
            con.close()
        self._aliases = {kind: [a for a, ms in self._entries.items() if any(m.kind == kind for m in ms)] for kind in KINDS}

    def _add(self, kind: str, id_: str, name: str, aliases, rank: int = 0) -> None:
        for alias in {a for a in aliases if a}:
            norm = normalize(alias)
            if not norm:
                continue
            m = Match(kind, id_, name, 100.0, norm, rank)
            self._entries.setdefault(norm, []).append(m)
            self._by_compact.setdefault(norm.replace(" ", ""), []).append(m)

    def _load(self, con: duckdb.DuckDBPyConnection) -> None:
        for identifier, name, rom in con.execute("SELECT identifier, name, rom_name FROM species").fetchall():
            extra = [identifier.replace("nidoran-f", "nidoran female").replace("nidoran-m", "nidoran male")]
            self._add("species", identifier, name, [identifier, name, rom, *extra])
        for identifier, name, rom in con.execute("SELECT identifier, name, rom_name FROM moves").fetchall():
            self._add("move", identifier, name, [identifier, name, rom])
        locations = con.execute(
            """
            SELECT l.identifier, l.name, list(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL)
            FROM locations l
            LEFT JOIN map_sections s ON s.location = l.identifier
            WHERE l.identifier IN (SELECT location FROM maps UNION SELECT location FROM location_areas)
            GROUP BY 1, 2
            """
        ).fetchall()
        for identifier, name, rom_names in locations:
            plain = identifier.removeprefix("hoenn-").removesuffix("-hoenn")
            self._add("location", identifier, name or identifier, [identifier, plain, name, *(rom_names or [])])
        trainers = con.execute(
            "SELECT trainer_const, name, class_name, trainer_id FROM trainers WHERE party_size > 0 ORDER BY trainer_id"
        ).fetchall()
        for const, name, class_name, trainer_id in trainers:
            # Rematch variants (_2.._5) and generic grunts rank below the first, story-relevant fight.
            rank = trainer_id + (10_000 if re.search(r"_[2-5]$", const) else 0)
            label = f"{class_name} {name}".strip()
            base = re.sub(r"_\d+$", "", const.removeprefix("TRAINER_")).replace("_", " ")
            self._add("trainer", const, label, [name, label, base, const.removeprefix("TRAINER_")], rank)

    def match(self, text: str, kinds: tuple[str, ...] | str | None = None, limit: int = 5, cutoff: float = 70.0) -> list[Match]:
        """Candidates for `text`, best first. Exact (normalised) hits score 100."""
        kinds = (kinds,) if isinstance(kinds, str) else (kinds or KINDS)
        query = normalize(text)
        if not query:
            return []
        exact = [m for m in self._by_compact.get(query.replace(" ", ""), []) if m.kind in kinds]
        if exact:
            return self._dedupe(exact)[:limit]
        found: list[Match] = []
        for kind in kinds:
            for alias, score, _ in process.extract(query, self._aliases[kind], scorer=fuzz.WRatio, limit=limit * 3, score_cutoff=cutoff):
                found += [Match(m.kind, m.id, m.name, score, alias, m.rank) for m in self._entries[alias] if m.kind == kind]
        return self._dedupe(found)[:limit]

    def resolve(self, text: str, kind: str, cutoff: float = 70.0) -> Match | None:
        matches = self.match(text, kind, limit=2, cutoff=cutoff)
        return matches[0] if matches else None

    @staticmethod
    def is_ambiguous(matches: list[Match]) -> bool:
        """True when the runner-up is a different entity scored within AMBIGUITY_MARGIN of the best."""
        return len(matches) > 1 and matches[0].score - matches[1].score < AMBIGUITY_MARGIN and matches[0].score < 100

    @staticmethod
    def _dedupe(matches: list[Match]) -> list[Match]:
        best: dict[tuple[str, str], Match] = {}
        for m in matches:
            key = (m.kind, m.id)
            if key not in best or (m.score, -m.rank) > (best[key].score, -best[key].rank):
                best[key] = m
        return sorted(best.values(), key=lambda m: (-m.score, m.rank, m.id))
