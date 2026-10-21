# STDY-APP

A deep Bible study app. One subject at the centre, six facets orbiting it:
historical context, literary context, original-language word roots, images of
real places and objects, related passages, and open scholarly disputes.

**Live:** https://2wavey141.github.io/STDY-APP/
**Build plan:** [BUILD-PLAN.md](BUILD-PLAN.md)

## The core principle

Two colours, never sharing a visual treatment:

- **Gold** (`#E0A458`) marks anything retrieved from a lexicon, morphology
  database, cross-reference set, or named commentary. Cited and checkable.
- **Violet** (`#9B8AD4`) marks anything written by the model, always reasoned
  from the gold above it, never floating free.

This is not a disclaimer at the bottom of a screen. It is a colour system, and
it is enforced in the data: every facet has separate `sourced` and `written`
fields, and every sourced item carries `verified: false` until a human checks
the page number.

## Layout

```
index.html              gallery (the Pages root)
verse.html              THE APP - the orbit running on data/
nightfall-orbit-v2.html design prototype, static, self-contained
nightfall-topic.html    topic view - fellowship / koinonia
nightfall-landing.html  discovery - search, curated tiles, catalog rails
v1/v2/v3-*.html         earlier passes, light theme, superseded

scripts/sources.json       pinned API and translation IDs
scripts/passages.json      the v1 passage set
scripts/build_data.py      scripture ingest, merges curated content
scripts/build_commentary.py public-domain commentary ingest
scripts/verify_quotes.py   checks every quote against its source

content/still-argued/*.json hand-written facet content (ours)

data/index.json            passage list for the app
data/passages/*.json       one file per passage
data/commentary/*.json     full commentary text per passage
```

`content/` is hand-written and is the app's voice. `data/` is generated and
can be rebuilt from scratch at any time.

## Building the data

Python 3 only. No dependencies, nothing to install.

```sh
python3 scripts/build_commentary.py   # fetch public-domain commentary
python3 scripts/build_data.py         # fetch scripture, merge curated content
python3 scripts/verify_quotes.py      # gate: every quote must be verbatim
```

Each takes an optional slug to do one passage: `python3 scripts/build_data.py acts-2-42`.
Run the commentary step first - `build_data.py` verifies curated quotes against it.

This fetches scripture from the [Free Use Bible
API](https://bible.helloao.org/docs/) and writes `data/passages/<slug>.json`.
The app reads those files and **never calls the API at runtime** - that keeps it
fast, keeps it working when a third party is down, and makes every passage
reviewable before it ships.

To add a passage, add an entry to `scripts/passages.json` and re-run.

### Translation IDs are not guessable

Verified against the live API: the bare id `KJV` returns a **Thai** Bible, and
`WEB` is not an id at all. The four English public-domain translations are
`BSB`, `eng_kjv`, `ENGWEBP`, `eng_asv`. They are pinned in `scripts/sources.json` -
don't replace them with guesses.

## Citations are checked, not trusted

"Still argued" is built from commentators whose **full text ships with the app**,
so there are no page numbers in books nobody owns. Every quote is checked
verbatim against that text in two places: `build_data.py` refuses to mark a
quote verified without checking it, and `verify_quotes.py` exits non-zero if any
quote in `content/` is not found in its source. Run it before any commit that
touches `content/`.

That makes the failure this project exists to correct - a plausible-sounding
invented reference - structurally impossible for the public-domain tier.

These commentators died between 1564 and 1910, so the facet shows how a question
**was** argued, not how it is argued now. Modern scholarship is a later layer,
and the facet is labelled `scope: historical` so the UI can say so.

## Status

Interface prototypes are done and should not be redesigned.

- Scripture: **5 passages, 4 translations each**
- Commentary: **24 notes, ~159k chars**, 6 public-domain commentators
- Facets: **1 of 30 filled** - Acts 2:42 "still argued", 5 verified quotes
- `verse.html` reads it all: four translations, three positions, and every
  quote expandable to show itself highlighted inside the full source note

`verse.html` fetches from `data/`, so a browser will not load it over
`file://`. Serve the folder - `python3 -m http.server`, then
`localhost:8000/verse.html` - or use the live URL. The five facets that are
still placeholder copy are badged in rust and say they must not be trusted.

The remaining 29 are the real work. [BUILD-PLAN.md](BUILD-PLAN.md) says who does
it and in what order.

Citations still visible in the *prototype HTML* are unverified placeholders and
must be verified or deleted before anything is public. The ones in `content/`
are checked.

## Attribution

Scripture texts and commentary via the Free Use Bible API (AO Lab),
bible.helloao.org - public domain. Berean Standard Bible - public domain,
berean.bible. Commentary by Calvin, Matthew Henry, Gill, Clarke, and
Jamieson-Fausset-Brown - public domain.

Tyndale Open Study Notes are deliberately **not** ingested: they are CC BY-SA,
and share-alike is kept at arm's length. See [BUILD-PLAN.md](BUILD-PLAN.md).
