"""Plain-text summary of the run state that every agent gets at the top of its input."""

from agent.context import RequestContext

# What a log can randomize, in words, for saying what it left alone
VANILLA_KINDS = {
    "wild": "wild Pokémon", "trainers": "trainer teams", "statics": "static and gift Pokémon", "starters": "starters",
    "tm_moves": "TM moves", "base_stats": "stats and types", "evolutions": "evolutions", "movesets": "movesets",
}


# One line per game on how it differs, so no agent answers from another game's memory.
# Ruby/Sapphire's field-ability rules are from pokeruby (docs/audit/engine.txt): wild_encounter.c checks only
# Stench and Illuminate; SetWildMonHeldItem (pokemon_3.c), the fishing bite (field_player_avatar.c) and egg steps
# (daycare.c) check none; Pickup (atkE5_pickup, battle_script_commands.c) runs after every won battle from one
# fixed table, where Emerald's Cmd_pickup picks from level-based tables.
RS_FIELD_ABILITIES = (
    "A lead Pokémon's ability changes wild encounters only through the encounter rate (Stench lowers it, "
    "Illuminate raises it): Synchronize, Cute Charm, Magnet Pull, Static, Intimidate, Keen Eye, Compound Eyes, "
    "Suction Cups, Flame Body and the other field effects start in Emerald, so don't suggest them here. Pickup "
    "does work: after each battle you win, every party Pokémon with Pickup holding nothing has a 10% chance to "
    "find an item, from one table at every level (Super Potion 30%; Full Heal, Ultra Ball, Rare Candy, Full "
    "Restore, Revive and Nugget 10% each; Protein 5%; PP Up 4%; King's Rock 1%). Emerald's table depends on level."
)
# FireRed/LeafGreen's engine checks the same two abilities (pokefirered wild_encounter.c; nothing in
# field_player_avatar.c or daycare.c), and its Pickup has its own table (battle_script_commands.c
# sPickupItems), the only source of TM10 in those games.
FRLG_FIELD_ABILITIES = (
    "A lead Pokémon's ability changes wild encounters only through the encounter rate (Stench lowers it, "
    "Illuminate raises it): Synchronize, Cute Charm, Magnet Pull, Static, Intimidate, Keen Eye, Compound Eyes, "
    "Suction Cups, Flame Body and the other field effects start in Emerald, so don't suggest them here. Pickup "
    "works: after each battle you win, every party Pokémon with Pickup holding nothing has a 10% chance to find "
    "an item: Oran Berry 15%; Cheri, Chesto, Pecha, Rawst, Aspear and Persim Berry 10% each; TM10 Hidden Power, "
    "PP Up, Rare Candy and Nugget 5% each; Spelon, Pamtre, Watmel, Durin and Belue Berry 1% each. Pickup is the "
    "only way to get TM10 here."
)
FRLG_COMMON = (
    "Region: Kanto. The rival picks the starter strong against yours, and their team follows it all game; the "
    "rival is the Champion. Team Rocket's boss Giovanni is fought at the Rocket Hideout and Silph Co. and is the "
    "8th gym leader (Viridian). Before the National Dex (postgame: Oak gives it after the Hall of Fame once you've caught 60 species and visited One Island), no Pokémon can evolve "
    "into a species past #151 (no Crobat, Bellossom, Politoed, Slowking, Steelix, Scizor, Kingdra, Blissey, "
    "Porygon2), and Espeon and Umbreon never evolve (no clock). The Sevii Islands 1-3 trip Bill offers after Blaine "
    "is optional (the PC is off from the first meeting on One Island until you reach Three Island), Islands 4-7 are postgame. Move tutors teach once each. Wild "
    "Pokémon differ between FireRed and LeafGreen: trust the tools. " + FRLG_FIELD_ABILITIES
)
GAME_SOURCE = "rules:game"  # the line below, citable: the pipeline puts it in every request's ledger
GAME_LINES = {
    "emerald": "Game: Pokémon Emerald. Teams Magma and Aqua both appear; the 8th gym leader is Juan and the Champion is Wallace.",
    "ruby": ("Game: Pokémon Ruby (Game Boy Advance, not Omega Ruby). The villain is Team Magma only; the 8th gym "
             "leader is Wallace and the Champion is Steven; there are no move tutors; Groudon (Lv45) is a required "
             "battle in the Cave of Origin before the 8th gym; Sky Pillar and Rayquaza are postgame. Teams and "
             "encounters differ from Emerald's: trust the tools, not Emerald memory. " + RS_FIELD_ABILITIES),
    "sapphire": ("Game: Pokémon Sapphire (Game Boy Advance, not Alpha Sapphire). The villain is Team Aqua only; the "
                 "8th gym leader is Wallace and the Champion is Steven; there are no move tutors; Kyogre (Lv45) is a "
                 "required battle in the Cave of Origin before the 8th gym; Sky Pillar and Rayquaza are postgame. "
                 "Teams and encounters differ from Emerald's: trust the tools, not Emerald memory. " + RS_FIELD_ABILITIES),
    "firered": "Game: Pokémon FireRed (the Game Boy Advance remake of Red, not Let's Go). " + FRLG_COMMON,
    "leafgreen": "Game: Pokémon LeafGreen (the Game Boy Advance remake of Green, not Let's Go). " + FRLG_COMMON,
}


def state_brief(ctx: RequestContext) -> str:
    s = ctx.state
    p = ctx.progress if s.badges is not None else None
    lines = [
        f"{GAME_LINES[s.game]} [source id for this line: {GAME_SOURCE}]",
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
