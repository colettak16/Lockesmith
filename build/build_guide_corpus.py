"""Fetch the Bulbapedia Emerald walkthrough and cache it as searchable chunks.

    uv run python build/build_guide_corpus.py           # fetch missing pages, rebuild chunks
    uv run python build/build_guide_corpus.py --refresh # refetch every page

Writes data/guide/pages/*.json (raw wikitext plus revision id, for attribution and
reproducibility) and data/guide/chunks.jsonl (one plain-text chunk per section,
with a `guide:` source id). Only the 21-part Emerald walkthrough is fetched; TM
locations come from the decomp instead (docs/decisions.md, D1).

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


def render_template(body: str) -> str:
    parts = [p.strip() for p in body.split("|")]
    name = parts[0].lower()
    args = [p for p in parts[1:] if "=" not in p]
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


def wikitext_to_text(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    for _ in range(10):  # innermost templates first
        text, n = re.subn(r"\{\{([^{}]*)\}\}", lambda m: render_template(m.group(1)), text)
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


def chunks(page: dict) -> list[dict]:
    out, seen = [], {}
    for path, raw in sections(page["wikitext"]):
        text = wikitext_to_text(raw)
        if len(text) < 40:
            continue
        anchor = (path[-1] if path else "Intro").replace(" ", "_")
        seen[anchor] = seen.get(anchor, 0) + 1
        if seen[anchor] > 1:
            anchor = f"{anchor}_{seen[anchor]}"
        out.append(
            {
                "source_id": f"guide:{slug(page['title'])}#{anchor}",
                "page": page["title"],
                "section": " > ".join(path) or "Intro",
                "url": page["url"] + (f"#{quote(path[-1].replace(' ', '_'))}" if path else ""),
                "text": text,
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    PAGES.mkdir(parents=True, exist_ok=True)
    for title in TITLES:
        path = PAGES / f"{slug(title).replace('/', '_').replace(':', '_')}.json"
        if path.exists() and not args.refresh:
            continue
        page = fetch(title)
        path.write_text(json.dumps(page, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"fetched {title} (rev {page['revid']})")
        time.sleep(1.0)  # be polite to Bulbapedia
    all_chunks = []
    for title in TITLES:
        page = json.loads((PAGES / f"{slug(title).replace('/', '_').replace(':', '_')}.json").read_text(encoding="utf-8"))
        all_chunks.extend(chunks(page))
    with (GUIDE / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {len(all_chunks)} chunks to {(GUIDE / 'chunks.jsonl').relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
