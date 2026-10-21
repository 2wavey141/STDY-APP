#!/usr/bin/env python3
"""Build the passage data spine.

Fetches scripture from the Free Use Bible API and writes one JSON file per
passage into data/passages/. The app reads those files; it never calls the API
at runtime. That keeps it fast, keeps it working when a third party is down,
and makes every passage reviewable before it ships.

Stdlib only - nothing to install.

    python3 scripts/build_data.py            # build every passage
    python3 scripts/build_data.py acts-2-42  # build one
"""

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
OUT = ROOT / "data" / "passages"
SCHEMA = 1

# The six facets. Three are fixed and appear on every subject in the same
# orbital position; three flex by subject type. See HANDOFF / BUILD-PLAN.
FIXED_FACETS = ["where-and-when", "see-it", "still-argued"]
FACETS_BY_TYPE = {
    "verse": ["the-words", "where-it-sits", "read-next"],
    "topic": ["the-words", "how-it-develops", "key-passages"],
}

# Which facets can be filled by retrieval alone, and which need human work.
# Recorded in the data so the build can report honestly on what is outstanding.
RETRIEVABLE = {"the-words", "read-next", "where-it-sits"}


def load(name):
    with open(SCRIPTS / name, encoding="utf-8") as f:
        return json.load(f)


_chapter_cache = {}


def fetch_chapter(base, translation, book, chapter):
    """Fetch a chapter, caching so N passages in one chapter cost one request."""
    key = (translation, book, chapter)
    if key in _chapter_cache:
        return _chapter_cache[key]
    url = f"{base}/{translation}/{book}/{chapter}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "STDY-APP/build_data"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    _chapter_cache[key] = data
    return data


def verse_parts(content):
    """Flatten one verse's content into (text, footnote_ids).

    Verse content mixes three shapes, and getting this wrong corrupts text
    silently:
      "a plain string"              -> text
      {"text": ..., "poem": n}      -> ALSO text. Poetry lines live here, and a
                                       parser that keeps only strings drops
                                       them (115 of them in Acts 2 alone).
      {"noteId": n}                 -> a footnote marker, not text
      {"lineBreak": true}           -> spacing in poetry, not text
    """
    words, notes = [], []
    for part in content:
        if isinstance(part, str):
            words.append(part)
        elif isinstance(part, dict):
            if "text" in part:
                words.append(part["text"])
            elif "noteId" in part:
                notes.append(part["noteId"])
            # lineBreak and any unknown shape contribute no text
    text = re.sub(r"\s+", " ", " ".join(words)).strip()
    return text, notes


def extract(chapter_json, first, last):
    """Pull a verse range out of a chapter. Returns (text, verses, note_ids)."""
    verses, note_ids = [], []
    for item in chapter_json["chapter"]["content"]:
        if not isinstance(item, dict) or item.get("type") != "verse":
            continue
        n = item.get("number")
        if n is None or not (first <= n <= last):
            continue
        text, notes = verse_parts(item.get("content", []))
        verses.append({"verse": n, "text": text})
        note_ids.extend(notes)
    verses.sort(key=lambda v: v["verse"])
    return " ".join(v["text"] for v in verses), verses, note_ids


def footnotes_for(chapter_json, note_ids):
    """Translator footnotes for the range. These are sourced content - the
    translators' own notes - so they belong in the gold tier, cited."""
    wanted = set(note_ids)
    out = []
    for fn in chapter_json["chapter"].get("footnotes", []) or []:
        if fn.get("noteId") in wanted:
            out.append({
                "id": fn.get("noteId"),
                "text": re.sub(r"\s+", " ", (fn.get("text") or "")).strip(),
                "verse": (fn.get("reference") or {}).get("verse"),
            })
    return out


def empty_facet(name, subject_type):
    """A facet with the trust split built into its shape.

    'sourced' holds retrieved, citable items (gold). 'written' holds model
    prose (violet), which must name the sourced items it reasons from. The two
    are separate fields so the app cannot render one as the other by accident,
    and every sourced item carries verified=false until a human checks the page
    number - an app whose promise is "checkable" must not ship otherwise.
    """
    return {
        "position": FIXED_FACETS.index(name) if name in FIXED_FACETS else None,
        "fixed": name in FIXED_FACETS,
        "fillable_by": "retrieval" if name in RETRIEVABLE else "human",
        "sourced": [],
        "written": None,
        "status": "empty",
    }


def build(passage, cfg):
    base = cfg["api"]["base"]
    book = passage["book"]
    chapter = passage["chapter"]
    first = passage["verse"]
    last = passage.get("verse_end", first)
    subject_type = passage.get("type", "verse")

    texts, verses_by_tr, notes = {}, {}, []
    display = None

    for tr in cfg["translations"]:
        try:
            cj = fetch_chapter(base, tr["id"], book, chapter)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"    ! {tr['label']}: fetch failed ({e})", file=sys.stderr)
            continue
        text, verses, note_ids = extract(cj, first, last)
        if not text:
            print(f"    ! {tr['label']}: no text for verses {first}-{last}", file=sys.stderr)
            continue
        texts[tr["id"]] = text
        verses_by_tr[tr["id"]] = verses
        if tr.get("default"):
            notes = footnotes_for(cj, note_ids)
            display = cj["book"].get("commonName") or cj["book"].get("name")

    if not texts:
        raise RuntimeError(f"no text retrieved for {passage['slug']}")

    ref = f"{display or book} {chapter}:{first}" + (f"-{last}" if last != first else "")
    facets = FIXED_FACETS + FACETS_BY_TYPE.get(subject_type, [])

    return {
        "schema": SCHEMA,
        "slug": passage["slug"],
        "type": subject_type,
        "reference": {
            "display": ref,
            "book": book,
            "book_name": display,
            "chapter": chapter,
            "verse_first": first,
            "verse_last": last,
        },
        "why_included": passage.get("why"),
        "text": texts,
        "verses": verses_by_tr,
        "default_translation": next(t["id"] for t in cfg["translations"] if t.get("default")),
        "footnotes": notes,
        "facets": {name: empty_facet(name, subject_type) for name in facets},
        "attribution": cfg["attribution"],
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main():
    cfg = load("sources.json")
    passages = load("passages.json")["passages"]

    only = sys.argv[1:]
    if only:
        passages = [p for p in passages if p["slug"] in only]
        missing = set(only) - {p["slug"] for p in passages}
        if missing:
            sys.exit(f"unknown passage slug(s): {', '.join(sorted(missing))}")

    OUT.mkdir(parents=True, exist_ok=True)
    index, failed = [], []

    for p in passages:
        print(f"  {p['slug']}")
        try:
            doc = build(p, cfg)
        except Exception as e:
            print(f"    ! FAILED: {e}", file=sys.stderr)
            failed.append(p["slug"])
            continue
        path = OUT / f"{p['slug']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
            f.write("\n")
        got = len(doc["text"])
        print(f"    {doc['reference']['display']} - {got} translation(s), "
              f"{len(doc['footnotes'])} footnote(s)")
        index.append({
            "slug": doc["slug"],
            "type": doc["type"],
            "reference": doc["reference"]["display"],
            "text": doc["text"][doc["default_translation"]],
            "facets_filled": 0,
            "facets_total": len(doc["facets"]),
        })

    if index:
        with open(ROOT / "data" / "index.json", "w", encoding="utf-8") as f:
            json.dump({
                "schema": SCHEMA,
                "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "count": len(index),
                "passages": index,
            }, f, indent=2, ensure_ascii=False)
            f.write("\n")

    print(f"\n{len(index)} passage(s) written to data/passages/")
    if index:
        total = sum(i["facets_total"] for i in index)
        print(f"0 of {total} facets filled - that work is tracks A and B in BUILD-PLAN.md")
    if failed:
        sys.exit(f"{len(failed)} failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
