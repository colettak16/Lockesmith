"""Fetch a Bulbapedia walkthrough and cache it as searchable chunks.

    uv run python build/build_guide_corpus.py                 # every corpus: fetch missing pages, rebuild chunks
    uv run python build/build_guide_corpus.py --corpus rs     # only Ruby/Sapphire
    uv run python build/build_guide_corpus.py --refresh       # refetch every page

Writes <dir>/pages/*.json (raw wikitext plus revision id, for attribution and
reproducibility) and <dir>/chunks.jsonl (one plain-text chunk per section, with a
`guide:` source id). Two corpora: the 21-part Emerald walkthrough in data/guide and
the 23-part Ruby and Sapphire walkthrough in data/guide_rs. TM locations come from
the decomp instead (docs/decisions.md, D1).

The Ruby/Sapphire walkthrough marks version-specific text with {{sup/3|R}} and
{{sup/3|S}} ("VS Maxie(R)", "VS Archie(S)"). Those render as "(Ruby)"/"(Sapphire)",
headings are rendered to text for anchors, and each chunk lists the versions it
describes, so a Sapphire question isn't answered from a Ruby-only section.

Bulbapedia text is CC BY-NC-SA 2.5; the README carries the attribution.
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlencode

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "data" / "guide"
PAGES = GUIDE / "pages"
API = "https://bulbapedia.bulbagarden.net/w/api.php"
WIKI = "https://bulbapedia.bulbagarden.net/wiki/"
USER_AGENT = "Lockesmith/0.1 (IEOR E4570 course project)"
TITLES = [f"Walkthrough:Pokémon Emerald/Part {i}" for i in range(1, 22)]
CORPORA = {
    "emerald": {"dir": GUIDE, "titles": TITLES, "versions": ()},
    "rs": {
        "dir": ROOT / "data" / "guide_rs",
        "titles": [f"Walkthrough:Pokémon Ruby and Sapphire/Part {i}" for i in range(1, 24)],
        "versions": ("ruby", "sapphire"),
    },
    "frlg": {
        "dir": ROOT / "data" / "guide_frlg",
        "titles": [f"Walkthrough:Pokémon FireRed and LeafGreen/Part {i}" for i in range(1, 21)],
        "versions": ("firered", "leafgreen"),
    },
}
VERSION_MARKS = {
    "r": "ruby", "ru": "ruby", "ruby": "ruby", "s": "sapphire", "sa": "sapphire", "sapphire": "sapphire",
    "fr": "firered", "firered": "firered", "lg": "leafgreen", "leafgreen": "leafgreen",
}
VERSION_LABEL = {"ruby": "Ruby", "sapphire": "Sapphire", "firered": "FireRed", "leafgreen": "LeafGreen"}

# Link-style templates that render as their first argument plus a suffix.
SUFFIX_TEMPLATES = {"rt": ("Route ", ""), "ci": ("", " City"), "to": ("", " Town")}
# Templates that render as a fixed name with no arguments.
NAMED = {"player": "the player", "rival": "your rival"}
DROP_PREFIXES = ("party/", "catch/", "itlist", "itemlist", "trainerentry", "trainerheader", "trainerfooter",
                 "pokemon/", "roundy", "box", "-", "!", "sup", "tt", "shop", "mart", "gym", "gamecorner")


def slug(title: str) -> str:
    return title.replace("é", "e").replace(" ", "_")


def fetch(title: str) -> dict:
    # Bulbapedia's edge rejects httpx's client fingerprint but accepts urllib.
    query = urlencode({"action": "parse", "page": title, "prop": "wikitext|revid", "format": "json", "formatversion": 2})
    req = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        parse = json.load(r)["parse"]
    return {
        "title": parse["title"],
        "revid": parse["revid"],
        "url": WIKI + quote(parse["title"].replace(" ", "_")),
        "fetched": date.today().isoformat(),
        "license": "CC BY-NC-SA 2.5 (Bulbapedia)",
        "wikitext": parse["wikitext"],
    }


def render_template(body: str, versions: tuple[str, ...] = ()) -> str:
    parts = [p.strip() for p in body.split("|")]
    name = parts[0].lower()
    args = [p for p in parts[1:] if "=" not in p]
    if versions and name.startswith("sup") and args:
        marks = [VERSION_MARKS.get(a.lower()) for a in args]
        if any(m in versions for m in marks):
            return " (" + "/".join(VERSION_LABEL[m] for m in marks if m in versions) + ")"
    if name.startswith(DROP_PREFIXES):
        return ""
    if name in SUFFIX_TEMPLATES:
        prefix, suffix = SUFFIX_TEMPLATES[name]
        return f"{prefix}{args[0]}{suffix}" if args else ""
    if not args:
        return NAMED.get(name, name.title() if name.isalpha() and len(name) > 2 else "")
    if name in ("dl", "pkmn2"):  # deep links show their last argument
        return args[-1]
    return args[0]


def strip_tables(text: str) -> str:
    out, depth = [], 0
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("{|"):
            depth += 1
        elif s.startswith("|}") and depth:
            depth -= 1
            continue
        if depth == 0:
            out.append(line)
    return "\n".join(out)


def wikitext_to_text(text: str, versions: tuple[str, ...] = ()) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    for _ in range(10):  # innermost templates first
        text, n = re.subn(r"\{\{([^{}]*)\}\}", lambda m: render_template(m.group(1), versions), text)
        if not n:
            break
    text = strip_tables(text)
    text = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", "", text)
    text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^[:*#]+\s*", "- ", text, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def sections(wikitext: str) -> list[tuple[list[str], str]]:
    """[(heading path, raw section text)] in page order. Text before the first heading has path []."""
    out, path, buf = [], [], []
    for line in wikitext.split("\n"):
        m = re.match(r"^(={2,6})\s*(.*?)\s*\1\s*$", line)
        if m:
            out.append((list(path), "\n".join(buf)))
            level = len(m.group(1)) - 2
            path = path[:level] + [m.group(2)]
            buf = []
        else:
            buf.append(line)
    out.append((list(path), "\n".join(buf)))
    return [(p, t) for p, t in out if t.strip()]


def chunk_versions(path: list[str], raw: str, versions: tuple[str, ...]) -> list[str]:
    """The versions a section describes: a heading marked for one version ((R)/(S), (FR)/(LG))
    wins; otherwise both of the corpus's versions."""
    marks = {VERSION_MARKS.get(m.lower()) for h in path for m in re.findall(r"\{\{sup/\d\|(\w+)\}\}", h)} & set(versions)
    return sorted(marks) if marks else list(versions)


def chunks(page: dict, versions: tuple[str, ...] = ()) -> list[dict]:
    out, seen = [], {}
    for path, raw in sections(page["wikitext"]):
        text = wikitext_to_text(raw, versions)
        if len(text) < 40:
            continue
        shown = [wikitext_to_text(h, versions) for h in path] if versions else path
        anchor = (shown[-1] if shown else "Intro").replace(" ", "_")
        seen[anchor] = seen.get(anchor, 0) + 1
        if seen[anchor] > 1:
            anchor = f"{anchor}_{seen[anchor]}"
        chunk = {
            "source_id": f"guide:{slug(page['title'])}#{anchor}",
            "page": page["title"],
            "section": " > ".join(shown) or "Intro",
            "url": page["url"] + (f"#{quote(shown[-1].replace(' ', '_'))}" if shown else ""),
            "text": text,
        }
        if versions:
            chunk["versions"] = chunk_versions(path, raw, versions)
        out.append(chunk)
    return out


def build(corpus: dict, refresh: bool = False) -> None:
    guide, pages = corpus["dir"], corpus["dir"] / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    for title in corpus["titles"]:
        path = pages / f"{slug(title).replace('/', '_').replace(':', '_')}.json"
        if path.exists() and not refresh:
            continue
        page = fetch(title)
        path.write_text(json.dumps(page, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"fetched {title} (rev {page['revid']})")
        time.sleep(1.0)  # be polite to Bulbapedia
    all_chunks = []
    for title in corpus["titles"]:
        page = json.loads((pages / f"{slug(title).replace('/', '_').replace(':', '_')}.json").read_text(encoding="utf-8"))
        all_chunks.extend(chunks(page, corpus["versions"]))
    with (guide / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {len(all_chunks)} chunks to {(guide / 'chunks.jsonl').relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--corpus", choices=[*CORPORA, "all"], default="all")
    args = ap.parse_args()
    for name, corpus in CORPORA.items():
        if args.corpus in (name, "all"):
            build(corpus, args.refresh)


if __name__ == "__main__":
    sys.exit(main())
