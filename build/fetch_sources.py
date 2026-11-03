"""Download raw sources into build/.cache/ and pin their commits.

    uv run python build/fetch_sources.py            # use SHAs in data/sources.lock.json
    uv run python build/fetch_sources.py --update   # re-resolve to the latest upstream commits

PokeAPI CSVs come from raw.githubusercontent.com at a fixed commit. The decomps
(pokeemerald for Emerald, pokeruby for Ruby and Sapphire, pokefirered for FireRed and
LeafGreen) are sparse, blobless git checkouts of only the directories the build reads.
"""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "build" / ".cache"
LOCK = ROOT / "data" / "sources.lock.json"
USER_AGENT = "Lockesmith/0.1 (IEOR E4570 course project)"

POKEAPI_REPO = "PokeAPI/pokeapi"
POKEEMERALD_REPO = "pret/pokeemerald"
POKERUBY_REPO = "pret/pokeruby"
POKEFIRERED_REPO = "pret/pokefirered"

POKEAPI_CSVS = [
    "abilities", "ability_flavor_text", "ability_names",
    "egg_groups", "pokemon_egg_groups",
    "encounter_condition_value_map", "encounter_condition_values", "encounter_conditions",
    "encounter_methods", "encounter_slots", "encounters",
    "evolution_chains", "evolution_triggers", "pokemon_evolution",
    "generations", "growth_rates",
    "item_game_indices", "item_names", "items",
    "location_areas", "location_area_prose", "location_game_indices", "location_names", "locations",
    "machines",
    "move_changelog", "move_damage_classes", "move_flavor_text", "move_names", "move_targets", "moves",
    "pokemon", "pokemon_species", "pokemon_species_names", "pokemon_game_indices",
    "pokemon_abilities", "pokemon_abilities_past",
    "pokemon_move_methods", "pokemon_moves",
    "pokemon_stats", "pokemon_stats_past",
    "pokemon_types", "pokemon_types_past",
    "stats",
    "type_efficacy", "type_efficacy_past", "type_names", "types",
    "version_groups", "versions",
]

# Directories of pokeemerald the build reads. Map data feeds the TM-location table.
POKEEMERALD_PATHS = [
    "src/data/trainer_parties.h",
    "src/data/trainers.h",
    "src/data/pokemon",
    "src/data/battle_moves.h",
    "src/data/wild_encounters.json",
    "src/data/text/species_names.h",
    "src/data/text/trainer_class_names.h",
    "src/data/text/move_names.h",
    "src/data/text/abilities.h",
    "src/data/region_map",
    "src/battle_main.c",
    "src/pokemon.c",
    "include/constants",
    "data/maps",
    "data/scripts",
    "data/event_scripts.s",
]

# pokeruby keeps the same data under other names (base_stats.h, battle_moves.c, *_en.h, asm .inc
# tables) and adds constants/version.inc, the Ruby/Sapphire alias table (docs/decisions.md D13).
POKERUBY_PATHS = [
    "src/data/trainer_parties.h",
    "src/data/trainers_en.h",
    "src/data/pokemon",
    "src/data/battle_moves.c",
    "src/data/wild_encounters.json",
    "src/data/text/species_names_en.h",
    "src/data/text/trainer_class_names_en.h",
    "src/data/text/move_names_en.h",
    "src/data/region_map",
    "src/party_menu.c",
    "src/pokemon_3.c",
    "src/battle_controllers.c",
    "src/trade.c",
    "src/tv.c",
    "src/wild_encounter.c",
    "src/braille_puzzles.c",
    "src/time_events.c",
    "include/constants",
    "constants/version.inc",
    "data/maps",
    "data/scripts",
    "data/text/ability_names.inc",
    "data/type_effectiveness.inc",
    "data/item_ball_scripts.inc",
    "data/event_scripts.s",
]
# pokefirered builds FireRed or LeafGreen from one tree and keeps pokeemerald's layout and file names;
# the TM list is in party_menu.c, and trades, tutors and the National Dex gate are in their own files.
POKEFIRERED_PATHS = [
    "src/data/trainer_parties.h",
    "src/data/trainers.h",
    "src/data/pokemon",
    "src/data/battle_moves.h",
    "src/data/wild_encounters.json",
    "src/data/text/species_names.h",
    "src/data/text/trainer_class_names.h",
    "src/data/text/move_names.h",
    "src/data/text/abilities.h",
    "src/data/region_map",
    "src/data/ingame_trades.h",
    "src/data/party_menu.h",
    "src/battle_main.c",
    "src/pokemon.c",
    "src/party_menu.c",
    "src/evolution_scene.c",
    "src/field_specials.c",
    "src/trade.c",
    "src/wild_encounter.c",
    "src/battle_script_commands.c",
    "src/field_player_avatar.c",
    "src/daycare.c",
    "include/constants",
    "data/maps",
    "data/scripts",
    "data/text",
    "data/event_scripts.s",
    "data/specials.inc",
]
DECOMPS = {
    "pokeemerald": (POKEEMERALD_REPO, POKEEMERALD_PATHS),
    "pokeruby": (POKERUBY_REPO, POKERUBY_PATHS),
    "pokefirered": (POKEFIRERED_REPO, POKEFIRERED_PATHS),
}


def latest_sha(repo: str) -> str:
    r = httpx.get(
        f"https://api.github.com/repos/{repo}/commits/master",
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["sha"]


def fetch_pokeapi(sha: str) -> None:
    out = CACHE / "pokeapi"
    out.mkdir(parents=True, exist_ok=True)
    marker = out / ".sha"
    if marker.exists() and marker.read_text().strip() == sha and all(
        (out / f"{n}.csv").exists() for n in POKEAPI_CSVS
    ):
        print(f"pokeapi: cached at {sha[:10]}")
        return
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=120, follow_redirects=True) as client:
        for name in POKEAPI_CSVS:
            url = f"https://raw.githubusercontent.com/{POKEAPI_REPO}/{sha}/data/v2/csv/{name}.csv"
            r = client.get(url)
            r.raise_for_status()
            (out / f"{name}.csv").write_bytes(r.content)
            print(f"pokeapi: {name}.csv ({len(r.content) // 1024} KB)")
    marker.write_text(sha)


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def fetch_decomp(name: str, sha: str) -> None:
    repo, paths = DECOMPS[name]
    out = CACHE / name
    if (out / ".git").exists():
        head = git("rev-parse", "HEAD", cwd=out).strip()
        wanted = git("sparse-checkout", "list", cwd=out).split()
        if head == sha and wanted == paths:
            print(f"{name}: cached at {sha[:10]}")
            return
    else:
        out.mkdir(parents=True, exist_ok=True)
        git("init", "-q", cwd=out)
        git("remote", "add", "origin", f"https://github.com/{repo}.git", cwd=out)
        git("config", "core.autocrlf", "false", cwd=out)
    git("sparse-checkout", "set", "--no-cone", *paths, cwd=out)
    git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", sha, cwd=out)
    git("checkout", "-q", "--force", "FETCH_HEAD", cwd=out)
    print(f"{name}: checked out {sha[:10]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="re-resolve upstream commits")
    args = ap.parse_args()

    lock = json.loads(LOCK.read_text()) if LOCK.exists() else {}
    if args.update or "pokeapi" not in lock:
        lock["pokeapi"] = {"repo": POKEAPI_REPO, "sha": latest_sha(POKEAPI_REPO), "path": "data/v2/csv"}
        lock["resolved_on"] = date.today().isoformat()
    for name, (repo, _) in DECOMPS.items():
        if args.update or name not in lock:
            lock[name] = {"repo": repo, "sha": latest_sha(repo)}
            lock["resolved_on"] = date.today().isoformat()

    fetch_pokeapi(lock["pokeapi"]["sha"])
    for name in DECOMPS:
        fetch_decomp(name, lock[name]["sha"])

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps(lock, indent=2) + "\n")
    print(f"wrote {LOCK.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
