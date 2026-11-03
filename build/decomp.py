"""Parsers for the pret decompilations: pokeemerald (Emerald), pokeruby (Ruby and Sapphire) and
pokefirered (FireRed and LeafGreen).

These read the ROM's own tables. The build uses them for trainer parties, the
default-moves rule and TM locations, and the tests use them to cross-check the
PokeAPI-derived tables after Gen 3 corrections.

`family` tells the decomps apart by layout. pokeruby holds the data in other files and
syntax (base_stats.h, battle_moves.c, *_en.h text, asm .inc tables, positional arrays);
pokefirered keeps pokeemerald's layout, with the TM list in data/party_menu.h. pokeruby and
pokefirered each build two versions from one tree, so functions whose answer depends on the
version take `version` ("RUBY"/"SAPPHIRE"/"FIRERED"/"LEAFGREEN"; None for Emerald): wild
tables come in `_Ruby`/`_Sapphire` (`_FireRed`/`_LeafGreen`) pairs, scripts branch on
`.ifdef SAPPHIRE` (`.ifdef LEAFGREEN`), pokeruby's `constants/version.inc` aliases trainers
and species, and its Lilycove hideout exists as two map sets of which each version uses one.

Identifiers are normalised to PokeAPI style (`SPECIES_MR_MIME` -> `mr-mime`,
`TYPE_DARK` -> `dark`) and species are keyed by National Dex number.
"""

import glob
import json
import re
from functools import cache
from pathlib import Path

TYPE_MUL = {"TYPE_MUL_NO_EFFECT": 0.0, "TYPE_MUL_NOT_EFFECTIVE": 0.5, "TYPE_MUL_SUPER_EFFECTIVE": 2.0}
RS_TYPE_MUL = {"0": 0.0, "5": 0.5, "20": 2.0}  # data/type_effectiveness.inc stores x10 fixed point

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
# pokeruby spells a few item constants differently from pokeemerald.
RS_ITEM_RENAMES = {
    "KINGS_ROCK": "kings-rock",
    "BLACK_GLASSES": "black-glasses",
    "NEVERMELTICE": "never-melt-ice",
    "NEVER_MELT_ICE": "never-melt-ice",
    "TWISTEDSPOON": "twisted-spoon",
    "SILVERPOWDER": "silver-powder",
    "ENERGYPOWDER": "energy-powder",
    "THUNDERSTONE": "thunder-stone",
    "DEEPSEATOOTH": "deep-sea-tooth",
    "DEEPSEASCALE": "deep-sea-scale",
    "PARLYZ_HEAL": "paralyze-heal",
    "X_DEFEND": "x-defense",
    "X_SPECIAL": "x-sp-atk",
    "UP_GRADE": "up-grade",
}
# The other version's hideout maps: pokeruby has both sets, and Lilycove opens one per version.
OTHER_HIDEOUT = {"RUBY": "AquaHideout_", "SAPPHIRE": "MagmaHideout_"}
# Build flags of the two-version decomps, and the suffix of each version's wild tables.
VERSION_WILD_SUFFIX = {"RUBY": "_Ruby", "SAPPHIRE": "_Sapphire", "FIRERED": "_FireRed", "LEAFGREEN": "_LeafGreen"}


def family(decomp: Path) -> str:
    """Which decomp a tree is, by layout: "rs" (pokeruby), "frlg" (pokefirered) or "emerald"."""
    d = Path(decomp)
    if (d / "src" / "data" / "pokemon" / "base_stats.h").exists():
        return "rs"
    if (d / "src" / "data" / "region_map" / "region_map_layout_kanto.h").exists():
        return "frlg"
    return "emerald"


def is_rs(decomp: Path) -> bool:
    """True for a pokeruby tree (Ruby/Sapphire)."""
    return family(decomp) == "rs"


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


def item_identifier(const: str, rs: bool = False) -> str | None:
    if const in ("ITEM_NONE", "0"):
        return None
    name = const.removeprefix("ITEM_")
    renames = RS_ITEM_RENAMES if rs else ITEM_RENAMES
    return renames.get(name, name.lower().replace("_", "-"))


def read(decomp: Path, rel: str) -> str:
    """A decomp file as text. A few pokeruby files carry Latin-1 bytes in comments."""
    data = (Path(decomp) / rel).read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


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


# --- version-specific scripts (pokeruby) ------------------------------------------------


def script_lines(text: str, version: str | None) -> list[str]:
    """The lines of an asm script that the given version compiles.

    `.ifdef`/`.ifndef` blocks for the other version (RUBY|SAPPHIRE, FIRERED|LEAFGREEN) are
    dropped, as are `.ifdef DEBUG` blocks. Other conditionals keep their first branch.
    Emerald (None) keeps every line.
    """
    if version is None:
        return text.splitlines()
    out, stack = [], []
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"\.(ifdef|ifndef)\s+(\w+)", s)
        if m:
            flag, positive = m.group(2), m.group(1) == "ifdef"
            if flag in VERSION_WILD_SUFFIX:
                stack.append((flag == version) == positive)
            elif flag == "DEBUG":
                stack.append(not positive)
            else:
                stack.append(True)
            continue
        if re.match(r"\.if\b", s):
            stack.append(True)
            continue
        if s.startswith(".else"):
            if stack:
                stack[-1] = not stack[-1]
            continue
        if s.startswith((".endif", ".endc")):
            if stack:
                stack.pop()
            continue
        if all(stack):
            out.append(line)
    return out


@cache
def version_aliases(decomp: Path, version: str | None) -> dict[str, str]:
    """`constants/version.inc` aliases for a version: TRAINER_MT_CHIMNEY_GRUNT_3 -> TRAINER_MAXIE_3
    in Ruby, SPECIES_GROUDON_OR_KYOGRE -> SPECIES_KYOGRE in Sapphire. Empty for Emerald."""
    if version is None or not (Path(decomp) / "constants" / "version.inc").exists():
        return {}
    out = {}
    for line in script_lines(read(decomp, "constants/version.inc"), version):
        m = re.match(r"\s*\.set\s+(\w+),\s*(\w+)", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


# --- species, moves, types --------------------------------------------------------------


@cache
def national_dex(decomp: Path) -> dict[str, int]:
    """`SPECIES_X` -> National Dex number, for #1-386."""
    if is_rs(decomp):
        dex = defines(decomp, "include/constants/species.h")
        return {
            "SPECIES_" + name.removeprefix("NATIONAL_DEX_"): n
            for name, n in dex.items()
            if name.startswith("NATIONAL_DEX_") and name != "NATIONAL_DEX_NONE" and 1 <= n <= 386
        }
    members = enum_members(decomp, "include/constants/pokedex.h", "NATIONAL_DEX_BULBASAUR")
    out = {}
    for i, name in enumerate(members):
        if name.startswith("NATIONAL_DEX_") and name != "NATIONAL_DEX_NONE" and 1 <= i <= 386:
            out["SPECIES_" + name.removeprefix("NATIONAL_DEX_")] = i
    return out


@cache
def species_by_index(decomp: Path) -> dict[int, str]:
    """pokeruby's internal species index -> `SPECIES_X` (positional tables are in this order)."""
    out = {}
    for name, n in defines(decomp, "include/constants/species.h").items():
        if name.startswith("SPECIES_"):
            out.setdefault(n, name)
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
    rel = "src/data/pokemon/base_stats.h" if is_rs(decomp) else "src/data/pokemon/species_info.h"
    blocks = bracket_blocks(strip_comments(read(decomp, rel)), "SPECIES_")
    out = {}
    for const, body in blocks.items():
        if const not in dex:
            continue
        f = fields(body)
        if is_rs(decomp):
            types, abilities = [f["type1"], f["type2"]], [f["ability1"], f["ability2"]]
        else:
            types, abilities = brace_list(f["types"]), brace_list(f["abilities"])
        t1, t2 = (type_identifier(t) for t in types)
        a1, a2 = (ability_identifier(a) for a in abilities)
        stats = [int(f[k]) for k in ("baseHP", "baseAttack", "baseDefense", "baseSpAttack", "baseSpDefense", "baseSpeed")]
        # A repeated type or ability fills both slots when a species has only one.
        out[dex[const]] = (t1, None if t2 == t1 else t2, *stats, a1, None if a2 == a1 else a2)
    return out


@cache
def battle_moves(decomp: Path) -> dict[int, tuple]:
    """Move id -> (type, power, accuracy, pp). Variable/fixed power (0 or 1) and never-miss accuracy (0) become None."""
    ids = move_ids(decomp)
    rel = "src/data/battle_moves.c" if is_rs(decomp) else "src/data/battle_moves.h"
    blocks = bracket_blocks(strip_comments(read(decomp, rel)), "MOVE_")
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
    """(attacking, defending) -> multiplier for every non-neutral pair in gTypeEffectiveness.

    The Foresight/end markers are skipped; the pairs after the Foresight marker (Normal
    and Fighting into Ghost) are the usual immunities and stay in."""
    if is_rs(decomp):
        rows = re.findall(r"\.byte\s+(TYPE_\w+),\s*(TYPE_\w+),\s*(\d+)", read(decomp, "data/type_effectiveness.inc"))
        return {
            (type_identifier(a), type_identifier(d)): RS_TYPE_MUL[str(int(m))]
            for a, d, m in rows
            if a not in ("TYPE_FORESIGHT", "TYPE_ENDTABLE")
        }
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
    for symbol, body in re.findall(r"const u16 ([sg]\w+LevelUpLearnset)\[\]\s*=\s*\{(.*?)\};", text, flags=re.S):
        sets[symbol] = [(int(lvl), ids[mv]) for lvl, mv in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+),\s*(MOVE_\w+)\)", body)]
    pointers = strip_comments(read(decomp, "src/data/pokemon/level_up_learnset_pointers.h"))
    out = {}
    if is_rs(decomp):
        # A positional array in internal species order.
        index = species_by_index(decomp)
        for i, symbol in enumerate(re.findall(r"\b(g\w+LevelUpLearnset)\b", pointers)):
            const = index.get(i)
            if const in dex:
                out[dex[const]] = sets[symbol]
        return out
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


def friendship_threshold(decomp: Path) -> int:
    """The friendship evolutions' threshold: FRIENDSHIP_EVO_THRESHOLD in pokeemerald's pokemon.c;
    pokeruby (pokemon_3.c) and pokefirered (pokemon.c) write `friendship >= 220` into each
    EVO_FRIENDSHIP case. pokefirered's pokemon.c has other friendship checks, so only the
    evolution cases count."""
    if is_rs(decomp):
        values = set(re.findall(r"friendship >= (\d+)", read(decomp, "src/pokemon_3.c")))
        assert len(values) == 1, f"several friendship thresholds in pokemon_3.c: {values}"
        return int(values.pop())
    if family(decomp) == "frlg":
        values = set(re.findall(r"case EVO_FRIENDSHIP:\s*if \(friendship >= (\d+)\)", read(decomp, "src/pokemon.c")))
        assert len(values) == 1, f"expected one EVO_FRIENDSHIP threshold in pokemon.c: {values}"
        return int(values.pop())
    return int(re.search(r"#define FRIENDSHIP_EVO_THRESHOLD (\d+)", read(decomp, "src/pokemon.c")).group(1))


# --- maps and wild encounters -----------------------------------------------------------


@cache
def map_sections(decomp: Path) -> list[dict]:
    """Region map sections in index order. A section's index is its MAPSEC id.

    pokeruby's town names embed a {NAME_END} control code ("PETALBURG{NAME_END} CITY");
    it's dropped here so names read as the game shows them. pokefirered keeps Hoenn's
    sections (indices 0-87) without names, ahead of Kanto's and the Sevii Islands'."""
    secs = json.loads(read(decomp, "src/data/region_map/region_map_sections.json"))["map_sections"]
    return [{"index": i, "id": s["id"], "name": s.get("name", "").replace("{NAME_END}", "")} for i, s in enumerate(secs)]


@cache
def maps(decomp: Path, version: str | None = None) -> dict[str, dict]:
    """Map id (`MAP_ROUTE119`) -> parsed map.json plus its folder name.

    For a Ruby/Sapphire version, the other version's hideout maps are left out."""
    skip = OTHER_HIDEOUT.get(version)
    out = {}
    for path in glob.glob(str(Path(decomp) / "data" / "maps" / "*" / "map.json")):
        folder = Path(path).parent.name
        if skip and folder.startswith(skip):
            continue
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        data["folder"] = folder
        out[data["id"]] = data
    return out


@cache
def wild_headers(decomp: Path, version: str | None = None) -> list[dict]:
    """gWildMonHeaders entries in ROM order (Battle Pyramid/Pike tables excluded).

    pokeruby lists every map twice, `<Map>_Ruby` and `<Map>_Sapphire`, and pokefirered as
    `<Map>_FireRed` and `<Map>_LeafGreen`; a version keeps its own."""
    groups = json.loads(read(decomp, "src/data/wild_encounters.json"))["wild_encounter_groups"]
    headers = next(g for g in groups if g["label"] == "gWildMonHeaders")["encounters"]
    if family(decomp) != "emerald":
        assert version in VERSION_WILD_SUFFIX, f"a {family(decomp)} wild table needs a version"
        headers = [h for h in headers if h["base_label"].endswith(VERSION_WILD_SUFFIX[version])]
    return headers


FISHING_RODS = {"old-rod": range(0, 2), "good-rod": range(2, 5), "super-rod": range(5, 10)}


def fishing_rod(slot: int) -> str:
    """Gen 3 splits the 10-slot fishing table by rod (wild_encounters.json `groups`)."""
    return next(rod for rod, slots in FISHING_RODS.items() if slot in slots)


def wild_species_by_location(
    decomp: Path, mapsec_to_location: dict[str, str], version: str | None = None
) -> dict[tuple[str, str], set[int]]:
    """(PokeAPI location, method) -> species set, from the ROM's wild tables.

    Altering Cave's alternate tables need a Mystery Event, so only the default one counts.
    """
    dex, map_data = national_dex(decomp), maps(decomp, version)
    out: dict[tuple[str, str], set[int]] = {}
    for header in wild_headers(decomp, version):
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


# --- TMs, trainers, names ---------------------------------------------------------------


@cache
def tm_hm_moves(decomp: Path) -> list[tuple[str, str]]:
    """[(label, MOVE_X)] for TM01-TM50 then HM01-HM08 (tms_hms.h; pokeruby's TMHMMoves[] in
    party_menu.c; pokefirered's sTMHMMoves[] in data/party_menu.h)."""
    if family(decomp) != "emerald":
        rel = "src/party_menu.c" if is_rs(decomp) else "src/data/party_menu.h"
        body = re.search(r"TMHMMoves\[\]\s*=\s*\{(.*?)\};", strip_comments(read(decomp, rel)), flags=re.S)
        moves = re.findall(r"\b(MOVE_\w+)\b", body.group(1))
        assert len(moves) == 58, f"expected 58 TM/HM moves, found {len(moves)}"
        return [(f"TM{i:02d}", m) for i, m in enumerate(moves[:50], 1)] + [
            (f"HM{i:02d}", m) for i, m in enumerate(moves[50:], 1)
        ]
    text = read(decomp, "include/constants/tms_hms.h")
    tms = re.findall(r"F\((\w+)\)", re.search(r"#define FOREACH_TM\(F\)(.*?)\n\n", text, flags=re.S).group(1))
    hms = re.findall(r"F\((\w+)\)", re.search(r"#define FOREACH_HM\(F\)(.*?)\n\n", text, flags=re.S).group(1))
    return [(f"TM{i:02d}", f"MOVE_{m}") for i, m in enumerate(tms, 1)] + [
        (f"HM{i:02d}", f"MOVE_{m}") for i, m in enumerate(hms, 1)
    ]


@cache
def trainer_class_names(decomp: Path) -> dict[str, str]:
    if is_rs(decomp):
        # A positional array in the order of the TRAINER_CLASS_ enum.
        names = re.findall(r'_\("([^"]*)"\)', read(decomp, "src/data/text/trainer_class_names_en.h"))
        members = enum_members(decomp, "include/constants/trainers.h", "TRAINER_CLASS_POKEMON_TRAINER_1")
        return {const: name.title() for const, name in zip(members, names)}
    text = read(decomp, "src/data/text/trainer_class_names.h")
    return {k: v.title() for k, v in re.findall(r"\[(TRAINER_CLASS_\w+)\]\s*=\s*_\(\"([^\"]*)\"\)", text)}


@cache
def rom_names(decomp: Path, rel: str) -> dict[str, str]:
    """`[CONST] = _("NAME")` tables (species, move, ability names as the ROM prints them)."""
    return dict(re.findall(r"\[(\w+)\]\s*=\s*_\(\"([^\"]*)\"\)", read(decomp, rel)))


@cache
def rom_name_tables(decomp: Path) -> dict[str, dict[str, str]]:
    """{"species": {SPECIES_X: name}, "moves": {MOVE_X: name}, "abilities": {ABILITY_X: name}}."""
    if is_rs(decomp):
        abilities = {}
        ids = {n: k for k, n in defines(decomp, "include/constants/abilities.h").items() if k.startswith("ABILITY_")}
        for i, name in enumerate(re.findall(r'\.string\s+"([^"]*)"', read(decomp, "data/text/ability_names.inc"))):
            if i in ids:
                abilities[ids[i]] = name.rstrip("$")
        return {
            "species": rom_names(decomp, "src/data/text/species_names_en.h"),
            "moves": rom_names(decomp, "src/data/text/move_names_en.h"),
            "abilities": abilities,
        }
    return {
        "species": rom_names(decomp, "src/data/text/species_names.h"),
        "moves": rom_names(decomp, "src/data/text/move_names.h"),
        "abilities": rom_names(decomp, "src/data/text/abilities.h"),
    }
