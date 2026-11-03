"""The games LockeSmith covers and where each one's data lives (docs/decisions.md D13).

Emerald is built from pret/pokeemerald. Ruby and Sapphire are both built from
pret/pokeruby, which compiles either game from one tree; `rom_version` picks the
version-specific wild tables, script branches (`.ifdef SAPPHIRE`) and aliases
(`constants/version.inc`). Each game gets its own database, progression file and
walkthrough corpus, so a session reads exactly one game's data.
"""

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Game:
    id: str  # "emerald" | "ruby" | "sapphire"
    short: str  # "Emerald"
    decomp: str  # key in data/sources.lock.json and the build cache directory
    repo: str  # GitHub repo of the decompilation
    version_id: int  # PokeAPI version
    version_group_id: int  # PokeAPI version group
    rom_version: str | None  # pokeruby's build flag; None for Emerald

    @property
    def name(self) -> str:
        return f"Pokémon {self.short}"

    @property
    def db_path(self) -> Path:
        return ROOT / "data" / f"{self.id}.duckdb"

    @property
    def progression_path(self) -> Path:
        return ROOT / "data" / ("progression.yaml" if self.id == "emerald" else "progression_rs.yaml")

    @property
    def guide_dir(self) -> Path:
        return ROOT / "data" / ("guide" if self.id == "emerald" else "guide_rs")

    @property
    def is_rs(self) -> bool:
        return self.rom_version is not None


GAMES = {
    "emerald": Game("emerald", "Emerald", "pokeemerald", "pret/pokeemerald", 9, 6, None),
    "ruby": Game("ruby", "Ruby", "pokeruby", "pret/pokeruby", 7, 5, "RUBY"),
    "sapphire": Game("sapphire", "Sapphire", "pokeruby", "pret/pokeruby", 8, 5, "SAPPHIRE"),
}
DEFAULT = "emerald"
EMERALD = GAMES["emerald"]


def get(game_id: str | None) -> Game:
    """The game for an id ("ruby", "Pokémon Sapphire", None for the default)."""
    key = (game_id or DEFAULT).strip().lower().removeprefix("pokémon ").removeprefix("pokemon ")
    if key not in GAMES:
        raise ValueError(f"unknown game {game_id!r}; use one of {sorted(GAMES)}")
    return GAMES[key]
