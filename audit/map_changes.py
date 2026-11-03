"""V-04 / V-09: map-script changes by condition, Ruby/Sapphire vs Emerald, reading both branch syntaxes.

    uv run python -m audit.map_changes RUBY|SAPPHIRE

pokeruby writes variable branches as `compare VAR, VAL` then a one-argument `goto_if_eq LABEL`;
pokeemerald as `goto_if_eq VAR, VAL, LABEL`. Flag branches are `goto_if_set FLAG, LABEL` in both.
For every conditional branch in a map's own scripts.inc, the target label's body (to its first
end, return or goto) is checked for what it changes: metatiles (setmetatile), the layout
(setmaplayoutindex), NPC positions (setobjectxyperm) or warps (setwarp, setdivewarp,
setescapewarp, setholewarp). Prints, per shared map, both games' (condition, change) sets when
the changes differ.
"""

import re
import sys

from audit.maps import VERSIONS, labels, load_maps, load_scripts
from audit.sources import tree

CHANGE = {"setmetatile": "tiles", "setmaplayoutindex": "layout", "setobjectxyperm": "npc-move", "setwarp": "warp",
          "setdivewarp": "divewarp", "setescapewarp": "escapewarp", "setholewarp": "holewarp"}


def changes(lines: list[str]) -> set[tuple[str, str, str]]:
    b = labels(lines)
    res, last = set(), None
    for ln in lines:
        s = ln.strip()
        m = re.match(r"compare\s+(\w+)\s*,\s*(\w+)", s)
        if m:
            last = f"{m.group(1)}={m.group(2)}"
            continue
        m = re.match(r"(call|goto)_if_(\w+)\s+(.*)$", s)
        if not m:
            continue
        kind, args = m.group(2), [a.strip() for a in m.group(3).split("@")[0].split(",")]
        if len(args) == 1:
            cond, label = f"{last} ({kind})", args[0]
        elif len(args) == 2:
            cond, label = f"{args[0]} ({kind})", args[1]
        else:
            cond, label = f"{args[0]}={args[1]} ({kind})", args[2]
        found: dict[str, list[str]] = {}
        for x in b.get(label, []):
            op = x.split()[0] if x.split() else ""
            if op in CHANGE:
                found.setdefault(CHANGE[op], []).append(x.split(None, 1)[1] if " " in x else "")
            if op in ("end", "return") or op.startswith("goto"):
                break
        for k, v in found.items():
            res.add((cond, k, f"{len(v)}" if k in ("tiles", "npc-move") else v[0][:60]))
    return res


def by_map(root, version) -> dict[str, set]:
    scripts = load_scripts(root, version)
    return {mid: changes(scripts.get(m["folder"], [])) for mid, m in load_maps(root).items()}


def main(version: str) -> list[str]:
    rm, em = by_map(tree("pokeruby"), version), by_map(tree("pokeemerald"), None)
    out = []
    for mid in sorted(set(rm) & set(em)):
        a, b = rm[mid], em[mid]
        norm = lambda s: sorted((k, d) for _, k, d in s)  # noqa: E731
        if norm(a) != norm(b):
            out.append(f"{mid[4:]}")
            out += [f"    RS  {x[0]:55} {x[1]:9} {x[2]}" for x in sorted(a)]
            out += [f"    E   {x[0]:55} {x[1]:9} {x[2]}" for x in sorted(b)]
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in VERSIONS:
        sys.exit(__doc__)
    print("\n".join(main(sys.argv[1])))
