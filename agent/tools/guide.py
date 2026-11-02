"""search_guide: BM25 over the Bulbapedia Emerald walkthrough chunks (docs/decisions.md D2)."""

import json
import math
import re
from collections import Counter
from functools import cache

from agent.context import RequestContext
from agent.evidence import CHUNKS

TOKEN_RE = re.compile(r"[a-z0-9]+")
K1, B = 1.5, 0.75
EXCERPT_CHARS = 900


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower().replace("é", "e"))


@cache
def index() -> tuple[list[dict], list[Counter], dict[str, float], float]:
    chunks = [json.loads(line) for line in CHUNKS.read_text(encoding="utf-8").splitlines()]
    docs = [Counter(tokens(f"{c['page']} {c['section']} {c['text']}")) for c in chunks]
    df = Counter(t for d in docs for t in d)
    n = len(docs)
    idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
    avg = sum(sum(d.values()) for d in docs) / n
    return chunks, docs, idf, avg


def search(query: str, k: int = 4) -> list[dict]:
    chunks, docs, idf, avg = index()
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
    return {"query": query, "passages": search(query, max(1, min(k, 6)))}
