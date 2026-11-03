"""Q-10 / SE-10: every script that starts an encounter, with what it checks first, Ruby/Sapphire vs Emerald.

    uv run python -m audit.encounter_scripts RUBY|SAPPHIRE

Finds every `setwildbattle`, `givemon` and `giveegg` outside the debug scripts, and every call
of the specials that create a Pokémon or start a wild encounter from a script: InitRoamer (the
roamer), CreateInGameTradePokemon (in-game trades), GiveEggFromDaycare (the daycare egg) and
(ScrSpecial_)RockSmashWildEncounter (Rock Smash). The specials that start the legendary and
Regi battles always follow a `setwildbattle`, so they're covered by it. Encounters that start
in C without any script (walking, surfing and fishing in the wild tables, and Feebas) aren't
here; audit.engine compares that code. For each one it walks back up the labels that lead to it (up to four levels of
goto/call within the same file) and prints the checks on the way: flags, variables, items,
party size and the battle or gift outcome. When a label in that chain is an object's script,
it also prints the object's hide flag and whether a new game starts with it set. Prints both
games side by side per species, for reading: flag and label names differ between the
decomps, so the comparison itself is done by eye.
"""

import re
import sys
from collections import defaultdict

from audit.maps import VERSIONS, flag_writers, labels, load_maps, load_scripts
from audit.sources import tree

START = re.compile(r"^\s*(setwildbattle|givemon|giveegg)\s+(SPECIES_\w+)|^\s*special\s+"
                   r"(InitRoamer|CreateInGameTradePokemon|GiveEggFromDaycare|ScrSpecial_RockSmashWildEncounter|RockSmashWildEncounter)\b")
GATE = re.compile(r"^(checkflag|checkitem|checkpartymove|getpartysize|compare|specialvar|"
                  r"(?:goto|call)_if_(?:set|unset|eq|ne|lt|ge|le|gt))\b")
JUMP = re.compile(r"^(?:goto|call)(?:_if_\w+)?\s+(?:.*,\s*)?(\w+)\s*$")
SPECIES_ALIASES = {"SPECIES_GROUDON_OR_KYOGRE": "SPECIES_GROUDON/KYOGRE", "SPECIES_GROUDON": "SPECIES_GROUDON/KYOGRE",
                   "SPECIES_KYOGRE": "SPECIES_GROUDON/KYOGRE", "SPECIES_LATIAS_OR_LATIOS": "SPECIES_LATIAS/LATIOS",
                   "InitRoamer": "roamer (InitRoamer)", "CreateInGameTradePokemon": "in-game trade (CreateInGameTradePokemon)",
                   "GiveEggFromDaycare": "daycare egg (GiveEggFromDaycare)",
                   "ScrSpecial_RockSmashWildEncounter": "Rock Smash encounter (RockSmashWildEncounter)",
                   "RockSmashWildEncounter": "Rock Smash encounter (RockSmashWildEncounter)"}


def callers(body_of: dict[str, list[str]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for label, body in body_of.items():
        for ln in body:
            m = JUMP.match(ln.split("@")[0].strip())
            if m:
                out[m.group(1)].add(label)
    return out


def object_scripts(maps: dict) -> dict[str, list[tuple[str, str, str]]]:
    """Script label -> [(map, graphics, hide flag)] for every object that runs it."""
    out: dict[str, list] = defaultdict(list)
    for mid, m in maps.items():
        for o in m.get("object_events") or []:
            if o.get("script") and o["script"] != "0x0":
                out[o["script"]].append((mid[4:], o["graphics_id"].removeprefix("OBJ_EVENT_GFX_"), o.get("flag", "0")))
    return out


def scan(root, version) -> dict[str, list[str]]:
    scripts = load_scripts(root, version)
    init, setters, clearers = flag_writers(scripts)
    objs = object_scripts(load_maps(root))
    found: dict[str, list[str]] = defaultdict(list)
    for where, lines in scripts.items():
        if where == "scripts/debug.inc":
            continue
        body_of = labels(lines)
        up = callers(body_of)
        for label, body in body_of.items():
            for i, ln in enumerate(body):
                m = START.match(ln)
                if not m or ln.lstrip().startswith("@"):
                    continue
                species = SPECIES_ALIASES.get(m.group(2) or m.group(3), m.group(2) or m.group(3))
                entry = [f"  {where}: {label}: {ln.strip()}"]
                gates = [g for g in body[:i] if GATE.match(g)]
                after = [g for g in body[i + 1:i + 6] if GATE.match(g)]
                if gates:
                    entry.append(f"    checks before, in {label}: {'; '.join(gates)}")
                if after:
                    entry.append(f"    checks after: {'; '.join(after)}")
                chain, frontier, seen = [], [label], {label}
                for _ in range(4):
                    nxt = []
                    for lab in frontier:
                        for c in sorted(up.get(lab, ())):
                            if c in seen:
                                continue
                            seen.add(c)
                            nxt.append(c)
                            g = [x for x in body_of.get(c, []) if GATE.match(x)]
                            chain.append(f"    reached from {c}" + (f": {'; '.join(g)}" if g else ""))
                    frontier = nxt
                entry += chain[:12]
                objects = []
                for lab in sorted(seen):
                    for mapname, gfx, flag in objs.get(lab, []):
                        state = "hidden at a new game" if flag in init else "visible at a new game"
                        flag_note = (f"{flag} ({state}; cleared by {sorted(clearers.get(flag, []))}; set by {sorted(setters.get(flag, []))[:4]})"
                                     if flag.startswith("FLAG_") else "no hide flag")
                        objects.append(f"    object on {mapname}: {gfx}, {flag_note}")
                entry += objects[:6] + ([f"    ... and {len(objects) - 6} more objects"] if len(objects) > 6 else [])
                found[species].append("\n".join(entry))
    return found


def main(version: str) -> list[str]:
    rs, em = scan(tree("pokeruby"), version), scan(tree("pokeemerald"), None)
    out = [f"# encounter-starting scripts: RS {sum(map(len, rs.values()))}, E {sum(map(len, em.values()))}"]
    for species in sorted(set(rs) | set(em)):
        out.append(f"\n== {species}" + ("" if species in rs and species in em else "  (only in " + ("RS" if species in rs else "E") + ")"))
        for name, side in (("RS", rs), ("E", em)):
            for entry in side.get(species, []):
                out.append(f" {name}\n{entry}")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in VERSIONS:
        sys.exit(__doc__)
    print("\n".join(main(sys.argv[1])))
