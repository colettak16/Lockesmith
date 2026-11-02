"""Static lists the front end needs (GET /catalog): species and moves for autocomplete, the
battles, badges and types for the run-state form, and the places a Nuzlocke encounter can be
used up in. Vanilla data; built once per process."""

from functools import cache

from agent.db import connect_readonly
from agent.progression import load
from agent.state import BADGES
from agent.tools.outlook import TYPES

WILD = ("walk", "surf", "old-rod", "good-rod", "super-rod", "rock-smash", "seaweed")


@cache
def catalog() -> dict:
    con = connect_readonly()
    prog = load()
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
    return {
        "species": species,
        "moves": moves,
        "types": TYPES,
        "badges": [{"id": badge, "gym": gym, "label": labels[gym]} for badge, gym in BADGES.items()],
        "battles": [{"id": b.id, "label": b.label, "order": b.order, "optional": b.optional} for b in prog.battles],
        "places": places,
    }
