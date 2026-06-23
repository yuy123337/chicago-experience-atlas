# Chicago — Experience Atlas

An interactive map of Chicago places, colored not by star rating but by the *kind of inner
experience* a place tends to afford: **psychologically rich**, **happy**, or **meaningful**.

> Pick an experience → the city opens → places glow by how strongly visitors' words suggest
> that experience. Then go, and maybe you'll grow one of your own.

## What this is (and isn't)

This is a **research prototype** from a psychology lab studying the *good life* across places.
It is **not** a travel-rating site. I'm not asking "is this place good?" — I'm asking
"what does being here tend to *feel* like, in people's own words?"

The framing follows the idea that a good life has more than one dimension — not only **happiness**
and **meaning**, but also **psychological richness**: novelty, variety, perspective-change, and
interesting experience. *(See Oishi & Westgate, 2022, Psychological Review — verify exact citation.)*

## How I calculated the scores

*(Conceptual overview. The exact scoring implementation is kept private pending an IP/patent
decision — see note below.)*

1. **Source.** I start from **public Google reviews** of Chicago places (a 2016–2021 snapshot).
2. **Meaning-space.** I represent each review with a sentence-embedding model, so that two passages
   that *mean* similar things sit near each other — beyond shared keywords.
3. **Anchoring each construct.** I define each experience (rich / happy / meaningful) by anchor
   phrases that capture it and its opposite.
4. **Scoring a review → a place.** Each review leans toward or away from a construct by how close it
   sits to that construct's anchors versus the opposite. I aggregate review-level signal up to the place.
5. **What I surface as "worth recommending."** I rank places by this **relative affordance** score —
   how distinctively a place leans toward an experience — *not* by star rating or popularity. A small,
   quiet place that consistently sparks rich experiences can outrank a famous one.

### Honest limits
- **Descriptive, not causal.** A high score means visitors *described* the experience there — not a
  guarantee you will have it.
- **A snapshot.** 2016–2021 language; places change.
- **Aggregate, not endorsement.** These are patterns in collective language, not the lab's stamp of approval.

## Data sources
- Place scores: my offline analysis of public Google reviews (this snapshot).
- Map tiles: CARTO / OpenStreetMap. Place links open Google Maps (attribution per Google's terms).

## IP / patent note
The precise scoring algorithm is intentionally **not** included here. If you are reading this and the
repository is public, treat the method description as conceptual only.

## Files
- `index.html` — the whole front-end (hand-maintained source of truth).
- `data.js` — the scored places + ZIP lookup the map reads.
- `leaflet.js` / `leaflet.css` — the mapping library (vendored).
- `APP_SKELETON.md` — design spec for the companion app (Good Life City Explorer).

---
*Built by Yue Yin. A psychology-of-place project — exploring how the city shapes inner life.*
