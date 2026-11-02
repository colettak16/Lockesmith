"""Run state and rulesets (PLAN.md §9, docs/decisions.md D8).

Required: the starter and which gym badges the player holds (a list, not a count, so a
deferred Brawly works). Optional: rival, last major battle, party, ruleset. `progress`
turns that into the battles already behind the player and the ones still ahead.
"""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from agent.progression import RIVALS, STARTERS, Battle, Progression

# Badge -> the gym battle that awards it. Leader names and battle ids are accepted too.
BADGES = {
    "stone": "gym1_roxanne",
    "knuckle": "gym2_brawly",
    "dynamo": "gym3_wattson",
    "heat": "gym4_flannery",
    "balance": "gym5_norman",
    "feather": "gym6_winona",
    "mind": "gym7_tate_liza",
    "rain": "gym8_juan",
}
LEADERS = {
    "roxanne": "stone", "brawly": "knuckle", "wattson": "dynamo", "flannery": "heat", "norman": "balance",
    "winona": "feather", "tate": "mind", "liza": "mind", "tate and liza": "mind", "tate & liza": "mind", "juan": "rain",
}
GYM_TO_BADGE = {gym: badge for badge, gym in BADGES.items()}


def normalize_badge(value: str) -> str:
    v = value.strip().lower().removesuffix(" badge").replace("_", " ")
    if v in BADGES:
        return v
    if v in LEADERS:
        return LEADERS[v]
    gym = value.strip().lower()
    if gym in GYM_TO_BADGE:
        return GYM_TO_BADGE[gym]
    raise ValueError(f"unknown badge {value!r}; use one of {sorted(BADGES)}")


class PartyMember(BaseModel):
    species: str
    level: int = Field(ge=1, le=100)
    moves: list[str] = Field(default_factory=list, description="Known moves, if the player gave them")


class Ruleset(BaseModel):
    """Challenge rules. Presets are checked in code; `notes` holds free-text rules that aren't."""

    nuzlocke: bool = False
    used_routes: list[str] = Field(default_factory=list, description="Locations whose one encounter is used up")
    dupes_clause: bool = False
    level_caps: bool = False
    monotype: str | None = Field(default=None, description="Every Pokémon must have this type (dual types count)")
    no_legendaries: bool = False
    banned_species: list[str] = Field(default_factory=list)
    wild_only: bool = Field(default=False, description="No gifts, static encounters or in-game trades")
    notes: list[str] = Field(default_factory=list, description="Free-text rules the agents follow but code can't check")

    def describe(self) -> list[str]:
        out = []
        if self.nuzlocke:
            out.append("Nuzlocke: first encounter per area only" + (", dupes clause" if self.dupes_clause else ""))
        if self.used_routes:
            out.append("encounters already used: " + ", ".join(self.used_routes))
        if self.level_caps:
            out.append("level caps: stay at or below the next boss's highest level")
        if self.monotype:
            out.append(f"{self.monotype}-type only")
        if self.no_legendaries:
            out.append("no legendary or mythical Pokémon")
        if self.banned_species:
            out.append("banned: " + ", ".join(self.banned_species))
        if self.wild_only:
            out.append("wild catches only (no gifts, static encounters or trades)")
        out += [f"{n} (followed, not checked automatically)" for n in self.notes]
        return out


class RunState(BaseModel):
    starter: Literal["treecko", "torchic", "mudkip"] | None = None
    badges: list[str] | None = Field(default=None, description="Badges held; [] means none yet, null means not given")
    rival: Literal["may", "brendan"] | None = None
    last_battle: str | None = Field(default=None, description="Id of the last major battle beaten (progression.yaml)")
    party: list[PartyMember] = Field(default_factory=list)
    current_location: str | None = None
    ruleset: Ruleset = Field(default_factory=Ruleset)
    randomizer_log_id: str | None = None

    @field_validator("starter", "rival", mode="before")
    @classmethod
    def _lower(cls, v):
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator("badges", mode="before")
    @classmethod
    def _badges(cls, v):
        if v is None:
            return None
        return sorted({normalize_badge(b) for b in v}, key=list(BADGES).index)

    def missing_required(self) -> list[str]:
        return [name for name, value in (("starter", self.starter), ("badges", self.badges)) if value is None]


@dataclass
class Progress:
    done: list[Battle]
    remaining: list[Battle]
    deferred: list[Battle]  # gyms behind the frontier whose badge the player doesn't hold
    next_battle: Battle | None
    assumptions: list[str] = field(default_factory=list)

    @property
    def next_required(self) -> Battle | None:
        """The next battle the story forces (optional rival fights skipped); the natural
        "before which battle" for catch and TM questions."""
        return next((b for b in self.remaining if not b.optional and b not in self.deferred), self.next_battle)


def progress(state: RunState, prog: Progression) -> Progress:
    """Which story battles are behind the player and which are ahead.

    The frontier is the later of the last battle given and the last gym whose badge is
    held. Everything up to it counts as done, except gyms whose badge is missing (the game
    lets Brawly wait until Norman), which stay ahead as deferred.
    """
    assumptions = []
    held = {BADGES[b] for b in state.badges or []}
    frontier = 0
    for b in prog.battles:
        if b.id in held:
            frontier = max(frontier, b.order)
    if state.last_battle:
        frontier = max(frontier, prog.get(state.last_battle).order)
    elif frontier:
        assumptions.append(
            f"Assumed every story battle up to {prog.battles[frontier - 1].label} is behind you (no last battle given)."
        )
    deferred = [b for b in prog.battles if b.order <= frontier and b.id.startswith("gym") and b.id not in held]
    done = [b for b in prog.battles if b.order <= frontier and b not in deferred]
    remaining = deferred + [b for b in prog.battles if b.order > frontier]
    ahead = [b for b in prog.battles if b.order > frontier]
    if deferred:
        assumptions.append("Deferred gyms still ahead: " + ", ".join(b.label for b in deferred) + ".")
    return Progress(done, remaining, deferred, ahead[0] if ahead else None, assumptions)


def rival_for(state: RunState) -> str | None:
    return state.rival if state.rival in RIVALS else None


def starter_for(state: RunState) -> str | None:
    return state.starter if state.starter in STARTERS else None
