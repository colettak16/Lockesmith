"""Where every TM and HM comes from, extracted from the decomp's map data (pokeemerald or pokeruby).

Five kinds of source, all machine-readable in the decomp:
  item-ball    object_events whose script is an item-ball script (`finditem ITEM_TM_X`)
  hidden-item  bg_events of type hidden_item
  gift         `giveitem ITEM_TM_X` in a map's scripts.inc (or a shared script a map uses)
  mart         `.2byte ITEM_TM_X` in a pokemart list
  game-corner  Mauville Game Corner prize list

Each row is tied to a map and, through its region map section, to a PokeAPI
location slug, so get_tm_availability can join it to progression.yaml. Gym TMs
are tagged with the leader they're awarded for. Gates map data can't show (an HM
to reach the item, a key, a side quest, a party condition) are in REQUIRES, each
checked against the decomp scripts or Bulbapedia (docs/decisions.md D1, D7).
HM gifts after a story beat are covered by progression.yaml's hm_gates_open.

pokeruby (Ruby/Sapphire) names TM items by number (`ITEM_TM01_FOCUS_PUNCH`), keeps the
item-ball scripts in data/item_ball_scripts.inc, gives Game Corner prizes with
`additem`, has leaders without a `_1` suffix, and has no move tutors. Its gates are
RS_REQUIRES (docs/review_packet_rs.md TM-01..TM-03).

pokefirered (FireRed/LeafGreen) aliases TM items like pokeruby, sells Game Corner prizes in
Celadon's prize room (`setvar VAR_TEMP_1, ITEM_TM13`), names leaders TRAINER_LEADER_BROCK,
and has 15 one-time tutors (`MOVETUTOR_X`, some in shared labels that a map calls) plus Cape
Brink's starter tutor, a C special with its own conditions. Its gates are FRLG_REQUIRES.
"""

import re
from pathlib import Path

import duckdb

from build import decomp


SLATEPORT_TM_SALESMAN = (
    "the Slateport TM salesman appears only after Route 111's Secret Power man gives you TM43 "
    "(secret_power_tm.inc clears FLAG_HIDE_SLATEPORT_CITY_TM_SALESMAN)"
)
PACIFIDLOG_FAN_CLUB = (
    "once a week, judged on the lead Pokemon's friendship: 150+ gets TM27 Return, under 50 gets TM21 "
    "Frustration, in between gets nothing (GetLeadMonFriendshipScore, FLAG_RECEIVED_FANCLUB_TM_THIS_WEEK)"
)
# Same in all three games: the rival stands on (27, 7), the only tile below the store's door (27, 6),
# and declining the battle leaves them there; only the battle's end removes them (RivalFlyAway).
LILYCOVE_RIVAL_AT_STORE_DOOR = (
    "the Lilycove rival stands on the only tile below the Department Store's door until you battle them; "
    "declining leaves them there (LilycoveCity_EventScript_DeclineMayBattle), so the store needs the "
    "Lilycove rival battle"
)
LILYCOVE_STORE_TMS = ("TM14", "TM15", "TM16", "TM17", "TM20", "TM25", "TM33", "TM38")
LILYCOVE_STORE = {(tm, "mart", "LilycoveCity_DepartmentStore_4F"): LILYCOVE_RIVAL_AT_STORE_DOOR for tm in LILYCOVE_STORE_TMS}
# (label, method, map folder) -> what else the source needs beyond reaching the map
REQUIRES = {
    ("TM02", "item-ball", "MeteorFalls_B1F_2R"): "Waterfall (Rain Badge) to reach Meteor Falls' back rooms",
    ("TM06", "item-ball", "FieryPath"): "Strength (Heat Badge) to move the boulders in front of it (Bulbapedia: Fiery Path)",
    ("TM07", "item-ball", "ShoalCave_LowTideIceRoom"): "Shoal Cave at low tide (the tide changes every six hours)",
    ("TM10", "mart", "SlateportCity"): SLATEPORT_TM_SALESMAN,
    ("TM11", "item-ball", "ScorchedSlab"): "Surf to reach Scorched Slab on Route 120",
    ("TM12", "gift", "Route110_TrickHouseEnd"): "a Trick House puzzle prize",
    ("TM12", "gift", "Route110_TrickHouseEntrance"): "a Trick House puzzle prize",
    ("TM13", "item-ball", "AbandonedShip_Room_B1F"): "the Storage Key from the Captain's Office unlocks this room (FLAG_USED_STORAGE_KEY)",
    ("TM18", "item-ball", "AbandonedShip_HiddenFloorRooms"): "Dive to reach the Abandoned Ship's hidden floor",
    ("TM19", "gift", "Route123"): "a Grass-type Pokemon in the party (IsGrassTypeInParty)",
    ("TM21", "gift", "PacifidlogTown_House2"): PACIFIDLOG_FAN_CLUB,
    ("TM24", "gift", "MauvilleCity"): "Wattson gives it after you finish New Mauville with his Basement Key",
    ("TM26", "item-ball", "SeafloorCavern_Room9"): "inside Seafloor Cavern (Dive)",
    ("TM27", "gift", "FallarborTown_CozmosHouse"): "Professor Cozmo gives it once you hand over the Meteorite (from Mt. Chimney)",
    ("TM27", "gift", "PacifidlogTown_House2"): PACIFIDLOG_FAN_CLUB,
    ("TM43", "mart", "SlateportCity"): SLATEPORT_TM_SALESMAN,
    ("TM49", "gift", "SSTidalRooms"): "postgame: the S.S. Ticket comes after the Hall of Fame (hall_of_fame.inc)",
    **LILYCOVE_STORE,
}


SLATEPORT_TM_SALESMAN_RS = (
    "the Slateport TM salesman appears only after Route 111's Secret Power man gives you TM43 "
    "(secret_power_tm.inc clears FLAG_HIDE_TM_SALESMAN_SLATEPORT)"
)
RS_REQUIRES = {
    ("TM02", "item-ball", "MeteorFalls_B1F_2R"): REQUIRES[("TM02", "item-ball", "MeteorFalls_B1F_2R")],
    ("TM06", "item-ball", "FieryPath"): REQUIRES[("TM06", "item-ball", "FieryPath")],
    ("TM07", "item-ball", "ShoalCave_LowTideIceRoom"): REQUIRES[("TM07", "item-ball", "ShoalCave_LowTideIceRoom")],
    ("TM10", "mart", "SlateportCity"): SLATEPORT_TM_SALESMAN_RS,
    ("TM11", "item-ball", "ScorchedSlab"): REQUIRES[("TM11", "item-ball", "ScorchedSlab")],
    ("TM12", "gift", "Route110_TrickHouseEnd"): "a Trick House puzzle prize",
    ("TM12", "gift", "Route110_TrickHouseEntrance"): "a Trick House puzzle prize",
    ("TM13", "item-ball", "AbandonedShip_Room_B1F"): REQUIRES[("TM13", "item-ball", "AbandonedShip_Room_B1F")],
    ("TM18", "item-ball", "AbandonedShip_HiddenFloorRooms"): REQUIRES[("TM18", "item-ball", "AbandonedShip_HiddenFloorRooms")],
    ("TM19", "gift", "Route123"): REQUIRES[("TM19", "gift", "Route123")],
    ("TM21", "gift", "PacifidlogTown_House2"): PACIFIDLOG_FAN_CLUB,
    ("TM24", "gift", "MauvilleCity"): (
        "Wattson gives it after you finish New Mauville with his Basement Key; he waits outside his gym "
        "once you've beaten Norman"
    ),
    ("TM26", "item-ball", "SeafloorCavern_Room9"): REQUIRES[("TM26", "item-ball", "SeafloorCavern_Room9")],
    ("TM27", "gift", "FallarborTown_House1"): "Professor Cozmo gives it once you hand over the Meteorite (from Mt. Chimney)",
    ("TM27", "gift", "PacifidlogTown_House2"): PACIFIDLOG_FAN_CLUB,
    ("TM31", "gift", "SootopolisCity_House1"): (
        "Sootopolis's doors stay shut until the Cave of Origin legendary battle (FLAG_LEGENDARY_BATTLE_COMPLETED)"
    ),
    ("TM43", "mart", "SlateportCity"): SLATEPORT_TM_SALESMAN_RS,
    ("TM49", "gift", "SSTidalRooms"): REQUIRES[("TM49", "gift", "SSTidalRooms")],
    **LILYCOVE_STORE,
}
# pokeruby leaders have no rematch numbering, so gym rewards are tagged with these constants.
RS_LEADERS = ("ROXANNE", "BRAWLY", "WATTSON", "FLANNERY", "NORMAN", "WINONA", "TATE_AND_LIZA", "WALLACE")
LEADER_BATTLE = {
    "emerald": r"trainerbattle_(?:single|double|no_intro)\s+(TRAINER_\w+_1)\b",
    "rs": r"trainerbattle_(?:single|double|no_intro)\s+(TRAINER_(?:" + "|".join(RS_LEADERS) + r"))\b",
    "frlg": r"trainerbattle_(?:single|double|no_intro)\s+(TRAINER_LEADER_\w+)\b",
}
# The Game Corner's prize counter: (map, how its script names a prize)
GAME_CORNER = {
    "emerald": ("MAP_MAUVILLE_CITY_GAME_CORNER", r"setvar\s+VAR_0x8004,\s*(ITEM_(?:TM|HM)\w+)"),
    "rs": ("MAP_MAUVILLE_CITY_GAME_CORNER", r"additem\s+(ITEM_(?:TM|HM)\w+)"),
    "frlg": ("MAP_CELADON_CITY_GAME_CORNER_PRIZE_ROOM", r"setvar\s+VAR_TEMP_1,\s*(ITEM_(?:TM|HM)\w+)"),
}
# FireRed/LeafGreen gates map data can't show; filled in from the decomp and the review rounds.
CELADON_ROOF = "CeladonCity_DepartmentStore_Roof"
THIRSTY_GIRL = (
    "the thirsty girl on the Celadon Department Store roof trades it for a drink from the roof's vending "
    "machines (the drink is in `detail`), once per drink"
)
FRLG_REQUIRES = {(tm, "gift", CELADON_ROOF): THIRSTY_GIRL for tm in ("TM16", "TM20", "TM33")}
# Cape Brink (Two Island) teaches the lead Pokemon its starter's ultimate move (field_specials.c)
CAPE_BRINK = "TwoIsland_CapeBrink_House"
CAPE_BRINK_MOVES = {"MOVE_FRENZY_PLANT": "Venusaur", "MOVE_BLAST_BURN": "Charizard", "MOVE_HYDRO_CANNON": "Blastoise"}


# `giveitem ITEM_TM39`, or pokefirered's `giveitem_msg <text>, ITEM_TM39`
GIFT = r"giveitem(?:_msg\s+\w+,)?\s+(ITEM_(?:TM|HM)\w+)"


def requires_for(decomp_dir: Path) -> dict[tuple[str, str, str], str]:
    return {"rs": RS_REQUIRES, "frlg": FRLG_REQUIRES}.get(decomp.family(decomp_dir), REQUIRES)


def item_aliases(decomp_dir: Path) -> dict[str, str]:
    """`ITEM_TM_SANDSTORM` and `ITEM_TM37` -> `TM37`; in pokeruby and pokefirered
    `ITEM_TM37_SANDSTORM` -> `TM37`."""
    out = {}
    for label, move in decomp.tm_hm_moves(decomp_dir):
        kind = label[:2]
        out[f"ITEM_{kind}_{move.removeprefix('MOVE_')}"] = label
        out[f"ITEM_{label}"] = label
    if decomp.family(decomp_dir) != "emerald":
        for name in decomp.defines(decomp_dir, "include/constants/items.h"):
            m = re.match(r"ITEM_(TM|HM)(\d\d)_\w+$", name)
            if m:
                out[name] = f"{m.group(1)}{m.group(2)}"
    return out


def labelled_blocks(text: str) -> dict[str, str]:
    """`Label::` (or `Label:`) -> the script text up to the next label. pokeruby labels may
    carry a trailing address comment (`Label:: @ 81B1A44`)."""
    parts = re.split(r"^(\w+)::?\s*(?:@.*)?$", text, flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def extract(decomp_dir: Path, version: str | None = None) -> list[dict]:
    aliases = item_aliases(decomp_dir)
    item_re = re.compile(r"\b(ITEM_(?:TM|HM)\w+)\b")
    maps = decomp.maps(decomp_dir, version)
    folder_to_map = {m["folder"]: map_id for map_id, m in maps.items()}
    rows = []

    def add(label, method, map_id, flag=None, detail=None):
        rows.append({"label": label, "method": method, "map": map_id, "flag": flag, "detail": detail})

    fam = decomp.family(decomp_dir)
    ball_file = "data/item_ball_scripts.inc" if fam == "rs" else "data/scripts/item_ball_scripts.inc"
    ball_scripts = {}
    for name, body in labelled_blocks(decomp.read(decomp_dir, ball_file)).items():
        # A ball gives the first item its script finds. pokeruby has an unlabeled `finditem
        # ITEM_HM08_DIVE` after Victory Road B2F's ball that no object uses, so don't search on.
        m = re.search(r"finditem\s+(ITEM_\w+)", body)
        if m and m.group(1) in aliases:
            ball_scripts[name] = aliases[m.group(1)]

    for map_id, m in maps.items():
        for obj in m.get("object_events") or []:
            if obj.get("script") in ball_scripts:
                add(ball_scripts[obj["script"]], "item-ball", map_id, obj.get("flag"))
        for bg in m.get("bg_events") or []:
            if bg.get("type") == "hidden_item" and bg.get("item") in aliases:
                add(aliases[bg["item"]], "hidden-item", map_id, bg.get("flag"))

    # Scripts shared across maps (data/scripts/*.inc) are attributed to every map that refers to
    # a label in the same file, from its scripts.inc or its map.json events. Route 111's Secret
    # Power man is an object event whose script lives in secret_power_tm.inc.
    map_texts = {}
    for folder, map_id in folder_to_map.items():
        path = Path(decomp_dir) / "data" / "maps" / folder / "scripts.inc"
        if path.exists():
            map_texts[map_id] = path.read_text(encoding="utf-8")
    shared = []  # (labels defined in the file, TM/HM labels it gives, file name)
    for path in (Path(decomp_dir) / "data" / "scripts").glob("*.inc"):
        if path.name == "item_ball_scripts.inc":
            continue
        text = path.read_text(encoding="utf-8")
        given = {aliases[i] for i in re.findall(GIFT, text) if i in aliases}
        if given:
            shared.append((set(labelled_blocks(text)), given, path.name))

    for map_id, m in maps.items():
        text = map_texts.get(map_id, "")
        for item in re.findall(GIFT, text):
            if item in aliases:
                add(aliases[item], "gift", map_id)
        refs = set(re.findall(r"\w+", text)) | {
            e.get("script") for key in ("object_events", "coord_events", "bg_events") for e in m.get(key) or []
        }
        for labels, given, file_name in shared:
            if refs & labels:
                for label in sorted(given):
                    add(label, "gift", map_id, detail=f"shared script {file_name}")
        for mart in re.findall(r"pokemart\s+(\w+)", text):
            body = labelled_blocks(text).get(mart, "")
            for item in re.findall(r"\.2byte\s+(ITEM_\w+)", body):
                if item in aliases:
                    add(aliases[item], "mart", map_id, detail=mart)
        corner, prize = GAME_CORNER[fam]
        if map_id == corner:
            for item in dict.fromkeys(re.findall(prize, text)):
                add(aliases[item], "game-corner", map_id)
        # FireRed/LeafGreen's thirsty girl: `setvar VAR_0x8008, <drink>` then `setvar VAR_0x8009, <TM>`
        if fam == "frlg" and m["folder"] == CELADON_ROOF:
            for drink, item in re.findall(r"setvar\s+VAR_0x8008,\s*ITEM_(\w+)\s+setvar\s+VAR_0x8009,\s*(ITEM_TM\w+)", text):
                add(aliases[item], "gift", map_id, detail=f"for {drink.replace('_', ' ').title()}")

    # Gym TMs are handed over after the leader's battle in the same map script.
    leader_re = LEADER_BATTLE[fam]
    for row in rows:
        if row["method"] == "gift" and "_GYM" in row["map"]:
            leaders = re.findall(leader_re, map_texts.get(row["map"], ""))
            if leaders:
                row["detail"] = f"after defeating {leaders[0]}"

    unique = {(r["label"], r["method"], r["map"]): r for r in rows}
    return sorted(unique.values(), key=lambda r: (r["label"], r["method"], r["map"]))


def extract_tutors(decomp_dir: Path, version: str | None = None) -> list[tuple[str, str, str | None]]:
    """[(map folder, MOVE_X, what else it needs)] for the move tutors. Each teaches once.

    Emerald's script labels are prefixed with the map folder they live in; its other 20
    tutors are in the Battle Frontier, which is out of scope. Ruby and Sapphire have no move
    tutors (Fallarbor's "move tutor" is the Move Relearner). FireRed/LeafGreen's labels are
    found through the maps that call them, and Cape Brink's starter tutor is added from
    field_specials.c (CapeBrinkGetMoveToTeachLeadPokemon).
    """
    fam = decomp.family(decomp_dir)
    if fam == "rs":
        return []
    blocks = labelled_blocks(decomp.read(decomp_dir, "data/scripts/move_tutors.inc"))
    if fam == "emerald":
        out = []
        for name, body in blocks.items():
            m = re.search(r"setvar\s+VAR_0x8005,\s*TUTOR_(MOVE_\w+)", body)
            if m and "_EventScript_" in name:
                out.append((name.split("_EventScript_")[0], m.group(1), None))
        return out
    tutors = {}
    for name, body in blocks.items():
        m = re.search(r"setvar\s+VAR_0x8005,\s*MOVETUTOR_(\w+)", body)
        if m:
            tutors[name] = f"MOVE_{m.group(1)}"
    out = []
    for m in decomp.maps(decomp_dir, version).values():
        path = Path(decomp_dir) / "data" / "maps" / m["folder"] / "scripts.inc"
        refs = set(re.findall(r"\w+", path.read_text(encoding="utf-8"))) if path.exists() else set()
        refs |= {e.get("script") for key in ("object_events", "coord_events", "bg_events") for e in m.get(key) or []}
        out += [(m["folder"], move, None) for label, move in tutors.items() if label in refs]
    found = {move for _, move, _ in out}
    assert found == set(tutors.values()), f"tutors no map calls: {sorted(set(tutors.values()) - found)}"
    specials = decomp.read(decomp_dir, "src/field_specials.c")
    for move, species in CAPE_BRINK_MOVES.items():
        assert f"SPECIES_{species.upper()}" in specials and move in specials, f"Cape Brink no longer teaches {move}"
        out.append((CAPE_BRINK, move, f"the lead Pokemon must be {species} with friendship 255 (CapeBrinkGetMoveToTeachLeadPokemon)"))
    return out


def build(con: duckdb.DuckDBPyConnection, decomp_dir: Path, version: str | None = None) -> None:
    """Create `tm_locations` and `move_tutors`. Needs `moves` and `map_sections` already built."""
    maps = decomp.maps(decomp_dir, version)
    requires = requires_for(decomp_dir)
    mapsec_location = dict(con.execute("SELECT mapsec, location FROM map_sections").fetchall())
    rows = []
    for r in extract(decomp_dir, version):
        m = maps[r["map"]]
        mapsec = m["region_map_section"]
        rows.append(
            (
                r["label"], r["method"], r["map"], m["folder"], mapsec, mapsec_location.get(mapsec), r["flag"],
                r["detail"], requires.get((r["label"], r["method"], m["folder"])),
                f"decomp:data/maps/{m['folder']}#{r['label']}",
            )
        )
    unmatched = set(requires) - {(r[0], r[1], r[3]) for r in rows}
    assert not unmatched, f"REQUIRES entries with no extracted source: {sorted(unmatched)}"
    con.execute(
        """
        CREATE TABLE tm_locations (
            label VARCHAR, method VARCHAR, map VARCHAR, map_folder VARCHAR, mapsec VARCHAR,
            location VARCHAR, flag VARCHAR, detail VARCHAR, requires VARCHAR, source_id VARCHAR
        )
        """
    )
    con.executemany("INSERT INTO tm_locations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)

    folders = {m["folder"]: map_id for map_id, m in maps.items()}
    move_ids = decomp.move_ids(decomp_dir)
    tutor_rows = []
    for folder, move_const, needs in extract_tutors(decomp_dir, version):
        map_id = folders[folder]
        mapsec = maps[map_id]["region_map_section"]
        source = "src/field_specials.c" if folder == CAPE_BRINK else "data/scripts/move_tutors.inc"
        tutor_rows.append(
            (move_ids[move_const], map_id, folder, mapsec, mapsec_location.get(mapsec), True, needs,
             f"decomp:{source}#{folder}")
        )
    con.execute(
        """
        CREATE TABLE move_tutors (
            move_id INTEGER, map VARCHAR, map_folder VARCHAR, mapsec VARCHAR, location VARCHAR,
            one_time BOOLEAN, requires VARCHAR, source_id VARCHAR
        )
        """
    )
    if tutor_rows:  # Ruby and Sapphire have none
        con.executemany("INSERT INTO move_tutors VALUES (?, ?, ?, ?, ?, ?, ?, ?)", tutor_rows)
