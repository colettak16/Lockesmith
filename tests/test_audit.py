"""The committed audit reports (docs/audit/) match the pinned decomps, and the reachability
model still finds what the review packet says. The model checks need the full decomps
(`uv run python -m audit.sources`) and skip without them."""

import json

import pytest

from audit import reach
from audit.sources import CACHE, LOCK, pinned

REPORTS = sorted((LOCK.parent.parent / "docs" / "audit").glob("*.txt"))
have_trees = all((CACHE / n / ".sha").exists() and (CACHE / n / ".sha").read_text().strip() == pinned(n)[1]
                 for n in ("pokeruby", "pokeemerald"))


def test_reports_name_the_pinned_commits():
    lock = json.loads(LOCK.read_text())
    want = f"{lock['pokeruby']['repo']}@{lock['pokeruby']['sha'][:12]} vs {lock['pokeemerald']['repo']}@{lock['pokeemerald']['sha'][:12]}"
    assert len(REPORTS) == 12
    assert [p.name for p in REPORTS if want not in p.read_text().splitlines()[0]] == []


def test_ruby_and_sapphire_reports_match():
    for p in REPORTS:
        if p.stem.endswith("_ruby"):
            assert p.read_text() == p.with_name(p.name.replace("_ruby", "_sapphire")).read_text(), p.name


@pytest.mark.skipif(not have_trees, reason="needs the full decomps: uv run python -m audit.sources")
def test_reach_finds_the_packets_differences():
    rs, em = reach.Game(CACHE / "pokeruby", True), reach.Game(CACHE / "pokeemerald", False)
    out = "\n".join(reach.report(rs, em, ["MAP_JAGGED_PASS", "MAP_SEAFLOOR_CAVERN_ROOM3", "MAP_ROUTE110", "MAP_LILYCOVE_CITY"]))
    assert "MAP_JAGGED_PASS:" in out and "MAP_SEAFLOOR_CAVERN_ROOM3:" in out
    assert "MAP_ROUTE110:" not in out and "MAP_LILYCOVE_CITY:" not in out
    assert out.endswith("maps with reachability differences: 2 of 4")


@pytest.mark.skipif(not have_trees, reason="needs the full decomps: uv run python -m audit.sources")
def test_each_bike_opens_its_own_safari_zone_area():
    # Review round 4: the Mach and Acro Bike are separate passes. Northwest: Mach up the muddy slope;
    # northeast: Acro side jumps onto the rails (Ruby/Sapphire's "Southeast" is Emerald's "South").
    for root, rs, east in ((CACHE / "pokeruby", True, "SAFARI_ZONE_SOUTHEAST"), (CACHE / "pokeemerald", False, "SAFARI_ZONE_SOUTH")):
        g = reach.Game(root, rs)
        gates = "\n".join(reach.bike_gates(g, [f"MAP_{east}", "MAP_SAFARI_ZONE_SOUTHWEST", "MAP_JAGGED_PASS"]))
        assert f"{east}" in gates and "Acro only: ['up']" in gates
        assert "SAFARI_ZONE_SOUTHWEST" in gates and "Mach only: ['up']" in gates
        assert "JAGGED_PASS" in gates and "Acro only: ['MT_CHIMNEY']" in gates.replace("'MAGMA_HIDEOUT_1F', ", "")
