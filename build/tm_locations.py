"""Where every TM and HM comes from, extracted from pokeemerald map data.

Five kinds of source, all machine-readable in the decomp:
  item-ball    object_events whose script is an item-ball script (`finditem ITEM_TM_X`)
  hidden-item  bg_events of type hidden_item
  gift         `giveitem ITEM_TM_X` in a map's scripts.inc (or a shared script a map uses)
  mart         `.2byte ITEM_TM_X` in a pokemart list
  game-corner  Mauville Game Corner prize list

Each row is tied to a map and, through its region map section, to a PokeAPI
location slug, so get_tm_availability can join it to progression.yaml. Gym TMs
are tagged with the leader they're awarded for. Other story gates (HM gifts after
a story beat, the Trick House) are not machine-readable and are listed for review
in docs/decisions.md.
"""

import re
from pathlib import Path

import duckdb

from build import decomp


def item_aliases(decomp_dir: Path) -> dict[str, str]:
    """`ITEM_TM_SANDSTORM` and `ITEM_TM37` -> `TM37`."""
    out = {}
    for label, move in decomp.tm_hm_moves(decomp_dir):
        kind = label[:2]
        out[f"ITEM_{kind}_{move.removeprefix('MOVE_')}"] = label
        out[f"ITEM_{label}"] = label
    return out


def labelled_blocks(text: str) -> dict[str, str]:
    """`Label::` (or `Label:`) -> the script text up to the next label."""
    parts = re.split(r"^(\w+)::?\s*$", text, flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def extract(decomp_dir: Path) -> list[dict]:
    aliases = item_aliases(decomp_dir)
    item_re = re.compile(r"\b(ITEM_(?:TM|HM)\w+)\b")
    maps = decomp.maps(decomp_dir)
    folder_to_map = {m["folder"]: map_id for map_id, m in maps.items()}
    rows = []

    def add(label, method, map_id, flag=None, detail=None):
        rows.append({"label": label, "method": method, "map": map_id, "flag": flag, "detail": detail})

    ball_scripts = {}
    for name, body in labelled_blocks(decomp.read(decomp_dir, "data/scripts/item_ball_scripts.inc")).items():
        m = item_re.search(body)
        if m and m.group(1) in aliases:
            ball_scripts[name] = aliases[m.group(1)]

    for map_id, m in maps.items():
        for obj in m.get("object_events") or []:
            if obj.get("script") in ball_scripts:
                add(ball_scripts[obj["script"]], "item-ball", map_id, obj.get("flag"))
        for bg in m.get("bg_events") or []:
            if bg.get("type") == "hidden_item" and bg.get("item") in aliases:
                add(aliases[bg["item"]], "hidden-item", map_id, bg.get("flag"))

    # Scripts shared across maps (data/scripts/*.inc) are attributed to the maps that call them.
    map_texts = {}
    for folder, map_id in folder_to_map.items():
        path = Path(decomp_dir) / "data" / "maps" / folder / "scripts.inc"
        if path.exists():
            map_texts[map_id] = path.read_text(encoding="utf-8")
    shared = {}
    for path in (Path(decomp_dir) / "data" / "scripts").glob("*.inc"):
        if path.name == "item_ball_scripts.inc":
            continue
        for name, body in labelled_blocks(path.read_text(encoding="utf-8")).items():
            for item in re.findall(r"giveitem\s+(ITEM_(?:TM|HM)\w+)", body):
                if item in aliases:
                    shared[name] = aliases[item]

    for map_id, text in map_texts.items():
        for item in re.findall(r"giveitem\s+(ITEM_(?:TM|HM)\w+)", text):
            if item in aliases:
                add(aliases[item], "gift", map_id)
        for name, label in shared.items():
            if re.search(rf"\b{name}\b", text):
                add(label, "gift", map_id, detail=f"shared script {name}")
        for mart in re.findall(r"pokemart\s+(\w+)", text):
            body = labelled_blocks(text).get(mart, "")
            for item in re.findall(r"\.2byte\s+(ITEM_\w+)", body):
                if item in aliases:
                    add(aliases[item], "mart", map_id, detail=mart)
        if map_id == "MAP_MAUVILLE_CITY_GAME_CORNER":
            for item in re.findall(r"setvar\s+VAR_0x8004,\s*(ITEM_(?:TM|HM)\w+)", text):
                add(aliases[item], "game-corner", map_id)

    # Gym TMs are handed over after the leader's battle in the same map script.
    for row in rows:
        if row["method"] == "gift" and "_GYM" in row["map"]:
            leaders = re.findall(r"trainerbattle_(?:single|double|no_intro)\s+(TRAINER_\w+_1)\b", map_texts.get(row["map"], ""))
            if leaders:
                row["detail"] = f"after defeating {leaders[0]}"

    unique = {(r["label"], r["method"], r["map"]): r for r in rows}
    return sorted(unique.values(), key=lambda r: (r["label"], r["method"], r["map"]))


def extract_tutors(decomp_dir: Path) -> list[tuple[str, str]]:
    """[(map folder, MOVE_X)] for the Hoenn move tutors. Each teaches once in Emerald.

    The script labels are prefixed with the map folder they live in. The other 20
    Emerald tutors are in the Battle Frontier, which is out of scope.
    """
    text = decomp.read(decomp_dir, "data/scripts/move_tutors.inc")
    out = []
    for name, body in labelled_blocks(text).items():
        m = re.search(r"setvar\s+VAR_0x8005,\s*TUTOR_(MOVE_\w+)", body)
        if m and "_EventScript_" in name:
            out.append((name.split("_EventScript_")[0], m.group(1)))
    return out


def build(con: duckdb.DuckDBPyConnection, decomp_dir: Path) -> None:
    """Create `tm_locations` and `move_tutors`. Needs `moves` and `map_sections` already built."""
    maps = decomp.maps(decomp_dir)
    mapsec_location = dict(con.execute("SELECT mapsec, location FROM map_sections").fetchall())
    rows = []
    for r in extract(decomp_dir):
        m = maps[r["map"]]
        mapsec = m["region_map_section"]
        rows.append(
            (
                r["label"], r["method"], r["map"], m["folder"], mapsec, mapsec_location.get(mapsec), r["flag"],
                r["detail"], f"decomp:data/maps/{m['folder']}#{r['label']}",
            )
        )
    con.execute(
        """
        CREATE TABLE tm_locations (
            label VARCHAR, method VARCHAR, map VARCHAR, map_folder VARCHAR, mapsec VARCHAR,
            location VARCHAR, flag VARCHAR, detail VARCHAR, source_id VARCHAR
        )
        """
    )
    con.executemany("INSERT INTO tm_locations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)

    folders = {m["folder"]: map_id for map_id, m in maps.items()}
    move_ids = decomp.move_ids(decomp_dir)
    tutor_rows = []
    for folder, move_const in extract_tutors(decomp_dir):
        map_id = folders[folder]
        mapsec = maps[map_id]["region_map_section"]
        tutor_rows.append(
            (move_ids[move_const], map_id, folder, mapsec, mapsec_location.get(mapsec), True,
             f"decomp:data/scripts/move_tutors.inc#{folder}")
        )
    con.execute(
        """
        CREATE TABLE move_tutors (
            move_id INTEGER, map VARCHAR, map_folder VARCHAR, mapsec VARCHAR, location VARCHAR,
            one_time BOOLEAN, source_id VARCHAR
        )
        """
    )
    con.executemany("INSERT INTO move_tutors VALUES (?, ?, ?, ?, ?, ?, ?)", tutor_rows)
