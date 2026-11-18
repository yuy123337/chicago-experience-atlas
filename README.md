# Chicago — Experience Atlas

*Hi! This is a research prototype, not a product — so this README is written the way I'd explain it
to my collaborator(s): what it is, how the data works, how to keep it alive, and what I'm still worried about.*

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
## Approach

- **A 2021 snapshot, shown as popularity bands.** The reviews run up to 2021, and some places have changed or closed since. So the map shows a broad popularity band ("lots of visitors") rather than exact star ratings or review counts. Live details (hours, ratings, whether a place is still open) will come from the Google Places API in the app, not from this file.
- **Separating the three experiences.** Each review is scored on happiness, meaning and psychological richness by its cosine similarity to each construct's anchors. These first scores overlap strongly: richness correlates .81 with happiness and .83 with meaning, about as much as with its own sub-dimensions (see the sub-dimension cell in `diagnose.ipynb`). The next step is to remove the shared general factor before comparing the three.
- **Controlling for review length.** Longer reviews tend to score lower, so the scores control for word count.
- **Keeping every kind of place.** Religious places (churches, temples and other places of worship) stay in the data. Each map shows only the top 5% of places for its construct, so they rarely appear, except on the Meaningfulness map, where meaning and religion overlap and a church can genuinely rank high. If religious places start to dominate that map, a category filter in `build_chicago_site.py` (`church|place of worship|temple|mosque|synagogue|…`) can take them out. Tobacco, cannabis and liquor stores ("vice" places) are kept too.
- **A validity check.** Vice places are about half as common among the top 5% richest places as in the data overall (1.6% vs 3.1%; see the `is_vice` cell in `diagnose.ipynb`), which fits what psychological richness should capture.

## Files
- `index.html` — the whole front-end (source of truth).
- `data.js` — the baked places + ZIP lookup the map reads.
- `build_chicago_site.py` — the generator (CSV → `data.js`); selection criteria live here.
- `places_by_zip.json` — 319-ZIP place sets for the three-good-lives survey site.
- `diagnose.ipynb` *(on the Drive, not here)* — data-quality + validity checks (sub-dimensions, `is_vice`).
- `APP_SKELETON.md` — design spec for the companion app (Good Life City Explorer).

---
## Exporting the collected data

Contributions land in the **`Chicago_feedbacks` Google Sheet** — **3 tabs**:
- **`been`** (visited places): *experienced* 1–5 ratings (`rich_1to5`, `meaning_1to5`, `happy_1to5`), emotions, `frequency`, `endorse`, free `text`.
- **`curious`** (places they're curious about): ***expected*** 1–5 ratings (`exp_rich_1to5`, `exp_meaning_1to5`, `exp_happy_1to5`) + a free-text `expectation`. (Same slider UI as `been`, future-tensed — lets us study expectation vs. experience.)
- **`explorers`** (opt-in): `email` + `home_zip` (the ZIP they live in), de-duplicated by email.

Every row also carries `ts` (UTC), `ts_local` (Chicago time), and `passport_id`.

**Emotions are dummy-coded** — one `0/1` column per word (`emo_*`) plus an `emotions_raw` string. **Nine words**: six positive (pleasant/enjoyable→happy, interesting/surprising→rich, fulfilling/purposeful→meaning) and three reverse-keyed negatives (**stressful**↔happy, **boring**↔rich, **shallow**↔meaning) to flag places the algorithm over-ranked. Full guide in **`DATA_PIPELINE.md`**. Quick paths:
- **Manual (most reliable):** open a tab → **File → Download → CSV** (or **Excel `.xlsx`**) → `pd.read_csv("been.csv")`.
- **Live in a notebook:** **File → Share → Publish to web → pick the tab → CSV** → copy URL → `pd.read_csv(URL)` (re-run = latest data). *(Publish-to-web is publicly readable; use manual download or `gspread` for private.)*

Then **join to place metadata** on `place_id` = `gmap_id`:
```python
feedback.merge(master, left_on="place_id", right_on="gmap_id", how="left")
```

> **The schema self-heals.** The Apps Script (`apps_script.gs`) adds new columns automatically when we add questions — you **never clear or rebuild the Sheet**. One caveat: on a tab that already has rows, a new field appears as a **new column at the far right** (existing rows stay aligned, nothing shifts). So don't assume a fixed column order — **select by column name** in pandas.
>
> **Concurrency & no data loss.** Writes are serialized by a script lock (simultaneous submissions queue, never collide). Beyond that, delivery is **durable + acknowledged**: every submission carries a unique `cid` (**idempotency key**) and sits in a `localStorage` **outbox**. It's sent in CORS mode so the client can *read* the `{ok:true}` acknowledgement; any unconfirmed send is **retried** (jittered + exponential backoff, and again on the next page load). The server **dedups on `cid`**, so a retry can never create a duplicate row. Net effect: each submission is delivered **exactly once** — surviving wifi drops, closed tabs, and bursts. *(For web-scale traffic you'd move to Firestore/Supabase; this is the production *pattern* on the lightweight stack.)*

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
*Oishi Lab · 2026 — Yin*
