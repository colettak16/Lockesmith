"""The games LockeSmith covers and where each one's data lives (docs/decisions.md D13, D16).

Emerald is built from pret/pokeemerald. Ruby and Sapphire are both built from
pret/pokeruby, and FireRed and LeafGreen from pret/pokefirered; each of those compiles
either version from one tree, and `rom_version` picks the version-specific wild tables,
script branches (`.ifdef SAPPHIRE`, `.ifdef LEAFGREEN`) and aliases. Each game gets its own
database; the two versions of a pair share a progression file (resolved per version) and
a walkthrough corpus (passages tagged by version), named after the decomp family.
"""

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAMILIES = {"pokeemerald": "emerald", "pokeruby": "rs", "pokefirered": "frlg"}
# Data files are named after the family: progression.yaml, progression_rs.yaml, progression_frlg.yaml
FILE_SUFFIX = {"emerald": "", "rs": "_rs", "frlg": "_frlg"}


@dataclass(frozen=True)
class Game:
    id: str  # "emerald" | "ruby" | "sapphire" | "firered" | "leafgreen"
    short: str  # "Emerald"
    decomp: str  # key in data/sources.lock.json and the build cache directory
    repo: str  # GitHub repo of the decompilation
    version_id: int  # PokeAPI version
    version_group_id: int  # PokeAPI version group
    rom_version: str | None  # the decomp's build flag for two-version trees; None for Emerald
    region: str = "hoenn"

    @property
    def name(self) -> str:
        return f"Pokémon {self.short}"

    @property
    def family(self) -> str:
        """"emerald", "rs" (Ruby/Sapphire) or "frlg" (FireRed/LeafGreen)."""
        return FAMILIES[self.decomp]

    @property
    def db_path(self) -> Path:
        return ROOT / "data" / f"{self.id}.duckdb"

    @property
    def progression_path(self) -> Path:
        return ROOT / "data" / f"progression{FILE_SUFFIX[self.family]}.yaml"

    @property
    def guide_dir(self) -> Path:
        return ROOT / "data" / f"guide{FILE_SUFFIX[self.family]}"

    @property
    def is_rs(self) -> bool:
        return self.family == "rs"

    @property
    def is_frlg(self) -> bool:
        return self.family == "frlg"


GAMES = {
    "emerald": Game("emerald", "Emerald", "pokeemerald", "pret/pokeemerald", 9, 6, None),
    "ruby": Game("ruby", "Ruby", "pokeruby", "pret/pokeruby", 7, 5, "RUBY"),
    "sapphire": Game("sapphire", "Sapphire", "pokeruby", "pret/pokeruby", 8, 5, "SAPPHIRE"),
    "firered": Game("firered", "FireRed", "pokefirered", "pret/pokefirered", 10, 7, "FIRERED", "kanto"),
    "leafgreen": Game("leafgreen", "LeafGreen", "pokefirered", "pret/pokefirered", 11, 7, "LEAFGREEN", "kanto"),
}
DEFAULT = "emerald"
EMERALD = GAMES["emerald"]


def get(game_id: str | None) -> Game:
    """The game for an id ("ruby", "Pokémon Sapphire", None for the default)."""
    key = (game_id or DEFAULT).strip().lower().removeprefix("pokémon ").removeprefix("pokemon ")
    if key not in GAMES:
        raise ValueError(f"unknown game {game_id!r}; use one of {sorted(GAMES)}")
    return GAMES[key]
