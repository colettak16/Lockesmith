"""V-10 / V-11: the engine-level facts behind section 12, Ruby/Sapphire vs Emerald, compared mechanically.

    uv run python -m audit.engine

1. Metatile behavior numbering (include/constants/metatile_behaviors.h): which numbers name
   different behaviors.
2. Tile bits per behavior (sTileBitAttributes in src/metatile_behavior.c): has-encounters,
   surfable, unused.
3. Behavior predicates (MetatileBehavior_Is* in src/metatile_behavior.c): each function's body
   with MB_ names replaced by their numbers, compared across games (three renamed functions mapped).
4. Map headers on shared maps: map type, weather, Flash, region map section, battle scene.
5. Bike, Escape Rope/Dig and running permissions: Ruby/Sapphire's hardcoded rules
   (Overworld_IsBikingAllowed and the map-type tests) against Emerald's allow_* header fields.
6. Heal locations (Fly and whiteout targets).
7. Abilities that act outside battle: every ABILITY_ constant named in the wild-encounter,
   fishing, daycare and egg code, and in SetWildMonHeldItem.
8. Wild-encounter functions only one game has (src/wild_encounter.c).

The movement rules in audit.reach (ledges, elevation, Surf, doors) were read from
field_player_avatar.c, field_control_avatar.c and event_object_movement.c by hand: compare
those files directly to check them.
"""

import collections
import json
import re
from pathlib import Path

from audit.maps import load_maps
from audit.sources import tree

RENAMED_PREDICATES = {"MetatileBehavior_IsNotSurfacable": "MetatileBehavior_IsUnableToEmerge",
                      "MetatileBehavior_IsMountainTop": "MetatileBehavior_IsMountain",
                      "MetatileBehavior_IsBridge": "MetatileBehavior_IsBridgeOverWater"}
RS_BIKE_ALWAYS = ("MAP_ROUTE110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE", "MAP_ROUTE110_SEASIDE_CYCLING_ROAD_NORTH_ENTRANCE")
RS_BIKE_NEVER = ("MAP_SEAFLOOR_CAVERN_ROOM9", "MAP_CAVE_OF_ORIGIN_B4F")


def strip_c(src: str) -> str:
    return re.sub(r"/\*.*?\*/", "", re.sub(r"//[^\n]*", "", src), flags=re.S)


def rs_behaviors(root: Path) -> dict[str, int]:
    text = (root / "include/constants/metatile_behaviors.h").read_text()
    return {k: int(v, 16) for k, v in re.findall(r"#define (MB_\w+)\s+(0x[0-9A-Fa-f]+)", text)}


def e_behaviors(root: Path) -> dict[str, int]:
    text = (root / "include/constants/metatile_behaviors.h").read_text()
    body = text[text.index("enum {") + 6: text.index("NUM_METATILE_BEHAVIORS")]
    return {tok: i for i, tok in enumerate(re.findall(r"^\s*(MB_\w+)\s*,", body, re.M))}


def numbering(R, E) -> list[str]:
    r, e = {v: k for k, v in rs_behaviors(R).items()}, {v: k for k, v in e_behaviors(E).items()}
    out = [f"{hex(v)} RS {r.get(v)} | E {e.get(v)}" for v in range(0xF0) if r.get(v) != e.get(v)]
    return out + [f"behaviors named: RS {len(r)}, E {len(e)}"]


def tile_bits(R, E) -> list[str]:
    rs, es = rs_behaviors(R), e_behaviors(E)
    src = (R / "src/metatile_behavior.c").read_text()
    tab = src[src.index("sTileBitAttributes[] ="):]
    tab = tab[:tab.index("};")]
    rt = {}
    for i, m in enumerate(re.finditer(r"TILE_ATTRIBUTES\((\w+), (\w+), (\w+)\),?\s*// (MB_\w+)", tab)):
        u, s, w, name = m.groups()
        assert rs[name] == i, (name, i)
        rt[i] = (u == "TRUE") * 4 | (s == "TRUE") * 2 | (w == "TRUE") * 1
    src = (E / "src/metatile_behavior.c").read_text()
    tab = src[src.index("sTileBitAttributes[NUM_METATILE_BEHAVIORS] ="):]
    tab = tab[:tab.index("};")]
    et = {}
    for m in re.finditer(r"\[(MB_\w+)\]\s*=\s*([^,\n]+),", tab):
        name, expr = m.groups()
        et[es[name]] = ("TILE_FLAG_UNUSED" in expr) * 4 | ("TILE_FLAG_SURFABLE" in expr) * 2 | ("TILE_FLAG_HAS_ENCOUNTERS" in expr) * 1
    inv = {v: k for k, v in rs.items()}
    out = [f"{hex(v)} {inv.get(v)} RS={rt.get(v, 0)} E={et.get(v, 0)}" for v in range(0xF0) if rt.get(v, 0) != et.get(v, 0)]
    return out + [f"(bits: 4 unused, 2 surfable, 1 has encounters); behaviors with different bits: {len(out)}"]


def predicates(R, E) -> list[str]:
    def funcs(path: Path, consts: dict[str, int]) -> dict[str, str]:
        src = strip_c(path.read_text())
        out = {}
        for m in re.finditer(r"^(?:bool8|u8|bool32|static bool8|static u8|int|bool16)\s+(\w+)\s*\(([^)]*)\)\s*\n\{", src, re.M):
            start = i = m.end() - 1
            depth = 0
            while True:
                depth += {"{": 1, "}": -1}.get(src[i], 0)
                if depth == 0:
                    break
                i += 1
            body = re.sub(r"\bMB_\w+\b", lambda mm: hex(consts[mm.group(0)]) if mm.group(0) in consts else mm.group(0), src[start:i + 1])
            out[m.group(1)] = re.sub(r"\s+", " ", body)
        return out

    es = e_behaviors(E) | {"MB_INVALID": 0xFF}
    rf, ef = funcs(R / "src/metatile_behavior.c", rs_behaviors(R)), funcs(E / "src/metatile_behavior.c", es)
    out = []
    for n in sorted(rf):
        en = RENAMED_PREDICATES.get(n, n)
        if en not in ef:
            out.append(f"RS only {n}: {rf[n][:200]}")
        elif rf[n] != ef[en]:
            out += [f"DIFF {n} -> {en}", f"  RS: {rf[n]}", f"  E : {ef[en]}"]
    out += [f"E only {n}: {ef[n][:200]}" for n in sorted(ef) if n not in rf and n not in RENAMED_PREDICATES.values()]
    same = sum(1 for n in rf if RENAMED_PREDICATES.get(n, n) in ef and rf[n] == ef[RENAMED_PREDICATES.get(n, n)])
    return out + [f"predicates: RS {len(rf)}, E {len(ef)}, identical after renumbering: {same}"]


def headers(rm, em) -> list[str]:
    shared = sorted(set(rm) & set(em))
    out = []
    for f in ("map_type", "weather", "requires_flash", "region_map_section", "battle_scene"):
        diffs = [(m, rm[m].get(f), em[m].get(f)) for m in shared if rm[m].get(f) != em[m].get(f)]
        out.append(f"== {f}: {len(diffs)} differ")
        out += [f"   {m[4:]}: RS {a} | E {b}" for m, a, b in diffs]
    return out


def permissions(rm, em) -> list[str]:
    def rs_cycle(m, t):
        if m in RS_BIKE_ALWAYS:
            return True
        return t not in ("MAP_TYPE_INDOOR", "MAP_TYPE_SECRET_BASE", "MAP_TYPE_UNDERWATER") and m not in RS_BIKE_NEVER

    shared = sorted(set(rm) & set(em))
    out = []
    for name, rule, key in (("cycling", lambda m: rs_cycle(m, rm[m]["map_type"]), "allow_cycling"),
                            ("escaping (Escape Rope, Dig)", lambda m: rm[m]["map_type"] == "MAP_TYPE_UNDERGROUND", "allow_escaping"),
                            ("running", lambda m: rm[m]["map_type"] != "MAP_TYPE_INDOOR", "allow_running")):
        diffs = [(m, rm[m]["map_type"], rule(m), em[m][key]) for m in shared if rule(m) != em[m][key]]
        out.append(f"== {name}: {len(diffs)} shared maps differ")
        out += [f"   {m[4:]} ({t}): RS {a} | E {b}" for m, t, a, b in diffs]
    return out


def heal_locations(R, E) -> list[str]:
    def norm(root):
        j = json.loads((root / "src/data/heal_locations.json").read_text())
        return {h["id"]: {k: v for k, v in h.items() if k != "id"} for h in j["heal_locations"]}

    a, b = norm(R), norm(E)
    out = [f"{k}: RS {a.get(k)} | E {b.get(k)}" for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
    return out + [f"heal locations: RS {len(a)}, E {len(b)}, differing: {len(out)}"]


def function_body(src: str, name: str) -> str:
    m = re.search(rf"\b{name}\s*\([^)]*\)\s*\n\{{", src)
    if not m:
        return ""
    i, depth = m.end() - 1, 0
    for j in range(i, len(src)):
        depth += {"{": 1, "}": -1}.get(src[j], 0)
        if depth == 0:
            return src[i:j + 1]
    return ""


def field_abilities(R, E) -> list[str]:
    places = {"wild encounters": "src/wild_encounter.c", "fishing (field_player_avatar.c)": "src/field_player_avatar.c",
              "daycare": "src/daycare.c", "egg hatching": "src/egg_hatch.c"}
    out = []
    for what, rel in places.items():
        for name, root in (("RS", R), ("E", E)):
            p = root / rel
            found = sorted(set(re.findall(r"ABILITY_\w+", strip_c(p.read_text())))) if p.exists() else ["(file missing)"]
            out.append(f"{what:32} {name:2} {', '.join(found) or 'none'}")
    for name, root, rel in (("RS", R, "src/pokemon_3.c"), ("E", E, "src/pokemon.c")):
        body = function_body(strip_c((root / rel).read_text()), "SetWildMonHeldItem")
        rolls = re.findall(r"rnd\s*[<>]=?\s*\d+|chance\w*\s*=\s*\d+", body)
        out.append(f"{'SetWildMonHeldItem':32} {name:2} abilities: {', '.join(sorted(set(re.findall(r'ABILITY_\w+', body)))) or 'none'}; rolls: {', '.join(rolls)}")
    return out


def encounter_functions(R, E) -> list[str]:
    def names(root):
        src = strip_c((root / "src/wild_encounter.c").read_text())
        return set(re.findall(r"^(?:static\s+)?(?:bool8|u8|u16|u32|void|bool32|s32)\s+(\w+)\s*\(", src, re.M))

    r, e = names(R), names(E)
    return [f"RS only: {sorted(r - e)}", f"E only:  {sorted(e - r)}",
            "(names only; Emerald renamed some pokeruby functions, so read both files for any that matter)"]


def main() -> list[str]:
    R, E = tree("pokeruby"), tree("pokeemerald")
    rm, em = load_maps(R), load_maps(E)
    sections = [
        ("1. Metatile behavior numbering", numbering(R, E)),
        ("2. Tile bits per behavior", tile_bits(R, E)),
        ("3. Behavior predicates", predicates(R, E)),
        ("4. Map headers on shared maps", headers(rm, em)),
        ("5. Bike, Escape Rope/Dig and running permissions", permissions(rm, em)),
        ("6. Heal locations", heal_locations(R, E)),
        ("7. Abilities that act outside battle", field_abilities(R, E)),
        ("8. Wild-encounter functions in one game only", encounter_functions(R, E)),
    ]
    out = []
    for title, lines in sections:
        out += [f"== {title}", *lines, ""]
    counts = collections.Counter(m["map_type"] for m in rm.values())
    out.append(f"(map types in pokeruby: {dict(sorted(counts.items()))})")
    return out


if __name__ == "__main__":
    print("\n".join(main()))
