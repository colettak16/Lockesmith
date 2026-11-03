"""V-02 (the rest) / V-03 / V-08: story blockers on the same tile, and step triggers, Ruby/Sapphire vs Emerald.

    uv run python -m audit.story_gates RUBY|SAPPHIRE

1. Blockers: objects visible at a new game (their hide flag isn't set by new_game.inc) that a
   script later hides with `setflag`: the people, Kecleon, Wailmer and grunts that stand in a
   path. Matched across games by map and tile; lists those in only one game.
1b. Blockers on the same tile in both games whose removing script lives in a different place
   (compared by the first word of the script's folder or file name).
2. Coordinate (step) triggers on a story variable whose tile is in only one game.

Objects removed by `removeobject` and ones never removed are covered by audit.chokepoints.
"""

import sys

from audit.maps import VERSIONS, flag_writers, load_maps, load_scripts
from audit.sources import tree


def blockers(maps, init, setters):
    out = {}
    for mid, m in maps.items():
        for o in m.get("object_events") or []:
            f = o.get("flag", "0")
            if f.startswith("FLAG_") and f not in init and f in setters and "ITEM" not in o["graphics_id"]:
                out.setdefault(mid, {})[(o["x"], o["y"])] = (o["graphics_id"].removeprefix("OBJ_EVENT_GFX_"), f, sorted(setters[f]))
    return out


def main(version: str) -> list[str]:
    rr, er = tree("pokeruby"), tree("pokeemerald")
    rm, em = load_maps(rr), load_maps(er)
    rinit, rset, _ = flag_writers(load_scripts(rr, version))
    einit, eset, _ = flag_writers(load_scripts(er, None))
    rb, eb = blockers(rm, rinit, rset), blockers(em, einit, eset)
    shared = sorted(set(rm) & set(em))
    out = ["== 1. Blockers removed by a story script (R/S vs Emerald, same map and tile)"]
    for mid in shared:
        a, b = rb.get(mid, {}), eb.get(mid, {})
        for pos in sorted(set(a) | set(b)):
            if pos in a and pos in b:
                continue  # same blocker in both (flags may be renamed); removal checked below
            side = "RS only" if pos in a else "E only "
            g, f, w = (a if pos in a else b)[pos]
            out.append(f"  {mid[4:]:34} {side} {pos} {g:22} {f}  removed by {w}")
    out.append("\n== 1b. Same-position blockers whose removing script lives in a different place")
    same = differ = 0
    for mid in shared:
        a, b = rb.get(mid, {}), eb.get(mid, {})
        for pos in sorted(set(a) & set(b)):
            wa = {w.split("/")[-1].split("_")[0] for w in a[pos][2]}
            wb = {w.split("/")[-1].split("_")[0] for w in b[pos][2]}
            if wa != wb:
                differ += 1
                out.append(f"  {mid[4:]:34} {pos} {a[pos][0]:20} RS: {a[pos][1]} by {a[pos][2]} | E: {b[pos][1]} by {b[pos][2]}")
            else:
                same += 1
    out.append(f"  # same-tile blockers: {same + differ}; removed from the same place in both: {same}; listed above: {differ}")
    out.append("\n== 2. Coordinate triggers on a story variable that differ")
    for mid in shared:
        ca = {(c["x"], c["y"]): (c.get("var"), c.get("var_value")) for c in rm[mid].get("coord_events") or [] if c.get("script") not in (None, "0x0")}
        cb = {(c["x"], c["y"]): (c.get("var"), c.get("var_value")) for c in em[mid].get("coord_events") or [] if c.get("script") not in (None, "0x0")}
        onlya, onlyb = set(ca) - set(cb), set(cb) - set(ca)
        if onlya or onlyb:
            out.append(f"  {mid[4:]:34} RS only {sorted((p, ca[p]) for p in onlya)[:4]} | E only {sorted((p, cb[p]) for p in onlyb)[:4]}")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in VERSIONS:
        sys.exit(__doc__)
    print("\n".join(main(sys.argv[1])))
