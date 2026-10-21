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
index.html              prototype gallery (the Pages root)
nightfall-orbit-v2.html verse visualizer - Acts 2:42, tilted orbit
nightfall-topic.html    topic view - fellowship / koinonia
nightfall-landing.html  discovery - search, curated tiles, catalog rails
v1/v2/v3-*.html         earlier passes, light theme, superseded

scripts/sources.json    pinned API and translation IDs
scripts/passages.json   the v1 passage set
scripts/build_data.py   the ingest

data/index.json         passage list for the app
data/passages/*.json    one file per passage
```

## Building the data

Python 3 only. No dependencies, nothing to install.

```sh
python3 scripts/build_data.py            # build every passage
python3 scripts/build_data.py acts-2-42  # build one
```

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

## Status

Interface prototypes are done and should not be redesigned. The data spine
fetches scripture for 5 passages. **0 of 30 facets are filled** - three per
passage are retrieval work, three need a human. That is the real remaining work,
and [BUILD-PLAN.md](BUILD-PLAN.md) says who does it and in what order.

Every citation currently visible in the prototypes is an unverified placeholder
and must be verified or deleted before anything is public.

## Attribution

Scripture texts via the Free Use Bible API (AO Lab), bible.helloao.org -
public-domain translations. Berean Standard Bible - public domain, berean.bible.
