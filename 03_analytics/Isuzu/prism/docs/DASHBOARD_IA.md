# PRISM Dashboard IA — target information architecture

**Date:** 2026-07-17 · **Status:** proposal on paper — no code changed
**Scope:** 19 pages under `prism/pages/` + `app.py` cockpit. Goal: ≤10 visible nav entries without losing a single insight. Portability rule: IA is path-neutral (everything reads `config.DERIVED_DIR`); `FACTS.md` stays the quote gate for any number leaving the app.

---

## 1 · Inventory — every page, its question, its audience

| Page | Primary question | Tabs / sections (real names) | Audience | Verdict |
|---|---|---|---|---|
| `app.py` (Home) | Where do I click? Any alert? | KPI strip, alert ribbon, GPS traffic-light heatmap, cockpit grid | MD+all | **KEEP** — fix: `18_Decision_Models.py` is not linked anywhere in `SECTIONS` |
| `1_UIO.py` | How big is the parc, where, growing? | single page (fleet by DB / model / reg-year) | MD | **KEEP** → Fleet |
| `2_GPS.py` | € per truck per year, who's red? | GPS Overview · Trends · Part Explorer · Export | MD (Overview/Trends) · analyst (Part Explorer) | **KEEP** → Spend |
| `3_PMS.py` | Capture vs expected demand, € gap? | Capture Rate by Category · Revenue Opportunity Table · Distributor Breakdown · Network Capture League · ITUK Incentive Structure · 2026 PMS Marketing Calendar | MD (league, gap) · ops (calendar) | **KEEP** → Capture; move ITUK Incentive → ITUK hub; Marketing Calendar → Tools |
| `4_BVP.py` | Genuine vs BVP mix — GP quality? | Overview · PMS capture · Mix & trends · Substitution story · GPS / SPU · AIM risk · Catalog | MD (Overview/Mix) · analyst (Catalog) | **KEEP** → Mix, minus 3 duplicate tabs (see §4.1) |
| `13_DB_Parts_Mix.py` | Genuine / contested / BVP split per DB? | single page | analyst | **MERGE INTO Mix** (one extra tab) |
| `5_Insights.py` | Cross-signal: where does the network win/leak? | Opportunity Matrix · BVP × Capture · Growth Decomp · Trajectory · Benchmark · Displacement · Seasonal · Pareto | mixed | **MERGE INTO Network Intelligence** (§4.2) |
| `5_Strategic.py` | 15 contract dashboards | Most exposed (triple threat) · PMS opportunity (€) · Network ranking · Airfreight cost · Stockout seasonality · Stockout profile · Capture trend · Part lifecycle · Revenue concentration · Revenue bridge · Price vs aftermarket · Basket correlation · Aftermarket substitution · Geographic risk · Capture recovery (€) | mixed | **MERGE INTO Network Intelligence** (§4.2) |
| `12_Offset_Insights.py` | Movement / leakage / VOR power | 1·Movement · 2·Lumpiness→Airfreight · 3·Demand-Flow (Sankey) · 4·VOR Pricing Power · 5·Premium vs Defection · 6·Capture Ceiling | analyst; Sankey/leakage flagged **internal only** in-page | **MERGE INTO Network Intelligence** (non-leakage) + internal shelf (leakage) |
| `6_Scorecard.py` | One-page PDF per distributor | PDF generator | ops (meeting prep) | **MERGE INTO Review Pack** — Review Pack already imports `build_scorecard`; add a "scorecard-only" option |
| `9_Review_Pack.py` | Full QBR document | PDF generator (scorecard + trends + AIM + substitution) | ops | **DEMOTE → Tools** (generator, not a view) |
| `15_Customer_Risk.py` | Which DB is most at aftersales risk? | Ranking · Signal breakdown · Threat map · Aftermarket scrape · Export | MD (Ranking) · analyst (scrape) | **MERGE INTO Network Intelligence** (Ranking/Breakdown/Map); Aftermarket scrape → internal shelf |
| `11_ITUK_PMS_Story.py` | ITUK: mix, not capture deficit | 1·Oil filter mix-shift · 2·Where the recoverable money is · 3·Air filter opportunity · 4·Category scorecard | MD | **KEEP** → ITUK hub |
| `6_ITUK_PMS_Audit.py` | Which PNs carry each ITUK category? | single page (Contract 16) | analyst | **MERGE INTO ITUK hub** (audit tab) |
| `7_AIM_Review.py` | Pricing-risk exposure by family? | Network Overview · Family Detail · Gap Closer · Export | analyst; MD reads only the high-risk % | **MERGE INTO Network Intelligence** → Pricing & competition tab |
| `16_AIM_GPS_Matrix.py` | SPU × PMS-capture quadrant | single quadrant (x-axis re-based 2026-07-17: AIM gate at 0.12 was dead — all-time max 0.0487) | MD | **MERGE INTO Network Intelligence** → Benchmark tab |
| `8_ASP_Monitor.py` | Who sells above/below network norm? | single page (from `pms_opportunity.avg_sp_eur`) | analyst | **MERGE INTO Network Intelligence** → Pricing & competition tab |
| `14_Tender_Pipeline.py` | Which public tenders to attack? | funnel · country · owner · scatter · action queue (value on only 12/520 rows) | ops | **DEMOTE → Tools** |
| `10_Data_Integrity.py` | Is the pipeline green? | verification report + cross-system reconciliation | analyst/ops | **DEMOTE → Tools** (its pass/warn/fail already surfaces on Home KPI strip) |
| `18_Decision_Models.py` | Wallet → captured → gap; who defects? | € Waterfall · Revenue Runway · Defection · Attach · ITUK Leakage · Elasticity | MD (first 3) · internal (last 3) | **SPLIT** (§4.3) |

**KILL list (nothing else dies):**
- `5_Insights.py` tab "BVP × Capture" — same quadrant family as `16_AIM_GPS_Matrix` (SPU/capture) and the Mix Overview KPIs (BVP unit share + capture side by side). One quadrant survives, in Benchmark.
- `5_Strategic.py` tab "Basket correlation" (Contract 8) — analyst curiosity with no decision attached; park the CSV, drop the tab.
- `6_Scorecard.py` as a separate page — functionality absorbed by Review Pack (same bundle, same `build_scorecard` call).

---

## 2 · Target IA — 10 visible entries

**Revised 2026-07-17**: Early Warning was built ahead of the phased plan (see §6) and added as its own top-nav entry rather than folded into Network Intelligence. It supersedes NI tab 1 "Most exposed" (§4.2) and the Decision "Defection" tab (§4.3) — both are absorbed, not duplicated.

```
1. Early Warning   silence · capture slope · VOR stress — one ranked priority list, € exposed
2. Home            app.py — KPI strip, alert ribbon, heatmap, cockpit grid
3. Fleet (UIO)     parc size, model mix, growth
4. Spend (GPS)     SPU €/truck, traffic lights, trends, part explorer
5. Capture (PMS)   capture rate, € gap league, distributor breakdown
6. Mix (BVP)       genuine vs BVP quality-of-capture + catalog + DB mix split
7. Network Intelligence   sanitized Insights ∪ Strategic ∪ Offset ∪ AIM/ASP/Risk — 7 tabs (was 8; "Most exposed" → Early Warning)
8. ITUK            Story · IML gap reconcile · PN audit · Incentive · (internal: dealer leakage, attach)
9. Decision        MD-safe only: € Waterfall · Revenue Runway (Defection → Early Warning)
10. Tools          collapsed: Review Pack/Scorecard · Tender Pipeline · Data Integrity ·
                   PMS Marketing Calendar · internal shelf (leakage Sankey, scrape, elasticity)
```

MD acceptance check (≤3 clicks each):
- **GPS%** → Home heatmap (0 clicks, traffic-light per DB) or Spend → GPS Overview. Wallet-based share (captured ÷ ceiling): Decision → € Waterfall.
- **Wallet ceiling** → Decision → € Waterfall → first metric ("Wallet ceiling", from `wallet_waterfall.csv`).
- **ITUK capture gap (IML)** → ITUK → "Where the recoverable money is" + the IML-reconcile note (the €2.0M IML v7 absolute gap currently lives only in a warning inside `18_Decision_Models.py` ITUK Leakage tab — it moves to the ITUK hub where an MD will actually look for it).
- **Any defection alert?** → **Early Warning** (0 clicks from top nav) — supersedes the old Decision → Defection route; the same `defection_alerts.csv` rows are ranked there alongside capture slope and VOR, with dead categories separated out.

---

## 3 · Before / after menu tree

### Before (19 pages, 8 cockpit sections, ~60 tab-level destinations)

```
Home (app.py)
├─ Layer 1 · Fleet
│  └─ 1_UIO
├─ Layer 2 · Methodologies
│  ├─ 2_GPS ······················ 4 tabs
│  └─ 3_PMS ······················ 6 sections
├─ Product Line · Genuine vs Best Value
│  ├─ 4_BVP ······················ 7 tabs
│  └─ 13_DB_Parts_Mix
├─ Layer 3 · Cross-Module Intelligence
│  ├─ 5_Insights ················· 8 tabs
│  ├─ 5_Strategic ················ 15 tabs
│  └─ 12_Offset_Insights ········· 6 tabs
├─ Distributor Lens
│  ├─ 6_Scorecard
│  ├─ 9_Review_Pack
│  └─ 15_Customer_Risk ··········· 5 tabs
├─ ITUK Deep-Dive
│  ├─ 11_ITUK_PMS_Story ·········· 4 sections
│  └─ 6_ITUK_PMS_Audit
├─ Pricing & Risk
│  ├─ 7_AIM_Review ··············· 4 tabs
│  ├─ 16_AIM_GPS_Matrix
│  └─ 8_ASP_Monitor
├─ Pipeline & Governance
│  ├─ 14_Tender_Pipeline
│  └─ 10_Data_Integrity
└─ (orphan — no cockpit link) 18_Decision_Models ·· 6 tabs
```

### After (originally 9 entries; revised to 10 with Early Warning, see §2 — tree below not yet redrawn)

```
Home
├─ Fleet (UIO)
├─ Spend (GPS) ··············· Overview · Trends · Part Explorer      [Export → download button]
├─ Capture (PMS) ············· Category capture · € gap league · Distributor breakdown
├─ Mix (BVP) ················· Overview · Mix & trends · Substitution story · DB mix split · Catalog
├─ Network Intelligence ······ Most exposed · Opportunity € · Trajectory & growth ·
│                              Benchmark & quadrant · Pricing & competition ·
│                              Substitution pressure · Supply stress (VOR) · Revenue structure
├─ ITUK ······················ Story · Recoverable € (IML reconcile) · PN audit · Incentive
│                              [internal] Dealer leakage · Attach
├─ Decision (MD-safe) ········ € Waterfall · Revenue Runway · Defection
└─ Tools ····················· Review Pack (incl. scorecard-only) · Tender Pipeline ·
                               Data Integrity · PMS Marketing Calendar ·
                               [internal] Demand-flow Sankey · Aftermarket scrape · Elasticity
```

---

## 4 · Concrete merges

### 4.1 Mix (BVP) — 7 tabs → 5, duplicates return to their home page

`4_BVP.py` currently re-implements three other pages inside itself:

| BVP tab | Duplicate of | Action |
|---|---|---|
| PMS capture | `3_PMS.py` capture views (same `pms_capture` bundle slice) | drop tab; Overview keeps its 4 KPIs (Total capture · Genuine capture · BVP unit share · Untapped €) + cross-link to Capture |
| GPS / SPU | `2_GPS.py` Overview (same `gps_db`) | drop tab; cross-link |
| AIM risk | `7_AIM_Review.py` (same `aim_db`) | drop tab; AIM lands in Network Intelligence → Pricing & competition |
| — | `13_DB_Parts_Mix.py` | absorb as new tab "DB mix split" (genuine / contested / BVP € per DB — one chart set, no reason to be a page) |

### 4.2 Network Intelligence — 29 tabs (8 Insights + 15 Strategic + 6 Offset) + 3 pages (AIM, ASP, Customer Risk) → 7 tabs (tab 1 superseded by Early Warning, 2026-07-17)

Same-question pairs, tab by tab:

| New tab | Absorbs (source → tab) | Shared question |
|---|---|---|
| ~~1 · Most exposed~~ | **SUPERSEDED — moved to Early Warning (own top-nav entry, 2026-07-17)** | Triple threat (capture × premium × VOR) and the Customer-Risk weighted index are now one ranked list with a generated reason and a €, not a scatter to eyeball. Customer Risk's Ranking + Signal breakdown + Threat map are only *partly* absorbed — the ranking is, the threat-map/breakdown views are not and still need a home (Tools → internal shelf, §4.5/§6 phase 7) |
| **2 · Opportunity €** | Insights → "Opportunity Matrix"; Strategic → "PMS opportunity (€)" (Contract 3, **same CSV `pms_opportunity_matrix.csv` rendered twice today**); Strategic → "Capture recovery (€)" (Contract 15); Offset → "6 · Capture Ceiling" | "Where is uncaptured €, how much is realistically recoverable?" Matrix on top, recovery bridge below for the highlighted DB |
| **3 · Trajectory & growth** | Insights → "Trajectory" (capture heatmap by year) + "Growth Decomp" (SPU-YoY × UIO-YoY); Strategic → "Capture trend" (Contract 7 `capture_trajectory.csv`); Offset → "1 · Movement" (quiver) | "Who is improving/declining, and is it fleet or penetration?" — currently answered four times in four places |
| **4 · Benchmark & quadrant** | Insights → "Benchmark" (parts per 100 trucks); Strategic → "Network ranking" (Contract 10 percentile radar); `16_AIM_GPS_Matrix.py` (SPU × capture quadrant) | "Where does each DB rank vs best-in-class?" |
| **5 · Pricing & competition** | Strategic → "Price vs aftermarket" (Contract 13); Offset → "5 · Premium vs Defection"; `8_ASP_Monitor.py` (ASP vs network norm); `7_AIM_Review.py` → Network Overview + Family Detail + Gap Closer | "Are we priced out, and where is pricing undisciplined?" Premium-vs-aftermarket (external) and ASP-vs-norm (internal) side by side; AIM high-risk % as the risk overlay |
| **6 · Substitution pressure** | Insights → "Displacement" (pair ratio BVP÷genuine); Strategic → "Aftermarket substitution" (Contract 2 invasion curve) + "Part lifecycle" (Contract 9) | "Which parts are being displaced, how fast, at what lifecycle stage?" (Mix keeps its own "Substitution story" — that one is genuine-vs-BVP in-tent, per [[feedback_bvp_not_leakage]]: different question) |
| **7 · Supply stress (VOR)** | Strategic → "Airfreight cost" (Contract 1) + "Stockout seasonality" (Contract 6) + "Stockout profile" (Contract 12); Offset → "2 · Lumpiness→Airfreight" + "4 · VOR Pricing Power" | "Where do stockouts cost money, and who ships urgent at zero premium?" 5 tabs → 2 views (cost map + pricing-power scatter) |
| **8 · Revenue structure** | Insights → "Pareto" + "Seasonal"; Strategic → "Revenue concentration" (Contract 14 Gini) + "Revenue bridge" (Contract 5) + "Geographic risk" (Contract 11) | "How concentrated / seasonal / geographically skewed is the book, and what moved YoY?" |

Sanitization: nothing in these tabs shows an inferred-leakage € — the Offset Sankey ("Demand-Flow") and its leakage leg go to the internal shelf under Tools, keeping the page's own warning ("INFERENCE… internal use only"). Customer Risk's "Aftermarket scrape" tab (scraped competitor prices) goes with it.

### 4.3 Decision Models — 6 tabs split by audience

| Tab | Destination | Why |
|---|---|---|
| € Waterfall | **Decision** (stays) | The EUR identity wallet → captured → gap; MD-safe, caveats already in-page ("Ceiling = GPS max-spend, not a forecast") |
| Revenue Runway | **Decision** (stays) | Golden-Window wallet projection to 2030; scenario note in-page |
| ~~Defection~~ | **SUPERSEDED — moved to Early Warning** | Removed from `18_Decision_Models.py` 2026-07-17 (st.info pointer left in its place); the MD's "any defection alert?" answer is now 0 clicks from top nav instead of a Decision tab. **Verified, uncommitted** — same file carries an unrelated in-flight waterfall edit from another writer; commits once that lands |
| Attach | **ITUK hub → internal** | ITUK dealer-year grain; in-page caveat "association, not causal" — sparring material, not MD reading |
| ITUK Leakage | **ITUK hub → internal** | In-page warning says it: "call-order hint, not a € commitment; NOT the IML v7 absolute gap (€2.0M)". The IML-reconcile *sentence* moves to the visible ITUK hub; the dealer call list stays internal |
| Elasticity | **Tools → internal shelf** | "LOW POWER by construction… never quote a beta externally" — by its own warning it must not sit on any MD path |

The orphan bug (Decision Models absent from `app.py` nav) was fixed by phase 1 (`a626249`) — it has had a first-class nav tile since 2026-07-17.

### 4.4 ITUK hub — 2 pages + 3 strays → 1 entry

- `11_ITUK_PMS_Story.py` (4 sections) = visible spine.
- `6_ITUK_PMS_Audit.py` = "PN audit" tab (Contract 16 — the receipts behind the story).
- `3_PMS.py` § "ITUK Incentive Structure" moves here (ITUK content has no business in the network Capture page).
- Decision "Attach" + "ITUK Leakage" tabs land here behind the internal flag (both are ITUK-dealer grain).
- Scorecard/Review Pack keep ITUK as default distributor but remain generic generators in Tools.

### 4.5 Export tabs → download buttons

`2_GPS.py`, `7_AIM_Review.py`, `15_Customer_Risk.py` each burn a tab slot on "Export". Replace with `st.download_button` on the relevant tab — 3 nav destinations disappear at zero information cost.

---

## 5 · Non-goals honoured

No new models (elasticity/attach untouched, only relocated). No hosting/auth assumptions for the new work environment — the IA is a Streamlit `pages/` + `st.tabs` reshuffle reading the same `DERIVED_DIR` CSVs, portable as-is. No implementation done: this document is the deliverable.

---

## 6 · Implementation plan (added 2026-07-17; phases 0-2 + Early Warning shipped same day — status below)

### Mechanism

**`st.navigation` + `st.Page`** (Streamlit 1.55 installed; requirements already pin ≥1.36). Declaring navigation in `app.py` replaces the file-based `pages/` auto-sidebar entirely — visible entries, grouping, and hidden pages become code, and page files never need renaming for order. The entrypoint runs on every page load, so the shared frame (page config, CSS, beta banner, internal gate) hoists into `app.py` once; per-page `st.set_page_config` calls die (only offender: `18_Decision_Models.py:29`). `st.Page(url_path=…)` preserves bookmarked slugs for pages that keep their identity (GPS, PMS, BVP, UIO).

**Internal gate**: `INTERNAL_MODE = os.getenv("PRISM_INTERNAL", "false").lower() == "true"` in `config.py`, cloning the `BETA_MODE` pattern (config.py:182). Default **off** → the app is MD-safe by default; internal entries (dealer leakage, attach, elasticity, demand-flow Sankey, aftermarket scrape) simply don't register in `st.navigation` / don't render as tabs. New launcher `run_prism_internal.ps1` sets the env var; existing `run_prism.ps1` stays the sanitized default.

### Phases — app stays green after every phase

| # | Phase | Status | Content | Size |
|---|---|---|---|---|
| 0 | Safety net | ✅ **done** `13d0314` | Branch `ia-restructure` (prism is a git repo). Pipeline green gate (`scripts/run_pipeline_and_verify.ps1`). `tests/test_pages_smoke.py`: AppTest runs every registered page with 0 exceptions | 0.5 session |
| 1 | Nav shell | ✅ **done** `a626249` | `app.py`: `st.navigation({section: [st.Page(...)]})` in the (now 10-entry, see §2) layout. Fixed the Decision-Models orphan | 0.5 |
| — | **Early Warning** *(not in original plan — built out-of-band)* | ✅ **done** `d68cffa` | New top-nav entry, ahead of the Network Intelligence merge: `scripts/build_early_warning.py` + `pages/0_Early_Warning.py`. Ranks silence (`defection_alerts.csv`) × capture slope (recomputed, partial-year + level-gated) × VOR stress (`vor_seasonality.csv`) into one priority list, €307K exposed at last build. Supersedes NI tab 1 "Most exposed" (§4.2) and Decision → Defection (§4.3). Design + data-trap writeup: `docs/EARLY_WARNING_DESIGN.md` | 1 (unplanned) |
| 2 | Extraction | ✅ **done** `d8fac81` | Render functions extracted to `modules/`: `strategic_charts.py`, `insights_charts.py`, `aim_review_charts.py`, `asp_charts.py`, `customer_risk_charts.py` (`15_Customer_Risk.py` 364→147 lines). Mechanical lift-and-shift, no visual changes | 1.5–2 |
| 2b | **Decision trim (partial)** *(pulled forward from phase 6, alongside Early Warning)* | ⏳ **verified, blocked on commit** | Defection tab removed from `18_Decision_Models.py`, st.info pointer to Early Warning added. 5 tabs, 0 exceptions, smoke green. **Cannot commit yet** — the same file has an unrelated in-flight waterfall rework (`over_target_eur`) from another writer in the shared working tree; commit once that lands, or split the hunks | 0.2 (mostly done) |
| **NEW** | **`capture_trajectory` partial-year fix** *(discovered building Early Warning — not in original scope)* | 🔄 **in progress** (background task, spawned 2026-07-17) | `modules/strategic_build.build_capture_trajectory()` regresses through the current partial year → 35 declining alerts, 29 of them (83%) artifacts (network median capture 2026 = 0.019 vs 0.094 in 2025; 0 real declines hidden when excluded). New `modules/year_coverage.py` (`latest_complete_year()` / `is_partial()`) has landed as shared infra; the actual fix inside `build_capture_trajectory()` has not yet. **Blast radius wider than the Strategic tab**: `modules/scorecard_pdf.py` and `modules/review_pack_pdf.py` both read `trend_slope_pp_per_year` / `alert_declining` straight from the CSV — the same 83% false-alarm rate is printing into the distributor scorecard and QBR review-pack PDFs today. Fixing the builder + re-running `scripts/build_strategic_contracts.py` fixes the PDFs for free; verify the fix targets the builder, not just the page render | 0.5 (in flight) |
| 3 | Network Intelligence | ⏳ **not started** | New `pages/network_intelligence.py`: **7 tabs** (§4.2 — tab 1 dropped, absorbed by Early Warning) calling the phase-2 extracted fns; one shared sidebar scope. Deregister 5_Insights, 5_Strategic, 12_Offset, 7_AIM, 8_ASP, 16_Matrix; files → `_archive/`. **15_Customer_Risk is a partial deregister only**: its Ranking is superseded by Early Warning, but Threat map / Signal breakdown / Aftermarket scrape are real analyst views Early Warning does not cover — they need the Tools internal shelf (phase 7), not deletion | 1 |
| 4 | Mix | ⏳ not started | `4_BVP.py`: drop tabs "PMS capture", "GPS / SPU", "AIM risk" (cross-link captions instead); new tab "DB mix split" = body of `13_DB_Parts_Mix.py` as a function; archive 13 | 0.5 |
| 5 | ITUK hub | ⏳ not started | New `pages/ituk.py`: tabs = Story (4 sections of `11_ITUK_PMS_Story.py`) · PN audit (`6_ITUK_PMS_Audit.py` body) · Incentive (block from `3_PMS.py:684`) · *internal:* Dealer leakage + Attach (from `18_Decision_Models.py`). IML v7 €2.0M reconcile sentence surfaces in the visible "Recoverable €" tab | 1 |
| 6 | Decision (remainder) | ⏳ **Defection done (see 2b)**, rest not started | Remove `st.set_page_config` (line 29 — still there); Elasticity render → internal shelf. Waterfall/Runway already MD-safe as-is | 0.3 (reduced — Defection already out) |
| 7 | Tools | ⏳ not started | Tools nav section: Review Pack (+ "scorecard only" checkbox; retire `6_Scorecard.py`) · Tender Pipeline · Data Integrity · PMS Marketing Calendar (block from `3_PMS.py:751`) · *internal shelf page*: Demand-flow Sankey + Customer-Risk Threat map/Breakdown/Aftermarket scrape (see phase 3 note) + Elasticity | 1 |
| 8 | Polish & verify | ⏳ not started | Export tabs → `st.download_button` (GPS, AIM — Customer Risk's is arguably now redundant with Early Warning's export). Migrate remaining `use_container_width=`. Update README/ARCHITECTURE/`dashboard_contracts.md`. AppTest parity sweep + real-browser render before calling it done | 0.5 |

**Remaining ≈ 3.5–4 sessions** (phases 3–5, 6-remainder, 7–8) **+ the in-flight capture_trajectory fix**. Phases 0–2 plus the unplanned Early Warning delivered same-day; most of the perceived MD-facing value (nav fixed, one ranked risk list, Decision Models slimmed) already shipped.

### Housekeeping blocking clean commits (not architectural, but on the critical path)

- **Shared working tree, ≥4 concurrent writers** as of 2026-07-17 (this session, the extraction commits, the capture_trajectory background task, and whoever owns the uncommitted waterfall rework). `git status` carries unrelated in-flight changes (`config.py`, several `data/*.yaml`, deleted `mockups/*`, deleted `run-prism.ps1`) — not this roadmap's concern, but don't `git add -A` on this branch without reviewing the diff first.
- `18_Decision_Models.py` specifically has two independent uncommitted changes stacked (Defection removal + the waterfall `over_target_eur` rework) — resolve by whoever owns the waterfall change committing first, then Decision's trim commits clean on top.

### Risks / gotchas

- **Widget-key collisions**: merging pages into one script makes duplicate `st.selectbox` keys fatal (`StreamlitDuplicateElementKey`). Rule: every widget in a merged page gets an explicit tab-prefixed key (`ni_traj_cat`, not `traj_cat`).
- **Live-compute tabs**: Insights "Growth Decomp", "Seasonal", "Pareto" compute from raw sales via `sales_loader`/`gps_engine` (not derived CSVs) — Network Intelligence inherits that first-open latency; keep their `@st.cache_data` wrappers intact.
- **Partial-year guard**: `16_AIM_GPS_Matrix.py:44-60` (complete-year default + partial-year warning) must survive the move into the Benchmark tab — it exists to stop a calendar artifact reading as a network collapse.
- **Cache behaviour improves**: today 6+ pages each trigger `load_bvp_bundle()`; post-merge one page shares one cached bundle.
- **Zero pipeline risk**: no build script or derived CSV changes anywhere in the plan.
- **Portability**: everything routes through `config.py` (`paths.yaml` + FACTS.md root discovery) — no new absolute paths; survives the work-environment migration as-is.
