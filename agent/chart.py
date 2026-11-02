"""The `chart` in /chat (PLAN.md §8, §10): a Vega-Lite heatmap of how the party and the
recommended picks match up against each remaining major battle. Built in code from the same
tables the tools read (so it follows a loaded randomizer log); the model doesn't draw it."""

from agent.context import RequestContext
from agent.tools.common import ToolError, effectiveness, rows
from agent.tools.outlook import remaining_opponents

MAJOR = ("gym", "e4_", "champion")  # battle id prefixes worth a column


def members(ctx: RequestContext, plan: dict | None) -> list[dict]:
    """Party members, then each pick in the form the plan relies on (its evolve_to, if any)."""
    cur = ctx.cursor()
    out, seen = [], set()

    def add(name: str, label: str, kind: str) -> None:
        match = ctx.index.resolve(name, "species", cutoff=85)
        if match is None or (match.id, kind) in seen:
            return
        seen.add((match.id, kind))
        r = rows(cur, "SELECT name, type1, type2 FROM species WHERE identifier = ?", [match.id])[0]
        out.append({"label": label.format(name=r["name"]), "kind": kind, "types": [t for t in (r["type1"], r["type2"]) if t]})

    for m in ctx.state.party:
        add(m.species, "{name} (party)", "party")
    for rec in (plan or {}).get("recommendations", []):
        target = rec.get("evolve_to") or rec["species"]
        label = f"{rec['species']} → {{name}} (pick)" if rec.get("evolve_to") and rec["evolve_to"] != rec["species"] else "{name} (pick)"
        add(target, label, "pick")
    return out


def coverage_chart(ctx: RequestContext, plan: dict | None) -> dict | None:
    """None when there's nothing to compare (no party or picks, or no battles left)."""
    if ctx.state.badges is None:
        return None
    team = members(ctx, plan)
    if not team:
        return None
    try:
        opps, _ = remaining_opponents(ctx)
    except ToolError:
        return None
    battles: dict[str, dict] = {}
    for o in opps:
        if o["battle_id"].startswith(MAJOR):
            battles.setdefault(o["battle_id"], {"label": o["battle"], "opps": []})["opps"].append(o)
    if not battles:
        return None
    order = {b.id: b.order for b in ctx.prog.battles}
    values = []
    for bid, b in sorted(battles.items(), key=lambda kv: order[kv[0]]):
        n = len(b["opps"])
        for m in team:
            hits = sum(any(effectiveness(t, o["types"]) >= 2 for t in m["types"]) for o in b["opps"])
            threats = sum(any(effectiveness(a, m["types"]) >= 2 for a in o["attack_types"]) for o in b["opps"])
            values.append({
                "member": m["label"], "kind": m["kind"], "battle": short(b["label"]), "order": order[bid],
                "hits": hits, "threats": threats, "team_size": n, "share": round(hits / n, 2),
            })
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "title": {"text": "Type coverage over the rest of the run",
                  "subtitle": "Share of each battle's team your STAB types hit super-effectively (type chart only, no damage rolls)"},
        "data": {"values": values},
        "width": {"step": 46}, "height": {"step": 30},
        "encoding": {
            "x": {"field": "battle", "type": "ordinal", "sort": {"field": "order"}, "title": None,
                  "axis": {"labelAngle": -40, "labelLimit": 120}},
            "y": {"field": "member", "type": "nominal", "title": None,
                  "sort": [m["label"] for m in team], "axis": {"labelLimit": 220}},
        },
        "layer": [
            {"mark": {"type": "rect", "stroke": "#fffdf6", "strokeWidth": 2, "cornerRadius": 3},
             "encoding": {
                 "color": {"field": "share", "type": "quantitative", "title": "Hit super-effectively",
                           "scale": {"domain": [0, 1], "scheme": "greens"}, "legend": {"format": ".0%"}},
                 "tooltip": [{"field": "member"}, {"field": "battle"},
                             {"field": "hits", "title": "opponents hit super-effectively"},
                             {"field": "threats", "title": "opponents with a super-effective move on it"},
                             {"field": "team_size", "title": "team size"}],
             }},
            {"mark": {"type": "text", "fontSize": 11},
             "encoding": {
                 "text": {"field": "hits"},
                 "color": {"condition": {"test": "datum.share > 0.6", "value": "#ffffff"}, "value": "#2b2a26"},
             }},
        ],
        "config": {"view": {"stroke": None}, "axis": {"domain": False, "ticks": False}},
        "usermeta": {"source": "emerald.duckdb trainer teams (or the loaded randomizer log) and the Gen 3 type chart"},
    }


def short(label: str) -> str:
    """"Mossdeep Gym: Tate & Liza" -> "Tate & Liza"; "Elite Four: Sidney" -> "Sidney"."""
    return label.split(": ", 1)[-1]
