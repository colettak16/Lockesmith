"""Load a progression file: the ordered story battles and what's reachable before each.

Emerald's is data/progression.yaml; Ruby and Sapphire share data/progression_rs.yaml,
where any value written as `{ruby: ..., sapphire: ...}` is resolved for the version
being loaded (the villain fights, hideouts and legendary differ). A step can be a
required wild battle (`wild: {species, level}`, the Cave of Origin legendary in
Ruby/Sapphire), and `events` lists the non-battle story milestones that gate areas.

An area spec in the YAML is `location` (every area), `location/area` (one PokeAPI
area) or `location/main` (the unnamed main area), optionally as a mapping
`{area: <spec>, methods: [...]}` when only some encounter methods open at that point
(Route 115's beach allows fishing long before its grass). `areas_reachable`
accumulates `areas_new` up to and including a battle, so "catchable before X" is a
join of encounters against that set, with method gates (surf, rods, dive, ...) on top.

Areas don't only open. `closes` lists the ones that close for good: with `after`, the
area can still be reached before that battle and is gone for every later one (Ruby and
Sapphire wall off Lilycove's hideout at the Mind Badge); without `after`, it closes on
something the player does (Emerald's Mirage Tower falls when a fossil is taken), so it's
never removed, only flagged as missable.
"""

from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import yaml

from agent.games import EMERALD, Game

PATH = EMERALD.progression_path
VERSIONS = ("ruby", "sapphire")
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
    wild: dict | None = None  # a required wild battle: {"species": "groudon", "level": 45}

    def trainers_for(self, starter: str | None = None, rival: str | None = None) -> list[str]:
        """Trainer consts for this fight. Rival fights need the player's starter; the rival
        (May or Brendan) only matters for the two fights where their teams differ."""
        if self.trainer_consts is not None:
            return list(self.trainer_consts)
        if self.wild is not None:
            return []
        if starter not in STARTERS:
            raise ValueError(f"{self.id} depends on the player's starter")
        variants = self.starter_variants[starter]
        return [variants[rival]] if rival in RIVALS else sorted(set(variants.values()))


@dataclass(frozen=True)
class Closing:
    spec: AreaSpec
    after: str | None  # the last battle it can be reached before; None = closes on a player action
    reason: str


@dataclass
class Progression:
    battles: list[Battle]
    never_reachable: list[tuple[AreaSpec, str]] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)  # story milestones that aren't battles
    closes: list[Closing] = field(default_factory=list)

    def get(self, battle_id: str) -> Battle:
        return next(b for b in self.battles if b.id == battle_id)

    def areas_reachable(self, battle_id: str) -> list[AreaSpec]:
        """Every area spec opened up to and including `battle_id` (closings not applied)."""
        target = self.get(battle_id).order
        return [spec for b in self.battles if b.order <= target for spec in b.areas_new]

    def opened(self, battle_id: str, location: str, area: str | None, method: str | None = None) -> bool:
        """Has this area (and method) opened by `battle_id`, whether or not it has closed since?"""
        return any(area_matches(spec, location, area, method) for spec in self.areas_reachable(battle_id))

    def closed_reason(self, battle_id: str, location: str, area: str | None, method: str | None = None) -> str | None:
        """Why this area is gone for good before `battle_id` (it closed after an earlier battle), or None."""
        target = self.get(battle_id).order
        return next((c.reason for c in self.closes if c.after is not None and self.get(c.after).order < target
                     and area_matches(c.spec, location, area, method)), None)

    def missable_reason(self, battle_id: str, location: str, area: str | None, method: str | None = None) -> str | None:
        """Why this area, still open before `battle_id`, will close for good later, or None."""
        target = self.get(battle_id).order
        return next((c.reason for c in self.closes if (c.after is None or self.get(c.after).order >= target)
                     and area_matches(c.spec, location, area, method)), None)

    def events_needed(self, battle_id: str, location: str, area: str | None, method: str | None = None) -> list[dict]:
        """Story events (not battles) this area still needs before `battle_id`: those with `areas`
        whose `required_by` battle isn't behind the player yet. Whether the player has done them
        is unknown, so callers present them as conditions."""
        target = self.get(battle_id).order
        return [e for e in self.events if e.get("areas") and self.get(e["required_by"]).order >= target
                and any(area_matches(parse_area(a), location, area, method) for a in e["areas"])]

    def is_reachable(self, battle_id: str, location: str, area: str | None, method: str | None = None) -> bool:
        """Can the player be in this area before `battle_id`, with this encounter method open?

        Without `method`, any opened method counts. Item and HM gates (rods, Surf, Dive)
        still apply on top; this answers only where the player can stand. An area that
        closed after an earlier battle (`closes`) isn't reachable any more.
        """
        return self.opened(battle_id, location, area, method) and not self.closed_reason(battle_id, location, area, method)

    def never_reason(self, location: str, area: str | None, method: str | None = None) -> str | None:
        """Why an encounter can't be had before the Champion, or None. Entries limited to some
        methods (Littleroot's gift) only answer for those methods, or for any method if none is given."""
        return next(
            (reason for spec, reason in self.never_reachable if area_matches(spec, location, area, method)), None
        )

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
        wild=raw.get("wild"),
    )


def resolve_versions(value, version: str | None):
    """Replace every `{ruby: x, sapphire: y}` mapping with the value for `version`."""
    if isinstance(value, dict):
        if value and set(value) <= set(VERSIONS):
            if version not in value:
                raise ValueError(f"no {version!r} value in {value}")
            return resolve_versions(value[version], version)
        return {k: resolve_versions(v, version) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_versions(v, version) for v in value]
    return value


@cache
def load(path: Path = PATH, version: str | None = None) -> Progression:
    data = resolve_versions(yaml.safe_load(Path(path).read_text(encoding="utf-8")), version)
    battles = sorted((_battle(b) for b in data["battles"]), key=lambda b: b.order)
    def spec(n: dict) -> AreaSpec:
        return parse_area({"area": n["area"], "methods": n["methods"]} if "methods" in n else n["area"])

    never = [(spec(n), n["reason"]) for n in data.get("never_reachable") or []]
    closes = [Closing(spec(c), c.get("after"), c["reason"]) for c in data.get("closes") or []]
    return Progression(battles, never, data.get("events") or [], closes)


def load_game(game: Game = EMERALD) -> Progression:
    """The progression for a game: Emerald's file, or the shared Ruby/Sapphire file resolved for the version."""
    return load(game.progression_path, game.id if game.is_rs else None)
