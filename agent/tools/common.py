"""Helpers shared by the tools: SQL rows, name resolution, gates, the type chart, output."""

import json
from functools import cache

from agent.context import RequestContext
from agent.db import connect_readonly
from agent.overlay import UNREAD_KINDS
from agent.progression import Battle

MAX_TOOL_CHARS = 16000  # tools cap their own lists well below this; it's a last resort
TYPE_CHART_SOURCE = "rules:gen3_type_chart"

# Encounter method -> what must be usable before the battle: an HM in hm_gates_open or a key item
METHOD_GATES = {
    "surf": ("hm", "surf"),
    "seaweed": ("hm", "dive"),
    "rock-smash": ("hm", "rock-smash"),
    "old-rod": ("item", "old-rod"),
    "good-rod": ("item", "good-rod"),
    "super-rod": ("item", "super-rod"),
    "feebas-tile-fishing": ("item", "old-rod"),  # any rod works on a Feebas tile
    "devon-scope": ("item", "devon-scope"),
}
NOT_WILD = {"gift", "gift-egg", "static", "npc-trade"}


class ToolError(Exception):
    """A problem the model can fix (unknown name, missing run state); returned as {"error": ...}."""


def rows(cur, sql: str, params=()) -> list[dict]:
    res = cur.execute(sql, list(params))
    cols = [d[0] for d in res.description]
    return [dict(zip(cols, r)) for r in res.fetchall()]


def _source_ids(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "source_id" and isinstance(v, str):
                yield v
            elif k == "source_ids" and isinstance(v, list):
                yield from (s for s in v if isinstance(s, str))
            else:
                yield from _source_ids(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _source_ids(v)


def output(ctx: RequestContext, payload: dict) -> str:
    """Record the payload's source ids in the evidence ledger and serialize it for the model."""
    for sid in _source_ids(payload):
        ctx.ledger.add(sid)
    text = json.dumps(payload, default=str, ensure_ascii=False)
    if len(text) > MAX_TOOL_CHARS:
        text = text[:MAX_TOOL_CHARS] + ' ... [truncated; narrow the query for the rest]'
    return text


def guarded(fn):
    """Turn ToolErrors into {"error": ...} so the model can correct itself."""

    def wrapper(ctx: RequestContext, *args, **kwargs) -> str:
        try:
            return output(ctx, fn(ctx, *args, **kwargs))
        except ToolError as e:
            return json.dumps({"error": str(e)})

    wrapper.__name__, wrapper.__doc__ = fn.__name__, fn.__doc__
    return wrapper


def unread(ctx: RequestContext, kind: str) -> str | None:
    """Why the tools can't answer `kind` (e.g. "movesets") from their tables in this run, or None.
    Set when the session's randomizer log changed that kind and Lockesmith doesn't read it."""
    status = ctx.log_changes.get(kind, "unchanged")
    if status == "metronome-only":
        return f"in this randomized run every Pokémon's {UNREAD_KINDS.get(kind, kind)} are Metronome only"
    if status == "unparsed":
        return (f"this run's randomizer log changed {UNREAD_KINDS.get(kind, kind)}, and Lockesmith can't read "
                "that part of the log, so the vanilla data would be wrong here")
    return None


def resolve(ctx: RequestContext, text: str, kind: str) -> str:
    match = ctx.index.resolve(text, kind, cutoff=80)
    if match is None:
        guesses = [m.name for m in ctx.index.match(text, kinds=[kind], limit=3, cutoff=60)]
        raise ToolError(f"unknown {kind} {text!r}" + (f"; did you mean {', '.join(guesses)}?" if guesses else ""))
    return match.id


def battle(ctx: RequestContext, ref: str | None) -> Battle:
    """A battle by id ('gym8_juan') or by a name in its label ('Juan', 'Tate & Liza'); the
    player's next required battle when ref is empty."""
    if not ref:
        nxt = ctx.progress.next_required
        if nxt is None:
            raise ToolError("the run state has every story battle done; nothing is ahead")
        return nxt
    key = ref.strip().lower()
    for b in ctx.prog.battles:
        if b.id == key:
            return b
    hits = [b for b in ctx.prog.battles if key in b.label.lower() or key.replace(" ", "_") in b.id]
    if len(hits) == 1:
        return hits[0]
    options = ", ".join(b.id for b in (hits or ctx.prog.battles))
    raise ToolError(f"battle {ref!r} is {'ambiguous' if hits else 'unknown'}; use one of: {options}")


def method_open(method: str, b: Battle) -> str | None:
    """None if the encounter method is usable before battle `b`, else why not."""
    gate = METHOD_GATES.get(method)
    if gate is None:
        return None
    kind, need = gate
    have = b.hm_gates_open if kind == "hm" else b.key_items
    if need in have:
        return None
    return f"needs {'HM ' if kind == 'hm' else ''}{need}, not usable before {b.label}"


@cache
def type_chart() -> dict[tuple[str, str], float]:
    con = connect_readonly()
    return {(a, d): m for a, d, m in con.execute("SELECT attacking_type, defending_type, multiplier FROM type_efficacy").fetchall()}


def effectiveness(attacking: str, defending: list[str]) -> float:
    chart = type_chart()
    out = 1.0
    for t in defending:
        out *= chart.get((attacking, t), 1.0)
    return out
