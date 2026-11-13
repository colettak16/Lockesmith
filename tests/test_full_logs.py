"""The randomizer log parser at full size, on all five games, and its ROM identity checks (R-17).

No real UPR ZX log exists for these tests (no ROM was available; docs/decisions.md D19), so
tests/upr_log_writer.py writes one per game in UPR's format from the game's own tables:
every wild set in ROM order, every trainer, all 50 TMs, the starters, the footer and the ROM
diagnostics. The parser must read each back exactly, with no warnings. The fixture tests in
test_log_parser.py still wait for a real log.
"""

import pytest

from agent.db import connect_session
from agent.entities import EntityIndex
from agent.games import GAMES
from agent.randomizer_log import load_overlay, parse_log, read_rom
from upr_log_writer import write_log

# One ROM per game, mixing revisions: (UPR's name for it, revision)
ROMS = {
    "emerald": ("Emerald (U)", 0),
    "ruby": ("Ruby (U)", 0),
    "sapphire": ("Sapphire (E)", 1),
    "firered": ("Fire Red (U) 1.0", 0),
    "leafgreen": ("Leaf Green (U) 1.1", 1),
}


@pytest.fixture(scope="module", params=[(g, m) for g in ROMS for m in (False, True)],
                ids=lambda p: f"{p[0]}-{'movesets' if p[1] else 'compact'}")
def case(request):
    game, movesets = request.param
    con = connect_session(GAMES[game])
    text, written = write_log(con, ROMS[game][0], movesets=movesets)
    log = parse_log(text, con, EntityIndex(con))
    yield game, movesets, con, text, written, log
    con.close()


def test_reads_with_no_warnings(case):
    _, _, _, _, _, log = case
    assert log.warnings == []
    assert log.rom_notes == []
    assert log.unparsed_sections == []
    # The footer's dash rules and the diagnostics aren't sections (a real log's footer used to
    # read as a section called "------...")
    assert log.sections == ["Random Starters", "TM Moves", "Trainers Pokemon", "Wild Pokemon"]


def test_rom_identity(case):
    game, _, _, _, _, log = case
    name, revision = ROMS[game]
    assert log.game == game
    assert (log.rom.name, log.rom.revision, log.rom.language, log.rom.clean) == (name, revision, "English", True)


def test_every_wild_set_lines_up_and_reads_back(case):
    _, _, con, _, written, log = case
    (n,) = con.execute("SELECT count(*) FROM wild_headers").fetchone()
    assert len(log.wild_sets) == n == len(written.wild)
    assert [ws.set_no for ws in log.wild_sets if not ws.aligned] == []
    assert [ws.set_no for ws in log.wild_sets if not ws.location] == []
    read = {ws.set_no: [(m.species, m.min_level, m.max_level) for m in ws.mons] for ws in log.wild_sets}
    assert read == written.wild


def test_fishing_sets_split_by_rod(case):
    _, _, _, _, _, log = case
    for ws in log.wild_sets:
        if ws.method == "fishing":
            assert [m.method for m in ws.mons] == ["old-rod"] * 2 + ["good-rod"] * 3 + ["super-rod"] * 5


def test_every_trainer_joins_and_reads_back(case):
    game, movesets, con, _, written, log = case
    known = dict(con.execute("SELECT trainer_id, party_size FROM trainers WHERE trainer_id > 0").fetchall())
    assert set(log.trainers) == set(written.trainers)
    partner = [t.index for t in log.trainers.values() if t.is_partner]
    assert partner == ([max(known) + 1] if game == "emerald" else [])
    for t in log.trainers.values():
        if not t.is_partner:
            assert t.trainer_const and len(t.mons) == known[t.index], t.index
    read = {
        t.index: [(m.species, m.level, m.held_item, m.moves if movesets else None) for m in t.mons]
        for t in log.trainers.values()
    }
    assert read == written.trainers


def test_tms_and_starters_read_back(case):
    _, _, _, _, written, log = case
    assert log.tm_moves == written.tm_moves and len(log.tm_moves) == 50
    assert log.starters == written.starters


def test_overlay_loads_everything(case):
    game, movesets, con, _, written, log = case
    log_id = f"full-{game}-{movesets}"
    load_overlay(con, log, log_id)
    count = lambda table: con.execute(f"SELECT count(*) FROM {table} WHERE log_id = ?", [log_id]).fetchone()[0]  # noqa: E731
    assert count("overlay_encounters") == sum(len(v) for v in written.wild.values())
    assert count("overlay_trainer_mons") == sum(len(v) for v in written.trainers.values())
    assert count("overlay_tm_moves") == 50
    assert count("overlay_starters") == 3


# --- ROM identity on its own (R-17) --------------------------------------------------------


def footer(name: str, crc: str | None) -> str:
    rule = "-" * 66
    diag = f"\n--ROM Diagnostics--\nFile name: rom.gba\nOriginal ROM CRC32: {crc}\n" if crc else ""
    return f"--TM Moves--\nTM01 FOCUS PUNCH\n\n{rule}\nRandomization of {name} completed.\n{rule}\n{diag}"


def test_later_revisions_are_named_and_clean():
    rom, notes = read_rom(footer("Ruby (U/E) 1.2", "AEAC73E6"))
    assert (rom.revision, rom.clean, notes) == (2, True, [])


def test_modified_rom_is_flagged():
    """UPR names a ROM by its header, so a hacked Emerald still says "Emerald (U)"."""
    rom, notes = read_rom(footer("Emerald (U)", "12345678"))
    assert rom.clean is False
    assert len(notes) == 1 and "ROM hack" in notes[0] and "1F1C08FB" in notes[0]


def test_non_english_rom_is_flagged():
    rom, notes = read_rom(footer("Fire Red (G)", "1A81EEDF"))
    assert (rom.language, rom.clean) == ("German", True)
    assert len(notes) == 1 and "German" in notes[0]


def test_unlisted_rom_and_missing_footer():
    rom, notes = read_rom(footer("Emerald (X) 9.9", "00000000"))
    assert rom.revision is None and "isn't in its list" in notes[0]
    rom, notes = read_rom("--TM Moves--\nTM01 FOCUS PUNCH\n")
    assert rom.name is None and "no closing footer" in notes[0]


def test_other_games_are_refused():
    from agent import pipeline

    with pytest.raises(ValueError, match="Crystal"):
        pipeline.load_log(footer("Crystal (U)", "EE6F5188"), "crystal.log", None)
