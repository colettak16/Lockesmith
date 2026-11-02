"""Load data/progression.yaml: the ordered story battles and what's reachable before each.

An area spec in the YAML is `location` (every area), `location/area` (one PokeAPI
area) or `location/main` (the unnamed main area), optionally as a mapping
`{area: <spec>, methods: [...]}` when only some encounter methods open at that point
(Route 115's beach allows fishing long before its grass). `areas_reachable`
accumulates `areas_new` up to and including a battle, so "catchable before X" is a
join of encounters against that set, with method gates (surf, rods, dive, ...) on top.
"""

from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import yaml

PATH = Path(__file__).resolve().parent.parent / "data" / "progression.yaml"
ALL = "*"
STARTERS = ("treecko", "torchic", "mudkip")
RIVALS = ("may", "brendan")


AreaSpec = tuple[str, str | None, tuple[str, ...] | None]  # (location, area or ALL/None, methods or None = all)


def parse_area(spec: str | dict) -> AreaSpec:
    """'mt-pyre' -> ('mt-pyre', '*', None); 'hoenn-route-119/main' -> (..., None, None);
    {'area': 'x/b1f', 'methods': ['old-rod']} -> ('x', 'b1f', ('old-rod',))."""
    methods = None
    if isinstance(spec, dict):
        spec, methods = spec["area"], tuple(spec["methods"])
    location, _, area = spec.partition("/")
    if not area:
        return location, ALL, methods
    return location, None if area == "main" else area, methods


def area_matches(spec: AreaSpec, location: str, area: str | None, method: str | None = None) -> bool:
    """Does the spec cover this area (and this encounter method, when one is given)?"""
    return (
        spec[0] == location
        and (spec[1] == ALL or spec[1] == area)
        and (method is None or spec[2] is None or method in spec[2])
    )


@dataclass(frozen=True)
class Battle:
    id: str
    order: int
    label: str
    badges_before: int
    trainer_consts: tuple[str, ...] | None
    starter_variants: dict | None
    battle_format: str
    optional: bool
    location: str
    hm_gates_open: tuple[str, ...]
    key_items: tuple[str, ...]
    areas_new: tuple[AreaSpec, ...]
    source: str
    notes: str | None = None
    review: str | None = None
    partner: dict | None = None

    def trainers_for(self, starter: str | None = None, rival: str | None = None) -> list[str]:
        """Trainer consts for this fight. Rival fights need the player's starter; the rival
        (May or Brendan) only matters for the two fights where their teams differ."""
        if self.trainer_consts is not None:
            return list(self.trainer_consts)
        if starter not in STARTERS:
            raise ValueError(f"{self.id} depends on the player's starter")
        variants = self.starter_variants[starter]
        return [variants[rival]] if rival in RIVALS else sorted(set(variants.values()))


@dataclass
class Progression:
    battles: list[Battle]
    never_reachable: list[tuple[AreaSpec, str]] = field(default_factory=list)

    def get(self, battle_id: str) -> Battle:
        return next(b for b in self.battles if b.id == battle_id)

    def areas_reachable(self, battle_id: str) -> list[AreaSpec]:
        """Every area spec opened up to and including `battle_id`."""
        target = self.get(battle_id).order
        return [spec for b in self.battles if b.order <= target for spec in b.areas_new]

    def is_reachable(self, battle_id: str, location: str, area: str | None, method: str | None = None) -> bool:
        """Can the player be in this area before `battle_id`, with this encounter method open?

        Without `method`, any opened method counts. Item and HM gates (rods, Surf, Dive)
        still apply on top; this answers only where the player can stand.
        """
        return any(area_matches(spec, location, area, method) for spec in self.areas_reachable(battle_id))

    def never_reason(self, location: str, area: str | None) -> str | None:
        return next((reason for spec, reason in self.never_reachable if area_matches(spec, location, area)), None)

    def remaining(self, badges: int, include_optional: bool = True) -> list[Battle]:
        """Battles not yet fought for a player holding `badges` badges.

        Badges alone can't place a player between fights at the same badge count, so this
        returns everything from the first battle at that count; callers narrow it with
        the run state's last battle when known.
        """
        return [b for b in self.battles if b.badges_before >= badges and (include_optional or not b.optional)]


def _battle(raw: dict) -> Battle:
    consts = raw.get("trainer_consts")
    return Battle(
        id=raw["id"],
        order=raw["order"],
        label=raw["label"],
        badges_before=raw["badges_before"],
        trainer_consts=tuple(consts) if consts is not None else None,
        starter_variants=raw.get("starter_variants"),
        battle_format=raw["battle_format"],
        optional=bool(raw.get("optional", False)),
        location=raw["location"],
        hm_gates_open=tuple(raw.get("hm_gates_open") or ()),
        key_items=tuple(raw.get("key_items") or ()),
        areas_new=tuple(parse_area(a) for a in raw.get("areas_new") or ()),
        source=raw["source"],
        notes=raw.get("notes"),
        review=raw.get("review"),
        partner=raw.get("partner"),
    )


@cache
def load(path: Path = PATH) -> Progression:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    battles = sorted((_battle(b) for b in data["battles"]), key=lambda b: b.order)
    never = [(parse_area(n["area"]), n["reason"]) for n in data.get("never_reachable") or []]
    return Progression(battles, never)
