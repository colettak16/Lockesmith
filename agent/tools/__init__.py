"""The function tools the agents call (PLAN.md §5, docs/decisions.md D8).

Each wraps a plain function in this package (which the tests call directly). The run
state comes from the request context, so the model never passes it; every result's
source ids land in the evidence ledger, and problems come back as {"error": ...}.
"""

from agents import RunContextWrapper, function_tool

from agent.context import RequestContext
from agent.tools import battles, encounters, guide, moves, outlook, sql, story
from agent.tools.common import guarded

Ctx = RunContextWrapper[RequestContext]


@function_tool
def get_remaining_battles(ctx: Ctx) -> str:
    """Story battles still ahead of the player, in order (deferred gyms included), with each
    team's highest level and whether it's optional."""
    return guarded(battles.remaining_battles)(ctx.context)


@function_tool
def get_trainer_team(ctx: Ctx, battle: str) -> str:
    """The opposing team for one story battle: species, types, levels, held items, abilities and
    moves. Rival teams follow the player's starter and rival.

    Args:
        battle: A battle id from get_remaining_battles (e.g. "gym8_juan") or a name ("Juan").
    """
    return guarded(battles.trainer_team)(ctx.context, battle)


@function_tool
def threat_matrix(ctx: Ctx, battle: str) -> str:
    """Gen 3 type matchups between the player's party and one battle's team: which opponents
    hit which party members super effectively, which party members answer each opponent, and
    which opponents nobody answers. Needs a party in the run state.

    Args:
        battle: A battle id or name.
    """
    return guarded(battles.threat_matrix)(ctx.context, battle)


@function_tool
def scout_battle(ctx: Ctx, battle: str) -> str:
    """One battle in one call: the opposing team (species, types, levels, items, abilities, moves)
    and, when the party is known, the type matchups against the party and the level gap.

    Args:
        battle: A battle id (e.g. "gym7_tate_liza") or a name ("Tate & Liza").
    """
    return guarded(battles.scout_battle)(ctx.context, battle)


@function_tool
def gauntlet_overview(ctx: Ctx) -> str:
    """Every remaining story battle's type profile up to the Champion, plus which attacking and
    defending types pay off over the whole rest of the run. Use it to judge long-term value."""
    return guarded(outlook.gauntlet_overview)(ctx.context)


@function_tool
def assess_candidates(ctx: Ctx, species: list[str]) -> str:
    """Long-term value of up to 6 species for the rest of the run: final evolution and how it's
    reached (trade evolutions are impossible solo), final-form stats, how many remaining story
    opponents it hits super effectively, which battles it's strongest in and most threatened by,
    and what it adds to (or duplicates in) the current party.

    Args:
        species: Species names, e.g. ["Poochyena", "Absol", "Shuppet"].
    """
    return guarded(outlook.assess_candidates)(ctx.context, species)


@function_tool
def moves_outlook(ctx: Ctx, species: list[str], before_battle: str | None = None, level: int | None = None) -> str:
    """For up to 6 species at once: their best level-up attacks by the battle, next evolution, and
    the strongest compatible TMs obtainable before the battle (with any requirement).

    Args:
        species: Species names.
        before_battle: Battle id or name; defaults to the next required battle.
        level: Level to check at; defaults to the battle's top opponent level.
    """
    return guarded(moves.moves_outlook)(ctx.context, species, before_battle, level)


@function_tool
def get_catchable(ctx: Ctx, before_battle: str | None = None, species: str | None = None,
                  types: list[str] | None = None) -> str:
    """Species the player can obtain before a battle, with locations, methods, levels and slot
    odds. Applies reachability, HM and key-item gates, the player's rules and rejected picks.
    With `species`, says where it is or why it isn't available yet.

    Args:
        before_battle: Battle id or name; defaults to the next required battle.
        species: Only this species.
        types: Only species with any of these types, e.g. ["dark", "ghost", "bug"].
    """
    return guarded(encounters.catchable)(ctx.context, before_battle, species, types)


@function_tool
def encounter_odds(ctx: Ctx, location: str, method: str | None = None) -> str:
    """Per-species slot odds and levels at one location (for a Nuzlocke: the odds of each
    species being the area's first encounter).

    Args:
        location: A location name or id, e.g. "Route 119".
        method: Optional method filter: walk, surf, old-rod, good-rod, super-rod, rock-smash, seaweed.
    """
    return guarded(encounters.encounter_odds)(ctx.context, location, method)


@function_tool
def species_info(ctx: Ctx, name: str) -> str:
    """Gen 3 types, base stats, abilities, legendary status and evolution methods of a species.

    Args:
        name: Species name.
    """
    return guarded(moves.species_info)(ctx.context, name)


@function_tool
def move_info(ctx: Ctx, name: str) -> str:
    """Gen 3 type, physical/special category, power, accuracy and PP of a move.

    Args:
        name: Move name.
    """
    return guarded(moves.move_info)(ctx.context, name)


@function_tool
def get_learnset(ctx: Ctx, species: str, max_level: int | None = None) -> str:
    """Level-up moves up to a level (and the next few), the default moveset at that level,
    TM/HM compatibility and Hoenn tutor moves for a species.

    Args:
        species: Species name.
        max_level: Level to stop at, e.g. the level it will be at by the battle.
    """
    return guarded(moves.learnset)(ctx.context, species, max_level)


@function_tool
def get_tm_availability(ctx: Ctx, before_battle: str | None = None, species: str | None = None) -> str:
    """TMs and HMs obtainable before a battle and where, with any extra requirement (an HM, a
    key, a side quest). With `species`, only the ones that species can learn.

    Args:
        before_battle: Battle id or name; defaults to the player's next battle.
        species: Only TMs this species is compatible with.
    """
    return guarded(moves.tm_availability)(ctx.context, before_battle, species)


@function_tool
def get_next_steps(ctx: Ctx) -> str:
    """The player's next story battle, what opens on the way (areas, HMs, key items), the two
    battles after it, and any deferred gyms."""
    return guarded(story.next_steps)(ctx.context)


@function_tool
def get_story_outline(ctx: Ctx) -> str:
    """Every remaining story battle up to the Champion with location, top level, HMs and key
    items gained, and a short note."""
    return guarded(story.story_outline)(ctx.context)


@function_tool
def search_guide(ctx: Ctx, query: str) -> str:
    """Search the Bulbapedia walkthrough of the player's game; returns the best-matching passages with ids.

    Args:
        query: What to look for, e.g. "Feebas Route 119" or "how to get to Lilycove".
    """
    return guarded(guide.search_guide)(ctx.context, query)


def _query_db(ctx: Ctx, sql_query: str) -> str:
    return guarded(sql.query_db)(ctx.context, sql_query)


_query_db.__doc__ = (
    "Read-only SQL over the player's game database (Emerald, Ruby, Sapphire, FireRed or LeafGreen), for questions the other tools don't cover. "
    "One SELECT only, at most 50 rows.\n\n" + sql.SCHEMA + "\n\nArgs:\n    sql_query: A single SELECT statement."
)
query_db = function_tool(_query_db, name_override="query_db")

# Composite tools first: one call per investigative step keeps researchers to a few turns
# (docs/decisions.md D10). The narrower tools stay for follow-ups.
# No guide search for the battle researcher: in live runs it wandered through guide queries
# after scout_battle had already answered (docs/decisions.md D10).
BATTLE_TOOLS = [scout_battle, gauntlet_overview, move_info]
# No query_db for the catch researcher: raw encounter rows skip the reachability and HM gates.
CATCH_TOOLS = [get_catchable, assess_candidates, encounter_odds, species_info, search_guide]
MOVES_TOOLS = [moves_outlook, get_learnset, get_tm_availability, move_info, query_db]
STORY_TOOLS = [get_next_steps, get_story_outline, gauntlet_overview, get_tm_availability, search_guide]
