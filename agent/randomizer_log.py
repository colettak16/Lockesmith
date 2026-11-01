"""Parse a Universal Pokemon Randomizer ZX spoiler log for Emerald (PLAN.md section 4.5).

Written against the format described in PLAN.md and not yet checked against a real
log (tests/fixtures/ is empty), so each section parser is tolerant and records
anything it can't read in `warnings` instead of failing.

A log only has sections for what was randomized; missing sections mean "use the
vanilla tables". `load_overlay` writes what was parsed into per-session tables
that the tools read in preference to vanilla.

Wild sets are pinned to exact maps by position: UPR walks the ROM's wild-header
table in order (grass, surf, rock smash, fishing per header), and `wild_headers`
in emerald.duckdb holds that order. When a set's name or method disagrees with the
expected header, the parser falls back to a name lookup and says so.
"""

import re
from dataclasses import dataclass, field

import duckdb

from agent.entities import EntityIndex

SECTION_RE = re.compile(r"^--\s*(.+?)\s*--\s*$")
WILD_SET_RE = re.compile(r"^Set #(\d+)\s*-\s*(.+?)\s+(Grass/Cave|Surfing|Rock Smash|Fishing)\s*\(rate=(\d+)\)\s*$")
WILD_MON_RE = re.compile(r"^(?P<species>\S.*?)\s+Lvs?\s*(?P<min>\d+)(?:\s*-\s*(?P<max>\d+))?(?:\s+HP\b.*)?\s*$")
TRAINER_RE = re.compile(r"^#(\d+)\s*\((.*?)\)\s*(?:@[0-9A-Fa-f]+)?\s*-\s*(.*)$")
TRAINER_MON_RE = re.compile(
    r"^(?P<species>[^@]+?)(?:\s*@\s*(?P<item>[^@]+?))?\s+Lv\s*(?P<level>\d+)(?:\s*@\s*(?P<item2>[^-]+?))?"
    r"(?:\s*\((?P<ability>[^)]*)\))?(?:\s*-\s*(?P<moves>.*))?$"
)
TM_RE = re.compile(r"^((?:TM|HM)\d{2})\s*[-:]?\s*(.+)$")
STARTER_RE = re.compile(r"starter\s*(\d)\s*to\s*(.+)$", re.I)
ARROW_RE = re.compile(r"^(.+?)\s*(?:=>|->)\s*(.+)$")

METHODS = {"Grass/Cave": "walk", "Surfing": "surf", "Rock Smash": "rock-smash", "Fishing": "fishing"}
# Gen 3 fishing tables are one 10-slot list split by rod (pokeemerald wild_encounters.json `groups`).
FISHING_SPLIT = [("old-rod", range(0, 2)), ("good-rod", range(2, 5)), ("super-rod", range(5, 10))]

SECTION_KEYS = {
    "wild pokemon": "wild",
    "trainers pokemon": "trainers",
    "tm moves": "tm_moves",
    "pokemon base stats & types": "base_stats",
    "randomized evolutions": "evolutions",
    "static pokemon": "statics",
    "move tutor moves": "move_tutors",
}


@dataclass
class WildMon:
    slot: int
    species: str | None
    raw: str
    min_level: int
    max_level: int
    method: str


@dataclass
class WildSet:
    set_no: int
    map_name: str
    method: str  # walk | surf | seaweed | rock-smash | fishing
    rate: int
    mons: list[WildMon] = field(default_factory=list)
    location: str | None = None
    area: str | None = None
    rom_map: str | None = None  # decomp map id when the set lines up with wild_headers
    aligned: bool = False


@dataclass
class TrainerMon:
    slot: int
    species: str | None
    raw: str
    level: int
    held_item: str | None = None
    ability: str | None = None
    moves: list[str] | None = None  # None unless the log has moveset logging


@dataclass
class TrainerEntry:
    index: int
    name: str
    trainer_const: str | None
    mons: list[TrainerMon] = field(default_factory=list)


@dataclass
class RandomizerLog:
    header: dict[str, str] = field(default_factory=dict)
    sections: list[str] = field(default_factory=list)
    unparsed_sections: list[str] = field(default_factory=list)
    wild_sets: list[WildSet] = field(default_factory=list)
    trainers: dict[int, TrainerEntry] = field(default_factory=dict)
    tm_moves: dict[str, str] = field(default_factory=dict)  # TM01 -> move identifier
    base_stats: dict[str, dict] = field(default_factory=dict)  # species identifier -> stats/types/abilities
    evolutions: dict[str, list[str]] = field(default_factory=dict)
    starters: list[str] = field(default_factory=list)
    statics: list[tuple[str, str]] = field(default_factory=list)  # (vanilla species, new species)
    move_tutors: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def randomized(self, key: str) -> bool:
        return key in {SECTION_KEYS.get(s.lower(), s.lower()) for s in self.sections}


def split_sections(text: str) -> tuple[list[str], dict[str, list[str]]]:
    """Header lines before the first `--Section--`, and section name -> its lines."""
    header, sections, current = [], {}, None
    for line in text.splitlines():
        m = SECTION_RE.match(line.strip())
        if m:
            current = m.group(1)
            sections.setdefault(current, [])
        elif current is None:
            header.append(line)
        else:
            sections[current].append(line.rstrip())
    return header, sections


class LogParser:
    def __init__(self, con: duckdb.DuckDBPyConnection, index: EntityIndex | None = None):
        self.con = con
        self.index = index or EntityIndex(con)
        self.expected_sets = {
            n: (m, method, slots)
            for n, m, method, slots in con.execute("SELECT set_no, map, method, slots FROM wild_headers").fetchall()
        }
        self.map_section = {
            m: (name, loc, area)
            for m, name, loc, area in con.execute(
                "SELECT m.map, s.name, s.location, s.area FROM maps m JOIN map_sections s USING (mapsec)"
            ).fetchall()
        }
        self.section_location = {}
        for name, location, area in con.execute(
            "SELECT name, location, area FROM map_sections WHERE location IS NOT NULL"
        ).fetchall():
            self.section_location.setdefault(name.upper(), []).append((location, area))
        self.trainer_names = dict(con.execute("SELECT trainer_id, trainer_const FROM trainers").fetchall())
        self.tm_labels = {r[0] for r in con.execute("SELECT label FROM machines").fetchall()}

    def species(self, raw: str, log: RandomizerLog) -> str | None:
        m = self.index.resolve(raw, "species", cutoff=85)
        if m is None:
            log.warnings.append(f"unknown species {raw!r}")
        return m.id if m else None

    def move(self, raw: str, log: RandomizerLog) -> str | None:
        m = self.index.resolve(raw, "move", cutoff=85)
        if m is None:
            log.warnings.append(f"unknown move {raw!r}")
        return m.id if m else None

    def parse(self, text: str) -> RandomizerLog:
        log = RandomizerLog()
        header, sections = split_sections(text)
        for line in header:
            if ":" in line:
                k, v = line.split(":", 1)
                log.header[k.strip()] = v.strip()
        log.sections = list(sections)
        handlers = {
            "wild": self._wild,
            "trainers": self._trainers,
            "tm_moves": self._tm_moves,
            "base_stats": self._base_stats,
            "evolutions": self._evolutions,
            "statics": self._statics,
            "move_tutors": self._move_tutors,
        }
        for name, lines in sections.items():
            key = SECTION_KEYS.get(name.lower())
            if key is None and "starter" in name.lower():
                self._starters(lines, log)
            elif key in handlers:
                handlers[key](lines, log)
            else:
                log.unparsed_sections.append(name)
        return log

    # --- sections ---------------------------------------------------------------------

    def _wild(self, lines: list[str], log: RandomizerLog) -> None:
        current = None
        for line in lines:
            s = line.strip()
            if not s:
                continue
            m = WILD_SET_RE.match(s)
            if m:
                current = WildSet(int(m.group(1)), m.group(2).strip(), METHODS[m.group(3)], int(m.group(4)))
                self._place(current, m.group(3), log)
                log.wild_sets.append(current)
                continue
            mon = WILD_MON_RE.match(s)
            if current is None or mon is None:
                log.warnings.append(f"wild: unreadable line {s!r}")
                continue
            lo = int(mon.group("min"))
            current.mons.append(
                WildMon(len(current.mons), self.species(mon.group("species"), log), mon.group("species"), lo,
                        int(mon.group("max") or lo), current.method)
            )
        for ws in log.wild_sets:
            if ws.method == "fishing":
                if len(ws.mons) == 10:
                    for mon in ws.mons:
                        mon.method = next(rod for rod, slots in FISHING_SPLIT if mon.slot in slots)
                else:
                    log.warnings.append(f"wild: fishing set #{ws.set_no} has {len(ws.mons)} slots, expected 10")

    def _place(self, ws: WildSet, upr_method: str, log: RandomizerLog) -> None:
        """Pin a set to a ROM map by position, else to a location by its section name."""
        expected = self.expected_sets.get(ws.set_no)
        if expected:
            rom_map, method, _ = expected
            name, location, area = self.map_section.get(rom_map, (None, None, None))
            if method == upr_method and name and name.upper() == ws.map_name.upper():
                ws.rom_map, ws.location, ws.area, ws.aligned = rom_map, location, area, True
        if not ws.aligned:
            candidates = self.section_location.get(ws.map_name.upper(), [])
            if len(candidates) == 1:
                ws.location, ws.area = candidates[0]
            log.warnings.append(
                f"wild: set #{ws.set_no} ({ws.map_name} {upr_method}) doesn't line up with the ROM header order"
                + ("" if ws.location else "; location unknown")
            )
        if ws.area == "underwater" and ws.method == "surf":
            ws.method = "seaweed"

    def _trainers(self, lines: list[str], log: RandomizerLog) -> None:
        current = None
        for line in lines:
            s = line.strip()
            if not s:
                continue
            m = TRAINER_RE.match(s)
            if m:
                idx = int(m.group(1))
                current = TrainerEntry(idx, m.group(2).strip(), self.trainer_names.get(idx))
                if current.trainer_const is None:
                    log.warnings.append(f"trainers: #{idx} is not a known trainer id")
                log.trainers[idx] = current
                rest = m.group(3).strip()
                if rest:  # compact form: "Geodude Lv12, Geodude Lv12, Nosepass Lv15"
                    for part in re.split(r",\s*(?=[^,]+\bLv\s*\d)", rest):
                        self._trainer_mon(part, current, log)
                continue
            if current is not None:  # moveset-logging form: one line per Pokemon
                self._trainer_mon(s, current, log)
            else:
                log.warnings.append(f"trainers: unreadable line {s!r}")

    def _trainer_mon(self, text: str, trainer: TrainerEntry, log: RandomizerLog) -> None:
        m = TRAINER_MON_RE.match(text.strip())
        if not m:
            log.warnings.append(f"trainers: #{trainer.index} unreadable Pokemon {text!r}")
            return
        moves = None
        if m.group("moves"):
            moves = [self.move(x, log) for x in re.split(r"\s*[,/]\s*", m.group("moves")) if x.strip() and x.strip() != "-"]
        item = (m.group("item") or m.group("item2") or "").strip() or None
        trainer.mons.append(
            TrainerMon(len(trainer.mons) + 1, self.species(m.group("species"), log), m.group("species").strip(),
                       int(m.group("level")), item, (m.group("ability") or None), moves)
        )

    def _tm_moves(self, lines: list[str], log: RandomizerLog) -> None:
        for line in lines:
            m = TM_RE.match(line.strip())
            if m and m.group(1) in self.tm_labels:
                move = self.move(m.group(2), log)
                if move:
                    log.tm_moves[m.group(1)] = move
            elif line.strip():
                log.warnings.append(f"tm: unreadable line {line.strip()!r}")

    def _base_stats(self, lines: list[str], log: RandomizerLog) -> None:
        rows = [[c.strip() for c in line.split("|")] for line in lines if "|" in line]
        if not rows:
            return
        head = [h.upper() for h in rows[0]]
        col = {name: head.index(name) for name in head}
        stat_cols = {"HP": "hp", "ATK": "attack", "DEF": "defense", "SATK": "sp_attack", "SDEF": "sp_defense", "SPD": "speed"}
        for row in rows[1:]:
            if len(row) < len(head) or "NAME" not in col:
                continue
            species = self.species(row[col["NAME"]], log)
            if not species:
                continue
            entry = {}
            if "TYPE" in col:
                types = [t.strip().lower() for t in row[col["TYPE"]].split("/") if t.strip()]
                entry["type1"], entry["type2"] = types[0], (types[1] if len(types) > 1 else None)
            for c, key in stat_cols.items():
                if c in col and row[col[c]].isdigit():
                    entry[key] = int(row[col[c]])
            for c, key in (("ABILITY1", "ability1"), ("ABILITY2", "ability2")):
                if c in col:
                    entry[key] = row[col[c]].strip() or None
            log.base_stats[species] = entry

    def _evolutions(self, lines: list[str], log: RandomizerLog) -> None:
        for line in lines:
            m = ARROW_RE.match(line.strip())
            if not m:
                if line.strip():
                    log.warnings.append(f"evolutions: unreadable line {line.strip()!r}")
                continue
            src = self.species(m.group(1), log)
            targets = [self.species(t, log) for t in re.split(r",\s*|\s+and\s+", m.group(2)) if t.strip()]
            if src:
                log.evolutions[src] = [t for t in targets if t]

    def _starters(self, lines: list[str], log: RandomizerLog) -> None:
        for line in lines:
            m = STARTER_RE.search(line)
            if m:
                species = self.species(m.group(2), log)
                if species:
                    log.starters.append(species)

    def _statics(self, lines: list[str], log: RandomizerLog) -> None:
        for line in lines:
            m = ARROW_RE.match(line.strip())
            if m:
                old = self.species(re.sub(r"\s+Lv\s*\d+.*$", "", m.group(1)), log)
                new = self.species(re.sub(r"\s+Lv\s*\d+.*$", "", m.group(2)), log)
                if old and new:
                    log.statics.append((old, new))

    def _move_tutors(self, lines: list[str], log: RandomizerLog) -> None:
        for line in lines:
            m = ARROW_RE.match(line.strip())
            if m:
                old, new = self.move(m.group(1), log), self.move(m.group(2), log)
                if old and new:
                    log.move_tutors.append((old, new))


def parse_log(text: str, con: duckdb.DuckDBPyConnection, index: EntityIndex | None = None) -> RandomizerLog:
    return LogParser(con, index).parse(text)


def load_overlay(con: duckdb.DuckDBPyConnection, log: RandomizerLog, log_id: str) -> None:
    """Write a parsed log into overlay_* tables keyed by log_id (created on first use).

    Tools read an overlay table when the log randomized that section and fall back to
    vanilla otherwise; `overlay_sections` records which sections the log had.
    """
    ids = dict(con.execute("SELECT identifier, species_id FROM species").fetchall())
    move_ids = dict(con.execute("SELECT identifier, move_id FROM moves").fetchall())
    ddl = {
        "overlay_sections": "log_id VARCHAR, section VARCHAR, parsed BOOLEAN",
        "overlay_encounters": "log_id VARCHAR, set_no INTEGER, location VARCHAR, area VARCHAR, rom_map VARCHAR, "
        "method VARCHAR, slot INTEGER, species_id INTEGER, min_level INTEGER, max_level INTEGER, source_id VARCHAR",
        "overlay_trainer_mons": "log_id VARCHAR, trainer_id INTEGER, trainer_const VARCHAR, slot INTEGER, species_id INTEGER, "
        "level INTEGER, held_item VARCHAR, moves VARCHAR[], source_id VARCHAR",
        "overlay_tm_moves": "log_id VARCHAR, label VARCHAR, move_id INTEGER, source_id VARCHAR",
        "overlay_species": "log_id VARCHAR, species_id INTEGER, type1 VARCHAR, type2 VARCHAR, hp INTEGER, attack INTEGER, "
        "defense INTEGER, sp_attack INTEGER, sp_defense INTEGER, speed INTEGER, ability1 VARCHAR, ability2 VARCHAR, source_id VARCHAR",
        "overlay_evolutions": "log_id VARCHAR, from_species_id INTEGER, to_species_id INTEGER, source_id VARCHAR",
        "overlay_starters": "log_id VARCHAR, slot INTEGER, species_id INTEGER, source_id VARCHAR",
        "overlay_statics": "log_id VARCHAR, vanilla_species_id INTEGER, species_id INTEGER, source_id VARCHAR",
    }
    for table, cols in ddl.items():
        con.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols})")
        con.execute(f"DELETE FROM {table} WHERE log_id = ?", [log_id])

    def insert(table, rows):
        if rows:
            marks = ", ".join("?" * len(rows[0]))
            con.executemany(f"INSERT INTO {table} VALUES ({marks})", rows)

    insert("overlay_sections", [(log_id, s, s not in log.unparsed_sections) for s in log.sections])
    insert(
        "overlay_encounters",
        [
            (log_id, ws.set_no, ws.location, ws.area, ws.rom_map, mon.method, mon.slot, ids[mon.species],
             mon.min_level, mon.max_level, f"log:wild#Set{ws.set_no}")
            for ws in log.wild_sets for mon in ws.mons if mon.species
        ],
    )
    insert(
        "overlay_trainer_mons",
        [
            (log_id, t.index, t.trainer_const, mon.slot, ids[mon.species], mon.level, mon.held_item, mon.moves,
             f"log:trainers#{t.index}")
            for t in log.trainers.values() for mon in t.mons if mon.species
        ],
    )
    insert("overlay_tm_moves", [(log_id, label, move_ids[mv], f"log:tm#{label}") for label, mv in log.tm_moves.items()])
    insert(
        "overlay_species",
        [
            (log_id, ids[sp], e.get("type1"), e.get("type2"), e.get("hp"), e.get("attack"), e.get("defense"),
             e.get("sp_attack"), e.get("sp_defense"), e.get("speed"), e.get("ability1"), e.get("ability2"), f"log:stats#{sp}")
            for sp, e in log.base_stats.items()
        ],
    )
    insert(
        "overlay_evolutions",
        [(log_id, ids[src], ids[dst], f"log:evolutions#{src}") for src, dsts in log.evolutions.items() for dst in dsts],
    )
    insert("overlay_starters", [(log_id, i, ids[sp], f"log:starters#{i}") for i, sp in enumerate(log.starters, 1)])
    insert("overlay_statics", [(log_id, ids[a], ids[b], f"log:statics#{a}") for a, b in log.statics])
