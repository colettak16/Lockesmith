"""V-06 (first number): which shared maps have any different blocks, Ruby/Sapphire vs Emerald.

    uv run python -m audit.layouts

Each block in a layout's map.bin is a u16: metatile (bits 0-9), collision (10-11), elevation
(12-15). Prints, per shared map whose layout differs, the size or tileset change, or how many
blocks differ in metatile, collision or elevation with the bounding box of the changes.
audit.reach then decides which of these differences change what's reachable.
"""

import json
import struct

from audit.maps import load_maps
from audit.sources import tree


def layouts(root):
    return {l["id"]: l for l in json.loads((root / "data/layouts/layouts.json").read_text())["layouts"] if l}


def blocks(root, lay):
    data = (root / lay["blockdata_filepath"]).read_bytes()
    return struct.unpack(f"<{len(data) // 2}H", data)


def main() -> list[str]:
    R, E = tree("pokeruby"), tree("pokeemerald")
    rm, em = load_maps(R), load_maps(E)
    rl, el = layouts(R), layouts(E)
    same = diff = 0
    rows = []
    for mid in sorted(set(rm) & set(em)):
        a, b = rl.get(rm[mid]["layout"]), el.get(em[mid]["layout"])
        if not a or not b:
            rows.append(f"  {mid[4:]}: layout missing")
            continue
        if (a["width"], a["height"]) != (b["width"], b["height"]):
            rows.append(f"  {mid[4:]}: size {a['width']}x{a['height']} vs {b['width']}x{b['height']}")
            diff += 1
            continue
        ba, bb = blocks(R, a), blocks(E, b)
        tiles = a["primary_tileset"] != b["primary_tileset"] or a["secondary_tileset"] != b["secondary_tileset"]
        if ba == bb and not tiles:
            same += 1
            continue
        diff += 1
        w = a["width"]
        kinds: dict[str, list[int]] = {"metatile": [], "collision": [], "elevation": []}
        for i, (x, y) in enumerate(zip(ba, bb)):
            if x == y:
                continue
            if (x & 0x3FF) != (y & 0x3FF):
                kinds["metatile"].append(i)
            if ((x >> 10) & 3) != ((y >> 10) & 3):
                kinds["collision"].append(i)
            if (x >> 12) != (y >> 12):
                kinds["elevation"].append(i)
        desc = []
        for k, idx in kinds.items():
            if idx:
                xs, ys = [i % w for i in idx], [i // w for i in idx]
                desc.append(f"{k} {len(idx)} blocks x{min(xs)}-{max(xs)} y{min(ys)}-{max(ys)}")
        if tiles:
            desc.append(f"tilesets {a['primary_tileset']}/{a['secondary_tileset']} vs {b['primary_tileset']}/{b['secondary_tileset']}")
        rows.append(f"  {mid[4:]}: {'; '.join(desc)}")
    return [f"shared maps: {len(set(rm) & set(em))}  identical geometry: {same}  different: {diff}", *rows]


if __name__ == "__main__":
    print("\n".join(main()))
