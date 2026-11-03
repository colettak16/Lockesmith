"""Ruby/Sapphire randomizer logs (docs/review_packet_rs.md R-10..R-17). No real Ruby or Sapphire
UPR ZX log has been run yet: this hand-made log follows the formats UPR's source prints, with
the predicted `\\c` in a town name. R-12..R-14 stay provisional until a real log is in tests/fixtures/."""

import pytest

from agent import pipeline
from agent.context import shared_index
from agent.db import connect_session
from agent.games import GAMES
from agent.randomizer_log import detect_game, parse_log
from agent.session import SESSIONS

SAPPHIRE_LOG = """\
Randomizer Version: 4.6.1
Random Seed: 42

--Trainers Pokemon--
#265 (LEADER ROXANNE) - Bagon Lv14, Numel Lv15
#272 (LEADER WALLACE) - Pikachu Lv40, Magneton Lv42

--Wild Pokemon--
Set #1 - PETALBURG\\c  CITY Surfing (rate=4)
Marill Lv20-30     HP 70 ATK 20 DEF 50 SPATK 20 SPDEF 50 SPEED 40
Marill Lv10-20     HP 70 ATK 20 DEF 50 SPATK 20 SPDEF 50 SPEED 40
Marill Lv30-35     HP 70 ATK 20 DEF 50 SPATK 20 SPDEF 50 SPEED 40
Marill Lv5-10      HP 70 ATK 20 DEF 50 SPATK 20 SPDEF 50 SPEED 40
Marill Lv5-10      HP 70 ATK 20 DEF 50 SPATK 20 SPDEF 50 SPEED 40

------------------------------------------------------------------
Randomization of Sapphire (U) completed.
Time elapsed: 1234ms
------------------------------------------------------------------
"""


@pytest.fixture(scope="module")
def con():
    c = connect_session(GAMES["sapphire"])
    yield c
    c.close()


def test_detect_game():
    assert detect_game(SAPPHIRE_LOG) == "sapphire"
    assert detect_game("no footer") is None


def test_parse_against_sapphire(con):
    log = parse_log(SAPPHIRE_LOG, con, shared_index("sapphire"))
    assert log.game == "sapphire" and not [w for w in log.warnings if "being read against" in w]
    assert log.trainers[272].trainer_const == "TRAINER_WALLACE" and not log.trainers[272].is_partner
    ws = log.wild_sets[0]
    assert ws.aligned and ws.location == "petalburg-city"  # "PETALBURG\\c  CITY" matched the plain name


def test_no_partner_pseudo_trainer_in_ruby_sapphire(con):
    text = SAPPHIRE_LOG.replace("--Wild Pokemon--", "#694 (STEVEN) - Metang Lv42\n\n--Wild Pokemon--")
    log = parse_log(text, con, shared_index("sapphire"))
    assert 694 in log.trainers and not log.trainers[694].is_partner


def test_uploading_a_sapphire_log_switches_the_session():
    sid = "rs-randomizer-test"
    out = pipeline.load_log(SAPPHIRE_LOG, "sapphire-test", sid)
    session = SESSIONS.peek(sid)
    assert out["game"] == "sapphire" and session.state.game == "sapphire" and session.con_game == "sapphire"
    team = session.con.execute("SELECT species FROM trainer_mons WHERE trainer_const = 'TRAINER_WALLACE' ORDER BY slot").fetchall()
    assert team == [("pikachu",), ("magneton",)]
    SESSIONS.clear(sid)
