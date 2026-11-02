"""Story tools: what to do next and the road to the Champion (docs/decisions.md D8)."""

from agent.context import RequestContext
from agent.progression import Battle
from agent.tools.battles import team
from agent.tools.common import ToolError


def _area_text(spec) -> str:
    loc, area, methods = spec
    text = loc if area == "*" else f"{loc}/{area or 'main'}"
    return text + (f" ({', '.join(methods)} only)" if methods else "")


def _ace(ctx: RequestContext, b: Battle) -> int | None:
    try:
        return max(m["level"] for m in team(ctx, b)[0])
    except ToolError:
        return None


def _step(ctx: RequestContext, b: Battle, prev: Battle | None) -> dict:
    return {
        "battle_id": b.id, "label": b.label, "location": b.location, "optional": b.optional,
        "format": b.battle_format, "highest_level": _ace(ctx, b),
        "new_hms_usable": sorted(set(b.hm_gates_open) - set(prev.hm_gates_open if prev else ())),
        "new_key_items": sorted(set(b.key_items) - set(prev.key_items if prev else ())),
        "areas_opened_before_it": [_area_text(s) for s in b.areas_new],
        "notes": b.notes, "source_ids": [f"progression:{b.id}", b.source],
    }


def next_steps(ctx: RequestContext) -> dict:
    """The next story battle and what opens on the way to it, plus the two after it and any
    gyms the player has deferred."""
    p = ctx.progress
    if p.next_battle is None:
        return {"done": True, "note": "Every story battle up to the Champion is behind the player; postgame is out of scope."}
    order = [b for b in ctx.prog.battles if b.order >= p.next_battle.order]
    prev = next((b for b in reversed(ctx.prog.battles) if b.order < p.next_battle.order), None)
    steps = [_step(ctx, order[0], prev)]
    for a, b in zip(order, order[1:3]):
        steps.append(_step(ctx, b, a))
    return {
        "next": steps[0], "then": steps[1:],
        "deferred_gyms": [{"battle_id": b.id, "label": b.label, "source_id": f"progression:{b.id}"} for b in p.deferred],
        "assumptions": p.assumptions,
    }


def story_outline(ctx: RequestContext) -> dict:
    """Every remaining story battle in order with location, top level, HMs and key items
    gained, and a short note: the outline of the road to the Champion."""
    p = ctx.progress
    outline, prev = [], next((b for b in reversed(ctx.prog.battles) if p.next_battle and b.order < p.next_battle.order), None)
    for b in p.remaining:
        s = _step(ctx, b, prev)
        s["notes"] = (b.notes or "")[:160]
        s.pop("areas_opened_before_it")
        s["areas_opened_count"] = len(b.areas_new)
        outline.append(s)
        prev = b
    return {"remaining": outline, "assumptions": p.assumptions}
