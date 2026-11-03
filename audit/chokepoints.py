"""V-02 / V-07: story NPCs that stand on a chokepoint, in every shared map, however they're removed.

    uv run python -m audit.chokepoints RUBY|SAPPHIRE

Candidates: every object visible at a new game (its hide flag isn't set by new_game.inc), except
item balls and field-move obstacles, so objects removed by `setflag`, by `removeobject` (which
sets the object's flag) or never are all included. Objects sharing a hide flag are walled off
together; flagless objects one at a time. A candidate is a chokepoint if walling it costs any
entrance an exit, walkable encounter tiles or water, with every field move and either bike (audit.reach).

Prints the chokepoints in only one game (matched by map and tiles), and for those in both,
whether the scripts that remove them live in the same place. Per-game group counts go to stderr.
"""

import copy
import glob
import json
import re
import sys
import time
from pathlib import Path

from audit import reach
from audit.maps import VERSIONS, flag_writers, load_scripts
from audit.sources import tree

SKIP = ("ITEM_BALL", "CUTTABLE_TREE", "BREAKABLE_ROCK", "PUSHABLE_BOULDER")
ALL_ABILITIES = {k: v for k, v in reach.CAPS.items() if k.startswith("+waterfall/")}  # every move, with each bike


def removers(root: Path, scripts: dict[str, list[str]]) -> dict[str, set[str]]:
    """Flag -> scripts that set it, by `setflag` or by `removeobject` of an object carrying it."""
    out: dict[str, set[str]] = {}
    objflag = {}
    for p in glob.glob(str(root / "data/maps/*/map.json")):
        m = json.load(open(p))
        for i, o in enumerate(m.get("object_events") or [], 1):
            objflag[(Path(p).parent.name, str(i))] = o.get("flag", "0")
            if o.get("local_id"):
                objflag[(Path(p).parent.name, o["local_id"])] = o.get("flag", "0")
    for where, lines in scripts.items():
        for line in lines:
            for f in re.findall(r"setflag\s+(FLAG_\w+)", line):
                out.setdefault(f, set()).add(where)
            m = re.match(r"\s*removeobject\s+(\w+)", line)
            if m and not where.startswith("scripts/"):
                f = objflag.get((where, m.group(1)))
                if f and f.startswith("FLAG_"):
                    out.setdefault(f, set()).add(where + "(removeobject)")
    return out


def chokes(game: reach.Game, init: set[str], rem: dict[str, set[str]]) -> dict:
    res = {}
    for mid, orig in game.maps.items():
        try:
            base = reach.summarize(game, mid, caps=ALL_ABILITIES)
        except Exception:  # noqa: BLE001 (a map whose layout can't be read; reach reports those)
            continue
        lay = game.layouts[orig["layout"]]
        groups: dict[str, list] = {}
        for i, o in enumerate(orig.get("object_events") or []):
            f = o.get("flag", "0")
            if any(s in o["graphics_id"] for s in SKIP) or (f.startswith("FLAG_") and f in init):
                continue
            if not (0 <= o["x"] < lay["width"] and 0 <= o["y"] < lay["height"]):
                continue
            groups.setdefault(f if f.startswith("FLAG_") else f"none#{i}", []).append(o)
        for key, objs in groups.items():
            m = copy.deepcopy(orig)
            m["object_events"] = list(m.get("object_events") or []) + [{"graphics_id": reach.WALL, "x": o["x"], "y": o["y"]} for o in objs]
            new = reach.summarize(game, mid, m, caps=ALL_ABILITIES)
            lost = sorted({f"{k[0][0]}:{k[0][1].removeprefix('MAP_')}" for k in base if base[k] != new.get(k)})
            if lost:
                pos = tuple(sorted((o["x"], o["y"]) for o in objs))
                gfx = sorted({o["graphics_id"].removeprefix("OBJ_EVENT_GFX_") for o in objs})
                res[(mid, pos)] = (gfx, key, sorted(rem.get(key, [])) if key.startswith("FLAG_") else ["(never removed)"], lost)
    return res


def main(version: str) -> list[str]:
    t = time.time()
    out = {}
    for name, root, rs, ver in (("RS", tree("pokeruby"), True, version), ("E", tree("pokeemerald"), False, None)):
        scripts = load_scripts(root, ver)
        init, _, _ = flag_writers(scripts)
        out[name] = chokes(reach.Game(root, rs), init, removers(root, scripts))
        print(f"# {name}: {len(out[name])} chokepoint groups ({time.time() - t:.0f}s)", file=sys.stderr)
    lines = [f"# chokepoint groups: RS {len(out['RS'])}, E {len(out['E'])}"]
    for k in sorted(set(out["RS"]) | set(out["E"])):
        a, b = out["RS"].get(k), out["E"].get(k)
        mid, pos = k
        if a and b:
            place = lambda ws: {s.split("(")[0].split("/")[-1].split("_")[0] for s in ws}  # noqa: E731
            tag = "BOTH same-remover" if place(a[2]) == place(b[2]) else "BOTH diff-remover"
            lines.append(f"{tag:18} {mid[4:]:30} {pos} {a[0]} RS {a[1]} <- {a[2]} | E {b[1]} <- {b[2]}")
        else:
            side, v = ("RS only", a) if a else ("E only", b)
            lines.append(f"{side:18} {mid[4:]:30} {pos} {v[0]} {v[1]} <- {v[2]} | loses from {v[3][:4]}")
    return lines


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in VERSIONS:
        sys.exit(__doc__)
    print("\n".join(main(sys.argv[1])))
