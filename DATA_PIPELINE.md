# Data Pipeline — Chicago Experience Atlas

> **Current version is a *data-collection prototype*.** The map + contribute panel exist to gather
> how people experience places (Been here / Curious → ratings, descriptors, free text). It is not
> yet a public product — it's the instrument that fills the dataset.

## Where the data lives (storage, now → later)

- **Now → Google Sheet** (via the Apps Script web app). It's effectively a **lightweight database
  already**: structured rows, the **6 construct×relation tabs** (`rich_been`, `rich_curious`,
  `happy_been`, `happy_curious`, `meaning_been`, `meaning_curious`), queryable with `pd.read_csv`.
  Perfect for the prototype + early real collection.
- **Later → a real database (Supabase / Postgres)** — when you need **accounts, scale, public reads,
  and live queries.** Same columns/schema, so migrating is just **pointing the Apps Script's POST at
  Supabase instead. No redesign.**

So the Sheet is your database for now; Supabase is the grown-up database when you scale — and nothing
is wasted, because the contribution schema is identical either way.

## How the data flows

```
contribute panel  →  POST (JSON)  →  Apps Script doPost  →  appends a row to the right tab
                                                            (place_id links to chicago_eligible_master.csv)
```
Each row carries `place_id` (the Google gmap_id), so you **join back to the place metadata**:
```python
feedback.merge(master, left_on="place_id", right_on="gmap_id", how="left")
```

## How to export the data (3 ways)

### 1. Before the Sheet is wired — from the browser (localStorage)
The submissions are saved in the browser. On the site, open the console (**Cmd+Option+J**) and run:
```js
exportFeedback()
```
→ downloads CSV files. (⚠️ localStorage is **only your own browser** — for testing, not real collection.)

### 2. From the Google Sheet — manual (most reliable)
Open the Sheet → pick a tab → **File → Download → Comma-separated values (.csv)** *or* **Microsoft Excel (.xlsx)**.
Then:
```python
import pandas as pd
df = pd.read_csv("rich_been.csv")
```

### 3. From the Google Sheet — live in your notebook (always current)
In the Sheet: **File → Share → Publish to web → choose the tab → CSV → Publish** → copy the URL.
```python
import pandas as pd
URL = "https://docs.google.com/.../pub?gid=...&single=true&output=csv"
df = pd.read_csv(URL)   # re-run anytime = latest data, no download
```
⚠️ *Publish-to-web makes that tab publicly readable.* For private data, use **manual download** (#2) or
**gspread** (authenticated Sheets API) instead.

## To turn the live connection on
1. Open the **Chicago Feedback** Sheet → **Extensions → Apps Script** → paste `apps_script.gs` → Save.
2. **Deploy → Web app** (Execute as: Me · Who has access: Anyone) → copy the `…/exec` URL.
3. Paste that URL into `FEEDBACK_URL` at the top of the `<script>` in `index.html`.

Then every submission appends to your Sheet in real time, sorted into the 6 tabs, joinable on `place_id`.
