"""Verifier: deterministic checks on the Lead's draft, no LLM (PLAN.md §6, D8).

Every recommendation and every backup is checked against the data: obtainable before its
battle, evolution reachable in time, key moves learnable by then, the player's rules, Gen III
facts, and citations. Errors send the pick back (a passing backup is promoted, otherwise the
Lead gets one repair round); warnings go to the Writer. Finally `correct_places` rewrites any
"where" line (place, method, odds) that disagrees with the encounter data.
"""

import re
from dataclasses import asdict, dataclass

from agent.context import RequestContext
from agent.schemas import Alternative, LeadDraft, Recommendation
from agent.tools.common import NOT_WILD, ToolError, battle, effectiveness, rows, unread
from agent.tools.battles import team
from agent.tools.encounters import _norm, area_used, available_rows
from agent.tools.moves import location_reachable
from agent.tools.outlook import TYPES, final_forms

ERROR, WARNING = "error", "warning"
CODES = {
    "NOT_OBTAINABLE_BEFORE": "not catchable in areas reachable before the battle",
    "EVOLUTION_NOT_REACHABLE": "relies on an evolution not achievable in time",
    "EVOLUTION_ITEM_UNVERIFIED": "relies on an evolution item whose availability isn't checked",
    "MOVE_NOT_LEARNABLE": "relies on a move not learnable by then",
    "MOVE_UNVERIFIABLE": "relies on a move whose learnability the randomizer log changed in a part LockeSmith can't read",
    "GEN3_SPLIT_MISMATCH": "the move's category doesn't suit the Pokémon's stronger attacking stat",
    "GEN3_ANACHRONISM": "mentions something that isn't in Generation III",
    "TYPE_CLAIM_WRONG": "states a type matchup that the Gen III type chart and abilities contradict",
    "NUZLOCKE_ROUTE_USED": "every place to get it is an area whose encounter is used",
    "NUZLOCKE_DUPE": "the dupes clause forbids it",
    "RULESET_TYPE_VIOLATION": "breaks the player's allowed or banned types",
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
        "SELECT species_id, identifier, name, type1, type2, ability1, ability2, attack, sp_attack, is_legendary, "
        "is_mythical, evolution_chain_id FROM species WHERE identifier = ?",
        [identifier],
    )[0]


def evolution_path(cur, start_id: int, target_id: int) -> list[dict] | None:
    for final, path in final_forms(cur, start_id):
        for i, step in enumerate(path):
            if step["to_species_id"] == target_id:
                return path[: i + 1]
    return None


LEARN_KINDS = {"level-up": "movesets", "machine": "tm_compatibility", "tutor": "tutor_compatibility"}


def move_learnable(ctx: RequestContext, cur, species_ids: list[int], move_id: int, battle_id: str, limit: int | None) -> str | None:
    """How the line can know the move by the battle, or None."""
    marks = ", ".join("?" * len(species_ids))
    learned = rows(
        cur,
        f"SELECT method, min(level) AS level FROM learnsets WHERE species_id IN ({marks}) AND move_id = ? GROUP BY method",
        [*species_ids, move_id],
    )
    # In a randomized run, a method whose data the log changed unreadably can't vouch for the move
    skip = {m for m, kind in LEARN_KINDS.items() if unread(ctx, kind)}
    by_method = {r["method"]: r["level"] for r in learned if r["method"] not in skip}
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
    if why := rules.type_problem([sp["type1"], sp["type2"]]):
        add("RULESET_TYPE_VIOLATION", f"{sp['name']} is {why}")
    elif form is not sp and (why := rules.type_problem([form["type1"], form["type2"]])):
        add("RULESET_TYPE_VIOLATION", f"{form['name']}, its evolution, is {why}")
    # The party and the Pokémon the player has in the PC are already caught: no need to obtain them,
    # and for a dupes clause their families count
    party_ids = [ctx.index.resolve(n, "species", cutoff=80) for n in [m.species for m in ctx.state.party] + ctx.state.owned]
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
            why = next(iter(blocked.values()), [f"no {ctx.game.short} encounter"])[0]
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
    dex_limit = ctx.game.evolution_limit
    for step in path:
        if dex_limit is not None and step["to_species_id"] > dex_limit:
            add("EVOLUTION_NOT_REACHABLE", f"{step['to_name']} is past #{dex_limit}: {ctx.game.short} cancels evolutions "
                "into it until the National Dex, which comes after the Hall of Fame")
        elif step["needs_trade"]:
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
            gaps = [why for why in (unread(ctx, kind) for kind in LEARN_KINDS.values()) if why]
            if gaps:
                add("MOVE_UNVERIFIABLE", f"can't check that {form['name']} can know {m['name']} by {b.label}: {gaps[0]}", WARNING)
            else:
                add("MOVE_NOT_LEARNABLE", f"{form['name']} can't know {m['name']} by {b.label}")
        if m["power"] and m["damage_class"] in ("physical", "special") and not unread(ctx, "move_data"):
            atk, spa = form["attack"], form["sp_attack"]
            if m["damage_class"] == "physical" and spa - atk >= 20 or m["damage_class"] == "special" and atk - spa >= 20:
                add("GEN3_SPLIT_MISMATCH",
                    f"{m['name']} is {m['damage_class']} in Gen III ({m['type']}), but {form['name']} has Attack {atk} and Sp. Atk {spa}",
                    WARNING)

    # --- type matchups it states ----------------------------------------------------------
    me = Target(form["name"], tuple(tuple(t for t in (r["type1"], r["type2"]) if t) for r in (sp, form)),
                frozenset(a for r in (sp, form) for a in (r["ability1"], r["ability2"]) if a))
    for detail in matchup_errors(ctx, text, me, frozenset({sp["name"], form["name"]})):
        add("TYPE_CLAIM_WRONG", detail, WARNING)

    # --- citations -------------------------------------------------------------------
    if not pick.source_ids:
        add("UNCITED_CLAIM", "the pick has no source ids")
    missing = [s for s in pick.source_ids if s not in ctx.ledger]
    # Only when nothing real is left: a pick citing real sources plus an invented id (a live Ruby run's
    # assess_candidates#Lanturn) keeps the real ones, and the pipeline strips the rest without a repair round
    if missing and len(missing) == len(pick.source_ids):
        add("CITATION_NOT_IN_EVIDENCE", f"no tool returned {', '.join(missing[:3])}")
    return out


# --- type matchups the draft states -----------------------------------------------------------
# Two shapes, in a pick's why/long-term text, the battle notes and the steps:
#   "Lanturn resists Ice", "it double-resists Water", "Whiscash is immune to Electric": a claim word,
#   then the types, about the Pokémon named before it (or the pick, for "it"/"its typing")
#   "Ice Beam hits Breloom for 4x damage", "Earthquake deals 2x damage to Manectric", "2x against
#   Electric types": a multiplier, read with the attack named before it and what it hits
# Abilities count (Levitate, Volt Absorb, Thick Fat, ...). A claim that holds for any reading of the
# sentence passes, so only clear mistakes are flagged.

TYPE_RE = "|".join(TYPES)
CLAIM_RE = re.compile(
    r"(?P<word>double[- ]resists?|resists?|resisting|immune to|immunity to|neutral to|neutral against|absorbs?|absorbing|"
    r"4x weak(?:ness)? to|quadruple weak(?:ness)? to|weak(?:ness)? to|(?:1/4x?|x?0\.25x?|a quarter)(?: damage)? from)"
    # a second type, unless it starts a move's name ("immune to Ground and Ice Beam is ...")
    rf"\s+(?:both\s+|all\s+)?(?P<t1>{TYPE_RE})(?:[- ]type)?(?:\s*(?:,|and|&|/|or)\s*(?P<t2>{TYPE_RE})(?-i:(?!\s+[A-Z])))?",
    re.I,
)
MULT_RE = re.compile(
    r"(?<![\w./])(?:(?P<num>4|2|1|0\.5|1/2|0\.25|1/4)\s?[x×](?!\w)|(?P<word>quadruple|double|half|quarter)(?= damage)"
    r"|(?P<se>super[- ]effective(?:ly)?)|(?P<nve>not very effective)|(?P<none>no effect)\b)",
    re.I,
)
MULT_KIND = {"4": "4x", "2": "2x", "1": "neutral", "0.5": "half", "1/2": "half", "0.25": "quarter", "1/4": "quarter",
             "quadruple": "4x", "double": "2x", "half": "half", "quarter": "quarter"}
# A type named as the attack: "Electric attacks", "Ice-type moves", "STAB Grass", "Ice does 2x to ..."
TYPE_ATTACK_RE = re.compile(
    rf"\b(?P<t>{TYPE_RE})(?:[- ]type)?\s+(?:attacks?|moves?|STAB)\b|\bSTAB\s+(?P<s>{TYPE_RE})\b"
    rf"|\b(?P<d>{TYPE_RE})\s+(?=(?:does|deals|hits)\b)",
    re.I,
)
TARGETS_RE = re.compile(r"\s*(?:damage\s+)?(?:to|against|on)\s+(?:both\s+|all\s+)?", re.I)  # "... 2x damage to"
OWNER_RE = re.compile(r"(?:[A-Z][\w.]*(?:'s|’s)\s+)?")  # "to Wallace's Milotic"
TYPE_TARGET_RE = re.compile(rf"(?P<a>{TYPE_RE})(?:\s*/\s*(?P<b>{TYPE_RE}))?(?P<suffix>[- ]types?|[- ]type Pokémon| Pokémon)?(?!\w)", re.I)
LIST_SEP_RE = re.compile(r"\s*(?:,\s*(?:and\s+|or\s+)?|and\s+|or\s+|&\s*)")
# A later item in "to Sceptile and Breloom." ends the list or continues it; "to Kingdra and Whiscash
# resists Ground" starts a new clause, so Whiscash isn't hit by the 2x
LIST_END_RE = re.compile(r"\s*(?:[.,;:!?)]|$|and\b|or\b|&)")
CLAIM_OK = {
    "quarter": lambda m: m == 0.25, "immune": lambda m: m == 0, "neutral": lambda m: m == 1,
    "resist": lambda m: m < 1, "4x": lambda m: m == 4, "weak": lambda m: m >= 2, "2x": lambda m: m == 2,
    "half": lambda m: m == 0.5, "super": lambda m: m >= 2, "not-very": lambda m: 0 < m < 1,
}
NOT_ABOUT_PICK = re.compile(r"\b(their|they|team|opponents?|enemy|foes?)\b", re.I)
PICK_SUBJECT = re.compile(r"\b(it|its|it's|typing)\b", re.I)
# What an ability does to an attacking type's multiplier in Gen III
ABILITY_EFFECT = {
    "levitate": lambda a, m: 0 if a == "ground" else m,
    "volt-absorb": lambda a, m: 0 if a == "electric" else m,
    "water-absorb": lambda a, m: 0 if a == "water" else m,
    "flash-fire": lambda a, m: 0 if a == "fire" else m,
    "thick-fat": lambda a, m: m / 2 if a in ("fire", "ice") else m,
    "wonder-guard": lambda a, m: m if m >= 2 else 0,
}
ABSORBS = {"volt-absorb": "electric", "water-absorb": "water", "flash-fire": "fire"}


def claim_kind(word: str) -> str:
    w = word.lower()
    for prefix, kind in (("double", "quarter"), ("1/4", "quarter"), ("x0.25", "quarter"), ("0.25", "quarter"),
                         ("a quarter", "quarter"), ("immun", "immune"), ("neutral", "neutral"), ("resist", "resist"),
                         ("absorb", "absorb"), ("4x", "4x"), ("quadruple", "4x")):
        if w.startswith(prefix):
            return kind
    return "weak"


def mult_kind(m: re.Match) -> str:
    if m["num"] or m["word"]:
        return MULT_KIND[(m["num"] or m["word"]).lower()]
    return "super" if m["se"] else "not-very" if m["nve"] else "immune"


def ability_name(identifier: str) -> str:
    return identifier.replace("-", " ").title()


@dataclass(frozen=True)
class Target:
    """What a matchup is stated about: a Pokémon (a pick counts as itself or its evolution) or a type."""
    name: str
    typings: tuple[tuple[str, ...], ...]
    abilities: frozenset[str] = frozenset()

    def takes(self, attack: str) -> list[float]:
        """Every multiplier `attack` can do to it, with each of its abilities."""
        out = []
        for types in self.typings:
            m = effectiveness(attack, list(types))
            out += [m] + [ABILITY_EFFECT[a](attack, m) for a in self.abilities if a in ABILITY_EFFECT]
        return out

    def holds(self, kind: str, attack: str) -> bool:
        if kind == "absorb":
            return any(ABSORBS.get(a) == attack for a in self.abilities)
        return any(CLAIM_OK[kind](m) for m in self.takes(attack))

    def actual(self, attack: str) -> str:
        """What `attack` really does to it, for the Writer."""
        types = list(self.typings[-1])
        chart = effectiveness(attack, types)
        out = f"{attack.title()} does {chart:g}x to {'/'.join(types).title()} in Gen III"
        changed = [f"{ABILITY_EFFECT[a](attack, chart):g}x with {ability_name(a)}" for a in sorted(self.abilities)
                   if a in ABILITY_EFFECT and ABILITY_EFFECT[a](attack, chart) != chart]
        return out + (f" ({'; '.join(changed)})" if changed else "")


_NAMES: dict[str, tuple[re.Pattern, dict[str, str], re.Pattern, dict[str, str]]] = {}


def name_patterns(ctx: RequestContext) -> tuple[re.Pattern, dict[str, str], re.Pattern, dict[str, str]]:
    """Regexes that find species and damaging-move names in free text, and name -> identifier.
    Case-sensitive: drafts capitalize names, and that keeps prose like "counter" or "return" out."""
    if ctx.game.id not in _NAMES:
        cur = ctx.cursor()
        species = {name: i for i, name in cur.execute("SELECT identifier, name FROM species").fetchall()}
        moves: dict[str, str] = {}
        for i, name in cur.execute(
            "SELECT identifier, name FROM moves WHERE power > 1 AND damage_class IN ('physical', 'special')"
        ).fetchall():
            moves[name] = i
            moves.setdefault(name.replace(" ", ""), i)  # the Gen III spellings: SolarBeam, ThunderPunch

        def pattern(names) -> re.Pattern:
            return re.compile(r"(?<!\w)(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")(?!\w)")
        _NAMES[ctx.game.id] = (pattern(species), species, pattern(moves), moves)
    return _NAMES[ctx.game.id]


def species_target(ctx: RequestContext, identifier: str) -> Target:
    r = rows(ctx.cursor(), "SELECT name, type1, type2, ability1, ability2 FROM species WHERE identifier = ?", [identifier])[0]
    return Target(r["name"], (tuple(t for t in (r["type1"], r["type2"]) if t),), frozenset(a for a in (r["ability1"], r["ability2"]) if a))


def matchup_errors(ctx: RequestContext, text: str, pick: Target | None = None, pick_names: frozenset[str] = frozenset()) -> list[str]:
    """What's wrong with each type matchup `text` states, as "says ..., but ..." for the Writer."""
    species_re, species_ids, move_re, move_ids = name_patterns(ctx)
    targets: dict[str, Target] = {}

    def named(name: str) -> Target:
        if name in pick_names and pick:
            return pick
        if name not in targets:
            targets[name] = species_target(ctx, species_ids[name])
        return targets[name]

    moves_ok = not unread(ctx, "move_data")
    out = []
    for sentence in re.split(r"(?<=[.;!?])\s+", text):
        masked = sentence
        for m in CLAIM_RE.finditer(sentence):
            before = sentence[: m.start()]
            cands = [named(s.group(1)) for s in species_re.finditer(before)]
            if pick and PICK_SUBJECT.search(before) and not NOT_ABOUT_PICK.search(before):
                cands.append(pick)
            masked = masked[: m.start()] + " " * (m.end() - m.start()) + masked[m.end():]  # not an attack below
            if not cands:
                continue
            kind, word = claim_kind(m["word"]), m["word"].lower()
            for attack in (t.lower() for t in (m["t1"], m["t2"]) if t):
                if not any(c.holds(kind, attack) for c in cands):
                    t = cands[-1]
                    out.append(f"says {t.name} \"{word} {attack.title()}\", but " + (
                        f"none of its abilities ({', '.join(ability_name(a) for a in sorted(t.abilities))}) absorbs {attack.title()}"
                        if kind == "absorb" else t.actual(attack)))

        attacks = []  # (start, end, label, type)
        if moves_ok:
            for mv in move_re.finditer(masked):
                row = rows(ctx.cursor(), "SELECT type FROM moves WHERE identifier = ?", [move_ids[mv.group(1)]])[0]
                attacks.append((mv.start(), mv.end(), mv.group(1), row["type"]))
        for ta in TYPE_ATTACK_RE.finditer(masked):
            t = (ta["t"] or ta["s"] or ta["d"]).lower()
            attacks.append((ta.start(), ta.end(), t.title(), t))
        attacks.sort()
        mentions = [(s.start(), s.end(), s.group(1)) for s in species_re.finditer(masked)
                    if not masked.startswith(("'s", "’s"), s.end())]  # "Milotic's Ice Beam": the attacker
        prev = 0
        for mm in MULT_RE.finditer(masked):
            since = [a for a in attacks if prev <= a[0] < mm.start()]
            used = since or [a for a in attacks if a[0] < mm.start()][-1:]
            if not used:
                prev = mm.end()
                continue
            hit, end = targets_after(sentence, mm.end(), species_re)  # unmasked: same positions, full clauses
            if not hit:  # "Ice Beam hits Breloom for 4x damage"
                start = max(prev, used[-1][1])
                hit = [("species", s[2]) for s in mentions if s[0] >= start and s[1] <= mm.start()]
            kind = mult_kind(mm)
            claim = (f"does {mm.group(0)}{' damage' if mm['word'] else ''} to" if mm["num"] or mm["word"]
                     else f"is {mm.group(0).lower()} against")
            for what, value in hit:
                t = named(value) if what == "species" else Target(f"{'/'.join(value).title()} types", (tuple(value),))
                if not any(t.holds(kind, a[3]) for a in used):
                    out.append(f"says {used[-1][2]} {claim} {t.name}, but {t.actual(used[-1][3])}")
            prev = max(mm.end(), end)
    return out


def targets_after(text: str, pos: int, species_re: re.Pattern) -> tuple[list[tuple[str, object]], int]:
    """What a multiplier says it hits, from "to/against ..." right after it: Pokémon or types."""
    lead = TARGETS_RE.match(text, pos)
    if not lead:
        return [], pos
    out, p, end = [], lead.end(), pos
    while True:
        q = OWNER_RE.match(text, p).end()
        if m := species_re.match(text, q):
            item = ("species", m.group(1))
        elif (m := TYPE_TARGET_RE.match(text, q)) and (m["suffix"] or m.group(0)[0].isupper()):
            item = ("types", [t.lower() for t in (m["a"], m["b"]) if t])
        else:
            break
        if out and not LIST_END_RE.match(text, m.end()):
            break
        out.append(item)
        end = m.end()
        sep = LIST_SEP_RE.match(text, end)
        if not sep:
            break
        p = sep.end()
    return out, end


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
        text = getattr(item, "note", None) or f"{getattr(item, 'title', '')}. {getattr(item, 'detail', '')}"
        out += [Violation("TYPE_CLAIM_WRONG", WARNING, label, d) for d in matchup_errors(ctx, text)]
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


# --- where to catch it ---------------------------------------------------------------------

METHOD_WORDS = {  # how a `where` line names an encounter method
    "old-rod": r"old rod", "good-rod": r"good rod", "super-rod": r"super rod", "surf": r"surf",
    "rock-smash": r"rock smash", "seaweed": r"seaweed|underwater|\bdiv(?:e|ing)\b",
    "walk": r"\bwalk|grass|\bcave\b|floor|\bin the\b", "gift": r"\bgift", "static": r"static|stationary",
}
METHOD_LABEL = {"old-rod": "Old Rod", "good-rod": "Good Rod", "super-rod": "Super Rod", "surf": "Surfing",
                "rock-smash": "Rock Smash", "seaweed": "Dive (seaweed)", "walk": "walking"}


def places_for(ctx: RequestContext, species: str, battle_id: str) -> dict[tuple[str, str], dict]:
    """(location name, method) -> best rate, levels and a source id, before the battle, under the rules."""
    found, _, _ = available_rows(ctx, ctx.prog.get(battle_id), species, apply_rules=True)
    out: dict[tuple[str, str], dict] = {}
    by_area: dict[tuple[str, str, str | None], dict] = {}
    for r in found:
        a = by_area.setdefault((r["location_name"] or r["location"], r["method"], r["area"]),
                               {"rate": 0, "lv": [r["min_level"], r["max_level"]], "source_id": r["source_id"]})
        a["rate"] += r["rarity"] or 0
        a["lv"] = [min(a["lv"][0], r["min_level"]), max(a["lv"][1], r["max_level"])]
    for (loc, method, _), a in by_area.items():
        p = out.setdefault((loc, method), {"rates": set(), "lv": a["lv"], "source_id": a["source_id"]})
        p["rates"].add(min(a["rate"], 100))
        p["lv"] = [min(p["lv"][0], a["lv"][0]), max(p["lv"][1], a["lv"][1])]
    return out


def describe_places(places: dict[tuple[str, str], dict], prefer: set[str]) -> str:
    """"Route 119: Super Rod (Lv20-45, 100%) or Good Rod (Lv10-30, 20%)" for the places to name."""
    chosen = [k for k in places if k[0] in prefer] or sorted(places, key=lambda k: -max(places[k]["rates"]))[:2]
    parts: dict[str, list[str]] = {}
    for loc, method in sorted(chosen, key=lambda k: -max(places[k]["rates"])):
        p = places[(loc, method)]
        rate = f", {max(p['rates'])}%" if method in METHOD_LABEL else ""
        parts.setdefault(loc, []).append(f"{METHOD_LABEL.get(method, method)} (Lv{p['lv'][0]}-{p['lv'][1]}{rate})")
    return "; ".join(f"{loc}: {' or '.join(ms)}" for loc, ms in parts.items())


def where_problem(where: str, places: dict[tuple[str, str], dict], all_places=()) -> tuple[str, set[str]] | None:
    """Why a `where` line disagrees with the encounter data (and the places it names), or None.
    `all_places` (every location name) catches a line that also names a place without it."""
    text = where.lower()
    named = {loc for loc, _ in places if loc.lower() in text}
    if not named:
        return "names no place where it's available", named
    elsewhere = sorted(p for p in all_places if p not in named and not any(p.lower() in n.lower() for n in named)
                       and re.search(rf"\b{re.escape(p.lower())}\b", text))
    if elsewhere:
        return f"not found at {', '.join(elsewhere)} before that battle", named
    methods = {m for m, pattern in METHOD_WORDS.items() if re.search(pattern, text)}
    here = {m for loc, m in places if loc in named}
    if methods and not methods & here:
        return f"not by {', '.join(sorted(methods))} there", named
    stated = {int(x) for x in re.findall(r"(\d{1,3})\s*%", text)}
    rates = set().union(*(p["rates"] for (loc, m), p in places.items() if loc in named and (not methods or m in methods)))
    if stated and rates and not stated & rates:
        return f"the odds there are {', '.join(f'{r}%' for r in sorted(rates))}, not {', '.join(f'{s}%' for s in sorted(stated))}", named
    return None


def correct_places(ctx: RequestContext, draft: LeadDraft) -> tuple[LeadDraft, list[str]]:
    """Rewrite any pick's or backup's `where` that disagrees with the encounter data, from the
    data itself (no model call), and cite the row it now comes from."""
    actions: list[str] = []
    party = {p.id for p in (ctx.index.resolve(m.species, "species", cutoff=80) for m in ctx.state.party) if p}
    all_places = [n for (n,) in ctx.cursor().execute("SELECT DISTINCT name FROM locations WHERE name IS NOT NULL").fetchall()]

    def fix(item, battle_id: str):
        match = ctx.index.resolve(item.species, "species", cutoff=88)
        if match is None or match.id in party:
            return item
        places = places_for(ctx, match.id, battle_id)
        if not places:
            return item
        problem = where_problem(item.where, places, all_places)
        if problem is None:
            return item
        why, named = problem
        new = describe_places(places, named)
        sources = [places[k]["source_id"] for k in places if k[0] in (named or {k[0] for k in places})][:3]
        for s in sources:
            ctx.ledger.add(s)
        actions.append(f"corrected where for {item.species} ({why}): {item.where!r} -> {new!r}")
        return item.model_copy(update={"where": new, "source_ids": list(dict.fromkeys([*item.source_ids, *sources]))})

    recs = []
    for rec in draft.recommendations:
        try:
            battle_id = battle(ctx, rec.before_battle or None).id
        except ToolError:
            battle_id = battle(ctx, None).id
        rec = fix(rec, battle_id)
        recs.append(rec.model_copy(update={"alternatives": [fix(a, battle_id) for a in rec.alternatives]}))
    return draft.model_copy(update={"recommendations": recs}), actions
