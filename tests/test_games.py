"""Each game's cast (agent/games.py): starters, rival choice, badges and leaders drive the run
state, so adding a game is data, not new special cases (docs/decisions.md D16)."""

import pytest
from pydantic import ValidationError

from agent.games import GAMES
from agent.pipeline import apply_state
from agent.progression import Battle
from agent.schemas import StateUpdate
from agent.state import RunState

NO_UPDATE = dict(game=None, starter=None, badges=None, rival=None, last_battle=None, party=None)


@pytest.mark.parametrize("game", list(GAMES.values()), ids=list(GAMES))
def test_every_game_has_three_starters_and_eight_gyms(game):
    cast = game.cast
    assert len(cast.starters) == 3 and len(cast.badges) == len(cast.gyms) == 8
    assert {badge for _, badge in cast.leaders} == set(cast.badges)


def test_kanto_run_state():
    s = RunState(game="firered", starter="Bulbasaur", badges=["Lt. Surge", "Boulder Badge", "misty"], rival="may")
    assert s.starter == "bulbasaur" and s.badges == ["boulder", "cascade", "thunder"]
    assert s.rival is None  # Kanto has no rival to pick; a leftover Hoenn choice is dropped


def test_a_starter_or_badge_from_another_region_is_refused():
    with pytest.raises(ValidationError):
        RunState(game="leafgreen", starter="treecko")
    with pytest.raises(ValidationError):
        RunState(game="firered", badges=["stone"])
    with pytest.raises(ValidationError):
        RunState(game="emerald", rival="gary")


def test_switching_region_in_chat_drops_the_other_regions_run():
    sapphire = RunState(game="sapphire", starter="mudkip", badges=["stone", "knuckle"], rival="may",
                        party=[{"species": "Marshtomp", "level": 20}])
    s = apply_state(sapphire, StateUpdate(**{**NO_UPDATE, "game": "firered"}), None)
    assert (s.game, s.starter, s.badges, s.rival, s.party) == ("firered", None, None, None, [])
    s = apply_state(sapphire, StateUpdate(**{**NO_UPDATE, "game": "leafgreen", "starter": "squirtle", "badges": ["brock"]}), None)
    assert (s.game, s.starter, s.badges) == ("leafgreen", "squirtle", ["boulder"])


def test_switching_within_hoenn_keeps_the_run():
    emerald = RunState(game="emerald", starter="mudkip", badges=["stone", "knuckle"])
    s = apply_state(emerald, StateUpdate(**{**NO_UPDATE, "game": "sapphire"}), None)
    assert (s.game, s.starter, s.badges) == ("sapphire", "mudkip", ["stone", "knuckle"])


def test_a_kanto_rival_fight_is_one_trainer_per_starter():
    fight = Battle(id="rival1", order=1, label="Rival", badges_before=0, trainer_consts=None,
                   starter_variants={"bulbasaur": "TRAINER_RIVAL_OAKS_LAB_CHARMANDER"}, battle_format="single",
                   optional=False, location="pallet-town", hm_gates_open=(), key_items=(), areas_new=(), source="s")
    assert fight.trainers_for("bulbasaur") == ["TRAINER_RIVAL_OAKS_LAB_CHARMANDER"]
    with pytest.raises(ValueError):
        fight.trainers_for("treecko")


def test_kanto_evolutions_stop_at_mew_before_the_national_dex():
    """FireRed/LeafGreen cancel evolutions past #151 until the National Dex (postgame)."""
    import duckdb

    from agent.tools.outlook import final_forms

    con = duckdb.connect(str(GAMES["firered"].db_path), read_only=True)
    zubat, golbat, crobat = 41, 42, 169
    assert [f for f, _ in final_forms(con, zubat, GAMES["firered"].evolution_limit)] == [golbat]
    assert [f for f, _ in final_forms(con, zubat, GAMES["emerald"].evolution_limit)] == [crobat]
