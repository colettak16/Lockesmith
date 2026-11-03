"""Battle tools: what's left, who's on each team, and how the party matches up (PLAN.md §5)."""

from build.parse_decomp_trainers import default_moves

from agent.context import RequestContext
from agent.progression import Battle
from agent.state import rival_for, starter_for
from agent.tools.common import TYPE_CHART_SOURCE, ToolError, battle, effectiveness, resolve, rows, unread

TEAM_SQL = """
    SELECT m.trainer_const, t.class_name, t.name AS trainer_name, m.slot, m.species_id, s.identifier, s.name AS species,
           s.type1, s.type2, m.level, m.held_item, m.ability, m.moves, m.moves_source, m.iv_value, m.source_id
    FROM trainer_mons m JOIN trainers t USING (trainer_const) JOIN species s USING (species_id)
    WHERE m.trainer_const IN ({marks}) ORDER BY m.trainer_const, m.slot
"""


def trainer_consts(ctx: RequestContext, b: Battle) -> tuple[list[str], str | None]:
    """The trainer structs for this player, plus a note when the rival is unknown and matters."""
    if b.trainer_consts is not None:
        return list(b.trainer_consts), None
    starter = starter_for(ctx.state)
    if starter is None:
        raise ToolError(f"{b.label} depends on the player's starter, which the run state doesn't have")
    variants = b.starter_variants[starter]
    if isinstance(variants, str):  # Kanto: one rival, whose team follows the player's starter
        return [variants], None
    rival = rival_for(ctx.state)
    if rival:
        return [variants[rival]], None
    consts = sorted(set(variants.values()))
    note = "Rival unknown: both May's and Brendan's teams are listed." if len(consts) > 1 else None
    return consts, note


def move_table(cur) -> dict[str, dict]:
    return {
        r["identifier"]: r
        for r in rows(cur, "SELECT identifier, name, type, damage_class, power, accuracy, pp FROM moves")
    }


def wild_team(ctx: RequestContext, b: Battle) -> list[dict]:
    """A required wild battle (Ruby/Sapphire's Cave of Origin legendary) as a one-Pokémon team:
    wild Pokémon know their species' last four level-up moves at their level, like trainers'
    defaults, and have random IVs."""
    cur = ctx.cursor()
    sp = rows(cur, "SELECT species_id, identifier, name, type1, type2, ability1, ability2 FROM species WHERE identifier = ?",
              [b.wild["species"]])[0]
    src = rows(cur, "SELECT source_id FROM encounters WHERE species_id = ? AND location = ? AND method = 'static' LIMIT 1",
               [sp["species_id"], b.location])
    moves = level_up_default(cur, sp["species_id"], b.wild["level"])
    table = move_table(cur)
    return [{
        "trainer_const": None, "class_name": "Wild", "trainer_name": sp["name"], "slot": 1,
        "species_id": sp["species_id"], "identifier": sp["identifier"], "species": sp["name"],
        "types": [t for t in (sp["type1"], sp["type2"]) if t], "level": b.wild["level"], "held_item": None,
        "ability": sp["ability1"] if not sp["ability2"] else f"{sp['ability1']} or {sp['ability2']}",
        "moves": moves, "moves_source": "default (a wild Pokémon's level-up moves)", "iv_value": None,
        "source_id": src[0]["source_id"] if src else f"progression:{b.id}",
        "move_details": [table[m] for m in moves if m in table],
    }]


def team(ctx: RequestContext, b: Battle) -> tuple[list[dict], str | None]:
    if b.wild is not None:
        return wild_team(ctx, b), "A required wild battle, not a trainer: it can be caught, knocked out or fled from."
    consts, note = trainer_consts(ctx, b)
    cur = ctx.cursor()
    mons = rows(cur, TEAM_SQL.format(marks=", ".join("?" * len(consts))), consts)
    moves = move_table(cur)
    movesets_unknown, move_data_unknown = unread(ctx, "movesets"), unread(ctx, "move_data")
    metronome = ctx.log_changes.get("movesets") == "metronome-only"
    for m in mons:
        m["types"] = [t for t in (m.pop("type1"), m.pop("type2")) if t]
        if metronome:  # UPR's Metronome-only mode gives trainers' Pokemon Metronome too
            m["moves"], m["moves_source"] = ["metronome"], "Metronome only (randomizer setting)"
        elif m["moves_source"] not in ("custom", "log"):  # the level-up default, vanilla or randomized
            if movesets_unknown:
                m["moves"], m["moves_source"] = [], f"unknown: {movesets_unknown}"
            elif m["moves_source"].startswith("unknown"):
                # UPR resets a randomized trainer Pokemon's moves to its new species' level-up default
                m["moves"] = level_up_default(cur, m["species_id"], m["level"])
                m["moves_source"] = "default (the new species' level-up moves; the log has no movesets)"
        m["move_details"] = [moves[x] for x in m["moves"] if x in moves]
    if move_data_unknown:
        note = "; ".join(filter(None, [note, f"{move_data_unknown} (move types and powers shown are vanilla)"]))
    return mons, note


def level_up_default(cur, species_id: int, level: int) -> list[str]:
    learnset = cur.execute(
        "SELECT l.level, m.identifier FROM learnsets l JOIN moves m USING (move_id) "
        "WHERE l.species_id = ? AND l.method = 'level-up' ORDER BY l.level, l.level_order",
        [species_id],
    ).fetchall()
    return default_moves(learnset, level)


def remaining_battles(ctx: RequestContext) -> dict:
    """Story battles still ahead of the player, in order, with each team's top level."""
    p = ctx.progress
    out = []
    for b in p.remaining:
        try:
            mons, _ = team(ctx, b)
            ace = max(m["level"] for m in mons)
        except ToolError:
            ace = None
        out.append(
            {
                "battle_id": b.id, "label": b.label, "order": b.order, "badges_before": b.badges_before,
                "format": b.battle_format, "optional": b.optional, "deferred": b in p.deferred,
                "location": b.location, "highest_level": ace, "source_id": f"progression:{b.id}",
            }
        )
    return {
        "next_battle": p.next_battle.id if p.next_battle else None,
        "battles": out,
        "assumptions": p.assumptions,
    }


def trainer_team(ctx: RequestContext, battle_ref: str) -> dict:
    """The opposing team(s) for one battle: species, types, levels, items, abilities, moves."""
    b = battle(ctx, battle_ref)
    mons, note = team(ctx, b)
    teams: dict[str, dict] = {}
    for m in mons:
        t = teams.setdefault(
            m["trainer_const"], {"trainer": f"{m['class_name']} {m['trainer_name']}", "trainer_const": m["trainer_const"], "pokemon": []}
        )
        t["pokemon"].append(
            {
                "species": m["species"], "types": m["types"], "level": m["level"], "held_item": m["held_item"],
                "ability": m["ability"], "iv": m["iv_value"], "moves_source": m["moves_source"],
                "moves": [f"{d['name']} ({d['type']}, {d['damage_class']}, power {d['power']})" for d in m["move_details"]],
                "source_id": m["source_id"],
            }
        )
    return {
        "battle_id": b.id, "label": b.label, "format": b.battle_format, "location": b.location,
        "partner": b.partner, "notes": b.notes, "team_note": note,
        "teams": list(teams.values()), "source_ids": [f"progression:{b.id}"],
    }


def scout_battle(ctx: RequestContext, battle_ref: str) -> dict:
    """One battle in one call: the opposing team, and (when the party is known) the type
    matchups between it and the player's party, plus the level gap."""
    out = trainer_team(ctx, battle_ref)
    if ctx.state.party:
        m = threat_matrix(ctx, battle_ref)
        out["matchups"] = m["matchups"]
        out["uncovered_opponents"] = m["uncovered"]
        out["level_gap"] = {"party_top": m["party_top_level"], "opponent_top": m["opponent_top_level"]}
        out["assumptions"] = m["assumptions"]
    else:
        out["matchups"] = None
        out["assumptions"] = ["No party given, so no matchup check."]
    return out


def party_moves(ctx: RequestContext, cur, species_id: int, level: int, given: list[str]) -> tuple[list[str], bool]:
    """Move identifiers for a party member: the ones given, else the level-up default."""
    if given:
        return [resolve(ctx, mv, "move") for mv in given], False
    if unread(ctx, "movesets"):
        return [], True
    return level_up_default(cur, species_id, level), True


def best_hit(move_details: list[dict], user_types: list[str], target_types: list[str]) -> dict | None:
    """The attacking move with the highest type multiplier (STAB included) against the target."""
    best = None
    for d in move_details:
        if not d["power"] or d["damage_class"] == "status":
            continue
        eff = effectiveness(d["type"], target_types)
        score = eff * (1.5 if d["type"] in user_types else 1.0)
        if best is None or score > best["score"]:
            best = {"move": d["name"], "type": d["type"], "effectiveness": eff, "stab": d["type"] in user_types, "score": score}
    return best


def threat_matrix(ctx: RequestContext, battle_ref: str) -> dict:
    """Gen 3 type matchups between the player's party and one battle's team (no damage rolls)."""
    if not ctx.state.party:
        raise ToolError("no party in the run state; ask the player for their party or skip the matchup check")
    b = battle(ctx, battle_ref)
    mons, note = team(ctx, b)
    cur = ctx.cursor()
    moves = move_table(cur)
    party, assumed = [], []
    for member in ctx.state.party:
        sid = resolve(ctx, member.species, "species")
        info = rows(cur, "SELECT species_id, name, type1, type2 FROM species WHERE identifier = ?", [sid])[0]
        known, was_default = party_moves(ctx, cur, info["species_id"], member.level, member.moves)
        if was_default:
            assumed.append(info["name"])
        party.append(
            {"name": info["name"], "level": member.level, "types": [t for t in (info["type1"], info["type2"]) if t],
             "moves": [moves[m] for m in known if m in moves]}
        )
    out = []
    for m in mons:
        threatens, answered_by = [], []
        for p in party:
            hit = best_hit(m["move_details"], m["types"], p["types"])
            if hit and hit["effectiveness"] >= 2:
                threatens.append({"member": p["name"], "move": hit["move"], "effectiveness": hit["effectiveness"], "stab": hit["stab"]})
            reply = best_hit(p["moves"], p["types"], m["types"])
            if reply and reply["effectiveness"] >= 2:
                answered_by.append({"member": p["name"], "move": reply["move"], "effectiveness": reply["effectiveness"], "stab": reply["stab"]})
        out.append(
            {"opponent": f"{m['species']} Lv{m['level']}", "types": m["types"], "trainer": m["trainer_const"],
             "threatens": threatens, "answered_by": answered_by, "source_ids": [m["source_id"], TYPE_CHART_SOURCE]}
        )
    top = max(p["level"] for p in party)
    return {
        "battle_id": b.id, "label": b.label, "team_note": note,
        "party_top_level": top, "opponent_top_level": max(m["level"] for m in mons),
        "matchups": out,
        "uncovered": [o["opponent"] for o in out if not o["answered_by"]],
        "assumptions": (
            [f"Moves not given for {', '.join(assumed)}: " + (f"no moves assumed, since {unread(ctx, 'movesets')}." if unread(ctx, "movesets")
                                                              else "used the level-up default moveset at their level.")]
            if assumed else []
        ) + ["Type matchups only; no damage rolls, abilities or stat stages. Hidden Power and Weather Ball count as Normal."],
    }
