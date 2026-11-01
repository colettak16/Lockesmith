"""Entity matching (PLAN.md section 4.6): what players type -> canonical ids."""

import pytest

from agent.entities import EntityIndex, normalize


@pytest.fixture(scope="module")
def index():
    return EntityIndex()


@pytest.mark.parametrize(
    "text, kind, expected",
    [
        # the PLAN.md examples
        ("mr mime", "species", "mr-mime"),
        ("farfetchd", "species", "farfetchd"),
        ("rt 119", "location", "hoenn-route-119"),
        ("tate and liza", "trainer", "TRAINER_TATE_AND_LIZA_1"),
        # spellings and typos
        ("Mr. Mime", "species", "mr-mime"),
        ("FARFETCH'D", "species", "farfetchd"),
        ("NIDORAN♀", "species", "nidoran-f"),
        ("nidoran female", "species", "nidoran-f"),
        ("gardevior", "species", "gardevoir"),
        ("ho oh", "species", "ho-oh"),
        # ROM move names from randomizer logs vs modern names
        ("FAINT ATTACK", "move", "feint-attack"),
        ("feint attack", "move", "feint-attack"),
        ("HI JUMP KICK", "move", "high-jump-kick"),
        ("thunderpunch", "move", "thunder-punch"),
        ("VICEGRIP", "move", "vice-grip"),
        ("vise grip", "move", "vice-grip"),
        ("SMELLINGSALT", "move", "smelling-salts"),
        ("ancientpower", "move", "ancient-power"),
        # locations
        ("route 119", "location", "hoenn-route-119"),
        ("r119", "location", "hoenn-route-119"),
        ("Route119", "location", "hoenn-route-119"),
        ("Mt Pyre", "location", "mt-pyre"),
        ("MT. PYRE", "location", "mt-pyre"),
        ("petalburg woods", "location", "petalburg-woods"),
        ("victory road", "location", "hoenn-victory-road"),
        ("safari zone", "location", "hoenn-safari-zone"),
        # trainers: the first, story fight wins over rematches
        ("juan", "trainer", "TRAINER_JUAN_1"),
        ("Leader Roxanne", "trainer", "TRAINER_ROXANNE_1"),
        ("wallace", "trainer", "TRAINER_WALLACE"),
        ("Tate & Liza", "trainer", "TRAINER_TATE_AND_LIZA_1"),
    ],
)
def test_resolves(index, text, kind, expected):
    match = index.resolve(text, kind)
    assert match is not None, text
    assert match.id == expected, (text, index.match(text, kind))


def test_kanto_locations_are_not_indexed(index):
    assert all(m.id != "pallet-town" for m in index.match("pallet town", "location"))


def test_unknown_names_return_nothing(index):
    assert index.resolve("pikachu tcg promo", "move") is None
    assert index.match("", "species") == []


def test_cross_kind_search_reports_kind(index):
    kinds = {m.kind for m in index.match("surf")}
    assert "move" in kinds


def test_ambiguity_flag(index):
    matches = index.match("wally", "trainer")
    assert matches[0].id.startswith("TRAINER_WALLY")
    exact = index.match("gardevoir", "species")
    assert not EntityIndex.is_ambiguous(exact)


def test_normalize():
    assert normalize("Rt. 104") == "route 104"
    assert normalize("Tate&Liza") == "tate and liza"
    assert normalize("Mt. Chimney") == "mount chimney"
