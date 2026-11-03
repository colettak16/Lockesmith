"""V-01 / V-06: per-map reachability, Ruby/Sapphire vs Emerald, under the engine's movement rules.

    uv run python -m audit.reach [MAP_ID ...]

For each shared map, each entrance (a warp tile, or a map edge with a connection) and each set
of field abilities, flood-fill the tiles the player can reach and record: the exits reached
(warps by destination map, edges by direction), and whether walkable encounter tiles, surfable
water and fishable water are reached. Prints the maps where any entrance differs between the
games. Story NPCs are left to audit.chokepoints; Cut trees, Rock Smash rocks and Strength
boulders need their move.

Each ability set carries one bike, Mach or Acro, since you can't swap bikes inside a map; the
report ends with the entrances where the two bikes reach different things.

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

# Ability sets, each with one bike: the player can't switch bikes inside a map (Rydel's shop is in Mauville).
_STEPS = {"+smash": {"cut", "rock-smash"}, "+strength": {"cut", "rock-smash", "strength"},
          "+surf": {"cut", "rock-smash", "strength", "surf"}, "+waterfall": {"cut", "rock-smash", "strength", "surf", "waterfall"}}
CAPS = {"none": frozenset(), "cut": frozenset({"cut"})} | {
    f"{step}/{bike}": frozenset(moves | {bike}) for step, moves in _STEPS.items() for bike in ("mach", "acro")
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
    # Bike tiles (bike.c, field_player_avatar.c, field_tasks.c; the same in both games):
    # - muddy slope: climbing north needs the Mach Bike at top speed; any other move slides you south
    #   (ForcedMovement_MuddySlope), so entering from the side or above is fine but you leave southward
    # - cracked floor: only the Mach Bike at top speed crosses before it breaks (CrackedFloorPerStepCallback);
    #   anyone slower falls to the floor below, and a hole drops you. Falls aren't counted as exits
    # - bumpy slope: Acro Bike only (COLLISION_WHEELIE_HOP, crossed in a wheelie)
    # - long rails: either bike rides onto them (COLLISION_*_RAIL >= COLLISION_VERTICAL_RAIL isn't a
    #   collision for bikes); walking can't. On a rail, riding only goes along it (CanBikeFaceDirOnMetatile)
    # - single-tile (isolated) rails: no ride lands on one; only the Acro Bike's side jump does
    # - the side jump (AcroBikeTransition_SideJump, Acro only) moves one tile in any direction, off a rail
    #   too, onto a plain tile or a rail lying across the jump (WillPlayerCollideWithCollision), never onto
    #   a bumpy slope or a rail lying along it
    # Elevation is checked before any of this, so a rail at another height is a wall.
    muddy, cracked, bumpy = mb["MB_MUDDY_SLOPE"], mb["MB_CRACKED_FLOOR"], mb["MB_BUMPY_SLOPE"]
    hole = mb.get("MB_CRACKED_FLOOR_HOLE")
    vertical = {mb["MB_VERTICAL_RAIL"], mb["MB_ISOLATED_VERTICAL_RAIL"]}
    horizontal = {mb["MB_HORIZONTAL_RAIL"], mb["MB_ISOLATED_HORIZONTAL_RAIL"]}
    isolated = {mb["MB_ISOLATED_VERTICAL_RAIL"], mb["MB_ISOLATED_HORIZONTAL_RAIL"]}
    rail_axis = {**{v: "v" for v in vertical}, **{h: "h" for h in horizontal}}

    def bike_ok(b, nb, dx, dy, caps):
        """May the player step from a tile with behavior b onto one with nb, in direction (dx, dy)?"""
        mach, acro = "mach" in caps, "acro" in caps
        if b == muddy and not (dy == 1 or dy == -1 and mach):
            return False  # on a slope you slide south unless climbing it on the Mach Bike
        if nb == muddy and dy == -1 and not mach:
            return False
        if nb == hole or nb == cracked and not mach:
            return False
        move = "v" if dy else "h"
        if rail_axis.get(b, move) == move:  # riding (or walking): on a rail, only along it
            if nb == bumpy:
                return acro
            if nb in isolated:
                pass  # only a side jump lands here
            elif nb in rail_axis:
                if mach or acro:
                    return True
            else:
                return True
        # the Acro Bike's side jump
        return acro and nb != bumpy and rail_axis.get(nb, None) != move
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
                if not bike_ok(b, nb, dx, dy, caps):
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


def bike_gates(g: Game, ids: list[str]) -> list[str]:
    """Entrances where the Mach and Acro Bike passes (with every other field move) reach different things."""
    out = []
    for mid in ids:
        try:
            res = summarize(g, mid)
        except Exception:  # noqa: BLE001 (reported by report())
            continue
        for (ent, cname), a in sorted(res.items(), key=str):
            if cname != "+waterfall/mach":
                continue
            b = res[(ent, "+waterfall/acro")]
            if a != b:
                name = lambda e: e[1].removeprefix("MAP_")  # noqa: E731
                out.append(f"  {mid[4:]:30} from {ent[0]} {name(ent):30} Mach only: {sorted(map(name, a[0] - b[0]))}  "
                           f"Acro only: {sorted(map(name, b[0] - a[0]))}  (grass, surf, fish: Mach {a[1:]}, Acro {b[1:]})")
    return out


def main(argv: list[str]) -> list[str]:
    rs, em = Game(tree("pokeruby"), True), Game(tree("pokeemerald"), False)
    ids = argv or sorted(set(rs.maps) & set(em.maps))
    out = report(rs, em, ids)
    for name, g in (("Ruby/Sapphire", rs), ("Emerald", em)):
        out += ["", f"== Where the bike matters in {name} (every field move, Mach Bike vs Acro Bike)",
                *bike_gates(g, argv or sorted(g.maps))]
    return out


if __name__ == "__main__":
    print("\n".join(main(sys.argv[1:])))
