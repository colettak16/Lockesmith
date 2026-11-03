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
