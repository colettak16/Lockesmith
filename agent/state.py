"""Run state and rulesets (PLAN.md §9, docs/decisions.md D8).

Required: the starter and which gym badges the player holds (a list, not a count, so a
deferred Brawly works). Optional: rival, last major battle, party, ruleset. `progress`
turns that into the battles already behind the player and the ones still ahead.
"""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from agent.games import DEFAULT, GAMES
from agent.games import get as get_game
from agent.progression import RIVALS, STARTERS, Battle, Progression

GameId = Literal["emerald", "ruby", "sapphire"]
BADGE_ORDER = ("stone", "knuckle", "dynamo", "heat", "balance", "feather", "mind", "rain")
# Badge -> the gym battle that awards it, per game (the 8th leader is Juan in Emerald, Wallace
# in Ruby/Sapphire). Leader names and battle ids are accepted too.
GYM_IDS = ("gym1_roxanne", "gym2_brawly", "gym3_wattson", "gym4_flannery", "gym5_norman", "gym6_winona", "gym7_tate_liza")
BADGE_GYMS = {
    game: dict(zip(BADGE_ORDER, (*GYM_IDS, "gym8_juan" if game == "emerald" else "gym8_wallace"))) for game in GAMES
}
BADGES = BADGE_GYMS[DEFAULT]
SHARED_LEADERS = {
    "roxanne": "stone", "brawly": "knuckle", "wattson": "dynamo", "flannery": "heat", "norman": "balance",
    "winona": "feather", "tate": "mind", "liza": "mind", "tate and liza": "mind", "tate & liza": "mind",
}
# "Wallace" is Emerald's Champion but Ruby/Sapphire's 8th leader, so leader names are per game.
GAME_LEADERS = {game: {**SHARED_LEADERS, ("juan" if game == "emerald" else "wallace"): "rain"} for game in GAMES}
LEADERS = GAME_LEADERS[DEFAULT]
GYM_TO_BADGE = {gym: badge for badge, gym in BADGES.items()}


def normalize_badge(value: str, game: str = DEFAULT) -> str:
    v = value.strip().lower().removesuffix(" badge").replace("_", " ")
    if v in BADGE_GYMS[game]:
        return v
    if v in GAME_LEADERS[game]:
        return GAME_LEADERS[game][v]
    gyms = {gym: badge for badge, gym in BADGE_GYMS[game].items()}
    gym = value.strip().lower()
    if gym in gyms:
        return gyms[gym]
    raise ValueError(f"unknown badge {value!r}; use one of {list(BADGE_ORDER)}")


class PartyMember(BaseModel):
    species: str
    level: int = Field(ge=1, le=100)
    moves: list[str] = Field(default_factory=list, description="Known moves, if the player gave them")


class Ruleset(BaseModel):
    """Challenge rules. Presets are checked in code; `notes` holds free-text rules that aren't."""

    nuzlocke: bool = False
    used_routes: list[str] = Field(default_factory=list, description="Areas whose one encounter is used up")
    encounter_scope: Literal["location", "area"] = Field(
        default="location",
        description="What one Nuzlocke encounter covers: each named location (Granite Cave is one) or each floor/room",
    )
    gifts_count_as_encounter: bool = Field(
        default=False, description="Whether gifts, static encounters and trades use up their area's encounter"
    )
    dupes_clause: bool = False
    level_caps: bool = False
    level_cap_offset: int = Field(default=0, description="Cap = the next boss's highest level plus this (e.g. -1)")
    allowed_types: list[str] = Field(
        default_factory=list, description="Every Pokémon must have at least one of these types (dual types count); empty allows all"
    )
    banned_types: list[str] = Field(default_factory=list, description="No Pokémon may have any of these types")
    no_legendaries: bool = False
    banned_species: list[str] = Field(default_factory=list)
    wild_only: bool = Field(default=False, description="No gifts, static encounters or in-game trades")
    notes: list[str] = Field(default_factory=list, description="Free-text rules the agents follow but code can't check")

    @model_validator(mode="before")
    @classmethod
    def _monotype(cls, data):
        """The single `monotype` field this replaced still works: it means one allowed type."""
        if isinstance(data, dict) and data.get("monotype"):
            data = {**data, "allowed_types": [*data.get("allowed_types", []), data["monotype"]]}
        return data

    @field_validator("allowed_types", "banned_types", mode="after")
    @classmethod
    def _types(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(t.strip().lower() for t in v if t and t.strip()))

    def type_problem(self, types: list[str | None]) -> str | None:
        """Why a Pokémon with these types breaks the type rules, or None."""
        have = {t for t in types if t}
        if self.allowed_types and not have & set(self.allowed_types):
            return "not " + " or ".join(t.title() for t in self.allowed_types) + "-type"
        if bad := sorted(have & set(self.banned_types)):
            return "/".join(t.title() for t in bad) + "-type, which is banned"
        return None

    def describe(self) -> list[str]:
        out = []
        if self.nuzlocke:
            scope = "named location" if self.encounter_scope == "location" else "floor or room"
            out.append(
                f"Nuzlocke: first encounter per {scope} only"
                + (", dupes clause" if self.dupes_clause else "")
                + ("; gifts, statics and trades use up their area's encounter" if self.gifts_count_as_encounter
                   else "; gifts, statics and trades are free")
            )
        if self.used_routes:
            out.append("encounters already used: " + ", ".join(self.used_routes))
        if self.level_caps:
            offset = f" {self.level_cap_offset:+d}" if self.level_cap_offset else ""
            out.append(f"level caps: stay at or below the next boss's highest level{offset}")
        if self.allowed_types:
            out.append("only " + " or ".join(t.title() for t in self.allowed_types) + " types")
        if self.banned_types:
            out.append("no " + " or ".join(t.title() for t in self.banned_types) + " types")
        if self.no_legendaries:
            out.append("no legendary or mythical Pokémon")
        if self.banned_species:
            out.append("banned: " + ", ".join(self.banned_species))
        if self.wild_only:
            out.append("wild catches only (no gifts, static encounters or trades)")
        out += [f"{n} (followed, not checked automatically)" for n in self.notes]
        return out


class RunState(BaseModel):
    game: GameId = Field(default=DEFAULT, description="Which game: emerald, ruby or sapphire")
    starter: Literal["treecko", "torchic", "mudkip"] | None = None
    badges: list[str] | None = Field(default=None, description="Badges held; [] means none yet, null means not given")
    rival: Literal["may", "brendan"] | None = None
    last_battle: str | None = Field(default=None, description="Id of the last major battle beaten (progression.yaml)")
    party: list[PartyMember] = Field(default_factory=list)
    current_location: str | None = None
    ruleset: Ruleset = Field(default_factory=Ruleset)
    randomizer_log_id: str | None = None

    @field_validator("game", mode="before")
    @classmethod
    def _game(cls, v):
        return get_game(v).id if isinstance(v, str) or v is None else v

    @field_validator("starter", "rival", mode="before")
    @classmethod
    def _lower(cls, v):
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator("badges", mode="before")
    @classmethod
    def _badges(cls, v, info: ValidationInfo):
        if v is None:
            return None
        game = info.data.get("game", DEFAULT)
        return sorted({normalize_badge(b, game) for b in v}, key=BADGE_ORDER.index)

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
    held = {BADGE_GYMS[state.game][b] for b in state.badges or []}
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
