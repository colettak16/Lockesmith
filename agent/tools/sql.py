"""query_db: read-only SQL over emerald.duckdb, the escape hatch (PLAN.md §5)."""

import hashlib
import re

from agent.context import RequestContext
from agent.tools.common import ToolError

MAX_ROWS = 50
WRITE_RE = re.compile(
    r"\b(insert|update|delete|create|drop|alter|attach|detach|copy|pragma|install|load|export|import|call|"
    r"checkpoint|vacuum|truncate|grant)\b",
    re.I,
)

SCHEMA = """Tables (DuckDB): species(species_id, identifier, name, type1, type2, hp, attack, defense, sp_attack,
sp_defense, speed, bst, ability1, ability2, is_legendary, is_mythical, evolution_chain_id),
moves(move_id, identifier, name, type, damage_class physical|special|status|varies, power, accuracy, pp),
learnsets(species_id, move_id, method level-up|machine|tutor|egg, level), machines(label TM01..HM08, move_id),
evolutions(from_species_id, to_species_id, trigger, min_level, item, min_happiness, note),
encounters(location, area, method walk|surf|old-rod|good-rod|super-rod|rock-smash|seaweed|gift|static|..., rarity,
species_id, min_level, max_level, conditions), locations(identifier, name),
trainers(trainer_const, class_name, name, is_double), trainer_mons(trainer_const, slot, species, level, held_item,
ability, moves), tm_locations(label, method, location, detail, requires), type_efficacy(attacking_type,
defending_type, multiplier). Identifiers are lowercase-hyphenated (e.g. 'mr-mime', 'feint-attack')."""


def query_db(ctx: RequestContext, sql: str) -> dict:
    """Run one read-only SELECT and return up to 50 rows."""
    stripped = sql.strip().rstrip(";").strip()
    if ";" in stripped or not re.match(r"^(select|with)\b", stripped, re.I) or WRITE_RE.search(stripped):
        raise ToolError("only a single read-only SELECT (or WITH ... SELECT) statement is allowed")
    cur = ctx.cursor()
    try:
        res = cur.execute(stripped)
    except Exception as e:  # noqa: BLE001 - surface the database's message to the model
        raise ToolError(f"query failed: {str(e)[:300]}") from None
    cols = [d[0] for d in res.description]
    data = res.fetchmany(MAX_ROWS + 1)
    qid = hashlib.sha1(stripped.encode()).hexdigest()[:10]
    out = {"columns": cols, "rows": [list(r) for r in data[:MAX_ROWS]], "source_id": f"sql:{qid}"}
    if len(data) > MAX_ROWS:
        out["note"] = f"more than {MAX_ROWS} rows; add a LIMIT or a tighter WHERE"
    if "source_id" in cols:
        out["source_ids"] = [r[cols.index("source_id")] for r in data[:MAX_ROWS]]
    return out
