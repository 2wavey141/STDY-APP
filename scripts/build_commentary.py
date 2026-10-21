#!/usr/bin/env python3
"""Ingest public-domain commentary for each passage.

Writes data/commentary/<slug>.json holding the FULL text of each commentator's
note on the passage. Holding the full text is the point: it is what makes a
citation checkable in one click instead of a page number in a book nobody owns.

Only public-domain commentaries are ingested. Tyndale's notes are CC BY-SA and
are deliberately excluded - see BUILD-PLAN.md on share-alike.

Stdlib only.

    python3 scripts/build_commentary.py            # all passages
    python3 scripts/build_commentary.py acts-2-42  # one
"""

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "commentary"
SCHEMA = 1

# Era is recorded so the UI can be honest that these are historical voices.
# "Still argued" built on these shows how a question WAS argued, not how it is
# argued now; modern scholarship is a later layer. Keil & Delitzsch is Old
# Testament only and will correctly return nothing for New Testament passages.
COMMENTATORS = {
    "john-calvin":            {"author": "John Calvin",                  "era": "1540s-1550s", "died": 1564},
    "matthew-henry":          {"author": "Matthew Henry",                "era": "1708-1710",   "died": 1714},
    "john-gill":              {"author": "John Gill",                    "era": "1746-1763",   "died": 1771},
    "adam-clarke":            {"author": "Adam Clarke",                  "era": "1810-1826",   "died": 1832},
    "jamieson-fausset-brown": {"author": "Jamieson, Fausset and Brown",  "era": "1871",        "died": 1910},
    "keil-delitzsch":         {"author": "Keil and Delitzsch",           "era": "1866-1891",   "died": 1890,
                               "scope": "Old Testament only"},
}

BASE = "https://bible.helloao.org/api"
_cache = {}


def fetch(cid, book, chapter):
    key = (cid, book, chapter)
    if key in _cache:
        return _cache[key]
    url = f"{BASE}/c/{cid}/{book}/{chapter}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "STDY-APP/build_commentary"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            data = None          # this commentator has nothing on this book
        else:
            raise
    _cache[key] = data
    return data


def note_covering(chapter_json, verse):
    """Find the note covering a verse.

    Commentary notes are anchored to verse RANGES, not single verses: a note
    filed at verse 40 runs until the next note begins. Calvin's note on Acts
    2:42 is filed at verse 40, so exact-match lookup finds nothing for him.
    Take the latest note anchored at or before the verse, and report the range
    it actually covers so the UI can say so.
    """
    if not chapter_json:
        return None
    items = [
        x for x in chapter_json.get("chapter", {}).get("content", [])
        if isinstance(x, dict) and x.get("type") == "verse" and x.get("number") is not None
    ]
    if not items:
        return None
    items.sort(key=lambda x: x["number"])
    starts = [x["number"] for x in items]

    at = None
    for i, n in enumerate(starts):
        if n <= verse:
            at = i
        else:
            break
    if at is None:
        return None

    anchored = starts[at]
    next_start = starts[at + 1] if at + 1 < len(starts) else None
    text = re.sub(r"\s+", " ", " ".join(
        p for p in items[at].get("content", []) if isinstance(p, str)
    )).strip()
    if not text:
        return None
    return {"anchored_at": anchored, "runs_until": next_start, "text": text}


def build(passage):
    book = passage["book"]
    chapter = passage["chapter"]
    verse = passage["verse"]
    out, missing = [], []

    for cid, meta in COMMENTATORS.items():
        try:
            cj = fetch(cid, book, chapter)
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"    ! {cid}: {e}", file=sys.stderr)
            missing.append({"id": cid, "reason": "fetch failed"})
            continue
        note = note_covering(cj, verse)
        if not note:
            missing.append({"id": cid, "reason": meta.get("scope") or "no note on this passage"})
            continue

        last = note["runs_until"]
        if note["anchored_at"] == verse:
            covers = f"{chapter}:{verse}"
        elif last:
            covers = f"{chapter}:{note['anchored_at']}-{last - 1}"
        else:
            covers = f"{chapter}:{note['anchored_at']} onward"

        out.append({
            "id": cid,
            "author": meta["author"],
            "era": meta["era"],
            "license": "public domain",
            "exact_verse_note": note["anchored_at"] == verse,
            "covers": covers,
            "chars": len(note["text"]),
            "text": note["text"],
            "source": f"{BASE}/c/{cid}/{book}/{chapter}.json",
        })

    return {
        "schema": SCHEMA,
        "slug": passage["slug"],
        "reference": f"{book} {chapter}:{verse}",
        "note": ("Full public-domain commentary text. Held locally so every citation in "
                 "the app is checkable against the source that ships with it."),
        "commentaries": out,
        "unavailable": missing,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main():
    with open(ROOT / "scripts" / "passages.json", encoding="utf-8") as f:
        passages = json.load(f)["passages"]

    only = sys.argv[1:]
    if only:
        passages = [p for p in passages if p["slug"] in only]
        if not passages:
            sys.exit(f"no matching passage for: {', '.join(only)}")

    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for p in passages:
        doc = build(p)
        with open(OUT / f"{p['slug']}.json", "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
            f.write("\n")
        got = len(doc["commentaries"])
        total += got
        chars = sum(c["chars"] for c in doc["commentaries"])
        print(f"  {p['slug']:<13} {got} commentator(s), {chars:>7,} chars"
              f"   (none from: {', '.join(m['id'] for m in doc['unavailable']) or '-'})")

    print(f"\n{total} commentary notes across {len(passages)} passage(s) -> data/commentary/")


if __name__ == "__main__":
    main()
