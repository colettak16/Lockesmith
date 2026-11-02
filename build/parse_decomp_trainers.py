"""Trainer parties from pokeemerald -> `trainers` and `trainer_mons` tables.

Sources: src/data/trainers.h (one struct per trainer, with the party symbol and
the double-battle flag), src/data/trainer_parties.h (854 party arrays) and
include/constants/opponents.h (TRAINER_X -> id; the randomizer log uses these ids).

Parties with default moves get what the game gives them at creation time
(GiveBoxMonInitialMoveset in src/pokemon.c): walk the species' level-up learnset in
ROM order up to the mon's level, skip moves it already knows, and when all four
slots are full drop the oldest move. That is "the last four distinct moves learned
at or below that level", with ROM order breaking ties within a level.
"""

import re
from pathlib import Path

import duckdb

from build import decomp
from build.decomp import bracket_blocks, brace_list, fields, item_identifier, strip_comments


def default_moves(learnset: list[tuple[int, str]], level: int) -> list[str]:
    """Moves a default-moveset trainer mon knows, given its learnset in ROM order."""
    known: list[str] = []
    for move_level, move in learnset:
        if move_level > level:
            break
        if move in known:
            continue
        if len(known) == 4:
            known.pop(0)
        known.append(move)
    return known


def split_top_level(body: str) -> list[str]:
    """Top-level `{ ... }` chunks of an array initialiser."""
    chunks, depth, start = [], 0, None
    for i, ch in enumerate(body):
        if ch == "{":
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                chunks.append(body[start:i])
    return chunks


def parse_parties(decomp_dir: Path) -> dict[str, list[dict]]:
    text = strip_comments(decomp.read(decomp_dir, "src/data/trainer_parties.h"))
    parties = {}
    for struct, symbol, body in re.findall(
        r"static const struct (TrainerMon\w+) (sParty_\w+)\[\]\s*=\s*\{(.*?)\n\};", text, flags=re.S
    ):
        mons = []
        for chunk in split_top_level(body):
            f = fields(chunk)
            mons.append(
                {
                    "iv": int(f["iv"]),
                    "level": int(f["lvl"]),
                    "species_const": f["species"],
                    "held_item": item_identifier(f.get("heldItem", "ITEM_NONE")),
                    "move_consts": [m for m in brace_list(f["moves"]) if m != "MOVE_NONE"] if "moves" in f else None,
                    "struct": struct,
                }
            )
        parties[symbol] = mons
    return parties


def parse_trainers(decomp_dir: Path) -> list[dict]:
    ids = {k: v for k, v in decomp.defines(decomp_dir, "include/constants/opponents.h").items() if k.startswith("TRAINER_")}
    class_names = decomp.trainer_class_names(decomp_dir)
    text = strip_comments(decomp.read(decomp_dir, "src/data/trainers.h"))
    out = []
    for const, body in bracket_blocks(text, "TRAINER_").items():
        f = fields(body)
        party = re.search(r"\((sParty_\w+)\)", f.get("party", ""))
        name = re.search(r'_\("([^"]*)"\)', f["trainerName"]).group(1)
        trainer_class = f["trainerClass"]
        out.append(
            {
                "trainer_id": ids[const],
                "trainer_const": const,
                "trainer_class": trainer_class,
                "class_name": class_names.get(trainer_class, "").replace("{Pkmn}", "Pokémon"),
                "name": name.title(),
                "is_female": "F_TRAINER_FEMALE" in f.get("encounterMusic_gender", ""),
                "is_double": f.get("doubleBattle") == "TRUE",
                "items": [i for i in (item_identifier(x) for x in brace_list(f.get("items", "{}"))) if i],
                "ai_flags": f.get("aiFlags", "0"),
                "party_symbol": party.group(1) if party else None,
            }
        )
    return out


def build(con: duckdb.DuckDBPyConnection, decomp_dir: Path) -> None:
    """Create `trainers` and `trainer_mons`. Needs `species` and `moves` already built."""
    dex = decomp.national_dex(decomp_dir)
    move_id_of = decomp.move_ids(decomp_dir)
    species_name = dict(con.execute("SELECT species_id, identifier FROM species").fetchall())
    move_name = dict(con.execute("SELECT move_id, identifier FROM moves").fetchall())
    learnsets = {
        sid: [(lvl, move_name[mid]) for lvl, mid in moves] for sid, moves in decomp.level_up_learnsets(decomp_dir).items()
    }
    parties = parse_parties(decomp_dir)
    trainers = parse_trainers(decomp_dir)

    trainer_rows, mon_rows = [], []
    for t in trainers:
        party = parties.get(t["party_symbol"], [])
        trainer_rows.append(
            (
                t["trainer_id"], t["trainer_const"], t["trainer_class"], t["class_name"], t["name"],
                t["is_female"], t["is_double"], t["items"], t["ai_flags"], t["party_symbol"], len(party),
                f"decomp:trainers.h#{t['trainer_const']}",
            )
        )
        for slot, mon in enumerate(party, 1):
            species_id = dex[mon["species_const"]]
            if mon["move_consts"] is not None:
                moves, source = [move_name[move_id_of[m]] for m in mon["move_consts"]], "custom"
            else:
                moves, source = default_moves(learnsets[species_id], mon["level"]), "default"
            mon_rows.append(
                (
                    t["trainer_id"], t["trainer_const"], slot, species_id, species_name[species_id], mon["level"],
                    mon["held_item"], moves, source, mon["iv"], mon["iv"] * 31 // 255,
                    f"decomp:trainer_parties.h#{t['party_symbol']}/{slot}",
                )
            )

    con.execute(
        """
        CREATE TABLE trainers (
            trainer_id INTEGER PRIMARY KEY, trainer_const VARCHAR UNIQUE, trainer_class VARCHAR, class_name VARCHAR,
            name VARCHAR, is_female BOOLEAN, is_double BOOLEAN, items VARCHAR[], ai_flags VARCHAR,
            party_symbol VARCHAR, party_size INTEGER, source_id VARCHAR
        )
        """
    )
    con.executemany("INSERT INTO trainers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", trainer_rows)
    con.execute(
        """
        CREATE TABLE trainer_mons (
            trainer_id INTEGER, trainer_const VARCHAR, slot INTEGER, species_id INTEGER, species VARCHAR,
            level INTEGER, held_item VARCHAR, moves VARCHAR[], moves_source VARCHAR,
            iv INTEGER, iv_value INTEGER, source_id VARCHAR
        )
        """
    )
    con.executemany("INSERT INTO trainer_mons VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", mon_rows)
    # CreateNPCTrainerParty (battle_main.c) gives every trainer Pokemon an even personality
    # (0x80/0x78/0x88 plus nameHash << 8), and CreateBoxMon (pokemon.c) takes the ability
    # slot from personality & 1, so trainer Pokemon always have their first ability.
    con.execute("ALTER TABLE trainer_mons ADD COLUMN ability VARCHAR")
    con.execute("UPDATE trainer_mons SET ability = s.ability1 FROM species s WHERE trainer_mons.species_id = s.species_id")
