"""Write a full-size Universal Pokemon Randomizer ZX log from a game's own tables.

No ROM was available to make a real log (docs/decisions.md D19), so tests/test_full_logs.py
uses this to run the parser at full size on all five games. Every line is printed the way
UPR ZX does it (commit 7f00eb8, the version the parser follows):
- header: Randomizer.java's first three lines
- wild sets: Randomizer.logWildPokemonChanges, in the ROM's header order (wild_headers),
  named by Gen3RomHandler.getEncounters: the map name plus " Grass/Cave", " Surfing",
  " Rock Smash" or " Fishing"
- trainers: Randomizer.maybeLogTrainerChanges and TrainerPokemon.toString, numbered from 1
  and named "<CLASS> <NAME>" (Gen3RomHandler.getTrainers); Emerald adds Steven's Space
  Center team after the last trainer
- TM moves, starters: logTMMoves, logStarters
- footer and ROM diagnostics: the log tail and AbstractGBRomHandler.printRomDiagnostics
Names are the ROM's own (species.rom_name, moves.rom_name), with the apostrophe UPR's text
table prints (’, gba_english.tbl).

It shows that the parser reads UPR's format at full size, for every map, trainer and name
in each game, and returns exactly what was written. It can't show that UPR really prints
these lines; only a real log in tests/fixtures/ can.
"""

import random
from dataclasses import dataclass, field

import duckdb

from agent.randomizer_log import UPR_GEN3_ROMS

RULE = "-" * 66


@dataclass
class Written:
    """What the log says, to compare with what the parser reads back."""

    wild: dict[int, list[tuple[str, int, int]]] = field(default_factory=dict)  # set_no -> (species, min, max)
    trainers: dict[int, list[tuple]] = field(default_factory=dict)  # index -> (species, level, item, moves)
    tm_moves: dict[str, str] = field(default_factory=dict)
    starters: list[str] = field(default_factory=list)


def rom_text(name: str) -> str:
    return name.replace("'", "’")


def words(identifier: str | None) -> str | None:
    """An item or ability identifier as the ROM spells it ("oran-berry" -> "ORAN BERRY")."""
    return identifier.replace("-", " ").upper() if identifier else None


def write_log(con: duckdb.DuckDBPyConnection, rom_name: str, *, seed: int = 4570, movesets: bool = False,
              crc32: str | None = None) -> tuple[str, Written]:
    """A log with wild Pokemon, trainers, TMs and starters randomized. `crc32` defaults to
    the clean ROM's."""
    rng = random.Random(seed)
    species = con.execute(
        "SELECT identifier, rom_name, hp, attack, defense, sp_attack, sp_defense, speed, ability1 "
        "FROM species WHERE rom_name IS NOT NULL ORDER BY species_id"
    ).fetchall()
    moves = con.execute("SELECT identifier, rom_name FROM moves WHERE rom_name IS NOT NULL ORDER BY move_id").fetchall()
    game = con.execute("SELECT value FROM build_info WHERE key = 'game'").fetchone()[0]
    out = Written()
    lines = ["Randomizer Version: 4.6.1", f"Random Seed: {seed}", "Settings String: 321synthetic", ""]

    lines.append("--Random Starters--")
    for i in range(1, 4):
        sp = rng.choice(species)
        out.starters.append(sp[0])
        lines.append(f"Set starter {i} to {rom_text(sp[1])}")
    lines.append("")

    lines.append("--TM Moves--")
    for (label,) in con.execute("SELECT label FROM machines WHERE label LIKE 'TM%' ORDER BY machine_number").fetchall():
        mv = rng.choice(moves)
        out.tm_moves[label] = mv[0]
        lines.append(f"{label} {rom_text(mv[1])}")
    lines.append("")

    lines.append("--Trainers Pokemon--")
    party = {}
    for tid, level, item in con.execute(
        "SELECT trainer_id, level, held_item FROM trainer_mons ORDER BY trainer_id, slot"
    ).fetchall():
        party.setdefault(tid, []).append((level, item))
    trainers = con.execute(
        "SELECT trainer_id, class_name, name FROM trainers WHERE trainer_id > 0 ORDER BY trainer_id"
    ).fetchall()
    if game == "emerald":  # Steven's Space Center team, appended after the last trainer
        trainers.append((trainers[-1][0] + 1, "Pkmn Trainer", "Steven"))
        party[trainers[-1][0]] = [(42, None), (43, None), (44, None)]
    for n, (tid, class_name, name) in enumerate(trainers):
        head = f"#{tid} ({(class_name or '').upper()} {(name or '').upper()})@{0x31F000 + 40 * n:X}"
        mons = []
        for level, item in party.get(tid, []):
            sp = rng.choice(species)
            picked = rng.sample(moves, 4) if movesets else None
            text = rom_text(sp[1]) + (f"@{words(item)}" if item else "") + f" Lv{level}"
            if movesets:
                text += f", Ability: {words(sp[8])} - " + ", ".join(rom_text(mv[1]) for mv in picked)
            mons.append(text)
            out.trainers.setdefault(tid, []).append(
                (sp[0], level, words(item), [mv[0] for mv in picked] if movesets else None)
            )
        out.trainers.setdefault(tid, [])
        lines.extend([head, *mons, ""] if movesets else [f"{head} - " + ", ".join(mons)])
    lines.append("")

    lines.append("--Wild Pokemon--")
    for set_no, method, rate, slots, map_name in con.execute(
        "SELECT h.set_no, h.method, h.rate, h.slots, s.name FROM wild_headers h "
        "JOIN maps m USING (map) JOIN map_sections s USING (mapsec) ORDER BY h.set_no"
    ).fetchall():
        lines.append(f"Set #{set_no} - {map_name} {method} (rate={rate})")
        out.wild[set_no] = []
        for _ in range(slots):
            sp = rng.choice(species)
            lo = rng.randint(2, 60)
            hi = lo if rng.random() < 0.5 else lo + rng.randint(1, 10)
            name_level = f"{rom_text(sp[1])} Lv" + (f"s {lo}-{hi}" if hi != lo else f"{lo}")
            stats = "HP {:<3d} ATK {:<3d} DEF {:<3d} SPATK {:<3d} SPDEF {:<3d} SPEED {:<3d}".format(*sp[2:8])
            lines.append(f"{name_level:<25s}{stats}")
            out.wild[set_no].append((sp[0], lo, hi))
        lines.append("")
    lines.append("")

    clean = UPR_GEN3_ROMS[rom_name][1]
    lines += [RULE, f"Randomization of {rom_name} completed.", "Time elapsed: 2512ms", "RNG Calls: 41213", RULE, "",
              "--ROM Diagnostics--", "File name: rom.gba", f"Original ROM CRC32: {crc32 or clean}"]
    return "\n".join(lines) + "\n", out
