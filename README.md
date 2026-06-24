# Chicago — Experience Atlas

*Hi! This is a research prototype, not a product — so this README is written the way I'd explain it
to a labmate: what it is, how the data works, how to keep it alive, and what I'm still worried about.*

An interactive map of Chicago places, colored **not by star rating** but by the *kind of inner
experience* a place tends to afford — **psychologically rich**, **happy**, or **meaningful**
(Oishi & Westgate, 2022).

From the perspective of the map users, * We're offering a **mental shortcut for
deciding where to go**: a way to evaluate a place by the experience it tends to open up in you — read
from how visitors narrate it, in their own words, and hopefully we can learn about a more general question: *"is this place provide happy, psychologically rich or meaningful experience?"

---

## What is `data.js`? (read this first)

`data.js` is **not the raw data** — it's the small, baked file the website actually reads. It holds:

- `window.DATA` — for each construct (`rich`, `happy`, `meaning`, + 7 richness sub-dimensions), a list
  of the **top recommended places**, each: `{name, cat, grp, lat, lon, score, rev, rating, url}`.
- `window.ZIPXY` — a ZIP → coordinate lookup for the "Jump to ZIP" box.

It's a **curated slice**, not everything. It's generated from our scoring output — see below.

## How places get picked (the criteria — all in `build_chicago_site.py`)

```
MIN_REV = 30     # only places with ≥ 30 reviews (reliability)
PCT     = 0.05   # keep the top 5% by each construct's score
CAP     = 400    # at most 400 per construct
```
- **Richness** uses a *composite* of 6 sub-scores (`RICH_DIMS` = Psychological_Richness, FG_Richness,
  Curiosity_Stretching, Surprise, Perspective_Change, Exploration_Behavior), not a single vector.
- Current result ≈ **917 places** across rich/happy/meaning. Want more? Raise `CAP` / loosen `PCT` —
  e.g. dropping the cap gives ~**2,958** (still ≥30 reviews). It's one line.

## Keeping the data sustainable (the update loop)

The **source of truth** is *not* `data.js` — it's the scoring CSV on the shared Drive:
`…/experience_city_project_2007_2021/website_dat/output/chicago_eligible_master.csv` (41,107 places).

To refresh the map after re-scoring or to widen the selection:
1. (optional) tweak `MIN_REV / PCT / CAP` in `build_chicago_site.py`.
2. `python build_chicago_site.py`  → rewrites `data.js` (and a reference `index.generated.html`).
3. Bump the `?v=` number on the `data.js` line in `index.html` so browsers reload.
4. `git add -A && git commit -m "refresh data" && git push`.

`index.html` is the **hand-maintained source of truth** for the site itself — the generator no longer
overwrites it (it only writes data + a reference copy), so your design edits are safe.

## How the scores are made (conceptual)

Public Google reviews (2016–2021) → sentence-embeddings → each construct anchored by phrases and its
opposite → a review leans toward/away from a construct by cosine to those anchors → aggregated to the
place. We rank by **relative affordance** (how distinctively a place leans), *not* popularity.
*(Exact implementation kept private pending an IP/patent decision — keep this repo private.)*

## Things to be improved (please poke at these)

- **It's a 2021 snapshot.** Some places have closed and details are stale — so I deliberately show a
  **vague** popularity band ("lots of visitors") instead of exact stars/counts. Live details should
  come from the Google Places API later (in the app), not this file.
- **Discriminant validity.** The original way (cosine similarity direction) of calculating scores for reviews for different constructs are *highly collinear* — richness correlates with happy (0.81) and meaning (0.83) about as much as with its own sub-dimensions. See the sub-dimension cell in
  `diagnose.ipynb`. We probably need to residualize on a general factor before trusting the split.
- **Length confound.** Scores correlate negatively with review length; we control for word count.
- **Religion (the one to watch):** religious places (churches, temples, places of worship) are **kept in** the dataset, *not* excluded. Because we show only the **top 5% per construct**, they rarely surface — *except* on **Meaningfulness**, where a church can genuinely rank high (a meaning ↔ religiosity confound). If one starts dominating the Meaningful map, add a category filter (`church|place of worship|temple|mosque|synagogue|…`) in `build_chicago_site.py`. (Vice places — tobacco/cannabis/liquor — are likewise kept but rare in top-rich; `is_vice` ≈ half the base rate.)
- Nice validity signal: "vice" places (tobacco/cannabis/liquor) are ~**half** as common in the top-5%
  rich (1.6% vs 3.1% base) — see the `is_vice` cell in `diagnose.ipynb`.

## Files
- `index.html` — the whole front-end (source of truth).
- `data.js` — the baked places + ZIP lookup the map reads.
- `build_chicago_site.py` — the generator (CSV → `data.js`); selection criteria live here.
- `places_by_zip.json` — 319-ZIP place sets for the three-good-lives survey site.
- `diagnose.ipynb` *(on the Drive, not here)* — data-quality + validity checks (sub-dimensions, `is_vice`).
- `APP_SKELETON.md` — design spec for the companion app (Good Life City Explorer).

---
## Exporting the collected data

Contributions land in the **`Chicago_feedbacks` Google Sheet** — **3 tabs**: `been` (visited places: all 3 ratings + emotions + free text), `curious` (intentions + expectation), and `explorers` (opt-in emails). Emotions are **dummy-coded** (one `0/1` column per option, plus an `emotions_raw` string). Full guide in **`DATA_PIPELINE.md`**. Quick paths:
- **Manual (most reliable):** open a tab → **File → Download → CSV** (or **Excel `.xlsx`**) → `pd.read_csv("been.csv")`.
- **Live in a notebook:** **File → Share → Publish to web → pick the tab → CSV** → copy URL → `pd.read_csv(URL)` (re-run = latest data). *(Publish-to-web is publicly readable; use manual download or `gspread` for private.)*

Then **join to place metadata** on `place_id` = `gmap_id`:
```python
feedback.merge(master, left_on="place_id", right_on="gmap_id", how="left")
```

---
## Mindworks event mode — TEMPORARY (passport ID)

**This feature exists only for the in-person Mindworks event, and is built to expire by itself.**

**How it works live (during the event):**
1. A visitor opens the site → a **maroon Mindworks Passport prompt** appears *before* anything else.
2. They enter their **Mindworks Research Passport ID** — **required, no skip** (if they don't have one, an organizer creates one for them).
3. They explore and contribute normally — and **every** submission carries their `passport_id` (a column in `been`, `curious`, and `explorers`). That's how their map contributions join to the rest of their event responses.

**Persistence is session-based** (`sessionStorage`): the ID is held while the tab stays open and **cleared when the tab closes** — the prompt warns them they'll re-enter it on return. (Chosen over device storage so a borrowed/returned phone never carries a stale ID.)

**Auto-expiry:** the prompt is gated by `EVENT_START`/`EVENT_END` near the top of the script in `index.html` (currently `2026-06-24`→`2026-06-26` — **event date is 6.25**). After `EVENT_END` the prompt **never shows again** and the site behaves exactly as it did before — **no redeploy needed**. The date window controls only the *prompt*: data already collected (passport IDs included) **stays in the Sheet permanently**. To end early, set `EVENT_END` to a past date and push.

---
*Oishi Lab · 2026 — Yue Yin. A psychology-of-place project, exploring how the city shapes inner life.*
