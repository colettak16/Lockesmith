"""Encounter tools: what can be caught before a battle, and the odds in one area (PLAN.md §5).

Availability = the area is reachable before the battle (progression.yaml, method-aware)
AND the method is usable then (Surf, rods, Dive, Rock Smash, Devon Scope) AND the
player's rules allow it (single type, no legendaries, bans, Nuzlocke used areas, dupes,
wild only) AND the player hasn't rejected the species this session.
"""

from collections import defaultdict

from agent.context import RequestContext
from agent.tools.common import NOT_WILD, ToolError, battle, method_open, resolve, rows

ENCOUNTER_SQL = """
    SELECT e.location, e.area, e.method, e.rarity, e.min_level, e.max_level, e.conditions, e.source_id,
           s.identifier, s.name, s.type1, s.type2, s.is_legendary, s.is_mythical, s.evolution_chain_id,
           l.name AS location_name
    FROM encounters e JOIN species s USING (species_id) JOIN locations l ON l.identifier = e.location
"""
POSTGAME_CONDITIONS = {"story-progress-hall-of-fame"}
# Condition -> the area that has to be reachable first, and what to tell the player
CONDITION_GATES = {
    "item-claw-fossil": ("mirage-tower", "needs the Claw Fossil from Mirage Tower (you get the Claw or the Root, not both)"),
    "item-root-fossil": ("mirage-tower", "needs the Root Fossil from Mirage Tower (you get the Claw or the Root, not both)"),
}
MAX_SPECIES = 30
# Methods drawn from a slot table, where summed slot rarity is a real percentage
SLOT_METHODS = {"walk", "surf", "old-rod", "good-rod", "super-rod", "rock-smash", "seaweed", "feebas-tile-fishing"}


def _norm(text: str) -> str:
    return text.strip().lower().replace(" ", "-")


def rule_filter(ctx: RequestContext, cur):
    """A function (row) -> reason it's excluded by the player's rules, or None."""
    rules = ctx.state.ruleset
    banned = {resolve(ctx, s, "species") for s in rules.banned_species} | set(ctx.excluded_species)
    used = {_norm(r) for r in rules.used_routes}
    party_chains = set()
    if rules.dupes_clause and ctx.state.party:
        ids = [resolve(ctx, m.species, "species") for m in ctx.state.party]
        party_chains = {
            c for (c,) in cur.execute(
                f"SELECT evolution_chain_id FROM species WHERE identifier IN ({', '.join('?' * len(ids))})", ids
            ).fetchall()
        }
    mono = rules.monotype.lower() if rules.monotype else None

    def check(r: dict) -> str | None:
        if r["identifier"] in banned:
            return "banned or rejected by the player"
        if mono and mono not in (r["type1"], r["type2"]):
            return f"not {mono}-type"
        if rules.no_legendaries and (r["is_legendary"] or r["is_mythical"]):
            return "legendary/mythical"
        if rules.wild_only and r["method"] in NOT_WILD:
            return "not a wild catch"
        if used and (_norm(r["location"]) in used or _norm(r["location_name"]) in used):
            return "Nuzlocke: this area's encounter is used"
        if r["evolution_chain_id"] in party_chains:
            return "dupes clause: family already in the party"
        return None

    return check


def catchable(ctx: RequestContext, before_battle: str | None = None, species: str | None = None,
              types: list[str] | None = None) -> dict:
    """Species obtainable before a battle, with where, how, levels and slot odds; optionally only
    species with any of `types`."""
    b = battle(ctx, before_battle)
    wanted = {t.strip().lower() for t in types or [] if t.strip()}
    cur = ctx.cursor()
    target = resolve(ctx, species, "species") if species else None
    excluded_by_rule = rule_filter(ctx, cur)
    found: dict[str, dict] = {}
    blocked: dict[str, list[str]] = defaultdict(list)
    removed: dict[str, int] = defaultdict(int)
    for r in rows(cur, ENCOUNTER_SQL):
        if target and r["identifier"] != target:
            continue
        if wanted and not wanted & {r["type1"], r["type2"]}:
            continue
        where = r["location"] + (f"/{r['area']}" if r["area"] else "")
        if r["location"] == "hoenn-route-101" and r["method"] == "gift":
            continue  # Birch's starter choice, already made (the run state's starter)
        needs = next((CONDITION_GATES[c] for c in r["conditions"] if c in CONDITION_GATES), None)
        if needs and not ctx.prog.is_reachable(b.id, needs[0], None):
            blocked[r["name"]].append(f"{where} {r['method']}: {needs[1]}, not reachable before {b.label}")
            continue
        if POSTGAME_CONDITIONS & set(r["conditions"]) or ctx.prog.never_reason(r["location"], r["area"], r["method"]):
            blocked[r["name"]].append(f"{where} {r['method']}: postgame or event only")
            continue
        if not ctx.prog.is_reachable(b.id, r["location"], r["area"], r["method"]):
            blocked[r["name"]].append(f"{where} {r['method']}: not reachable before {b.label}")
            continue
        closed = method_open(r["method"], b)
        if closed:
            blocked[r["name"]].append(f"{where} {r['method']}: {closed}")
            continue
        reason = excluded_by_rule(r)
        if reason:
            removed[reason] += 1
            continue
        sp = found.setdefault(
            r["identifier"],
            {"species": r["name"], "types": [t for t in (r["type1"], r["type2"]) if t], "places": {}},
        )
        key = (where, r["method"])
        place = sp["places"].setdefault(
            key,
            {"where": (r["location_name"] or r["location"]) + (f" ({r['area']})" if r["area"] else ""), "method": r["method"],
             "lv": [r["min_level"], r["max_level"]], "rate_pct": 0, "source_id": r["source_id"]},
        )
        if r["conditions"]:
            place["conditions"] = list(r["conditions"])
        if needs:
            place["note"] = needs[1]
        place["rate_pct"] += r["rarity"] or 0
        place["lv"] = [min(place["lv"][0], r["min_level"]), max(place["lv"][1], r["max_level"])]
    species_out = []
    for sp in found.values():
        for p in sp["places"].values():
            if p["method"] not in SLOT_METHODS:  # one-off encounters: a count, not a slot rate
                p["count"] = p.pop("rate_pct") // 100 or 1
        # slot-table places first (by odds), then one-off encounters (Devon Scope, statics, gifts, trades)
        places = sorted(sp.pop("places").values(), key=lambda p: (p["method"] not in SLOT_METHODS, -p.get("rate_pct", 0)))
        sp["places"] = places[:3]
        sp["wild"] = places[0]["method"] in SLOT_METHODS
        species_out.append(sp)
    species_out.sort(key=lambda s: (not s["wild"], -s["places"][0].get("rate_pct", 0), s["species"]))
    result = {
        "before_battle": b.id, "label": b.label,
        "hms_usable": list(b.hm_gates_open), "key_items": list(b.key_items),
        "species_count": len(species_out), "species": species_out[:MAX_SPECIES],
        "excluded_by_rules": dict(removed), "source_ids": [f"progression:{b.id}"],
    }
    if len(species_out) > MAX_SPECIES:
        result["note"] = f"Showing {MAX_SPECIES} of {len(species_out)}; pass types or species to narrow."
    if target and not found:
        result["why_not"] = blocked.get(next(iter(blocked), ""), [])[:6] or ["no Emerald encounter for this species"]
    return result


def encounter_odds(ctx: RequestContext, location: str, method: str | None = None) -> dict:
    """Slot odds per species for one location (all of it, or one method). In a Nuzlocke these are
    the chances that the area's first encounter is each species."""
    loc = resolve(ctx, location, "location")
    cur = ctx.cursor()
    sql = ENCOUNTER_SQL + " WHERE e.location = ?" + (" AND e.method = ?" if method else "")
    data = rows(cur, sql, [loc, method] if method else [loc])
    if not data:
        raise ToolError(f"no Emerald encounters at {location!r}" + (f" by {method}" if method else ""))
    groups: dict[tuple, dict] = {}
    for r in data:
        g = groups.setdefault(
            (r["area"], r["method"], r["name"]),
            {"area": r["area"], "method": r["method"], "species": r["name"], "slot_rate_pct": 0,
             "min_level": r["min_level"], "max_level": r["max_level"], "conditions": list(r["conditions"]), "source_ids": []},
        )
        g["slot_rate_pct"] += r["rarity"] or 0
        g["min_level"], g["max_level"] = min(g["min_level"], r["min_level"]), max(g["max_level"], r["max_level"])
        if len(g["source_ids"]) < 2:
            g["source_ids"].append(r["source_id"])
    out = sorted(groups.values(), key=lambda g: (str(g["area"]), g["method"], -g["slot_rate_pct"]))
    return {"location": loc, "encounters": out, "note": "Slot odds once an encounter happens; how often one happens is a separate per-area rate."}
