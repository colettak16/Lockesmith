"""Parsers for the pret/pokeemerald decompilation.

These read the ROM's own tables. The build uses them for trainer parties, the
default-moves rule and TM locations, and the tests use them to cross-check the
PokeAPI-derived tables after Gen 3 corrections.

Identifiers are normalised to PokeAPI style (`SPECIES_MR_MIME` -> `mr-mime`,
`TYPE_DARK` -> `dark`) and species are keyed by National Dex number.
"""

import glob
import json
import re
from functools import cache
from pathlib import Path

TYPE_MUL = {"TYPE_MUL_NO_EFFECT": 0.0, "TYPE_MUL_NOT_EFFECTIVE": 0.5, "TYPE_MUL_SUPER_EFFECTIVE": 2.0}

# Decomp constant suffixes whose PokeAPI identifier isn't a plain lower/hyphen conversion.
ABILITY_RENAMES = {}
ITEM_RENAMES = {
    "KINGS_ROCK": "kings-rock",
    "BLACK_GLASSES": "black-glasses",
    "NEVER_MELT_ICE": "never-melt-ice",
    "TWISTED_SPOON": "twisted-spoon",
    "SILK_SCARF": "silk-scarf",
    "UP_GRADE": "up-grade",
    "DEEP_SEA_TOOTH": "deep-sea-tooth",
    "DEEP_SEA_SCALE": "deep-sea-scale",
    "PARALYZE_HEAL": "paralyze-heal",
    "ENERGY_POWDER": "energy-powder",
    "SILVER_POWDER": "silver-powder",
    "THUNDER_STONE": "thunder-stone",
    "X_DEFEND": "x-defense",
    "X_SPECIAL": "x-sp-atk",
}


def to_identifier(const: str, prefix: str) -> str:
    return const.removeprefix(prefix).lower().replace("_", "-")


def type_identifier(const: str) -> str | None:
    if const == "TYPE_MYSTERY":
        return "???"
    if const == "TYPE_NONE":
        return None
    return to_identifier(const, "TYPE_")


def ability_identifier(const: str) -> str | None:
    if const == "ABILITY_NONE":
        return None
    name = const.removeprefix("ABILITY_")
    return ABILITY_RENAMES.get(name, name.lower().replace("_", "-"))


def item_identifier(const: str) -> str | None:
    if const in ("ITEM_NONE", "0"):
        return None
    name = const.removeprefix("ITEM_")
    return ITEM_RENAMES.get(name, name.lower().replace("_", "-"))


def read(decomp: Path, rel: str) -> str:
    return (Path(decomp) / rel).read_text(encoding="utf-8")


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


@cache
def defines(decomp: Path, rel: str) -> dict[str, int]:
    """Integer `#define NAME value` lines (decimal or hex)."""
    out = {}
    for name, value in re.findall(r"^#define\s+(\w+)\s+(0x[0-9A-Fa-f]+|\d+)\b", read(decomp, rel), flags=re.M):
        out[name] = int(value, 0)
    return out


@cache
def enum_members(decomp: Path, rel: str, first: str) -> list[str]:
    """Members of the enum that contains `first`, in declaration order."""
    text = strip_comments(read(decomp, rel))
    for body in re.findall(r"enum\s*\{(.*?)\};", text, flags=re.S):
        names = [m.split("=")[0].strip() for m in body.split(",")]
        names = [n for n in names if n]
        if first in names:
            return names
    raise ValueError(f"enum with {first} not found in {rel}")


@cache
def national_dex(decomp: Path) -> dict[str, int]:
    """`SPECIES_X` -> National Dex number, for #1-386."""
    members = enum_members(decomp, "include/constants/pokedex.h", "NATIONAL_DEX_BULBASAUR")
    out = {}
    for i, name in enumerate(members):
        if name.startswith("NATIONAL_DEX_") and name != "NATIONAL_DEX_NONE" and 1 <= i <= 386:
            out["SPECIES_" + name.removeprefix("NATIONAL_DEX_")] = i
    return out


@cache
def move_ids(decomp: Path) -> dict[str, int]:
    return {k: v for k, v in defines(decomp, "include/constants/moves.h").items() if k.startswith("MOVE_")}


def bracket_blocks(text: str, key_prefix: str) -> dict[str, str]:
    """Bodies of `[KEY_...] = { ... }` designated initialisers, matched by brace depth."""
    out = {}
    for m in re.finditer(r"\[(" + key_prefix + r"\w+)\]\s*=\s*\{", text):
        depth, i = 1, m.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        out[m.group(1)] = text[m.end() : i - 1]
    return out


def fields(body: str) -> dict[str, str]:
    """`.name = value` pairs from a struct body; brace values keep their braces."""
    return {k: v.strip() for k, v in re.findall(r"\.(\w+)\s*=\s*(\{[^}]*\}|[^,\n]+)", body)}


def brace_list(value: str) -> list[str]:
    return [x.strip() for x in value.strip("{} ").split(",") if x.strip()]


@cache
def species_info(decomp: Path) -> dict[int, tuple]:
    """National Dex -> (type1, type2, hp, atk, def, spa, spd, spe, ability1, ability2)."""
    dex = national_dex(decomp)
    blocks = bracket_blocks(strip_comments(read(decomp, "src/data/pokemon/species_info.h")), "SPECIES_")
    out = {}
    for const, body in blocks.items():
        if const not in dex:
            continue
        f = fields(body)
        t1, t2 = (type_identifier(t) for t in brace_list(f["types"]))
        a1, a2 = (ability_identifier(a) for a in brace_list(f["abilities"]))
        stats = [int(f[k]) for k in ("baseHP", "baseAttack", "baseDefense", "baseSpAttack", "baseSpDefense", "baseSpeed")]
        # A repeated type or ability fills both slots when a species has only one.
        out[dex[const]] = (t1, None if t2 == t1 else t2, *stats, a1, None if a2 == a1 else a2)
    return out


@cache
def battle_moves(decomp: Path) -> dict[int, tuple]:
    """Move id -> (type, power, accuracy, pp). Variable/fixed power (0 or 1) and never-miss accuracy (0) become None."""
    ids = move_ids(decomp)
    blocks = bracket_blocks(strip_comments(read(decomp, "src/data/battle_moves.h")), "MOVE_")
    out = {}
    for const, body in blocks.items():
        if const == "MOVE_NONE":
            continue
        f = fields(body)
        power, accuracy = int(f["power"]), int(f["accuracy"])
        out[ids[const]] = (type_identifier(f["type"]), power if power > 1 else None, accuracy or None, int(f["pp"]))
    return out


@cache
def type_chart(decomp: Path) -> dict[tuple[str, str], float]:
    """(attacking, defending) -> multiplier for every non-neutral pair in gTypeEffectiveness."""
    text = strip_comments(read(decomp, "src/battle_main.c"))
    body = re.search(r"gTypeEffectiveness\[\d*\]\s*=\s*\{(.*?)\};", text, flags=re.S).group(1)
    tokens = [t.strip() for t in body.split(",") if t.strip()]
    out = {}
    for atk, dfn, mul in zip(tokens[0::3], tokens[1::3], tokens[2::3]):
        if atk in ("TYPE_FORESIGHT", "TYPE_ENDTABLE"):
            continue
        out[(type_identifier(atk), type_identifier(dfn))] = TYPE_MUL[mul]
    return out


@cache
def level_up_learnsets(decomp: Path) -> dict[int, list[tuple[int, int]]]:
    """National Dex -> [(level, move_id), ...] in ROM order (order matters for default moves)."""
    dex, ids = national_dex(decomp), move_ids(decomp)
    text = strip_comments(read(decomp, "src/data/pokemon/level_up_learnsets.h"))
    sets = {}
    for symbol, body in re.findall(r"static const u16 (s\w+LevelUpLearnset)\[\]\s*=\s*\{(.*?)\};", text, flags=re.S):
        sets[symbol] = [(int(lvl), ids[mv]) for lvl, mv in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+),\s*(MOVE_\w+)\)", body)]
    pointers = strip_comments(read(decomp, "src/data/pokemon/level_up_learnset_pointers.h"))
    out = {}
    for const, symbol in re.findall(r"\[(SPECIES_\w+)\]\s*=\s*(s\w+LevelUpLearnset)", pointers):
        if const in dex:
            out[dex[const]] = sets[symbol]
    return out


@cache
def evolutions(decomp: Path) -> list[tuple[int, str, str, int]]:
    """(from National Dex, method, param, to National Dex) from gEvolutionTable."""
    dex = national_dex(decomp)
    text = strip_comments(read(decomp, "src/data/pokemon/evolution.h"))
    out = []
    for const, body in bracket_blocks(text, "SPECIES_").items():
        for method, param, target in re.findall(r"\{\s*(EVO_\w+),\s*(\w+),\s*(SPECIES_\w+)\s*\}", body):
            if const in dex and target in dex:
                out.append((dex[const], method, param, dex[target]))
    return out


def evolution_pairs(decomp: Path) -> set[tuple[int, int]]:
    return {(a, b) for a, _, _, b in evolutions(decomp)}


@cache
def map_sections(decomp: Path) -> list[dict]:
    """Region map sections in index order. A section's index is its MAPSEC id."""
    secs = json.loads(read(decomp, "src/data/region_map/region_map_sections.json"))["map_sections"]
    return [{"index": i, "id": s["id"], "name": s["name"]} for i, s in enumerate(secs)]


@cache
def maps(decomp: Path) -> dict[str, dict]:
    """Map id (`MAP_ROUTE119`) -> parsed map.json plus its folder name."""
    out = {}
    for path in glob.glob(str(Path(decomp) / "data" / "maps" / "*" / "map.json")):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        data["folder"] = Path(path).parent.name
        out[data["id"]] = data
    return out


@cache
def wild_headers(decomp: Path) -> list[dict]:
    """gWildMonHeaders entries in ROM order (Battle Pyramid/Pike tables excluded)."""
    groups = json.loads(read(decomp, "src/data/wild_encounters.json"))["wild_encounter_groups"]
    return next(g for g in groups if g["label"] == "gWildMonHeaders")["encounters"]


FISHING_RODS = {"old-rod": range(0, 2), "good-rod": range(2, 5), "super-rod": range(5, 10)}


def fishing_rod(slot: int) -> str:
    """Gen 3 splits the 10-slot fishing table by rod (wild_encounters.json `groups`)."""
    return next(rod for rod, slots in FISHING_RODS.items() if slot in slots)


def wild_species_by_location(decomp: Path, mapsec_to_location: dict[str, str]) -> dict[tuple[str, str], set[int]]:
    """(PokeAPI location, method) -> species set, from the ROM's wild tables.

    Altering Cave's alternate tables need a Mystery Event, so only the default one counts.
    """
    dex, map_data = national_dex(decomp), maps(decomp)
    out: dict[tuple[str, str], set[int]] = {}
    for header in wild_headers(decomp):
        if header["map"] == "MAP_ALTERING_CAVE" and header["base_label"] != "gAlteringCave1":
            continue
        mapsec = map_data[header["map"]]["region_map_section"]
        location = mapsec_to_location[mapsec]
        underwater = mapsec.startswith("MAPSEC_UNDERWATER")
        groups = {"land_mons": "walk", "water_mons": "seaweed" if underwater else "surf", "rock_smash_mons": "rock-smash"}
        for key, method in groups.items():
            for mon in header.get(key, {}).get("mons", []):
                out.setdefault((location, method), set()).add(dex[mon["species"]])
        for slot, mon in enumerate(header.get("fishing_mons", {}).get("mons", [])):
            out.setdefault((location, fishing_rod(slot)), set()).add(dex[mon["species"]])
    return out


@cache
def tm_hm_moves(decomp: Path) -> list[tuple[str, str]]:
    """[(label, MOVE_X)] for TM01-TM50 then HM01-HM08, from tms_hms.h."""
    text = read(decomp, "include/constants/tms_hms.h")
    tms = re.findall(r"F\((\w+)\)", re.search(r"#define FOREACH_TM\(F\)(.*?)\n\n", text, flags=re.S).group(1))
    hms = re.findall(r"F\((\w+)\)", re.search(r"#define FOREACH_HM\(F\)(.*?)\n\n", text, flags=re.S).group(1))
    return [(f"TM{i:02d}", f"MOVE_{m}") for i, m in enumerate(tms, 1)] + [
        (f"HM{i:02d}", f"MOVE_{m}") for i, m in enumerate(hms, 1)
    ]


@cache
def trainer_class_names(decomp: Path) -> dict[str, str]:
    text = read(decomp, "src/data/text/trainer_class_names.h")
    return {k: v.title() for k, v in re.findall(r"\[(TRAINER_CLASS_\w+)\]\s*=\s*_\(\"([^\"]*)\"\)", text)}


@cache
def rom_names(decomp: Path, rel: str) -> dict[str, str]:
    """`[CONST] = _("NAME")` tables (species, move, ability names as the ROM prints them)."""
    return dict(re.findall(r"\[(\w+)\]\s*=\s*_\(\"([^\"]*)\"\)", read(decomp, rel)))
