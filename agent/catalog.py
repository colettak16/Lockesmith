"""Static lists the front end needs (GET /catalog?game=...): species and moves for autocomplete,
the battles, badges and types for the run-state form, and the places a Nuzlocke encounter can be
used up in. Vanilla data for one game; built once per process per game."""

from functools import cache

from agent.db import connect_readonly
from agent.games import DEFAULT, GAMES
from agent.games import get as get_game
from agent.progression import load_game
from agent.state import BADGE_GYMS
from agent.tools.outlook import TYPES

WILD = ("walk", "surf", "old-rod", "good-rod", "super-rod", "rock-smash", "seaweed")


@cache
def catalog(game_id: str = DEFAULT) -> dict:
    game = get_game(game_id)
    con = connect_readonly(game)
    prog = load_game(game)
    species = [{"id": i, "name": n, "types": [t for t in (t1, t2) if t]} for i, n, t1, t2 in con.execute(
        "SELECT identifier, name, type1, type2 FROM species ORDER BY species_id").fetchall()]
    moves = [{"id": i, "name": n} for i, n in con.execute("SELECT identifier, name FROM moves ORDER BY name").fetchall()]
    # Places in the order the story opens them, so the used-routes picker reads like the run
    opened: dict[str, int] = {}
    for b in prog.battles:
        for spec in b.areas_new:
            opened.setdefault(spec[0], b.order)
    places = sorted(
        ({"id": i, "name": n or i.replace("-", " ").title()} for i, n in con.execute(
            f"SELECT identifier, name FROM locations WHERE identifier IN (SELECT location FROM encounters WHERE method IN {WILD})"
        ).fetchall()),
        key=lambda p: (opened.get(p["id"], 99), p["name"]),
    )
    labels = {b.id: b.label for b in prog.battles}
    by_id = {s["id"]: s for s in species}
    return {
        "game": game.id,
        "games": [{"id": g.id, "name": g.name, "short": g.short, "region": g.region} for g in GAMES.values()],
        "starters": [{"id": s, "name": by_id[s]["name"], "type": by_id[s]["types"][0]} for s in game.cast.starters],
        "rivals": [{"id": r, "name": r.title()} for r in game.cast.rivals],
        "species": species,
        "moves": moves,
        "types": TYPES,
        "badges": [{"id": badge, "gym": gym, "label": labels[gym]} for badge, gym in BADGE_GYMS[game.id].items()],
        "battles": [{"id": b.id, "label": b.label, "order": b.order, "optional": b.optional} for b in prog.battles],
        "places": places,
    }
