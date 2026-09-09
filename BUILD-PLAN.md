# Build plan — Bible study visualizer

*8 September 2026. Companion to HANDOFF.md, which listed this as the one thing never written.*

Readable version: https://claude.ai/code/artifact/f5d5f590-4239-4afa-b361-09da873694bd

**Gold** below means verified against live APIs and licence pages on the date above.
**Violet** means my judgment — estimates and recommendations, reasoned from the gold, not facts.

---

## The short version

The visualizer is the only thing here that doesn't exist elsewhere, and its
differentiator is *Still argued*.

That differentiator is not a software problem. Every other facet is a database
lookup buildable in weeks. *Still argued* requires a person to read real
scholarship and write honest summaries with verified page numbers. That work is
slow, manual, and cannot be automated without destroying the thing that makes
the product worth using.

**Critical path: start the scholarship before you start the code.** Building the
app takes months; researching fifty passages properly takes longer, and nothing
launches without it. Started together, the content is what delays the launch.

---

## Verified (gold)

| Source | Gives you | Licence | Status |
|---|---|---|---|
| Free Use Bible API (bible.helloao.org) | 1,256 translations, no key, no rate limit, commercial OK | MIT codebase | Confirmed live |
| Public-domain commentaries (same API) | Calvin, Matthew Henry, Jamieson-Fausset-Brown, Gill, Clarke, Keil & Delitzsch | Public domain | 7 available |
| SBLGNT | Greek NT text | CC BY 4.0 | Better than expected — the old EULA with the 25% rule no longer applies |
| MorphGNT | Morphological tagging, lemmatisation | CC BY-SA | Usable |
| Treasury of Scripture Knowledge (via OpenBible.info) | ~340,000 cross-references | Public domain | Usable |
| Theographic | 3,000+ people, 1,600+ places, events | CC BY-SA 4.0 | See share-alike trap |

**Finding that changes the plan.** The Bible API already serves seven
public-domain commentaries, including Calvin and Matthew Henry — two names the
handoff listed as quotable at length. A real chunk of the citation problem
solved for free, from an endpoint already being called, with no rights work.
Doesn't solve *Still argued*, which needs living scholars.

**Translation IDs are not guessable.** `KJV` resolves to a *Thai* Bible. The
English four are `BSB`, `ENGWEBP`, `eng_kjv`, `eng_asv`. Pin them in config.

`/api/BSB/ACT/2.json` returns Acts 2:42 correctly: "They devoted themselves to
the apostles' teaching and to the fellowship, to the breaking of bread and to
prayer."

---

## The share-alike trap

Theographic is CC BY-SA 4.0. Share-alike means derivative works inherit the
licence. Irrelevant for a free site; worth five minutes now if this ever takes
money. The risk isn't using the data — it's building your knowledge graph so
tightly on theirs that yours counts as an adaptation.

**Recommendation (violet):** query it as a reference layer, attribute clearly,
but store curated content — facet copy, image tags, scholarly positions — in
your own schema keyed by passage, not by their record IDs. Same for Tyndale's
study notes, also CC BY-SA.

---

## Build order

**0. Decide, don't build.** *Days, no code.* Three gating decisions: will this
ever make money; how Theographic sits in your schema; which passages ship.
On the last — 25 to 50, not the whole Bible, chosen for genuine scholarly
dispute as much as familiarity. A verse with no disagreement makes your best
facet look empty. Acts 2:42 and κοινωνία already qualify.

**1. The data spine.** *Foundation.* Ingest, don't call at runtime. BSB, KJV,
TSK, Strong's, MorphGNT into one local store; a static JSON file per passage
holding everything the gold facets need. Makes the app fast, resilient to third
parties going down, reviewable before it ships, and gives the research work
somewhere to land that can't silently vanish.

**2. The plain reader.** *Cheap, ships value immediately.* Sits directly on
phase 1, no new data. The tier everyone gets. Tests the two-tier premise before
the depth is finished.

**3. The visualizer, on real data.** *The centrepiece.* Interface is done — do
not redesign the orbit. Three facets are pure retrieval and could work in weeks:
the words (Strong's/MorphGNT), read next (TSK), where it sits (structure). Three
are blocked on human work: where and when (Theographic + curation), see it
(track A), still argued (track B).

**Track A — image library.** *Parallel, start now, runs for months.* ~400 images
of sites, artefacts, manuscripts, models. Places and objects, never scenes. The
work isn't downloading — every image needs its licence checked individually
(Wikimedia is a mixture, not blanket permission), provenance recorded, and
tagging to places and objects. Dull, parallelisable, delegable.

**Track B — the scholarship.** *Parallel, start first, the real critical path.*
Per passage: 2–4 genuine positions, who holds them, book and page, page
verified. Public domain quotable at length; modern scholars (Keener, Bock,
Wright, Dunn, Bruce) named and cited, prose never reproduced.

Two hard rules: every existing citation in the prototypes is a placeholder and
must be verified or deleted before anything is public. And this cannot be
generated — a model inventing plausible page numbers is precisely the failure
this product exists to correct.

**4. Discovery, caching, ship.** *Mostly assembly.* Wire the landing page to
real passages, pre-generate and store every facet, ship. No accounts, no notes,
no groups.

---

## Unit economics

Caching holds up: the Acts 2:42 map is identical for every user, so generate
once, store, serve static.

- **Compute, one time:** ~300 generations for a 50-passage launch (6 facets
  each). Single-digit dollars total; serving is static files. *Not* your
  constraint.
- **Human hours, unavoidable:** 200–500 (violet estimate) for 50 passages
  researched properly plus 400 images sourced and rights-checked.

The budget conversation that matters is whether you do the research yourself,
hire a graduate student or seminarian, or partner with a scholar. That decision
sets your launch date more than any technical choice here.

---

## What not to build

- **Community and discussion.** The danger isn't hate speech — a classifier
  catches that. It's denominational fighting and strangers explaining someone's
  suffering to them, which no moderation API detects. Defer entirely.
- **Accounts and notes.** Nothing in v1 needs to know who you are.
- **Person and Book facet sets.** Genuinely open, but each new subject type
  multiplies research work, and research is already the bottleneck. Design them
  after verse and topic are proven on real content.
- **Licensed translations.** BSB reads well and is free forever. Keep
  translations pluggable, then forget it until someone asks.
- **Redesigning the orbit.** It works. Spend the time on content.

---

## Decisions needed

1. **Will this ever make money?** *My take: assume yes even if you never do it.
   Constraints are mild; retrofitting is painful.*
2. **Which passages ship in v1?** *My take: let me propose 60 and you strike the
   ones that don't feel right.*
3. **Who does the scholarship?** *My take: do the first five yourself. You'll
   learn what good looks like before you hire.*
4. **Where to start building?** *My take: phase 1, the data spine. Unblocked
   today, nothing moves without it, and no open question changes it.*
