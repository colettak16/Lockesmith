"""The two decompilations, complete, at the commits the build pins (data/sources.lock.json).

    uv run python -m audit.sources        # download both into build/.cache/audit/

The build's own checkouts (build/fetch_sources.py) are sparse: they hold only the files the
database needs. The audit reads every map, layout, tileset attribute file and the engine
source, so it downloads each pinned commit's GitHub tarball and keeps data/, include/ and src/.
The files are only parsed as text and JSON, never built or run.
"""

import json
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "data" / "sources.lock.json"
CACHE = ROOT / "build" / ".cache" / "audit"
KEEP = ("data/", "include/", "src/")
NAMES = ("pokeruby", "pokeemerald")


def pinned(name: str) -> tuple[str, str]:
    entry = json.loads(LOCK.read_text(encoding="utf-8"))[name]
    return entry["repo"], entry["sha"]


def tree(name: str) -> Path:
    """The decomp's directory, downloading it first if it's missing or at another commit."""
    repo, sha = pinned(name)
    dest = CACHE / name
    marker = dest / ".sha"
    if not (marker.exists() and marker.read_text().strip() == sha):
        fetch(name, repo, sha, dest)
    return dest


def fetch(name: str, repo: str, sha: str, dest: Path) -> None:
    url = f"https://codeload.github.com/{repo}/tar.gz/{sha}"
    print(f"downloading {repo}@{sha[:12]} ...", file=sys.stderr)
    CACHE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=CACHE) as tmp:
        archive = Path(tmp) / f"{name}.tar.gz"
        with httpx.stream("GET", url, follow_redirects=True, timeout=300) as r:
            r.raise_for_status()
            with archive.open("wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
        out = Path(tmp) / "x"
        with tarfile.open(archive) as tar:
            members = []
            for m in tar.getmembers():
                _, _, rel = m.name.partition("/")  # drop the "<repo>-<sha>/" top directory
                if rel.startswith(KEEP) and (m.isfile() or m.isdir()):
                    m.name = rel
                    members.append(m)
            tar.extractall(out, members=members, filter="data")
        (out / ".sha").write_text(sha)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(out), dest)


if __name__ == "__main__":
    for n in NAMES:
        print(n, tree(n))
