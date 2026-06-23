# Good Life City Explorer — App Skeleton

*Working spec. North-star for the Expo app + the Chicago map. Confidence tags: **T1** established / **T2** reasoned design choice / **T3** speculative — verify before citing.*

---

## 1. The niche (why we stand out)

Travel apps (Yelp, TripAdvisor, Google) rank places by **quality, service, popularity**.
We map places by the **kind of inner experience they afford** — *psychologically rich*, *happy*, *meaningful* —
read from how real visitors **narrate** their experience.

- **T1** Grounded in Oishi & Westgate, *A psychologically rich life: Beyond happiness and meaning* (Psychological Review, 2022). The "good life" has **three** dimensions, not one. *(verify exact cite against your slides.)*
- **T2** Socioecological angle: places/situations shape minds — the "power of the situation" applied to a city. A place is not just *good*, it *affords* a kind of experience.
- **T2** We don't only recommend — we invite you to **add your own narration**, growing a living **ecology** of how a city's places shape people. That feedback loop *is* the research.
- **T2** Dispositional layer: **curiosity / openness to experience** is who seeks richness. A short trait intake personalizes the explorer and lets us study person × place. *(candidate scales: CEI-II curiosity, Big-Five Openness — T3, pick later.)*

**One-line pitch (rich):** *the accumulation of perspective-change and novel surprise across a life.*

**Social differentiation (T2):** break the web-trapped glass into a *real* place and log your feeling.
In the same gentle tone, you can see other explorers in the city — where they last paused, when they stopped —
and potentially make friends. The more you **contribute + explore**, the more **color** your little figure earns.
*(Presence/friends require a backend from the start — skeleton uses mock presence; real-time is Phase 6.)*

---

## 2. Core loop

1. **Choose a dimension** (rich / happy / meaningful) → *liquid glass shatters → break into the pixel city.*
2. **Explore the map** — places glow by how strongly they afford that experience.
3. **Portal a place** → three actions: 👣 *I've been here* · 🚪 *I want to go* · ✍️ *Memo / thought*.
4. **Go** → opens the real world (Google Maps). Return → narrate ("Already visited? Tell us how it felt, explorer.")
5. **Accumulate** → your **explorer avatar gains color** across the three dimensions → your garden / diary grows.
6. **(Research)** narrations feed the city's experiential ecology / dataset.

---

## 3. Screen skeleton (navigation)

```
Onboarding ──► Portal (choose dimension) ──► Map (explore)
                                              │
                                              ├─► Place sheet (portal: been / want / memo + narrate)
                                              │
   Me (avatar + garden, color accumulation) ◄─┘
   Diary (entries, decorate, redeem)
   [optional] Disposition intake (curiosity/openness)
```

---

## 4. Data topology (clean = easy to update)

Split **things** from **measurements** from **user-created**:

```
places      id, name, grp, lat, lon, url, rating, rev          # rarely changes
scores      place_id → { rich, happy, meaning, ... }           # your pipeline overwrites this
dimensions  key → { label, palette, pitch, richness_subdims[6] } # config
─────────────────────────────────────────────────────────────
user (local-first, AsyncStorage)
  profile     disposition scores (curiosity/openness)
  visits      [{ place_id, type: been|want|memo, text, ts }]   # the research gold
  avatar      { rich, happy, meaning } accumulation → color
  inventory   redeemable fonts / page colors
─────────────────────────────────────────────────────────────
(later, backend) narrations table  → research collection + cross-device sync
```

Efficiency win: each place stored **once**, not 3× (current `data.js` duplicates per construct).

---

## 5. Tech stack

| Layer | Choice | Note |
|---|---|---|
| App shell | **Expo (React Native)** | one codebase → iOS + Android; runs on your phone via Expo Go |
| Map | **A) WebView of the current Leaflet site** *(recommended to start)* | reuses ALL today's work (glass, pixel, portal) — fastest to "app on my phone" |
| | B) `react-native-maps` native | more native feel, but a rewrite |
| Local storage | `AsyncStorage` | RN's localStorage — gold/garden/diary/visits |
| Backend (later) | **Supabase** (free Postgres + auth) | when narrations must reach you / sync devices |
| Source of truth | `index.html` (web) + Expo project | generator emits **data only** now |

---

## 6. Build order (skeleton-first)

- **Phase 0** — Expo project scaffolds + runs on your phone (Expo Go). ← *next*
- **Phase 1** — empty navigation skeleton (the screens above).
- **Phase 2** — Map screen via WebView of the current site.
- **Phase 3** — Place portal + narration capture (AsyncStorage).
- **Phase 4** — Avatar / garden color accumulation.
- **Phase 5** — Diary (decorate, redeem).
- **Phase 6** — Backend collection (Supabase).
- **Phase 7** — Disposition intake (curiosity/openness) + person×place.

---

## 7. Data sources — website vs app (they are NOT the same)

| | Website | App |
|---|---|---|
| Places | **Research snapshot** (2016–2021 reviews, scored offline) | **Live Google Places** — current, open businesses |
| Purpose | demonstrate the method on frozen data | real exploration + logging today |
| Scores | precomputed per place | see tension below |

**⚠️ Scoring tension (T1):** our richness/happy/meaning scores need *many* reviews scored by our model offline.
The Google Places API returns only ~5 reviews per place and forbids bulk-harvesting reviews to rebuild a dataset.
So a brand-new live place **can't get a real score on the fly.** Likely resolution: app shows live places for
**discovery + logging**, and shows our **scores only where we have them** (the scored set), clearly labeled. Decide later.

## 8. IP, patents, citations, Google ToS

- **⚠️ Patent caution (T2 — consult counsel, I'm not a lawyer):** **publicly** posting the scoring method (GitHub, live site, app store) is a *public disclosure*. In the US that starts a **12-month** clock to file; in most other countries public disclosure **before** filing can **bar** a patent entirely. **If you might patent the algorithm or app, talk to your tech-transfer office BEFORE making the repo public.** Keep the scoring math in a private repo until then.
- **Citations:** include a **References / Methods page** (both site and app) — cite Oishi & Westgate (2022) and your own method. Keeps academic integrity and separates *your* IP from cited work.
- **Google Places ToS (T1, verify current terms):** attribution required; you may store **place IDs** long-term but generally **must not cache** other fields beyond ~30 days; can't build a competing places database from it. This shapes how the app stores live data.

## 9. Accounts, storage & safety (email signup)

**Where it's stored — recommend Supabase** (managed Postgres + built-in email auth, free tier):
- `auth.users` (Supabase-managed): email + **hashed** password, email-verification, password reset. We never see/store raw passwords.
- `profiles`: user_id → randomized handle, clan, avatar/3D-figure config, color progress. **Public identity = handle only.**
- `feedback` / `visits`: user_id → place_id, recommend, emotions[], comment, ts. The research data.
- Alt: Firebase (similar). Avoid rolling our own auth.

**Safety checklist (T2 — confirm specifics with your IRB/security):**
- **⚠️ IRB + consent FIRST.** Collecting narrations/emotions/location from people *for research* almost certainly needs **IRB approval, informed consent, and a privacy policy** before launch. This is the biggest item — flag to your advisor/IRB now.
- **Email stays private.** Never expose email or real name publicly; only the randomized handle.
- **Secret keys never ship.** App holds only Supabase's *public anon key*; the *service key* never goes in the app or GitHub. (Same lesson as the home-dir `.git` secrets risk.)
- **Row-Level Security** so each user can only read/write their own private data.
- **Location is sensitive** (the "last-seen, glows like Snapchat" feature = stalking risk). Make it **opt-in, coarse** (neighborhood, not exact point), and ideally friends-only.
- **Data rights:** let users delete their account + data; collect the minimum needed.

## 10. Visual direction (refs in ~/Desktop/materials)

Elegant, tactile, fine-art realism — NOT childish pixel. Pixel only as a small accent.
- **Avatar / clans:** voxel / blocky **3D cute figures** (`character1.webp`), colored per clan.
- **Material:** **pearlescent / iridescent / glass** (`pearltexture.jpg`, modernist glass house `images.jpeg`) — the app's "liquid glass" = pearly + tactile, not flat glassmorphism.
- **Tone:** Laila-Gohar-style **surreal-domestic still-life realism** (`gohar*`) — pastel, refined, warm whimsy.
- **Energy / color:** Tomokazu-Matsuyama-style **vibrant maximalist pops** (`tomokazu.jpeg`) over a calm neutral base; curated palette (`miya.jpeg` swatch strip).
- **Implications:** simple **modern** font at openings (not pixel); **one neutral base color + 3 construct accents**; tactile reaction on click; refined > cute.

## Open decisions
- [ ] Map: **WebView-reuse** vs native rebuild (recommend WebView to start).
- [ ] Collection: local-only now → Supabase when ready to gather narrations.
- [ ] Curiosity/openness scale: which validated items.
- [ ] Verify Oishi framing + citation against your slides.
- [ ] Expo project lives in a **local** folder (NOT Google Drive — node_modules + Drive sync conflict).
