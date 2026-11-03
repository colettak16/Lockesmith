"""search_guide: BM25 over the game's Bulbapedia walkthrough chunks (docs/decisions.md D2).

Emerald, Ruby/Sapphire and FireRed/LeafGreen have one corpus each. Paired chunks list the versions
they describe, so a Sapphire search skips Ruby-only sections (VS Maxie, the Magma Hideout)."""

import json
import math
import re
from collections import Counter
from functools import cache

from agent.context import RequestContext
from agent.evidence import chunks_path
from agent.games import DEFAULT
from agent.games import get as get_game

TOKEN_RE = re.compile(r"[a-z0-9]+")
K1, B = 1.5, 0.75
EXCERPT_CHARS = 900


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower().replace("é", "e"))


@cache
def index(game_id: str = DEFAULT) -> tuple[list[dict], list[Counter], dict[str, float], float]:
    chunks = [json.loads(line) for line in chunks_path(get_game(game_id)).read_text(encoding="utf-8").splitlines()]
    chunks = [c for c in chunks if game_id in c.get("versions", [game_id])]
    docs = [Counter(tokens(f"{c['page']} {c['section']} {c['text']}")) for c in chunks]
    df = Counter(t for d in docs for t in d)
    n = len(docs)
    idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
    avg = sum(sum(d.values()) for d in docs) / n
    return chunks, docs, idf, avg


def search(query: str, k: int = 4, game_id: str = DEFAULT) -> list[dict]:
    chunks, docs, idf, avg = index(game_id)
    q = tokens(query)
    scored = []
    for c, d in zip(chunks, docs):
        length = sum(d.values())
        s = sum(idf.get(t, 0) * d[t] * (K1 + 1) / (d[t] + K1 * (1 - B + B * length / avg)) for t in q if t in d)
        if s > 0:
            scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    return [
        {"source_id": c["source_id"], "page": c["page"], "section": c["section"], "text": c["text"][:EXCERPT_CHARS]}
        for _, c in scored[:k]
    ]


def search_guide(ctx: RequestContext, query: str, k: int = 4) -> dict:
    """Top walkthrough passages for a query, each with its guide source id."""
    out = {"query": query, "passages": search(query, max(1, min(k, 6)), ctx.game.id)}
    if ctx.randomizer:
        out["note"] = ("Randomized run: the walkthrough describes the vanilla game. Use it for the route, story and "
                       "puzzles, not for which Pokémon, teams or items appear; the other tools read the player's log.")
    return out
