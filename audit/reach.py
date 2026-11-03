"""V-01 / V-06: per-map reachability, Ruby/Sapphire vs Emerald, under the engine's movement rules.

    uv run python -m audit.reach [MAP_ID ...]

For each shared map, each entrance (a warp tile, or a map edge with a connection) and each set
of field abilities, flood-fill the tiles the player can reach and record: the exits reached
(warps by destination map, edges by direction), and whether walkable encounter tiles, surfable
water and fishable water are reached. Prints the maps where any entrance differs between the
games. Story NPCs are left to audit.chokepoints; Cut trees, Rock Smash rocks and Strength
boulders need their move.

Map data is the same for Ruby and Sapphire (pokeruby has one set of map.json files), so this
runs once for both.
"""

import glob
import json
import re
import struct
import sys
from collections import deque
from pathlib import Path

from audit.sources import tree

CAPS = {
    "none": frozenset(),
    "cut": frozenset({"cut"}),
    "+smash": frozenset({"cut", "rock-smash", "bike"}),
    "+strength": frozenset({"cut", "rock-smash", "bike", "strength"}),
    "+surf": frozenset({"cut", "rock-smash", "bike", "strength", "surf"}),
    "+waterfall": frozenset({"cut", "rock-smash", "bike", "strength", "surf", "waterfall"}),
}
OBSTACLES = {"OBJ_EVENT_GFX_CUTTABLE_TREE": "cut", "OBJ_EVENT_GFX_BREAKABLE_ROCK": "rock-smash",
             "OBJ_EVENT_GFX_PUSHABLE_BOULDER": "strength"}
WALL = "OBJ_EVENT_GFX_AUDIT_WALL"  # added by audit.chokepoints; nothing passes it
DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


class Game:
    """One game's tiles: behavior numbers, the encounter/surfable bits, tileset attributes, layouts, maps."""

    def __init__(self, root: Path, rs: bool):
        self.root, self.rs = root, rs
        self.mb = self.behaviors()
        self.flags = self.tile_flags()
        self.attrs = self.tileset_attrs()
        self.layouts = {l["id"]: l for l in json.load(open(root / "data/layouts/layouts.json"))["layouts"] if l}
        self.maps = {}
        for p in glob.glob(str(root / "data/maps/*/map.json")):
            m = json.load(open(p))
            self.maps[m["id"]] = m

    def behaviors(self) -> dict[str, int]:
        text = (self.root / "include/constants/metatile_behaviors.h").read_text()
        if self.rs:
            return {k: int(v, 0) for k, v in re.findall(r"#define (MB_\w+) (0x[0-9A-Fa-f]+|\d+)", text)}
        body = re.search(r"enum\s*\{(.*?)\}", text, re.S).group(1)
        names = [n.split("=")[0].strip() for n in re.sub(r"//[^\n]*", "", body).split(",")]
        return {n: i for i, n in enumerate(n for n in names if n)}

    def tile_flags(self) -> dict[int, int]:
        """Behavior -> bit 1 has encounters, bit 2 surfable (sTileBitAttributes)."""
        text = (self.root / "src/metatile_behavior.c").read_text(errors="replace")
        body = re.search(r"sTileBitAttributes\[[^\]]*\]\s*=\s*\{(.*?)\};", text, re.S).group(1)
        out = {}
        if self.rs:
            for i, (_unused, s, w) in enumerate(re.findall(r"TILE_ATTRIBUTES\((\w+),\s*(\w+),\s*(\w+)\)", body)):
                out[i] = (1 if w == "TRUE" else 0) | (2 if s == "TRUE" else 0)
        else:
            for name, val in re.findall(r"\[(MB_\w+)\]\s*=\s*([^,\n]+)", body):
                out[self.mb[name]] = (1 if "HAS_ENCOUNTERS" in val else 0) | (2 if "SURFABLE" in val else 0)
        return out

    def tileset_attrs(self) -> dict[str, list[int]]:
        out = {}
        if self.rs:
            text = (self.root / "data/tilesets/metatiles.inc").read_text()
            pairs = re.findall(r"gMetatileAttributes_(\w+)::[^\n]*\n\s*\.incbin \"([^\"]+)\"", text)
        else:
            text = (self.root / "src/data/tilesets/metatiles.h").read_text()
            pairs = re.findall(r"gMetatileAttributes_(\w+)\[\]\s*=\s*INCBIN_U16\(\"([^\"]+)\"\)", text)
        for name, path in pairs:
            data = (self.root / path).read_bytes()
            out[f"gTileset_{name}"] = list(struct.unpack(f"<{len(data) // 2}H", data))
        return out

    def grid(self, map_id: str, m: dict | None = None):
        """(map, width, height, tiles) where tiles[y][x] = (behavior, collision, elevation)."""
        m = m or self.maps[map_id]
        lay = self.layouts[m["layout"]]
        data = (self.root / lay["blockdata_filepath"]).read_bytes()
        blocks = struct.unpack(f"<{len(data) // 2}H", data)
        prim, sec = self.attrs.get(lay["primary_tileset"], []), self.attrs.get(lay["secondary_tileset"], [])

        def behavior(mt):
            table, i = (prim, mt) if mt < 512 else (sec, mt - 512)
            return table[i] & 0xFF if i < len(table) else 0

        w, h = lay["width"], lay["height"]
        tiles = [[(behavior(b & 0x3FF), (b >> 10) & 3, b >> 12) for b in blocks[y * w:(y + 1) * w]] for y in range(h)]
        return m, w, h, tiles


def summarize(g: Game, map_id: str, m: dict | None = None, caps: dict = CAPS) -> dict:
    """(entrance, ability set) -> (exits, walk-encounter tiles reached, surfed, could fish).

    `m` overrides the map's events (audit.chokepoints adds walls); `caps` limits the ability sets.
    """
    m, w, h, tiles = g.grid(map_id, m)
    mb = g.mb
    ledge = {mb["MB_JUMP_EAST"]: (1, 0), mb["MB_JUMP_WEST"]: (-1, 0), mb["MB_JUMP_NORTH"]: (0, -1), mb["MB_JUMP_SOUTH"]: (0, 1)}
    waterfall = mb["MB_WATERFALL"]
    door = mb["MB_ANIMATED_DOOR"]
    bike_mbs = {v for k, v in mb.items() if any(s in k for s in ("MUDDY_SLOPE", "CRACKED_FLOOR", "RAIL", "BUMPY_SLOPE"))}
    surfable = lambda b: bool(g.flags.get(b, 0) & 2)  # noqa: E731
    land_enc = lambda b: bool(g.flags.get(b, 0) & 1) and not surfable(b)  # noqa: E731
    obstacles = {(o["x"], o["y"]): ("never" if o["graphics_id"] == WALL else OBSTACLES[o["graphics_id"]])
                 for o in m.get("object_events") or [] if o["graphics_id"] in OBSTACLES or o["graphics_id"] == WALL}
    conns = {c["direction"]: c["map"] for c in m.get("connections") or [] if c["direction"] in DIRS}
    warps: dict[tuple[int, int], set[str]] = {}
    for wp in m.get("warp_events") or []:
        if 0 <= wp["x"] < w and 0 <= wp["y"] < h:  # a few warps sit outside the layout
            warps.setdefault((wp["x"], wp["y"]), set()).add(wp["dest_map"])

    def mismatch(cur, x, y):
        # IsElevationMismatchAt: the player's elevation is nonzero, the tile's isn't 0 or 15, and they differ
        e = tiles[y][x][2]
        return cur != 0 and e not in (0, 15) and e != cur

    def run(starts, caps):
        # Engine rules (field_player_avatar.c / field_control_avatar.c / item_use.c, the same in both games):
        # - Surf starts only from elevation-3 land facing water whose collision is 0 and elevation
        #   mismatches (IsPlayerFacingSurfableFishableWater); fishing from land uses the same test.
        # - Surf ends only onto an elevation-3 tile (CanStopSurfing, on an elevation mismatch).
        # - While surfing, a step with no elevation mismatch and no collision just moves (still surfing).
        # - Animated doors (MB_ANIMATED_DOOR) are solid and entered by moving north into them (TryDoorWarp).
        seen, q = set(), deque(starts)
        exits, enc, water, fish = set(), False, False, False
        while q:
            st = q.popleft()
            if st in seen:
                continue
            seen.add(st)
            x, y, elev, surf = st
            b, _coll, _e = tiles[y][x]
            if (x, y) in warps:
                exits |= {("warp", d) for d in warps[(x, y)]}
            if not surf and y > 0 and (x, y - 1) in warps and tiles[y - 1][x][0] == door:
                exits |= {("warp", d) for d in warps[(x, y - 1)]}
            if surf:
                water = True
            elif land_enc(b):
                enc = True
            for dname, (dx, dy) in DIRS.items():
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h):
                    if dname in conns:
                        exits.add(("edge", dname))
                    continue
                nb, ncoll, ne = tiles[ny][nx]
                need = obstacles.get((nx, ny))
                if need and need not in caps:
                    continue
                keep = elev if ne == 15 else ne  # ObjectEventUpdateElevation: 15 keeps, 0 resets
                if not surf and nb in ledge:  # ShouldJumpLedge runs before the collision result is used
                    if ledge[nb] == (dx, dy):
                        jx, jy = nx + dx, ny + dy
                        if 0 <= jx < w and 0 <= jy < h and tiles[jy][jx][1] == 0:
                            q.append((jx, jy, tiles[jy][jx][2] if tiles[jy][jx][2] != 15 else elev, False))
                    continue
                if ncoll != 0:
                    continue
                if surf:
                    if mismatch(elev, nx, ny):
                        if ne == 3:
                            q.append((nx, ny, 3, False))  # stop surfing
                        continue
                    if nb == waterfall and dy <= 0 and "waterfall" not in caps:
                        continue
                    q.append((nx, ny, keep, True))
                    continue
                if surfable(nb) and mismatch(elev, nx, ny):
                    if elev == 3 and nb != waterfall:
                        fish = True
                        if "surf" in caps:
                            q.append((nx, ny, ne, True))
                    continue
                if mismatch(elev, nx, ny):
                    continue
                if nb in bike_mbs and "bike" not in caps:
                    continue
                q.append((nx, ny, keep, False))
        return frozenset(exits), enc, water, fish

    entries: dict[tuple, list] = {}
    for (x, y), dests in warps.items():
        for d in dests:
            entries.setdefault(("warp", d), []).append((x, y, tiles[y][x][2], surfable(tiles[y][x][0])))  # arrive surfing on water
    for dname in conns:
        edge = ([(x, 0) for x in range(w)] if dname == "up" else [(x, h - 1) for x in range(w)] if dname == "down"
                else [(0, y) for y in range(h)] if dname == "left" else [(w - 1, y) for y in range(h)])
        entries[("edge", dname)] = [(x, y, tiles[y][x][2], surfable(tiles[y][x][0])) for x, y in edge if tiles[y][x][1] == 0]
    out = {}
    for ent, starts in entries.items():
        for cname, cset in caps.items():
            out[(ent, cname)] = run([s for s in starts if not s[3] or "surf" in cset], cset)
    return out


def fmt(r) -> str:
    exits, enc, water, fish = r
    return f"exits={sorted(f'{k}:{v.removeprefix('MAP_')}' for k, v in exits)} grass={enc} surf={water} fish={fish}"


def report(rs: Game, em: Game, ids: list[str]) -> list[str]:
    out, ndiff = [], 0
    for mid in ids:
        try:
            a, b = summarize(rs, mid), summarize(em, mid)
        except Exception as ex:  # noqa: BLE001
            out.append(f"{mid}: ERROR {type(ex).__name__}: {ex}")
            continue
        lines = []
        for k in sorted(set(a) | set(b), key=str):
            ra, rb = a.get(k), b.get(k)
            if ra is None or rb is None:
                continue  # an entrance only one game has (an Emerald-only warp)
            # ignore exits to maps only one game has
            shared = lambda ex: frozenset(e for e in ex if e[0] == "edge" or e[1] in rs.maps and e[1] in em.maps)  # noqa: E731
            if (shared(ra[0]), *ra[1:]) != (shared(rb[0]), *rb[1:]):
                lines.append(f"    from {k[0][0]} {k[0][1]} with {k[1]}:\n      RS: {fmt(ra)}\n      E : {fmt(rb)}")
        if lines:
            ndiff += 1
            out.append(f"{mid}:")
            out.append("\n".join(lines[:8]) + (f"\n    ... {len(lines) - 8} more" if len(lines) > 8 else ""))
    out.append(f"maps with reachability differences: {ndiff} of {len(ids)}")
    return out


def main(argv: list[str]) -> list[str]:
    rs, em = Game(tree("pokeruby"), True), Game(tree("pokeemerald"), False)
    return report(rs, em, argv or sorted(set(rs.maps) & set(em.maps)))


if __name__ == "__main__":
    print("\n".join(main(sys.argv[1:])))
