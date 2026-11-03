"""Write docs/review_packet.md: everything Lockesmith documents about how Emerald works,
laid out for a second model to cross-check.

    uv run python build/review_packet.py

Tables are generated from data/emerald.duckdb, data/progression.yaml and the cached
PokeAPI CSVs (build/.cache/pokeapi, for the modern values the Gen 3 layer replaced), so
the reviewer checks the data the agent actually uses, not a summary of it. Hand-written
claims cover rules and judgement calls the tables can't show; the data findings come
from docs/decisions.md. Every claim has an ID the reviewer answers against. Rerun after
any data change.
"""

import re
import sys
from datetime import date
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb
import yaml

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "emerald.duckdb"
PROGRESSION = ROOT / "data" / "progression.yaml"
DECISIONS = ROOT / "docs" / "decisions.md"
POKEAPI = ROOT / "build" / ".cache" / "pokeapi"
OUT = ROOT / "docs" / "review_packet.md"

MODERN_CSVS = (
    "moves", "types", "move_damage_classes", "pokemon", "pokemon_stats", "stats",
    "pokemon_types", "pokemon_abilities", "abilities", "pokemon_species",
)
CORE_METHODS = ("walk", "surf", "old-rod", "good-rod", "super-rod", "rock-smash", "seaweed")
STATS = ("hp", "attack", "defense", "special-attack", "special-defense", "speed")


# --- helpers ----------------------------------------------------------------------------


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"ATTACH '{DB.as_posix()}' AS e (READ_ONLY)")
    for name in MODERN_CSVS:
        path = (POKEAPI / f"{name}.csv").as_posix()
        con.execute(f"CREATE VIEW modern_{name} AS SELECT * FROM read_csv('{path}', header=true, sample_size=-1)")
    return con


def table(headers: list[str], rows: list[list]) -> str:
    def cell(v) -> str:
        if v is None or v == []:
            return "—"
        if isinstance(v, (list, tuple)):
            v = ", ".join(str(x) for x in v)
        return str(v).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


def title(identifier: str | None) -> str | None:
    return identifier.replace("-", " ").title() if identifier else identifier


def names(con, kind: str) -> dict[str, str]:
    key = {"moves": "identifier", "species": "identifier"}[kind]
    return dict(con.execute(f"SELECT {key}, name FROM e.{kind}").fetchall())


# --- hand-written sections ----------------------------------------------------------------

INSTRUCTIONS = """\
## How to review this packet

You are a second reviewer for **Lockesmith**, a research agent that answers questions about
**Pokémon Emerald (English, Gen 3, unmodified)**: what to catch, where, and how to beat the rest
of the main story, including Nuzlocke and randomized runs. Postgame and the Battle Frontier are
out of scope except where a claim says "postgame" to mark something unreachable.

Everything below is what the agent will treat as fact. Each claim has an ID (`M-03`, `P-12`,
`MV-242`, ...). Please check as many as you can, prioritising sections 4 to 6 (progression,
trainers, locations), where judgement calls live.

**About sources.** Most data comes from the **pret/pokeemerald decompilation** (the game's own
code and data; claims tagged `[decomp]`) and **PokeAPI** (tagged `[pokeapi]`), with Bulbapedia's
Emerald walkthrough for story order (`[guide]`). A decomp-tagged claim was read from the game's
code, so if you disagree, say what you think was misread, not only what you remember. Memory
of Ruby/Sapphire, FireRed/LeafGreen or the 3DS remakes is a common source of false alarms, so
please check that a disagreement applies to Emerald specifically.

**Answer in this format:**

1. **Disagreements**: a table with columns `ID | our claim (short) | what you believe instead |
   confidence (high/medium/low) | evidence (named source, or "memory") | suggested fix`.
2. **Unsure**: the same table, for claims you suspect but can't confirm.
3. **Missing**: facts, caveats or battles the agent should know that this packet omits, with the
   section they belong in.
4. **Answers to the open questions** (section 9, `Q-` IDs).
5. **Agreed**: the IDs or ID ranges you checked and agree with. Leave out IDs you didn't check.

Skip wording and formatting nitpicks. "Unsure" is a useful answer; a confident wrong correction
costs more than a missed one.
"""

METHOD = """\
## 1. Sources and method

- **Ground truth order**: decomp > PokeAPI > walkthrough. Where PokeAPI disagreed with the decomp,
  the build patches PokeAPI to match (see D-items). Tests cross-check species, moves, the type chart,
  all level-up learnsets, all evolutions and every wild table against the decomp.
- **Gen 3 correction layer** `[pokeapi]`: PokeAPI stores modern values plus history tables. For
  types, stats and abilities, a `*_past` row's `generation_id` is the *last* generation that value
  applied, so the build takes the earliest past row with `generation_id >= 3`. For moves, it takes
  the earliest `move_changelog` change after Gen 3 per field (the value before that change).
- **Scope of the database**: National Dex 1–386, moves 1–354, Gen 3 abilities, Emerald (version
  group 6) learnsets, Emerald (version 9) encounters, 855 trainer structs (854 with parties).
"""

MECHANICS = """\
## 2. Battle mechanics and game rules

- **M-01** `[decomp]` A damaging move's category comes from its **type**, not the move: Normal, Fighting,
  Flying, Poison, Ground, Rock, Bug, Ghost and Steel moves are physical; Fire, Water, Grass,
  Electric, Psychic, Ice, Dragon and Dark moves are special. Status moves stay status whatever
  their type. So Crunch (Dark) is special and Shadow Ball (Ghost) is physical in Emerald; the
  full list of moves whose category differs from modern games is MV-category. Hidden Power (type
  from IVs) and Weather Ball (type from weather) take their category from the type they have in
  battle (`typeOverride` in `pokemon.c`), so their category is stored as `varies`.
- **M-02** There are 17 types and **no Fairy type**. The `???` type exists only on Curse and has no
  matchups.
- **M-03** `[decomp]` Type chart: the generated chart below lists every non-neutral matchup. Versus
  Gen 6+, the differences are that Steel also resists Ghost and Dark, and nothing involves Fairy.
  (The ROM table also has Foresight-only entries letting Normal/Fighting hit Ghost; not modelled.)
- **M-04** No hidden abilities. Each species has one or two Gen 3 abilities (ability IDs 1–76).
- **M-05** `[decomp]` Species types, base stats and abilities are Gen 3's. Table SP lists every species
  whose Gen 3 values differ from the modern PokeAPI default form (e.g. Gardevoir is pure Psychic).
- **M-06** `[decomp]` Move type, power, accuracy and PP are Gen 3's. Table MV lists every move whose
  Gen 3 values differ from modern PokeAPI.
- **M-07** `[decomp]` Level-up learnsets are Emerald's and match the ROM exactly, in ROM order. TM/HM,
  tutor and egg moves come from PokeAPI's Emerald version group.
- **M-08** `[decomp]` **Default trainer movesets.** A trainer Pokémon whose party entry has no custom
  moves gets `GiveBoxMonInitialMoveset`: walk its level-up learnset in ROM order up to its level,
  skip moves it already knows, and when it already has four, drop the oldest (first) move and
  append the new one. Custom movesets are used as written.
- **M-09** `[decomp]` **Trainer IVs**: a party entry stores one IV byte 0–255; all six IVs are
  `iv * 31 / 255` (integer division). E.g. byte 200 -> 24.
- **M-10** `[pokeapi]` Encounter slot rates (generated below): which slot an encounter uses once one
  happens. How often an encounter happens is a separate per-map rate (the `rate=` of each table).
  Mirage Island's grass is stored as one Wynaut slot at 100%, because every slot there is Wynaut.
- **M-11** `[decomp]` Fishing: each map has one 10-slot fishing table split by rod: Old Rod slots 0–1,
  Good Rod 2–4, Super Rod 5–9 (`wild_encounters.json` groups). Feebas: Route 119 has up to 6 Feebas
  tiles drawn from a seed (the current Dewford trendy phrase); tile numbers 1-3 are re-rolled as
  inaccessible and duplicates aren't, so there can be fewer than six, and they move when the phrase
  changes. Fishing on one gives Feebas 50% of the time, otherwise the normal table
  (`wild_encounter.c` `CheckFeebas`, `NUM_FEEBAS_SPOTS`).
- **M-12** `[decomp]` Field-move badge requirements (an HM is usable outside battle only with the
  badge): Cut: Stone, Flash: Knuckle, Rock Smash: Dynamo, Strength: Heat, Surf: Balance,
  Fly: Feather, Dive: Mind, Waterfall: Rain. Only Waterfall was checked in code
  (`field_control_avatar.c`: climbing needs `FLAG_BADGE08_GET`); the rest are from the walkthrough.
- **M-13** Deoxys in Emerald is the **Speed Forme** at runtime (the ROM's species table keeps Normal
  Forme stats and swaps them in battle). Event-only, so out of scope.
- **M-14** `[decomp]` Tate & Liza is a double battle (trainer struct flag). The Mossdeep Space Center
  fight is a multi battle with Steven as partner, set up by a map script; both opposing trainer
  structs say single.
- **M-15** No Gen 4+ relatives exist: table LG lists the pre-evolutions and evolutions that were
  removed, and table EV lists every Emerald evolution with its method. Friendship evolutions need 220
  (`FRIENDSHIP_EVO_THRESHOLD`); Wurmple's branch depends on its personality value; Shedinja appears
  when Nincada evolves with an empty party slot (no Poké Ball needed in Gen 3).
- **M-16** `[decomp]` Story-trainer Pokémon always have their species' first ability:
  `CreateNPCTrainerParty` gives them even personality values (0x80/0x78/0x88 plus `nameHash << 8`) and
  the ability slot is `personality & 1`. Natures are fixed per trainer too, but not computed here.
"""

LOCATIONS = """\
## 5. Locations and encounter mapping

- **L-01** `[decomp]` The decomp's region-map sections (MAPSEC) bridge maps to PokeAPI: a section's
  index equals PokeAPI's Gen 3 `location_game_indices`. Randomizer logs name wild sets by MAPSEC name.
- **L-02** Underwater maps (Routes 124 and 126) are PokeAPI areas `hoenn-route-124/underwater` and
  `hoenn-route-126/underwater`; their encounters use the `seaweed` method and need Dive.
- **L-03** `[decomp]` Emerald's Aqua Hideout section has no PokeAPI Gen 3 index (the old index points
  at Ruby's Magma Hideout); the build maps it to `team-aqua-hideout` by hand.
- **L-04** `[decomp]` Altering Cave (Route 103) opens only after the Hall of Fame: `Route103_OnLoad`
  sets the cave-entrance tiles only when `FLAG_SYS_GAME_CLEAR` is set. Of its wild sets, only the
  first (Zubat) is active without Mystery Gift events, so only that set counts.
- **L-05** Mirage Island lives inside the Route 130 map and only appears on some days; its table is
  all Wynaut.
- **L-06** PokeAPI lists Emerald encounters for Cave of Origin B2F and B3F, which are unused
  Ruby/Sapphire maps in Emerald. They are marked never reachable.
- **L-07** Meteor Falls' PokeAPI areas map to ROM rooms by wild table: `main` = 1F 1R; `back` and
  `b1f` = 1F 2R and B1F 1R (identical tables, so which is which can't be told from data);
  `backsmall-room` = B1F 2R (the only Bagon room).
- **L-08** `[decomp]` Wild tables: 216 of 219 PokeAPI location/method pairs match the decomp outright;
  the other three are explained by the `seaweed` method and Mirage Island being in the Route 130 map.
- **L-09** Encounter conditions the data uses (generated below) gate fossils, in-game trades, the
  TV choice that sets the roaming Latios/Latias, and Hall of Fame progress.
"""

PROGRESSION_RULES = """\
## 4. Story progression (data/progression.yaml)

This is the most judgement-heavy section and the one we most want checked.

- **P-R1** The progression lists **32 story battles**, from the first rival fight to the Champion: all
  8 gyms, the Elite Four, the Champion, all 5 rival fights (Rustboro and Lilycove optional), both
  Wally fights, every Maxie/Archie fight, the Magma/Aqua admins, and the three early grunt fights that
  block the story. Generic hideout grunts and route trainers are left out.
- **P-R2** **Area rule**: each encounter area is listed (`areas_new`) at the first battle it can be
  reached before, having fought only the battles above it in this order. Detours that need no listed
  battle count, so an area can open before the walkthrough visits it. An area counts only once the
  player can *stand* in it (riding Mr. Briney's boat across open water doesn't count). An entry can be
  limited to some encounter methods, e.g. Route 115's beach opens for fishing before its grass.
  "Reachable before X" is the accumulation of `areas_new` up to and including X, minus the areas that
  have closed by then (P-R10). Item and HM gates still apply on top (Surf, rods, Rock Smash, Dive for
  seaweed).
- **P-R3** An HM counts as open (`hm_gates_open`) when the player holds it *and* has the badge that
  allows its field use (M-12), at the point the walkthrough hands it over.
- **P-R4** `[decomp]` **Badge order is looser than this list.** Only Norman's gym checks earlier badges:
  each of the first four gyms adds 1 to `VAR_PETALBURG_GYM_STATE`, and Norman's gym opens at 6
  (i.e. after all four, in any order). Brawly can be deferred until Norman, and nothing from Fortree
  to the Magma Hideout checks Winona's badge. The file keeps the standard order.
- **P-R5** Rival fights depend on the player's starter (the rival takes the starter with the type
  advantage) and on which rival you have (May if you play Brendan, and vice versa). May's and
  Brendan's teams differ in species in two fights: Rustboro if you chose Torchic (Torkoal vs Slugma)
  and Route 119 if you chose Mudkip (Lombre vs Pelipper). The Route 110 lead also differs for Mudkip
  players.
- **P-R6** Nothing is catchable before the first rival fight: Birch hands out Poké Balls afterwards.
- **P-R7** The **eight placements that were judgement calls** were checked against decomp event
  scripts and Bulbapedia on 2026-11-01; each battle's notes cite the evidence (variable and flag
  names are the decomp's). These are P-03, P-04, P-06, P-07, P-09, P-11, P-17/P-18 and P-26/P-27.
  A first cross-check round then moved the open-water routes, Route 115's grass, the eastern sea,
  Sootopolis and the Regi caves (D7).
- **P-R8** Grunt fights outside the 32 battles are noted on the battle they precede (Mt. Chimney,
  Weather Institute, Mt. Pyre summit, Space Center) with their trainer constants; the hideouts carry
  a general warning. The optional Winstrate family (Route 111, four battles with no healing) is noted
  at P-09.
- **P-R9** A route can open in stages: an entry limited to some methods (Route 110's grass before
  Brawly, its water after the museum; Route 111's pond and rocks from Mauville, its desert grass after
  the Go-Goggles). `never_reachable` entries can be method-limited the same way, so a postgame gift
  doesn't make its town unreachable.
- **P-R10** Areas can also close for good (`closes`, listed as CL below). One with a battle is still
  reachable before that battle and gone for every later one, so the tools stop offering its
  encounters; until then they flag them as missable. One without a battle closes on something the
  player does, so it's only flagged.
"""

RANDOMIZER = """\
## 8. Randomizer log format (Universal Pokémon Randomizer ZX)

These formats were read from **UPR ZX's own logging code** (`Randomizer.java` log methods,
`TrainerPokemon.toString`, `StaticEncounter.toString`, `Gen3RomHandler.java`), but no real Emerald log
has been through the parser yet.

- **R-01** Sections are headed `--Name--`: `--Wild Pokemon--`, `--Trainers Pokemon--`, `--TM Moves--`,
  `--Move Tutor Moves--`, `--Pokemon Base Stats & Types--`, `--Randomized Evolutions--`, `--Static Pokemon--`,
  and one of `--Custom Starters--` / `--Random Starters--` / `--Random 2-Evolution Starters--`. Evolution
  *methods* changed by settings get their own sections (`--Removing Impossible Evolutions--`,
  `--Making Evolutions Easier--` with "Friendship evolutions now take 160 happiness (was 220).",
  `--Removing Timed-Based Evolutions--`), parsed as `A -> B at level N` / `using a ITEM` / `now also
  evolves into B at minimum level N`. Between sections UPR prints status lines such as `Trainers:
  Unchanged.` and `Pokemon Movesets: Metronome Only.`
- **R-09** The parser keeps a per-kind record (`changes`): parsed, unparsed, metronome-only or unchanged.
  Tools answer a kind from vanilla only when the log never mentions it or says `Unchanged`. Sections it
  recognizes but doesn't parse yet (movesets, TM/tutor compatibility, move data, trades, shops) block
  vanilla answers for that kind.
- **R-02** Wild sets: `Set #N - ROUTE 104 Grass/Cave (rate=20)`; Gen 3 labels are `Grass/Cave`, `Surfing`,
  `Rock Smash`, `Fishing`. Then one line per slot: `Zigzagoon Lv2` or `Zigzagoon Lvs 2-4`, padded, then
  `HP .. ATK .. DEF .. SPATK .. SPDEF .. SPEED ..`.
- **R-03** Set numbers follow the ROM's wild-header order, grass/surf/rock smash/fishing per map. UPR skips
  a table whose data pointer it has already seen; no two Emerald tables share one, so all 209 sets
  appear and set N maps to an exact map even when several share a name (`GRANITE CAVE`).
- **R-04** Fishing is one 10-slot set split Old 0–1, Good 2–4, Super 5–9 (M-11).
- **R-05** Trainers: `#265 (ROXANNE)@31F0C8 - Geodude Lv12, Nosepass@Oran Berry Lv15` (compact). With
  moveset logging the header stands alone and each Pokémon has a line:
  `Geodude@Oran Berry Lv12, Ability: STURDY - TACKLE, DEFENSE CURL`. Renamed trainers print `(OLD => NEW)`.
  `#N` is the ROM trainer-table index, which equals the decomp id (`TRAINER_ROXANNE_1 = 265`).
  Emerald logs add one pseudo-trainer after the last real one (#855): Steven's Space Center team.
- **R-06** `--TM Moves--` lines are `TM01 THUNDERBOLT`; tutors are `OLDMOVE -> NEWMOVE`. Move names are the
  ROM's (e.g. `FAINT ATTACK` for Feint Attack).
- **R-07** Evolutions: `RALTS -> KIRLIA`, branching as `WURMPLE -> SILCOON and CASCOON`. Starters:
  `Set starter 1 to BAGON`. Statics: `VOLTORB Lv25 => PIKACHU Lv25`, with `(2)` on repeats.
- **R-08** A log that randomizes learnsets (`--Pokemon Movesets--`) isn't parsed; the agent says it can't
  answer movesets for that run.
"""

QUESTIONS = """\
## 9. Open questions

- **Q-01** Which other routes open in stages (P-R9) that the file still treats as one unlock point?
  Shorelines you can fish from before Surf are the likeliest cases.
- **Q-02** Are any TM sources still missing a `Requires` gate (section 7)?
- **Q-03** Does anything else in UPR's Emerald output change game data without its own section or
  status line (R-01, R-09)?
"""


# --- generated sections ---------------------------------------------------------------------


def header(con) -> str:
    info = dict(con.execute("SELECT key, value FROM e.build_info").fetchall())
    return (
        "# Lockesmith: Pokémon Emerald facts for cross-checking\n\n"
        f"Generated {date.today().isoformat()} by `build/review_packet.py` from the database built "
        f"{info['built_at'][:10]}: pokeemerald `{info['pokeemerald_sha'][:12]}`, PokeAPI "
        f"`{info['pokeapi_sha'][:12]}`. Bulbapedia text is CC BY-NC-SA 2.5.\n\n"
        "Two previous review rounds were applied after re-verification; docs/decisions.md D7 says what "
        "changed. Fresh eyes on sections 4, 5 and 7 are still the most useful.\n\n"
        "**ID prefixes**: M mechanics, MV moves, SP species, LG later-gen relatives, EV evolutions, "
        "D data findings, P/N progression, K trainer teams, L locations, SE special encounters, "
        "TM/TU machines and tutors, R randomizer, Q questions.\n"
    )


def type_chart(con) -> str:
    damage = con.execute(
        "SELECT identifier, damage_class FROM e.types ORDER BY type_id"
    ).fetchall()
    rows = con.execute(
        "SELECT attacking_type, multiplier, list(defending_type ORDER BY defending_type) "
        "FROM e.type_efficacy WHERE multiplier <> 1 GROUP BY ALL ORDER BY attacking_type, multiplier DESC"
    ).fetchall()
    by_attacker: dict[str, dict[float, list[str]]] = {}
    for attacker, mult, defenders in rows:
        by_attacker.setdefault(attacker, {})[mult] = defenders
    lines = [
        "**M-03 type chart** (attacker -> defenders; unlisted pairs are 1x):\n",
        table(
            ["Attacking type", "Category", "2x", "0.5x", "0x"],
            [
                [t, cls, by_attacker.get(t, {}).get(2.0), by_attacker.get(t, {}).get(0.5), by_attacker.get(t, {}).get(0.0)]
                for t, cls in damage
            ],
        ),
    ]
    return "\n".join(lines)


def slot_rates(con) -> str:
    rows = con.execute(
        "SELECT method, list(slot || ': ' || rarity || '%' ORDER BY slot) FROM ("
        " SELECT DISTINCT method, slot, rarity FROM e.encounters"
        " WHERE method IN ('walk','surf','old-rod','good-rod','super-rod','rock-smash','seaweed')"
        " AND location <> 'mirage-island') GROUP BY 1 ORDER BY 1"
    ).fetchall()
    return "**M-10 encounter slot rates**\n\n" + table(["Method", "Slot: rate"], [[m, s] for m, s in rows])


def move_diffs(con) -> str:
    rows = con.execute(
        """
        SELECT g.move_id, g.name, g.type, t.identifier, g.damage_class, dc.identifier,
               g.power, m.power, g.accuracy, m.accuracy, g.pp, m.pp, g.rom_patched
        FROM e.moves g
        JOIN modern_moves m ON m.id = g.move_id
        JOIN modern_types t ON t.id = m.type_id
        JOIN modern_move_damage_classes dc ON dc.id = m.damage_class_id
        ORDER BY g.move_id
        """
    ).fetchall()
    changed, category, never_miss = [], {"special": [], "physical": [], "varies": []}, []
    for mid, name, typ, m_typ, cls, m_cls, pw, m_pw, acc, m_acc, pp, m_pp, patched in rows:
        if cls != m_cls and "status" not in (cls, m_cls):
            category[cls].append(f"{name} ({typ}; now {m_cls})" if cls == "varies" else f"{name} ({typ})")
        diffs = []
        if typ != m_typ:
            diffs.append(f"type {typ} (now {m_typ})")
        if pw != m_pw:
            diffs.append(f"power {pw} (now {m_pw})")
        if acc != m_acc:
            if acc == 100 and m_acc is None:
                never_miss.append(name)
            else:
                diffs.append(f"accuracy {acc} (now {m_acc})")
        if pp != m_pp:
            diffs.append(f"PP {pp} (now {m_pp})")
        if cls != m_cls and "status" in (cls, m_cls):
            diffs.append(f"category {cls} (now {m_cls})")
        if diffs:
            changed.append([f"MV-{mid}", name, "; ".join(diffs), patched])
    return "\n\n".join([
        "### Moves (MV)\n\nEvery move whose Gen 3 type, power, accuracy or PP differs from modern PokeAPI. "
        "`ROM-patched` names fields the build took from the decomp because PokeAPI's history tables "
        "missed the change.",
        table(["ID", "Move", "Gen 3 value (modern value)", "ROM-patched"], changed),
        "**MV-category**: moves whose physical/special category differs from modern games because of "
        f"M-01.\n\n- Special in Gen 3, physical now ({len(category['special'])}): "
        + ", ".join(category["special"])
        + f"\n- Physical in Gen 3, special now ({len(category['physical'])}): "
        + ", ".join(category["physical"])
        + "\n- Category follows the in-battle type (M-01): " + ", ".join(category["varies"]),
        f"**MV-accuracy**: {len(never_miss)} moves the ROM stores with accuracy 100 where PokeAPI uses "
        "null (can't miss, or no accuracy check): " + ", ".join(never_miss) + ".",
    ])


def species_diffs(con) -> str:
    stat_cols = ", ".join(
        f"max(CASE WHEN st.identifier = '{s}' THEN ps.base_stat END) AS \"{s}\"" for s in STATS
    )
    rows = con.execute(
        f"""
        WITH d AS (SELECT id, species_id FROM modern_pokemon WHERE is_default = 1 AND species_id <= 386),
        ms AS (SELECT d.species_id, {stat_cols}
               FROM d JOIN modern_pokemon_stats ps ON ps.pokemon_id = d.id
               JOIN modern_stats st ON st.id = ps.stat_id GROUP BY 1),
        mt AS (SELECT d.species_id,
                      max(CASE WHEN pt.slot = 1 THEN t.identifier END) AS t1,
                      max(CASE WHEN pt.slot = 2 THEN t.identifier END) AS t2
               FROM d JOIN modern_pokemon_types pt ON pt.pokemon_id = d.id
               JOIN modern_types t ON t.id = pt.type_id GROUP BY 1),
        ma AS (SELECT d.species_id,
                      max(CASE WHEN pa.slot = 1 AND pa.is_hidden = 0 THEN a.identifier END) AS a1,
                      max(CASE WHEN pa.slot = 2 AND pa.is_hidden = 0 THEN a.identifier END) AS a2
               FROM d JOIN modern_pokemon_abilities pa ON pa.pokemon_id = d.id
               JOIN modern_abilities a ON a.id = pa.ability_id GROUP BY 1)
        SELECT g.species_id, g.name, g.type1, g.type2, mt.t1, mt.t2,
               [g.hp, g.attack, g.defense, g.sp_attack, g.sp_defense, g.speed],
               [ms."hp", ms."attack", ms."defense", ms."special-attack", ms."special-defense", ms."speed"],
               g.ability1, g.ability2, ma.a1, ma.a2
        FROM e.species g JOIN ms USING (species_id) JOIN mt USING (species_id) JOIN ma USING (species_id)
        ORDER BY g.species_id
        """
    ).fetchall()
    out = []
    for sid, name, t1, t2, m1, m2, stats, m_stats, a1, a2, ma1, ma2 in rows:
        diffs = []
        if (t1, t2) != (m1, m2):
            diffs.append(f"type {'/'.join(filter(None, (t1, t2)))} (now {'/'.join(filter(None, (m1, m2)))})")
        if list(stats) != list(m_stats):
            labels = ("HP", "Atk", "Def", "SpA", "SpD", "Spe")
            diffs.append("stats " + ", ".join(
                f"{lab} {a} (now {b})" for lab, a, b in zip(labels, stats, m_stats) if a != b
            ))
        if {a1, a2} - {None} != {ma1, ma2} - {None}:
            diffs.append(f"abilities {'/'.join(filter(None, (a1, a2)))} (now {'/'.join(filter(None, (ma1, ma2)))})")
        if diffs:
            out.append([f"SP-{sid}", name, "; ".join(diffs)])
    return (
        "### Species (SP)\n\nEvery species whose Gen 3 types, base stats or (non-hidden) abilities differ "
        "from the modern PokeAPI default form. Hidden abilities don't exist in Gen 3 (M-04) and aren't listed.\n\n"
        + table(["ID", "Species", "Gen 3 value (modern value)"], out)
    )


def later_gen_relatives(con) -> str:
    pre = con.execute(
        "SELECT s.id, g.name, p.identifier FROM modern_pokemon_species s "
        "JOIN modern_pokemon_species p ON p.id = s.evolves_from_species_id "
        "JOIN e.species g ON g.species_id = s.id WHERE s.id <= 386 AND p.id > 386 ORDER BY s.id"
    ).fetchall()
    post = con.execute(
        "SELECT p.id, g.name, list(c.identifier ORDER BY c.id) FROM modern_pokemon_species c "
        "JOIN modern_pokemon_species p ON p.id = c.evolves_from_species_id "
        "JOIN e.species g ON g.species_id = p.id WHERE p.id <= 386 AND c.id > 386 GROUP BY ALL ORDER BY p.id"
    ).fetchall()
    rows = [[f"LG-{sid}", name, "pre-evolution", title(p)] for sid, name, p in pre]
    rows += [[f"LG-{sid}", name, "evolution", ", ".join(title(c) for c in cs)] for sid, name, cs in post]
    return (
        "### Later-generation relatives that don't exist in Emerald (LG)\n\n"
        + table(["ID", "Species", "Relation", "Removed relative"], sorted(rows, key=lambda r: int(r[0][3:])))
    )


def evolutions(con) -> str:
    rows = con.execute(
        """
        SELECT f.species_id, f.name, t.name, ev.trigger, ev.min_level, ev.item, ev.held_item,
               ev.min_happiness, ev.min_beauty, ev.time_of_day, ev.relative_physical_stats, ev.needs_trade, ev.note
        FROM e.evolutions ev
        JOIN e.species f ON f.species_id = ev.from_species_id
        JOIN e.species t ON t.species_id = ev.to_species_id
        ORDER BY ev.from_species_id, ev.to_species_id
        """
    ).fetchall()
    rel = {1: "Atk > Def", 0: "Atk = Def", -1: "Atk < Def"}
    out = []
    for sid, frm, to, trig, lvl, item, held, happy, beauty, tod, phys, trade, note in rows:
        parts = [trig]
        if lvl is not None:
            parts.append(f"level {lvl}")
        if item:
            parts.append(f"item {item}")
        if held:
            parts.append(f"holding {held}")
        if happy is not None:
            parts.append(f"friendship >= {happy}")
        if beauty is not None:
            parts.append(f"beauty >= {beauty}")
        if tod:
            parts.append(tod)
        if phys is not None:
            parts.append(rel[phys])
        if trade:
            parts.append("trade")
        if note:
            parts.append(note)
        out.append([f"EV-{sid}", frm, to, ", ".join(parts)])
    return f"### Evolutions (EV), all {len(out)}\n\n" + table(["ID", "From", "To", "Method"], out)


def data_findings() -> str:
    text = DECISIONS.read_text(encoding="utf-8")
    findings = text.split("## Data findings", 1)[1]
    # decisions.md cross-references, rewritten to this packet's IDs
    refs = {"finding 1 below": "D-1", "(D5)": "(P-R5)"}

    def relink(s: str) -> str:
        for old, new in refs.items():
            s = s.replace(old, new)
        return s

    items = [(n, relink(b)) for n, b in re.findall(r"^(\d+)\. (.+)$", findings, flags=re.M)]
    d6 = text.split("## D6.", 1)[1].split("\n## ", 1)[0]
    bullets = [relink(b) for b in re.findall(r"^- (.+)$", d6, flags=re.M)]
    lines = ["## 3. Data findings (where sources disagree)\n",
             "Copied from docs/decisions.md. PokeAPI was patched to the decomp for each of these.\n"]
    lines += [f"- **D-{n}** {body}" for n, body in items]
    lines += ["", "What the build takes from the decomp instead of PokeAPI:", ""]
    lines += [f"- **D-R{i}** {b}" for i, b in enumerate(bullets, 1)]
    return "\n".join(lines)


def progression(con) -> str:
    raw = yaml.safe_load(PROGRESSION.read_text(encoding="utf-8"))
    out = [PROGRESSION_RULES, "### Battles in order\n"]
    for b in sorted(raw["battles"], key=lambda b: b["order"]):
        flags = [f"badges before: {b['badges_before']}", b["battle_format"], "optional" if b.get("optional") else "required"]
        out.append(f"- **P-{b['order']:02d}** {b['label']} (`{b['id']}`, at `{b['location']}`): {', '.join(flags)}.")
        if b.get("trainer_consts"):
            out.append(f"  - Trainers: {', '.join(b['trainer_consts'])} (teams: K-{b['id']})")
        else:
            out.append(f"  - Trainers: depend on starter and rival (teams: K-{b['id']})")
        if b.get("partner"):
            p = b["partner"]
            out.append(f"  - Partner: {p['name']}, " + ", ".join(f"{title(s)} Lv{lv}" for s, lv in p["team"]))
        out.append(f"  - HMs usable: {', '.join(b.get('hm_gates_open') or []) or 'none'}; "
                   f"key items: {', '.join(b.get('key_items') or []) or 'none'}")
        areas = [a if isinstance(a, str) else f"{a['area']} ({', '.join(a['methods'])} only)" for a in b.get("areas_new") or []]
        out.append(f"  - Areas newly reachable before this battle: {', '.join(areas) or 'none'}")
        if b.get("notes"):
            out.append(f"  - Notes: {b['notes']}")
        out.append(f"  - Source: `{b['source']}`")
    out.append("\n### Never reachable before the Champion (N)\n")
    out += [
        f"- **N-{i:02d}** `{n['area']}`" + (f" ({', '.join(n['methods'])} only)" if n.get("methods") else "")
        + f": {n['reason']}"
        for i, n in enumerate(raw["never_reachable"], 1)
    ]
    out.append("\n### Areas that close for good (CL)\n")
    out += [
        f"- **CL-{i:02d}** `{c['area']}`" + (f" ({', '.join(c['methods'])} only)" if c.get("methods") else "")
        + (f", gone after `{c['after']}`" if c.get("after") else ", closes on a player action")
        + f": {c['reason']}"
        for i, c in enumerate(raw.get("closes") or [], 1)
    ]
    return "\n".join(out)


def trainer_teams(con) -> str:
    raw = yaml.safe_load(PROGRESSION.read_text(encoding="utf-8"))
    move_names, species_names = names(con, "moves"), names(con, "species")
    out = ["## 6. Trainer teams for the story battles (K)\n",
           "`[decomp]` From `trainer_parties.h` and `trainers.h`. Moves marked *default* were computed with "
           "M-08; *custom* are written in the party data. IVs are on the 0–31 scale (M-09).\n"]
    for b in sorted(raw["battles"], key=lambda b: b["order"]):
        if b.get("trainer_consts"):
            consts = [(None, c) for c in b["trainer_consts"]]
        else:
            consts = [(f"{starter} player, rival {rival}", c)
                      for starter, v in b["starter_variants"].items() for rival, c in v.items()]
        out.append(f"### K-{b['id']}: {b['label']}\n")
        for variant, const in consts:
            t = con.execute(
                "SELECT class_name, name, is_double, items FROM e.trainers WHERE trainer_const = ?", [const]
            ).fetchone()
            mons = con.execute(
                "SELECT level, species, held_item, moves, moves_source, iv_value, ability FROM e.trainer_mons "
                "WHERE trainer_const = ? ORDER BY slot", [const]
            ).fetchall()
            bag = ", ".join(title(i) for i in (t[3] or [])) or "none"
            label = f"{t[0]} {t[1]}" + (" (double)" if t[2] else "")
            prefix = f"{variant}: " if variant else ""
            out.append(f"- {prefix}**{label}** `{const}`; bag: {bag}")
            for lvl, sp, held, moves, src, iv, ability in mons:
                item = f" @ {title(held)}" if held else ""
                ms = " / ".join(move_names.get(m, m) for m in moves)
                out.append(f"  - Lv{lvl} {species_names.get(sp, sp)}{item}, {title(ability)}, IVs {iv}: {ms} ({src})")
        out.append("")
    return "\n".join(out)


def locations(con) -> str:
    conds = [c for (c,) in con.execute(
        "SELECT DISTINCT unnest(conditions) AS c FROM e.encounters ORDER BY c").fetchall()]
    special = con.execute(
        f"""
        SELECT e.location, e.area, e.method, s.name, e.min_level, e.max_level, e.conditions
        FROM e.encounters e JOIN e.species s USING (species_id)
        WHERE e.method NOT IN {CORE_METHODS}
        ORDER BY e.method, e.location, s.species_id
        """
    ).fetchall()
    rows = [[f"SE-{i:02d}", loc + (f"/{area}" if area else ""), method, sp,
             f"{lo}" if lo == hi else f"{lo}-{hi}", cond] for i, (loc, area, method, sp, lo, hi, cond) in enumerate(special, 1)]
    rom = con.execute("SELECT condition, decomp_symbol, description FROM e.rom_conditions ORDER BY 1").fetchall()
    return "\n\n".join([
        LOCATIONS,
        "**L-09 encounter conditions**: " + ", ".join(f"`{c}`" for c in conds),
        "**L-10** `[decomp]` Conditions PokeAPI doesn't model, added by the build to the rows they gate "
        "(Regis, Rayquaza, Mirage Island):\n\n"
        + table(["Condition", "Decomp symbol", "Meaning"], [list(r) for r in rom]),
        "### Special encounters (SE): statics, gifts, trades, roamers and other non-wild methods\n\n"
        + table(["ID", "Location/area", "Method", "Species", "Level", "Conditions"], rows),
    ])


def machines(con) -> str:
    rows = con.execute(
        """
        SELECT m.label, mv.name, tl.method, tl.location, tl.map_folder, tl.detail, tl.requires
        FROM e.machines m JOIN e.moves mv USING (move_id)
        LEFT JOIN e.tm_locations tl ON tl.label = m.label
        ORDER BY m.machine_number, tl.method, tl.map_folder
        """
    ).fetchall()
    tutors = con.execute(
        "SELECT mv.name, t.location, t.map_folder, t.one_time FROM e.move_tutors t "
        "JOIN e.moves mv USING (move_id) ORDER BY mv.name"
    ).fetchall()
    return "\n\n".join([
        "## 7. TM/HM sources and move tutors\n\n`[decomp]` From map data: item balls, hidden items, NPC "
        "gifts, marts and Game Corner prizes. One row per source; a TM can have several. Gym TMs name "
        "the leader that triggers the gift. HM field use needs a badge (M-12).",
        "`Requires` is hand-checked against decomp scripts or Bulbapedia: what the source needs beyond "
        "reaching its map (an HM, a key, a side quest, a party condition, postgame).",
        table(["ID", "Move", "Method", "Location", "Map", "Detail", "Requires"],
              [[f"TM-{lab}", mv, meth, loc, mp, det, req] for lab, mv, meth, loc, mp, det, req in rows]),
        "### Move tutors (TU)\n\nEach Hoenn tutor teaches once in Emerald; the other tutors are at the "
        "postgame Battle Frontier.\n\n"
        + table(["ID", "Move", "Location", "Map", "One time"],
                [[f"TU-{i:02d}", mv, loc, mp, ot] for i, (mv, loc, mp, ot) in enumerate(tutors, 1)]),
    ])


def main() -> None:
    con = connect()
    parts = [
        header(con),
        INSTRUCTIONS,
        METHOD,
        MECHANICS,
        type_chart(con),
        slot_rates(con),
        move_diffs(con),
        species_diffs(con),
        later_gen_relatives(con),
        evolutions(con),
        data_findings(),
        progression(con),
        locations(con),
        trainer_teams(con),
        machines(con),
        RANDOMIZER,
        QUESTIONS,
    ]
    OUT.write_text("\n\n".join(p.strip() for p in parts) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
