"""Shared loaders: map headers and event scripts, read per version.

pokeruby builds Ruby and Sapphire from one tree, so its scripts are read with `.ifdef`
blocks resolved for one version (build.decomp.script_lines); Emerald (version None) keeps
every line.
"""

import glob
import json
import re
from pathlib import Path

from build.decomp import script_lines

VERSIONS = ("RUBY", "SAPPHIRE")


def load_maps(root: Path) -> dict[str, dict]:
    """Map id -> its map.json, with the folder name added as "folder"."""
    out = {}
    for p in sorted(glob.glob(str(root / "data/maps/*/map.json"))):
        m = json.loads(Path(p).read_text(encoding="utf-8"))
        m["folder"] = Path(p).parent.name
        out[m["id"]] = m
    return out


def load_scripts(root: Path, version: str | None) -> dict[str, list[str]]:
    """Where -> script lines: a map folder name, or "scripts/<file>" for data/scripts/*.inc."""
    out = {}
    for p in sorted(glob.glob(str(root / "data/maps/*/scripts.inc"))):
        out[Path(p).parent.name] = script_lines(Path(p).read_text(errors="replace"), version)
    for p in sorted(glob.glob(str(root / "data/scripts/*.inc"))):
        out["scripts/" + Path(p).name] = script_lines(Path(p).read_text(errors="replace"), version)
    return out


def flag_writers(scripts: dict[str, list[str]]) -> tuple[set[str], dict[str, set[str]], dict[str, set[str]]]:
    """(flags set at a new game, flag -> scripts that set it, flag -> scripts that clear it)."""
    init = set(re.findall(r"setflag\s+(FLAG_\w+)", "\n".join(scripts.get("scripts/new_game.inc", []))))
    setters: dict[str, set[str]] = {}
    clearers: dict[str, set[str]] = {}
    for where, lines in scripts.items():
        if where == "scripts/new_game.inc":
            continue
        for line in lines:
            for f in re.findall(r"setflag\s+(FLAG_\w+)", line):
                setters.setdefault(f, set()).add(where)
            for f in re.findall(r"clearflag\s+(FLAG_\w+)", line):
                clearers.setdefault(f, set()).add(where)
    return init, setters, clearers


def labels(lines: list[str]) -> dict[str, list[str]]:
    """Label -> the stripped lines under it, up to the next label."""
    out: dict[str, list[str]] = {}
    cur = None
    for ln in lines:
        m = re.match(r"^(\w+)::?", ln)
        if m:
            cur = m.group(1)
            out[cur] = []
            continue
        if cur:
            out[cur].append(ln.strip())
    return out
