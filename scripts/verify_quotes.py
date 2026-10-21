#!/usr/bin/env python3
"""Verify every curated quote against the source text that ships with it.

The app's promise is that anything marked as retrieved is checkable. This makes
that mechanical: every quote in content/ must appear verbatim in the
corresponding data/commentary/ file, attributed to the commentator it claims.
If one does not, this exits non-zero and the quote must be fixed or removed.

Run it before any commit that touches content/.

    python3 scripts/verify_quotes.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
COMMENTARY = ROOT / "data" / "commentary"


def norm(s):
    """Compare on normalised whitespace, and treat curly and straight quotes as
    equal - the sources mix them and that is not a citation error."""
    s = re.sub(r"\s+", " ", s).strip()
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("—", "-"), ("–", "-")):
        s = s.replace(a, b)
    return s


def main():
    files = sorted(CONTENT.glob("*/*.json"))
    if not files:
        print("no curated content found in content/ - nothing to verify")
        return 0

    checked = failures = 0

    for path in files:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        slug = doc.get("slug")
        rel = path.relative_to(ROOT)

        src = COMMENTARY / f"{slug}.json"
        if not src.exists():
            print(f"FAIL {rel}: no commentary data at {src.relative_to(ROOT)} "
                  f"- run build_commentary.py")
            failures += 1
            continue
        with open(src, encoding="utf-8") as f:
            texts = {c["id"]: norm(c["text"]) for c in json.load(f)["commentaries"]}

        print(f"\n{rel}")
        for position in doc.get("positions", []):
            for held in position.get("held_by", []):
                checked += 1
                cid = held.get("commentary_id")
                quote = held.get("quote", "")
                who = held.get("author", cid)

                if cid not in texts:
                    print(f"  FAIL  {who}: no note from '{cid}' on {slug}")
                    failures += 1
                    continue
                if norm(quote) not in texts[cid]:
                    print(f"  FAIL  {who}: quote not found verbatim in {cid}")
                    print(f"        {quote[:90]!r}")
                    failures += 1
                    continue
                print(f"  ok    {who} ({held.get('era','?')}) - {len(quote)} chars")

    print(f"\n{checked} quote(s) checked, {failures} failure(s)")
    if failures:
        print("\nA failing quote must be corrected or removed before this ships.")
        return 1
    print("Every curated quote appears verbatim in the source that ships with it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
