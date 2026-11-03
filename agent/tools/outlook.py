"""Whole-run outlook tools: what the rest of the run throws at the player, and how much a
candidate is worth for all of it, not just the next battle (docs/decisions.md D10)."""

from collections import Counter

from agent.context import RequestContext
from agent.tools.battles import team
from agent.tools.common import TYPE_CHART_SOURCE, ToolError, effectiveness, resolve, rows
from agent.tools.moves import evolution_text

TYPES = [
    "normal", "fighting", "flying", "poison", "ground", "rock", "bug", "ghost", "steel",
    "fire", "water", "grass", "electric", "psychic", "ice", "dragon", "dark",
]


def remaining_opponents(ctx: RequestContext) -> tuple[list[dict], list[str]]:
    """Every opponent Pokémon in the remaining story battles, tagged with its battle."""
    out, notes = [], []
    for b in ctx.progress.remaining:
        try:
            mons, note = team(ctx, b)
        except ToolError as e:
            notes.append(f"{b.label}: {e}")
            continue
        if note:
            notes.append(f"{b.label}: {note}")
        for m in mons:
            attack_types = sorted({d["type"] for d in m["move_details"] if d["power"] and d["damage_class"] != "status"})
            out.append({"battle_id": b.id, "battle": b.label, "types": m["types"], "attack_types": attack_types,
                        "level": m["level"], "source_id": m["source_id"]})
    return out, notes


def gauntlet_overview(ctx: RequestContext) -> dict:
    """The type profile of every remaining story battle, and which attacking and defending
    types pay off over the whole rest of the run."""
    opps, notes = remaining_opponents(ctx)
    if not opps:
        raise ToolError("no remaining battles with known teams")
    per_battle = {}
    for o in opps:
        b = per_battle.setdefault(o["battle_id"], {"battle": o["battle"], "levels": [99, 0], "types": Counter(), "attack_types": Counter()})
        b["levels"] = [min(b["levels"][0], o["level"]), max(b["levels"][1], o["level"])]
        b["types"].update(o["types"])
        b["attack_types"].update(o["attack_types"])
    offense = []
    for t in TYPES:
        hits = sum(effectiveness(t, o["types"]) >= 2 for o in opps)
        walled = sum(effectiveness(t, o["types"]) < 1 for o in opps)
        offense.append({"type": t, "super_effective_on": hits, "resisted_by": walled})
    defense = []
    for t in TYPES:
        resists = sum(effectiveness(a, [t]) < 1 for o in opps for a in o["attack_types"])
        weak = sum(effectiveness(a, [t]) >= 2 for o in opps for a in o["attack_types"])
        defense.append({"type": t, "resists_attacks": resists, "weak_to_attacks": weak})
    offense.sort(key=lambda r: (-(r["super_effective_on"] - r["resisted_by"]), r["type"]))
    defense.sort(key=lambda r: (-(r["resists_attacks"] - r["weak_to_attacks"]), r["type"]))
    return {
        "opponents_remaining": len(opps),
        "battles": [
            {"battle_id": k, "battle": v["battle"], "levels": v["levels"],
             "types": dict(v["types"].most_common(4)), "attack_types": dict(v["attack_types"].most_common(4))}
            for k, v in per_battle.items()
        ],
        "best_attacking_types": offense[:6],
        "worst_attacking_types": offense[-3:],
        "best_defensive_types": defense[:5],
        "notes": notes,
        "source_ids": [TYPE_CHART_SOURCE] + [f"progression:{k}" for k in per_battle],
    }


def final_forms(cur, species_id: int, limit: int | None = None) -> list[tuple[int, list[dict]]]:
    """[(final species_id, [evolution steps to reach it])]; a species with no evolutions is its own final form.
    `limit` is the game's evolution limit (agent/games.py): steps past it are left out, so in
    FireRed/LeafGreen Zubat's final form is Golbat."""
    steps = rows(
        cur,
        "SELECT e.*, t.name AS to_name FROM evolutions e JOIN species t ON t.species_id = e.to_species_id "
        "WHERE e.from_species_id = ? AND (CAST(? AS INTEGER) IS NULL OR e.to_species_id <= ?)",
        [species_id, limit, limit],
    )
    if not steps:
        return [(species_id, [])]
    out = []
    for s in steps:
        for final, path in final_forms(cur, s["to_species_id"], limit):
            out.append((final, [s, *path]))
    return out


def gated_evolutions(ctx: RequestContext, species_id: int) -> list[str]:
    """Evolutions of this line the game cancels before the National Dex (FireRed/LeafGreen), as text."""
    limit = ctx.game.evolution_limit
    if limit is None:
        return []
    out, todo = [], [species_id]
    while todo:
        for s in rows(ctx.cursor(), "SELECT e.to_species_id, f.name AS from_name, t.name AS to_name FROM evolutions e "
                      "JOIN species f ON f.species_id = e.from_species_id JOIN species t ON t.species_id = e.to_species_id "
                      "WHERE e.from_species_id = ?", [todo.pop()]):
            if s["to_species_id"] > limit:
                out.append(f"{s['from_name']} can't evolve into {s['to_name']} before the National Dex (postgame)")
            else:
                todo.append(s["to_species_id"])
    return out


def assess_candidates(ctx: RequestContext, species: list[str]) -> dict:
    """Long-term value of several species for the rest of the run: final evolution and how/when
    it's reached, final-form stats, how it matches up against every remaining battle, and what it
    adds to (or duplicates in) the current party."""
    if not species:
        raise ToolError("give one or more species names")
    cur = ctx.cursor()
    opps, notes = remaining_opponents(ctx)
    party_types: set[str] = set()
    for m in ctx.state.party:
        sid = resolve(ctx, m.species, "species")
        r = rows(cur, "SELECT type1, type2 FROM species WHERE identifier = ?", [sid])[0]
        party_types |= {t for t in (r["type1"], r["type2"]) if t}
    covered_by_party = {
        i for i, o in enumerate(opps) if any(effectiveness(t, o["types"]) >= 2 for t in party_types)
    }
    out = []
    for name in species[:6]:
        sid = resolve(ctx, name, "species")
        base = rows(cur, "SELECT species_id, name, is_legendary, is_mythical, source_id FROM species WHERE identifier = ?", [sid])[0]
        gated = gated_evolutions(ctx, base["species_id"])
        for final_id, path in final_forms(cur, base["species_id"], ctx.game.evolution_limit)[:2]:
            f = rows(
                cur,
                "SELECT name, type1, type2, hp, attack, defense, sp_attack, sp_defense, speed, bst, ability1, ability2, "
                "source_id FROM species WHERE species_id = ?",
                [final_id],
            )[0]
            types = [t for t in (f["type1"], f["type2"]) if t]
            strong_into, risky_into = Counter(), Counter()
            adds = 0
            for i, o in enumerate(opps):
                if any(effectiveness(t, o["types"]) >= 2 for t in types):
                    strong_into[o["battle"]] += 1
                    if i not in covered_by_party:
                        adds += 1
                if any(effectiveness(a, types) >= 2 for a in o["attack_types"]):
                    risky_into[o["battle"]] += 1
            out.append({
                "candidate": base["name"], "final_form": f["name"], "final_types": types,
                "final_bst": f["bst"],
                "final_stats": {k: f[k] for k in ("hp", "attack", "defense", "sp_attack", "sp_defense", "speed")},
                "abilities": [a for a in (f["ability1"], f["ability2"]) if a],
                "evolution_path": [f"{s['to_name']}: {evolution_text(s)}" for s in path],
                "needs_trade": any(s["needs_trade"] for s in path),
                **({"evolutions_not_available": gated} if gated else {}),
                "legendary": bool(base["is_legendary"] or base["is_mythical"]),
                "remaining_opponents_hit_super_effectively": sum(strong_into.values()),
                "of_remaining_opponents": len(opps),
                "new_coverage_vs_party": adds,
                "shares_types_with_party": sorted(set(types) & party_types),
                "strongest_into": [b for b, _ in strong_into.most_common(4)],
                "most_threatened_by": [b for b, _ in risky_into.most_common(3)],
                "source_ids": [base["source_id"], f["source_id"], TYPE_CHART_SOURCE] + [s["source_id"] for s in path],
            })
    return {
        "candidates": out,
        "party_types": sorted(party_types),
        "note": "Coverage counts use the final form's own types (STAB) against every remaining story opponent. "
                "needs_trade means it can't evolve in a single-player run.",
        "notes": notes,
    }
