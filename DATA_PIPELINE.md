# Data Backend — Chicago Experience Atlas

> The map + contribute panel are a **data-collection instrument**: they gather how people
> experience places (Been here / Curious → ratings, emotions, free text) and, optionally, an
> email + home ZIP. This doc explains how that data is stored, why the backend is built this
> way, and how to **test and analyze** it yourself.

---

## 1. Architecture — three independent layers

The website is **static** (plain `index.html` on GitHub Pages) and *cannot write to a database
itself*. So writing is delegated to a Google Apps Script web app that appends to a Google Sheet:

```
① Front end (index.html on GitHub Pages)   — shows the map, collects answers
        │   visitor hits "Share"  →  POST (JSON)
        ▼
② Backend (Google Apps Script web app)      — validates, dedups, appends a row
        │   appendRow
        ▼
③ Store (Google Sheet "Chicago_feedbacks")  — your data; analyze from here
```

Two **separate** deploy paths (this trips everyone up):

| Layer | Update by |
|---|---|
| Front end (`index.html`) | `git push` → GitHub Pages auto-deploys (~1 min) |
| Backend (`apps_script.gs`) | Apps Script → **Deploy → Manage deployments → ✎ → New version** (keeps the same URL) |

> ⚠️ Use **New version**, not "New deployment" — the latter mints a *new* URL and you'd have to
> re-wire `FEEDBACK_URL` in `index.html` every time.

---

## 2. The Sheet: 3 tabs, `construct` is a column (not a split)

| Tab | One row = | Key columns |
|---|---|---|
| `been` | a place someone **visited** | `rich_1to5, meaning_1to5, happy_1to5, frequency, endorse, emo_*, text` |
| `curious` | a place someone is **curious** about | `expectation, exp_rich_1to5, exp_meaning_1to5, exp_happy_1to5, emo_*` |
| `explorers` | an **email sign-up** | `email, home_zip` (de-duplicated by email) |

Every row also has: `ts` (UTC), `ts_local` (Chicago time), `cid` (dedup key), `passport_id`,
`construct` (the lens the visitor had open), and `place_id` (the Google `gmap_id`).

**Emotions are dummy-coded**: one `0/1` column per word (`emo_pleasant` … `emo_shallow`) + a raw
`emotions_raw` string. 9 words = 6 positive + 3 reverse-keyed (stressful/boring/shallow).

**When is a row written?** A contribution is sent the moment the visitor submits the panel; an
`explorers` row is written only when they enter an email in the sign-up modal.

---

## 3. Why the backend is built this way (4 ideas worth learning)

**a) Self-healing header** — the script writes the header only on an empty tab, and adds any
*new* field as a trailing column automatically. → Adding a question never means clearing the
Sheet. *Cost:* new columns appear at the far right, so in analysis **select by name, not by
position.**

**b) Idempotency key (`cid`)** — every submission carries a unique id; the backend skips a `cid`
it has already written. → A retry can **never** duplicate a row. (Same idea as Stripe's
"idempotency keys.")

**c) Acknowledged writes + retry outbox** — the browser reads the `{ok:true}` reply; anything
unconfirmed waits in a `localStorage` outbox and retries (backoff + on next page load). → No data
lost to wifi blips, closed tabs, or bursts. Safe *because* of (b).

**d) Concurrency lock** — `LockService` serializes writes, so simultaneous submissions queue
instead of colliding.

> This is the *production pattern* (acknowledged + idempotent + durable) on a zero-ops stack.
> When you outgrow it → **Supabase/Postgres**: same columns, just point the POST there. No redesign.

---

## 4. Test it yourself (learn by doing)

**① See the endpoint accept a row.** This POSTs a clearly-marked test row to the `been` tab — run
it, then look at the Sheet, then delete that row:

```bash
curl -sL -X POST -H "Content-Type: text/plain" \
  -d '{"relation":"been","place_id":"CURL_TEST","passport_id":"TEST","construct":"rich",
       "name":"CURL TEST — delete me","cat":"t","grp":"t","lat":41.88,"lon":-87.63,
       "rich_1to5":5,"meaning_1to5":4,"happy_1to5":5,"emotions":"interesting|pleasant",
       "text":"curl test, safe to delete","cid":"curltest-001"}' \
  "https://script.google.com/macros/s/AKfycbw00zKyE3uS8qiyW0ZpJtGzlMaGSA43LvjSFsIKeU0_PYJDWBDj-ftMnu5VtUF7QbTYJw/exec"
```
Expected reply: `{"ok":true}`.

**② See idempotency work.** Run the *exact same* command again (same `cid:"curltest-001"`).
Reply is `{"ok":true,"dup":true}` and **no second row appears** — the `cid` deduped it. Change the
`cid` and a new row appears. That's the whole safety mechanism, visible.

---

## 5. Export & analyze (in pandas)

The Sheet is for *collecting*; analyze in Python.

```bash
# Manual export (most reliable): in the Sheet, pick a tab →
# File → Download → Comma-separated values (.csv)
```
```python
import pandas as pd
been    = pd.read_csv("been.csv").drop_duplicates("cid")     # cid = offline safety net
curious = pd.read_csv("curious.csv").drop_duplicates("cid")

# join contributions back to place metadata on place_id = gmap_id
master = pd.read_csv("chicago_eligible_master.csv")
joined = been.merge(master, left_on="place_id", right_on="gmap_id", how="left")

# link one person's contributions across tabs via passport_id
been.groupby("passport_id").size()
```

**Live (always current):** in the Sheet → **File → Share → Publish to web → pick the tab → CSV**,
copy the URL, then `pd.read_csv(URL)` (re-run = latest). ⚠️ Publish-to-web makes that tab publicly
readable; for private data use the manual download or `gspread`.

---

## 6. Setup / re-wire (one time)

1. Open the **Chicago_feedbacks** Sheet → Extensions → Apps Script → paste `apps_script.gs` → Save.
2. Deploy → **New deployment** → Web app (Execute as: Me · Who has access: **Anyone**) → copy `/exec` URL.
3. Paste it into `FEEDBACK_URL` near the top of the `<script>` in `index.html` → `git push`.
4. Later backend edits: **Manage deployments → ✎ → New version** (same URL).
