"""Plain-text summary of the run state that every agent gets at the top of its input."""

from agent.context import RequestContext

# What a log can randomize, in words, for saying what it left alone
VANILLA_KINDS = {
    "wild": "wild Pokémon", "trainers": "trainer teams", "statics": "static and gift Pokémon", "starters": "starters",
    "tm_moves": "TM moves", "base_stats": "stats and types", "evolutions": "evolutions", "movesets": "movesets",
}


def state_brief(ctx: RequestContext) -> str:
    s = ctx.state
    p = ctx.progress if s.badges is not None else None
    lines = [
        f"Starter: {s.starter or 'not given'}. Rival: {s.rival or 'not given'}.",
        f"Badges held: {', '.join(s.badges) if s.badges else ('none yet' if s.badges == [] else 'not given')}.",
    ]
    if p is not None:
        if p.next_battle is None:
            lines.append("Next story battle: none, the Champion is beaten.")
        else:
            lines.append(f"Next story battle: {p.next_battle.label} ({p.next_battle.id}).")
            req = p.next_required
            if req is not None and req.id != p.next_battle.id:
                lines.append(f"Next required battle: {req.label} ({req.id}).")
        lines += p.assumptions
    if s.party:
        lines.append("Party: " + ", ".join(
            f"{m.species} Lv{m.level}" + (f" ({', '.join(m.moves)})" if m.moves else "") for m in s.party
        ) + ".")
    else:
        lines.append("Party: not given.")
    rules = s.ruleset.describe()
    lines.append("Rules: " + ("; ".join(rules) if rules else "none (a normal run)") + ".")
    if ctx.randomizer:
        r = ctx.randomizer
        lines.append("Randomized run (the player's UPR log is loaded): tools read the log for "
                     + (", ".join(r["shadowed"]) or "nothing yet") + "; trust them over the walkthrough or memory.")
        same = [label for kind, label in VANILLA_KINDS.items() if r["changes"].get(kind, "unchanged") == "unchanged"]
        if same:
            lines.append("The log left these as in the normal game (don't ask the player about them): " + ", ".join(same) + ".")
        if r["starters"] and s.starter in r["starters"]:
            lines.append(f"The player's starter slot ({s.starter}) is {r['starters'][s.starter]} in this run.")
        if r["unread"]:
            lines.append("Changed in the log but unreadable (tools refuse these; say so rather than guess): "
                         + ", ".join(r["unread"].values()) + ".")
    if ctx.excluded_species:
        lines.append("Rejected this session (never recommend): " + ", ".join(sorted(ctx.excluded_species)) + ".")
    return "\n".join(lines)
