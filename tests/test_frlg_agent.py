"""The agent on FireRed/LeafGreen: the Kanto progression (data/progression_frlg.yaml), the run state,
the tools and the Verifier's National Dex gate (docs/decisions.md D16)."""

import duckdb
import pytest

from agent.context import RequestContext
from agent.db import connect_session
from agent.games import GAMES
from agent.progression import load_game
from agent.schemas import Recommendation
from agent.state import RunState, progress
from agent.tools import battles, encounters
from agent.verifier import check_pick


@pytest.fixture(scope="module", params=["firered", "leafgreen"])
def game(request):
    return GAMES[request.param]


@pytest.fixture(scope="module")
def con(game):
    c = connect_session(game)
    yield c
    c.close()


def ctx_for(con, game, **kw) -> RequestContext:
    state = {"game": game.id, "starter": "charmander", "badges": ["boulder", "cascade", "thunder"], **kw}
    return RequestContext(state=RunState(**state), con=con)


def test_every_encounter_area_opens_somewhere_or_is_never_reachable(game):
    prog = load_game(game)
    db = duckdb.connect(str(game.db_path), read_only=True)
    last = prog.battles[-1].id
    open_or_never = [prog.opened(last, loc, area, m) or prog.never_reason(loc, area, m)
                     for loc, area, m in db.execute("SELECT DISTINCT location, area, method FROM encounters").fetchall()]
    assert all(open_or_never)


def test_battles_name_real_trainers_and_the_casts_gyms(game):
    prog = load_game(game)
    db = duckdb.connect(str(game.db_path), read_only=True)
    consts = {r[0] for r in db.execute("SELECT trainer_const FROM trainers").fetchall()}
    for b in prog.battles:
        named = list(b.trainer_consts or []) + list((b.starter_variants or {}).values())
        assert set(named) <= consts, b.id
        if b.starter_variants:
            assert set(b.starter_variants) == set(game.cast.starters), b.id
    assert set(game.cast.gyms) <= {b.id for b in prog.battles}


def test_rival_takes_the_starter_strong_against_yours(con, game):
    for starter, ace in (("bulbasaur", "Charizard"), ("charmander", "Blastoise"), ("squirtle", "Venusaur")):
        ctx = ctx_for(con, game, starter=starter)
        team = battles.scout_battle(ctx, "champion")["teams"][0]
        assert team["trainer"] == "Champion" and team["pokemon"][-1]["species"] == ace


def test_progress_puts_the_next_gym_after_three_badges(game):
    s = RunState(game=game.id, starter="squirtle", badges=["brock", "misty", "lt. surge"])
    assert progress(s, load_game(game)).next_required.id == "gym4_erika"


def test_ghosts_need_the_silph_scope_and_snorlax_the_poke_flute(con, game):
    ctx = ctx_for(con, game)
    for species in ("Gastly", "Snorlax"):  # asked by name: the full list stops at 30 species
        assert not encounters.catchable(ctx, "gym4_erika", species=species)["species"], species
        assert encounters.catchable(ctx, "gym5_koga", species=species)["species"], species


def test_kanto_evolutions_past_mew_fail_the_verifier(con, game):
    ctx = ctx_for(con, game)
    pick = Recommendation(species="Zubat", role="r", horizon="core", before_battle="gym5_koga", where="w", when="w",
                          why="fits", long_term="lt", evolve_to="Crobat", key_moves=[], source_ids=[], alternatives=[])
    details = [v.detail for v in check_pick(ctx, pick, "gym5_koga", 0, None) if v.code == "EVOLUTION_NOT_REACHABLE"]
    assert details and "National Dex" in details[0]
