"""Species, move, learnset and TM tools (PLAN.md §5)."""

import re

from build.parse_decomp_trainers import default_moves

from agent.context import RequestContext
from agent.tools.common import ToolError, battle, resolve, rows, unread

GYM_GIFT_RE = re.compile(r"after defeating (TRAINER_\w+)")


def evolution_text(e: dict) -> str:
    parts = [e["trigger"]]
    for key, label in (("min_level", "level"), ("item", "item"), ("held_item", "holding"),
                       ("min_happiness", "friendship >="), ("min_beauty", "beauty >=")):
        if e[key] is not None:
            parts.append(f"{label} {e[key]}")
    if e["time_of_day"]:
        parts.append(e["time_of_day"])
    if e["relative_physical_stats"] is not None:
        parts.append({1: "Atk > Def", 0: "Atk = Def", -1: "Atk < Def"}[e["relative_physical_stats"]])
    if e["note"]:
        parts.append(e["note"])
    return ", ".join(parts)


def species_info(ctx: RequestContext, name: str) -> dict:
    """Gen 3 types, base stats, abilities, legendary status and evolutions for one species."""
    sid = resolve(ctx, name, "species")
    cur = ctx.cursor()
    s = rows(
        cur,
        "SELECT name, type1, type2, hp, attack, defense, sp_attack, sp_defense, speed, bst, ability1, ability2, "
        "is_legendary, is_mythical, growth_rate, source_id FROM species WHERE identifier = ?",
        [sid],
    )[0]
    evos = rows(
        cur,
        "SELECT f.name AS from_name, t.name AS to_name, e.* FROM evolutions e "
        "JOIN species f ON f.species_id = e.from_species_id JOIN species t ON t.species_id = e.to_species_id "
        "WHERE f.identifier = ? OR t.identifier = ?",
        [sid, sid],
    )
    return {
        "species": s["name"], "types": [t for t in (s["type1"], s["type2"]) if t],
        "base_stats": {k: s[k] for k in ("hp", "attack", "defense", "sp_attack", "sp_defense", "speed", "bst")},
        "abilities": [a for a in (s["ability1"], s["ability2"]) if a],
        "legendary_or_mythical": bool(s["is_legendary"] or s["is_mythical"]), "growth_rate": s["growth_rate"],
        "evolutions": [{"from": e["from_name"], "to": e["to_name"], "how": evolution_text(e), "source_id": e["source_id"]} for e in evos],
        "source_id": s["source_id"],
    }


def move_info(ctx: RequestContext, name: str) -> dict:
    """Gen 3 type, category, power, accuracy, PP and description of one move."""
    mid = resolve(ctx, name, "move")
    if why := unread(ctx, "move_data"):
        raise ToolError(why)
    m = rows(
        ctx.cursor(),
        "SELECT name, type, damage_class, power, accuracy, pp, priority, effect_chance, description, source_id "
        "FROM moves WHERE identifier = ?",
        [mid],
    )[0]
    if m["damage_class"] == "varies":
        m["category_note"] = "Its type is set in battle (IVs for Hidden Power, weather for Weather Ball) and the category follows that type."
    return m


def learnset(ctx: RequestContext, species: str, max_level: int | None = None) -> dict:
    """Level-up moves up to max_level (plus the next few), the default moveset at that level,
    TM/HM compatibility and Hoenn move-tutor compatibility."""
    sid = resolve(ctx, species, "species")
    cur = ctx.cursor()
    level_up = rows(
        cur,
        "SELECT l.level, m.identifier, m.name, m.type, m.damage_class, m.power, l.source_id FROM learnsets l "
        "JOIN moves m USING (move_id) JOIN species s USING (species_id) "
        "WHERE s.identifier = ? AND l.method = 'level-up' ORDER BY l.level, l.level_order",
        [sid],
    )
    cap = max_level or 100
    known = default_moves([(r["level"], r["identifier"]) for r in level_up], cap)
    names = {r["identifier"]: r["name"] for r in level_up}
    machines = rows(
        cur,
        "SELECT DISTINCT mc.label, mc.machine_number, m.name, m.type, m.damage_class, m.power, l.source_id "
        "FROM learnsets l JOIN machines mc USING (move_id) JOIN moves m USING (move_id) JOIN species s USING (species_id) "
        "WHERE s.identifier = ? AND l.method = 'machine' ORDER BY mc.machine_number",
        [sid],
    )
    tutors = rows(
        cur,
        "SELECT DISTINCT m.name, m.type, t.location, l.source_id FROM learnsets l JOIN move_tutors t USING (move_id) "
        "JOIN moves m USING (move_id) JOIN species s USING (species_id) WHERE s.identifier = ? AND l.method = 'tutor'",
        [sid],
    )
    upto = [r for r in level_up if r["level"] <= cap]
    out = {
        "species": sid, "max_level": max_level,
        "level_up": [{k: r[k] for k in ("level", "name", "type", "damage_class", "power", "source_id")} for r in upto],
        "next_level_up": [{k: r[k] for k in ("level", "name", "type", "source_id")} for r in level_up if r["level"] > cap][:4],
        "default_moveset_at_level": [names[m] for m in known],
        "tm_hm": [{k: r[k] for k in ("label", "name", "type", "damage_class", "power", "source_id")} for r in machines],
        "hoenn_tutors": tutors,
    }
    # A randomized run whose log changed parts Lockesmith doesn't read: say so instead of answering from vanilla
    unknown = {}
    for kind, keys in (("movesets", ("level_up", "next_level_up", "default_moveset_at_level")),
                       ("tm_compatibility", ("tm_hm",)), ("tutor_compatibility", ("hoenn_tutors",))):
        if why := unread(ctx, kind):
            unknown[kind] = why
            for k in keys:
                out[k] = []
    if why := unread(ctx, "move_data"):
        unknown["move_data"] = why + " (the types and powers listed are vanilla)"
    if unknown:
        out["unknown"] = unknown
    return out


def moves_outlook(ctx: RequestContext, species: list[str], before_battle: str | None = None,
                  level: int | None = None) -> dict:
    """For several species at once: the attacking moves each has by the battle (level-up, at
    `level` or the battle's top opponent level), its next evolution, and the strongest compatible
    TMs obtainable before the battle."""
    if not species:
        raise ToolError("give one or more species names")
    from agent.tools.battles import team  # battles -> moves would be circular at import time

    b = battle(ctx, before_battle)
    target = level
    if target is None:
        try:
            target = max(m["level"] for m in team(ctx, b)[0])
        except ToolError:
            target = 50
    out = []
    for name in species[:6]:
        sid = resolve(ctx, name, "species")
        ls = learnset(ctx, sid, target)
        attacks = [m for m in ls["level_up"] if m["power"] and m["damage_class"] != "status"]
        attacks.sort(key=lambda m: -(m["power"] or 0))
        avail = tm_availability(ctx, b.id, sid)["available"]
        tms_here = sorted((t for t in avail if t.get("power")), key=lambda t: -t["power"])[:4]
        info = species_info(ctx, sid)
        nxt = [e for e in info["evolutions"] if e["from"] == info["species"]]
        out.append({
            "species": info["species"], "types": info["types"], "at_level": target,
            "default_moveset": ls["default_moveset_at_level"],
            "best_level_up_attacks": [f"{m['name']} ({m['type']}, {m['damage_class']}, {m['power']}) Lv{m['level']}" for m in attacks[:4]],
            "next_level_up": [f"{m['name']} Lv{m['level']}" for m in ls["next_level_up"][:2]],
            "evolves": [f"{e['to']}: {e['how']}" for e in nxt],
            "tms_obtainable_before": [f"{t['label']} {t['move']} ({t['type']}, {t['power']}) at {t.get('location')}"
                                      + (f" [requires: {t['requires']}]" if t.get("requires") else "") for t in tms_here],
            "source_ids": [m["source_id"] for m in attacks[:4]] + [t["source_id"] for t in tms_here]
                          + [e["source_id"] for e in nxt] + [info["source_id"]],
        } | ({"unknown": ls["unknown"]} if "unknown" in ls else {}))
    return {"before_battle": b.id, "label": b.label, "species": out,
            "note": "Gen III: the category comes from the move's type (Dark/Fire/Water/... special; Ghost/Fighting/... physical)."}


def location_reachable(ctx: RequestContext, battle_id: str, location: str) -> bool:
    """Any area of the location reachable before the battle."""
    return any(spec[0] == location for spec in ctx.prog.areas_reachable(battle_id))


def tm_availability(ctx: RequestContext, before_battle: str | None = None, species: str | None = None) -> dict:
    """TMs/HMs obtainable before a battle and where; optionally only those a species can learn."""
    b = battle(ctx, before_battle)
    cur = ctx.cursor()
    sql = (
        "SELECT tl.label, m.name AS move, m.type, m.damage_class, m.power, tl.method, tl.location, tl.detail, "
        "tl.requires, tl.source_id FROM tm_locations tl JOIN machines mc ON mc.label = tl.label JOIN moves m USING (move_id)"
    )
    params = []
    compat_unknown = unread(ctx, "tm_compatibility")
    if species and not compat_unknown:
        sid = resolve(ctx, species, "species")
        sql += (" WHERE mc.move_id IN (SELECT l.move_id FROM learnsets l JOIN species s USING (species_id) "
                "WHERE s.identifier = ? AND l.method = 'machine')")
        params.append(sid)
    gym_order = {const: bt.order for bt in ctx.prog.battles for const in (bt.trainer_consts or ())}
    available, later = [], 0
    for r in rows(cur, sql + " ORDER BY mc.machine_number", params):
        gym = GYM_GIFT_RE.search(r["detail"] or "")
        if gym:
            ok = gym_order.get(gym.group(1), 99) < b.order
        else:
            ok = r["location"] is not None and location_reachable(ctx, b.id, r["location"])
        if not ok:
            later += 1
            continue
        available.append({k: v for k, v in r.items() if v is not None})
    out = {
        "before_battle": b.id, "label": b.label, "available": available, "not_yet_available": later,
        "note": "`requires` lists conditions beyond reaching the place (an HM, a key, a side quest, a party condition).",
        "source_ids": [f"progression:{b.id}"],
    }
    if species and compat_unknown:
        out["unknown"] = {"tm_compatibility": compat_unknown + f"; these are all TMs, not only ones {species} can learn"}
    return out
