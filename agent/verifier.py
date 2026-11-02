"""Verifier: deterministic checks on the Lead's draft, no LLM (PLAN.md §6, D8).

Every recommendation and every backup is checked against the data: obtainable before its
battle, evolution reachable in time, key moves learnable by then, the player's rules, Gen III
facts, and citations. Errors send the pick back (a passing backup is promoted, otherwise the
Lead gets one repair round); warnings go to the Writer.
"""

import re
from dataclasses import asdict, dataclass

from agent.context import RequestContext
from agent.schemas import Alternative, LeadDraft, Recommendation
from agent.tools.common import NOT_WILD, ToolError, battle, rows
from agent.tools.battles import team
from agent.tools.encounters import _norm, area_used, available_rows
from agent.tools.moves import location_reachable
from agent.tools.outlook import final_forms

ERROR, WARNING = "error", "warning"
CODES = {
    "NOT_OBTAINABLE_BEFORE": "not catchable in areas reachable before the battle",
    "EVOLUTION_NOT_REACHABLE": "relies on an evolution not achievable in time",
    "EVOLUTION_ITEM_UNVERIFIED": "relies on an evolution item whose availability isn't checked",
    "MOVE_NOT_LEARNABLE": "relies on a move not learnable by then",
    "GEN3_SPLIT_MISMATCH": "the move's category doesn't suit the Pokémon's stronger attacking stat",
    "GEN3_ANACHRONISM": "mentions something that isn't in Generation III",
    "NUZLOCKE_ROUTE_USED": "every place to get it is an area whose encounter is used",
    "NUZLOCKE_DUPE": "the dupes clause forbids it",
    "RULESET_TYPE_VIOLATION": "breaks the single-type rule",
    "RULESET_BANNED": "the player banned it",
    "RULESET_REJECTED": "the player rejected it this session",
    "RULESET_NO_LEGENDARIES": "legendary or mythical, which the player's rules forbid",
    "RULESET_WILD_ONLY": "only obtainable as a gift, static encounter or trade",
    "OVER_LEVEL_CAP": "relies on a level above the level cap",
    "UNCITED_CLAIM": "has no source ids",
    "CITATION_NOT_IN_EVIDENCE": "cites ids that no tool returned",
}
LEVEL_TOLERANCE = 5  # without caps, a plan may expect the player a few levels above the battle's ace


@dataclass
class Violation:
    code: str
    severity: str
    species: str
    detail: str
    rec: int | None = None  # index of the recommendation
    alt: int | None = None  # index of the backup within it, if the problem is with a backup

    def to_dict(self) -> dict:
        return asdict(self)


def level_limit(ctx: RequestContext, battle_id: str) -> tuple[int | None, bool]:
    """(level the plan may rely on by the battle, whether that's a hard level cap)."""
    b = ctx.prog.get(battle_id)
    try:
        ace = max(m["level"] for m in team(ctx, b)[0])
    except ToolError:
        return None, False
    rules = ctx.state.ruleset
    if rules.level_caps:
        return ace + rules.level_cap_offset, True
    return ace + LEVEL_TOLERANCE, False


def species_row(cur, identifier: str) -> dict:
    return rows(
        cur,
        "SELECT species_id, identifier, name, type1, type2, attack, sp_attack, is_legendary, is_mythical, "
        "evolution_chain_id FROM species WHERE identifier = ?",
        [identifier],
    )[0]


def evolution_path(cur, start_id: int, target_id: int) -> list[dict] | None:
    for final, path in final_forms(cur, start_id):
        for i, step in enumerate(path):
            if step["to_species_id"] == target_id:
                return path[: i + 1]
    return None


def move_learnable(ctx: RequestContext, cur, species_ids: list[int], move_id: int, battle_id: str, limit: int | None) -> str | None:
    """How the line can know the move by the battle, or None."""
    marks = ", ".join("?" * len(species_ids))
    learned = rows(
        cur,
        f"SELECT method, min(level) AS level FROM learnsets WHERE species_id IN ({marks}) AND move_id = ? GROUP BY method",
        [*species_ids, move_id],
    )
    by_method = {r["method"]: r["level"] for r in learned}
    if "level-up" in by_method and (limit is None or by_method["level-up"] <= limit):
        return f"level-up at {by_method['level-up']}"
    if "machine" in by_method:
        for tm in rows(cur, "SELECT tl.label, tl.location, tl.detail FROM machines m JOIN tm_locations tl USING (label) WHERE m.move_id = ?", [move_id]):
            gym = re.search(r"after defeating (TRAINER_\w+)", tm["detail"] or "")
            if gym:
                gym_battle = next((bt for bt in ctx.prog.battles if gym.group(1) in (bt.trainer_consts or ())), None)
                if gym_battle and gym_battle.order < ctx.prog.get(battle_id).order:
                    return f"{tm['label']} (gym reward)"
            elif tm["location"] and location_reachable(ctx, battle_id, tm["location"]):
                return f"{tm['label']} at {tm['location']}"
    if "tutor" in by_method:
        for t in rows(cur, "SELECT location FROM move_tutors WHERE move_id = ?", [move_id]):
            if t["location"] and location_reachable(ctx, battle_id, t["location"]):
                return f"tutor at {t['location']}"
    if "level-up" in by_method:
        return None  # learned by level-up, but only above the limit (reported by the caller)
    return None


def check_pick(ctx: RequestContext, pick: Recommendation | Alternative, battle_id: str, rec: int, alt: int | None) -> list[Violation]:
    out: list[Violation] = []

    def add(code: str, detail: str, severity: str = ERROR) -> None:
        out.append(Violation(code, severity, pick.species, detail, rec, alt))

    cur = ctx.cursor()
    rules = ctx.state.ruleset
    text = f"{pick.why} {pick.long_term}"
    if re.search(r"\bfairy\b", text, re.I):
        add("GEN3_ANACHRONISM", "mentions the Fairy type, which Gen III doesn't have")
    match = ctx.index.resolve(pick.species, "species", cutoff=88)
    if match is None:
        add("GEN3_ANACHRONISM", f"{pick.species!r} isn't one of the 386 Gen III species")
        return out
    sp = species_row(cur, match.id)
    form = sp
    path = []
    if pick.evolve_to and _norm(pick.evolve_to) != _norm(sp["name"]):
        target = ctx.index.resolve(pick.evolve_to, "species", cutoff=88)
        if target is None:
            add("GEN3_ANACHRONISM", f"{pick.evolve_to!r} isn't one of the 386 Gen III species")
        else:
            form = species_row(cur, target.id)
            path = evolution_path(cur, sp["species_id"], form["species_id"])
            if path is None:
                add("EVOLUTION_NOT_REACHABLE", f"{sp['name']} doesn't evolve into {form['name']}")
                path = []

    # --- the player's rules -------------------------------------------------------------
    banned = {ctx.index.resolve(b, "species", cutoff=80) for b in rules.banned_species}
    if any(b and b.id == sp["identifier"] for b in banned):
        add("RULESET_BANNED", f"{sp['name']} is on the player's banned list")
    if sp["identifier"] in ctx.excluded_species:
        add("RULESET_REJECTED", f"the player rejected {sp['name']} earlier in this session")
    if rules.no_legendaries and (sp["is_legendary"] or sp["is_mythical"]):
        add("RULESET_NO_LEGENDARIES", f"{sp['name']} is legendary or mythical")
    if rules.monotype:
        mono = rules.monotype.lower()
        if mono not in (sp["type1"], sp["type2"]):
            add("RULESET_TYPE_VIOLATION", f"{sp['name']} isn't {mono}-type")
        elif form is not sp and mono not in (form["type1"], form["type2"]):
            add("RULESET_TYPE_VIOLATION", f"{form['name']} loses the {mono} type")
    party_ids = [ctx.index.resolve(m.species, "species", cutoff=80) for m in ctx.state.party]
    party_ids = [p.id for p in party_ids if p]
    in_party = sp["identifier"] in party_ids
    if rules.dupes_clause and not in_party and party_ids:
        chains = {r["evolution_chain_id"] for r in rows(cur, f"SELECT evolution_chain_id FROM species WHERE identifier IN ({', '.join('?' * len(party_ids))})", party_ids)}
        if sp["evolution_chain_id"] in chains:
            add("NUZLOCKE_DUPE", f"{sp['name']}'s evolution family is already in the party")

    # --- obtainable before the battle ----------------------------------------------------------
    limit, hard_cap = level_limit(ctx, battle_id)
    b = ctx.prog.get(battle_id)
    if not in_party:
        places, blocked, _ = available_rows(ctx, b, sp["identifier"], apply_rules=False)
        if not places:
            why = next(iter(blocked.values()), ["no Emerald encounter"])[0]
            add("NOT_OBTAINABLE_BEFORE", f"{sp['name']} isn't obtainable before {b.label} ({why})")
        else:
            if rules.wild_only and all(p["method"] in NOT_WILD for p in places):
                add("RULESET_WILD_ONLY", f"{sp['name']} is only a gift, static encounter or trade before {b.label}")
            if rules.nuzlocke and rules.used_routes:
                used = {_norm(u) for u in rules.used_routes}
                free = [p for p in places if not (area_used(p, used, rules.encounter_scope)
                                                   and (rules.gifts_count_as_encounter or p["method"] not in NOT_WILD))]
                if not free:
                    add("NUZLOCKE_ROUTE_USED", f"every place to get {sp['name']} before {b.label} is a used area")
            if hard_cap and limit is not None and min(p["min_level"] for p in places) > limit:
                add("OVER_LEVEL_CAP", f"{sp['name']} is caught at Lv{min(p['min_level'] for p in places)}, above the cap of {limit}", WARNING)

    # --- evolution in time -------------------------------------------------------------
    for step in path:
        if step["needs_trade"]:
            add("EVOLUTION_NOT_REACHABLE", f"{step['to_name']} needs a trade, impossible in a single-player run")
        elif step["min_level"] is not None and limit is not None and step["min_level"] > limit:
            if hard_cap:
                add("OVER_LEVEL_CAP", f"{step['to_name']} needs Lv{step['min_level']}, above the level cap of {limit} for {b.label}")
            else:
                add("EVOLUTION_NOT_REACHABLE", f"{step['to_name']} needs Lv{step['min_level']}, well above {b.label}'s levels", WARNING)
        elif step["item"]:
            add("EVOLUTION_ITEM_UNVERIFIED", f"{step['to_name']} needs a {step['item']}; make sure you can get one before {b.label}", WARNING)

    # --- key moves -------------------------------------------------------------------
    line = [sp["species_id"]] + [s["to_species_id"] for s in path]
    for name in pick.key_moves:
        mv = ctx.index.resolve(name, "move", cutoff=88)
        if mv is None:
            add("GEN3_ANACHRONISM", f"{name!r} isn't a Gen III move")
            continue
        m = rows(cur, "SELECT move_id, name, type, damage_class, power FROM moves WHERE identifier = ?", [mv.id])[0]
        if move_learnable(ctx, cur, line, m["move_id"], battle_id, limit) is None:
            add("MOVE_NOT_LEARNABLE", f"{form['name']} can't know {m['name']} by {b.label}")
        if m["power"] and m["damage_class"] in ("physical", "special"):
            atk, spa = form["attack"], form["sp_attack"]
            if m["damage_class"] == "physical" and spa - atk >= 20 or m["damage_class"] == "special" and atk - spa >= 20:
                add("GEN3_SPLIT_MISMATCH",
                    f"{m['name']} is {m['damage_class']} in Gen III ({m['type']}), but {form['name']} has Attack {atk} and Sp. Atk {spa}",
                    WARNING)

    # --- citations -------------------------------------------------------------------
    if not pick.source_ids:
        add("UNCITED_CLAIM", "the pick has no source ids")
    missing = [s for s in pick.source_ids if s not in ctx.ledger]
    if missing:
        add("CITATION_NOT_IN_EVIDENCE", f"no tool returned {', '.join(missing[:3])}")
    return out


def verify(ctx: RequestContext, draft: LeadDraft) -> list[Violation]:
    out: list[Violation] = []
    for i, rec in enumerate(draft.recommendations):
        try:
            battle_id = battle(ctx, rec.before_battle or None).id
        except ToolError:
            battle_id = battle(ctx, None).id
        out += check_pick(ctx, rec, battle_id, i, None)
        for j, alt in enumerate(rec.alternatives):
            out += check_pick(ctx, alt, battle_id, i, j)
    for item in [*draft.steps, *draft.battle_notes]:
        label = getattr(item, "title", None) or getattr(item, "battle_id", "")
        if not item.source_ids:
            out.append(Violation("UNCITED_CLAIM", ERROR, label, "has no source ids"))
        missing = [s for s in item.source_ids if s not in ctx.ledger]
        if missing:
            out.append(Violation("CITATION_NOT_IN_EVIDENCE", ERROR, label, f"no tool returned {', '.join(missing[:3])}"))
    return out


def errors_for(violations: list[Violation], rec: int, alt: int | None) -> list[Violation]:
    return [v for v in violations if v.severity == ERROR and v.rec == rec and v.alt == alt]


def promote_backups(draft: LeadDraft, violations: list[Violation]) -> tuple[LeadDraft, list[str], list[int]]:
    """Drop failing backups; replace a failing pick with its first passing backup. Returns the new
    draft, what was changed (for the trace and the Writer), and indexes of picks with no passing backup."""
    actions, unfixed, recs = [], [], []
    for i, rec in enumerate(draft.recommendations):
        good_alts = [a for j, a in enumerate(rec.alternatives) if not errors_for(violations, i, j)]
        dropped = [a.species for j, a in enumerate(rec.alternatives) if errors_for(violations, i, j)]
        if dropped:
            actions.append(f"dropped backup(s) {', '.join(dropped)} for {rec.species}")
        problems = errors_for(violations, i, None)
        if not problems:
            recs.append(rec.model_copy(update={"alternatives": good_alts}))
            continue
        reason = "; ".join(f"{v.code}: {v.detail}" for v in problems[:2])
        if good_alts:
            alt, rest = good_alts[0], good_alts[1:]
            recs.append(Recommendation(
                species=alt.species, role=rec.role, horizon=alt.horizon, before_battle=rec.before_battle,
                where=alt.where, when=rec.when, why=alt.why, long_term=alt.long_term, evolve_to=alt.evolve_to,
                key_moves=alt.key_moves, source_ids=alt.source_ids, alternatives=rest,
            ))
            actions.append(f"replaced {rec.species} with its backup {alt.species} ({reason})")
        else:
            recs.append(rec)
            unfixed.append(len(recs) - 1)
            actions.append(f"{rec.species} failed with no valid backup ({reason})")
    return draft.model_copy(update={"recommendations": recs}), actions, unfixed
