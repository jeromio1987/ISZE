# CURSOR BUILD ORDERS — ISZE one-distributor operating dashboard

**Applies to every DB.** Build the HTML once, parameterised; run it per DB.
Confirmed with Jerome 2026-08-14.

---

## 1. What to build

For each `<DB>` you are asked to produce:

```
09_meetings\<DB>_Operating_Dashboard_2026\<DB>_Operating_Dashboard.html
09_meetings\<DB>_Operating_Dashboard_2026\OPEN_<DB>_Operating_Dashboard.cmd
```

`.cmd` content: `start "" "%~dp0<DB>_Operating_Dashboard.html"`

The ledger is already there:

```bash
python 04_tools\db_operating_dashboard\build_ledger.py --all
```

18 DBs: BELGIUM CYPRUS DENMARK FINLAND GERMANY GREECE HUNGARY ICELAND IRELAND ITUK IUK MALTA NORWAY PORTUGAL ROMANIA SWEDEN UMI UTI.

## 2. Rule 0 — render, never compute

Every figure lives in `NUMBERS_LEDGER.json`. Embed it as
`<script type="application/json" id="payload">` and render from it. The only arithmetic
allowed in JS is display formatting and percent-of-total for a stacked bar.

If a number you want is missing, **extend `build_ledger.py`** — never compute it in the HTML.
Do not edit the ledger JSON by hand; it is regenerated.

## 3. Hard bans

1. **No CDN.** Zero `<script src="https://`, zero `<link href="https://`. Inline
   `02_dashboards\_ui\chart.umd.min.js` — verified 200,807 bytes, **0** `sourceMappingURL`,
   clean UMD setting `window.Chart`. Nothing to strip. Or inline SVG.
   ⚠ Do **not** copy the head of `02_dashboards\ids\IDS_2026_dealer_compare_*.html` (pulls
   Leaflet from unpkg.com) or `IBX_SaTy_Fill_Rate_Dashboard.html` (CDN Chart.js).
2. **No invented numbers.** Absent from the ledger → empty state. Never carry a network
   average into a DB slot.
3. **No filenames in the visible body.** One grey footer, human language, plus as-of date.
4. **Respect `flags`.** `SHOW_GPS_PCT` false → no percentage anywhere from that DB
   (Ireland, Finland, Iceland read ≥100% — the denominator is wrong, not capture complete).
5. **Grain on every chip.** FY = Apr–Mar labelled by end year. PMS capture = complete CY.
   Wallet = CY. Never convert FY↔CY by 9/12.
6. **Never blend Israel.** UMI 1797 and UTI 1799 share payer 1797. Two separate dashboards.
   Neither is ever labelled "Israel". IDS Israel LCV is UMI's network only.
7. **Best Value is retention, not erosion.** Genuine → Best Value is in-tent, a gross-margin
   question. Never in an erosion total, never red. Only IAM defection is real erosion.
8. **Three erosion lanes never summed.** No shared axis implying addition.
9. **White text on pale backgrounds is forbidden.** Navy header → paper text. Paper row → ink `#222`.
10. Write only under `C:\Users\jerom\Desktop\claude\`. Never touch `07_deploy\`.
11. English UI.

## 4. House style

Navy `#15233c` / `#1a2b4a` · terracotta `#c0552d` · paper `#f7f4ee` · line `#d9d3c8` ·
muted `#6b6256` · ink `#222`. Green `#1d9e75` good · amber `#eda100` watch · red `#b23b3b` bad.
Headings Georgia, body Segoe UI. Bars ≥18px, ≤6 axis ticks, round ticks, no overlapping labels.
Chart.js overlapping after two attempts → inline SVG. Wide content scrolls in its own
container; the body never scrolls sideways.

**Tooltip on every derived chip** (`data-tip`): formula, snapshot date, what is *not* included.
Navy panel, paper text, terracotta accent. The ledger carries a `tooltip` object with those keys.

---

## 5. Rooms, and the ledger key each reads

Sticky tab bar, hero strip persistent.

### Hero — `hero`, `business_plan`, `plan_tracking`
Four chips with grain labelled: GPS-eligible € (FY, warranty in) · same ex-warranty (a
**toggle**, not a rival headline) · PMS capture (complete CY, **always with the network
comparator**) · wallet ceiling / captured / addressable gap.
Plus BP FY2027 and EXT TARGET. One sentence: *where we are with this customer.*

### A. Plan tracking — `plan_tracking`
- `bp_match` — **all 18 DBs currently MATCH.** Show a green tick; if it ever reads DIFF that
  is the headline.
- `build_up` — waterfall: BP FY2027 → stretch → EXT TARGET, with `against_capacity.max_spend_fy27_eur`
  as a reference line. `over_ceiling` true → that is the story.
- `actual_vs_plan` — FY actuals vs EXT TARGET bars, target in terracotta. `implied_growth_pct`
  as a caption.
- Bullet gauge: EXT TARGET against max spend; GPS% at BP vs at target.

### B. GPS spine — `gps_fy_spine`, `rate_change_impact`
- **Max two FY lines** (blueprint lock): GPS % and GPS % ex-warranty. No CY third series.
- `max_spend_basis` says which denominator was used. `gps_pct_v31_published` is the audit
  trail — show it only in a tooltip or an appendix, never as a second headline.
- Obey `render_rules`: **do not publish FY2023**. Complete FY2024–FY2026 on **one method**: GPS% = GPS-eligible billed ÷ (V19 parc × that year’s ISZE-net rate). CY N → FY N+1. FY2024 uses CY2023. Two lines: GPS% and GPS% ex-warranty (blank if ex-warranty euro is invalid). Y-axis 0–100. No CY GPS% unless a published calendar-year GPS workbook figure exists — do not invent one from the wallet. Footnote why CY is blocked; no fake CY toggle.
- `rate_change_impact` — the D-Max rate moved to **€262.50** (FY2027; base €250.00). Put the
  rate and its date in the footer so the denominator is never ambiguous.
- `flags.HAS_V31_FY_SERIES` false (ITUK, UTI) → no FY GPS% series exists. Show euros and
  the Dashboard FY27 figures. **Do not synthesise a series.**

### C. PMS — `sections.pms`
Diverging bars, DB vs network, sorted by revenue gap.
- **Never bare** — always against the network on the same expected-quantity model.
- **Never over time** — `uio_units` is frozen identical across all years for every DB.
- Grey `quotable: false` categories; keep them out of every euro total.
- Show `interval_confidence` (oil/fuel CONFIRMED, air PROVISIONAL, urea/blower NO OEM INTERVAL).
- `available: false` (CIS, Palestine) → empty state.

### D. Genuine vs Best Value — `sections.genuine_vs_bvp`
Render **`whole_book`** (the one with `THIS_IS_THE_ONE_TO_SHOW: true`).
If you also show `paired_basket_only`, its `coverage_pct_of_book` must appear **on the chart**.
For UMI that basket is 5.0% of euros and reads 81.6% BVP while the book is 3.7% — a 22× misread.

### E. Order pattern — `sections.order_pattern`
- `history.rows` (CY) and `history.fy_rows` (FY). Complete years only. **PRD counts as stock** (`prd_folded_into_stock`). Tooltip: PRD is treated as stock on this screen.
- 80/20 is stock (SOR+PRD) vs rush (VOR/RUSH/SVOR). Remaining other codes keep their own band only if they still exist.
- `q1_fy2027` — lead with `coded_share_of_eur_pct`. Obey `verdict_colour`; below 70% coded is **amber**.
- Fire the terracotta "same-day warehouse" remark **only** when `verdict_colour` is red.
- `cadence.do_not_render` — invoicing-by-weekday stays off.

### F. Three erosion lanes — `sections.three_lanes`
Three separate cards, never a total.
`street_iam` is real but narrow: read `db_revenue_coverage_pct` and print it on the card.
**Obey `SIGN_CONVENTION`** — Δ % = (IAM published − **projected ISZE retail**) / projected ISZE retail.
Projected retail = PR00 × 1.40 × 1.275 = ×1.785 (`channel` on the ledger). Positive = ISZE cheaper at retail (green); negative = ISZE dearer (red).
Do not compare IAM retail to ISZE net. Flag IAM trade vs projected retail as not perfect like-for-like.
Use `db_revenue_on_exposed_pns_eur`; **never** `gp_at_risk_eur_NETWORK_LEVEL_DO_NOT_ATTRIBUTE`.
`available: false` (UTI) → empty state.

### G. Working set — `sections.working_set`
Top 30 PN by euro, CY complete, credits excluded. Per row: euro, qty, PMS flag, warranty flag,
BVP status, `lever`. Mark Shell rows distinctly — they are excluded from the GPS numerator.
Honour `warranty_exclusion_warning`: where most top PNs sit on warranty claim lines, do **not**
apply the binary exclusion — show both lenses and label the limitation.

### H. IDS — per-DB pack where one exists
Country vs network A–E. Lead with **Section D (Parts)** where it is the worse gap.
Any zero-scored section gets a distinct "not scored / participation to confirm" fill — never
the same red as a genuine low score. 5+ dealers → matrix, not cards.
No IDS pack (Germany, Ireland, Sweden, Finland, Iceland, UTI) → drop the room entirely.

### I. Data integrity strip
Traffic lights driven off `source.in_green_verification_report` plus the known holes.
Link to the DB's `DATA_INTEGRITY.md`.

### J. What they should send us — sales-to-dealer is the #1 ask
Registry covers only IRELAND, ITUK, IUK, UTI, GREECE. Everyone else sends nothing.
Ask card framed as what's in it for them: monthly StD (invoice date, PN, qty; EUR optional;
dealer dimension if they have it). We adapt to their layout. **Do not ask IUK for EUR** — UK
value comes from ITUK.

### K. Executive digest — `p-open`, customer mode only (proposed 2026-08-19, not yet confirmed)

**Why.** In `customer` mode (today: only GREECE — `build_ledger.py:391` sets
`audience` per DB, everyone else is `internal`), `p-open` is the landing tab. Right now it is
two tables (mail issues, meeting follow-ups) built at `render_dashboard.py:548-559`, plus
whatever `p-plan`'s panel happens to contain, DOM-moved onto the end of `p-open` by the block at
`render_dashboard.py:1851-1861`. No chart, no cross-room number, on the tab a distributor opens
first. `internal` mode does **not** have this problem — it already has full Plan/Mix/Orders/
Family tabs — so this room only fires inside `if(customer){...}`.

**Rule 0 still applies.** Every field below already exists on the ledger and is already read by
another room in this same template. Zero new keys in `build_ledger.py`. This is a render-order
and layout change only.

**Build target:** `render_dashboard.py` (the `TEMPLATE` string + the DOM-move block at its tail).
**Not** the rendered `09_meetings\<DB>_Operating_Dashboard_2026\*.html` files — those are
generated output, overwritten on the next run. Regenerate with:
```
python 04_tools\db_operating_dashboard\render_dashboard.py --db GREECE
```
then `--all` afterward as a regression check on the 17 `internal`-mode DBs (new code must sit
inside `if(customer)`; an internal-mode pack should render byte-for-byte the same before/after
except for whitespace from the edit).

**New DOM order inside `p-open`** (top to bottom):
1. `<h2>Executive overview</h2>` + lead — unchanged.
2. **Verdict callout** (new) — one templated sentence, not free text:
   ```js
   const verdictOk = plan.bp_match==='MATCH' && !cap.over_ceiling;
   const verdictText = plan.bp_match!=='MATCH'
     ? 'Business plan does not match the locked workbook — check Plan tracking below.'
     : cap.over_ceiling
       ? 'Business plan confirmed against the locked workbook. Extended target sits above the max-spend ceiling — that is this quarter’s story.'
       : 'Business plan confirmed against the locked workbook, on track for FY27.';
   ```
   `callout ok` / `callout amber` per `verdictOk`. `plan` and `cap` are both already in top-level
   scope by this point (`plan` from the hero block, `cap` from `P.against_capacity` in Plan
   tracking) — don't recompute, just reuse.
3. **Digest grid** (new) — `class="digest-grid"`, up to 4 cards, CSS below. Card order and specs:

   | Card | Guard | Headline | Sub-line | Mini chart |
   |---|---|---|---|---|
   | IDS | `idsOn` | `os.country_avg_pct` + `%`, else `—` | `${hits.length} on the visit hit list · ${leadLab} weakest${leadPp==null?'':' ('+leadPp+' pp vs network)'}` | small `indexAxis:'y'` bar, this-country vs network, from `ids.summary` (same data as `cIds`, no legend) |
   | GPS + PMS | always | latest complete-FY `gps_pct` from `gps.rows` (same filter as `drawGps()`: `publish!==false && !partial_year && fy!==2023`) if `L.flags.SHOW_GPS_PCT`, else latest `actual_eur` with a € prefix | `PMS ${pct(pms.capture_pct_total)} total capture · ${pms.vs_lcv_peer_pp>0?'+':''}${pms.vs_lcv_peer_pp} pp vs LCV-peer` | small line sparkline, same filtered `gps.rows`, no axes |
   | Aftermarket | always | `spa.n` SPA candidates | `${bq.n_iam_pns_in_this_db} matched aftermarket lines · ${bq.n_over_ceiling} over ceiling` | none — counts, not a series; don't force a chart on it |
   | Sales analysis | `salesOn` | `L.sales_analysis.verdict.chips[0]` (its `.label`/`.value`) | that chip's `.sub` | none |

   **Scope gotchas for whoever builds this:**
   - `os`, `hits`, `leadLab`, `leadPp` are declared `const` **inside** the IDS room's
     `else{...}` block (`ids.available` branch) — they do not exist at this later point in the
     script. Re-declare locally from the `ids` object itself: `ids.os`, `ids.os.hit_list`,
     `ids.lead_label`, `ids.lead_vs_network_pp`. `bq`, `spa`, `pms`, `gps`, `mixBlk`, `strat`,
     `P`/`cap` are all top-level `const`s and are safe to reuse as-is.
   - `L.sales_analysis.verdict` is a plain read off the ledger — do **not** call
     `paintSalesBook()` to get it; that function also builds all 7 sub-sections' charts and only
     runs lazily on tab click. Before hardcoding `chips[0]` as the YoY headline, grep
     `build_sales_analysis.py` for `"chips"` to confirm it's ordered with the primary metric
     first — not verified in this pass.
   - Chart.js is already vendored inline (`template/assets/chart.umd.min.js`) — use small
     Chart.js canvases for the two mini-charts (`.chart-wrap.mini`, ~46–60px tall, no legend, no
     axis ticks), not hand-rolled SVG. Consistent with every other room.
4. **Plan tracking** — existing content, unchanged, just repositioned. Currently the DOM-move
   block at `render_dashboard.py:1851-1854` (`while(planPanel.firstChild) ov.appendChild(...)`)
   appends it after the issue tables. Change to `insertBefore` against the issues wrapper (see
   below) so it lands after the digest grid and before the issue tables instead. No content
   change — the build-up/ceiling chart and actual-vs-target chart already exist and are already
   correct; this is purely an order fix.
5. **Open items** — the existing two cards (mail issues, meeting follow-ups), unchanged content,
   wrapped in a new `<div id="pOpenIssues">` at build time (`render_dashboard.py:548`) so step 4
   can `insertBefore` it. Demoted from "the whole tab" to "the tail."

**Open decision — do not resolve this silently:** a 5th card for **Family strategy**
(`sections.lost_sales_strategy`, `strat.counts` — families needing a BVP push, SPA/Hold split)
would be genuinely useful here, but `p-fam` is **not** in the customer `TABS` array
(`render_dashboard.py:506-520`) — it's internal-only today. Surfacing its counts on a
customer-visible digest either means adding it with no drill-through link (digest-only, numbers
the distributor has never seen before with no detail page behind them), or promoting `p-fam` to
a real 6th customer tab (a bigger scope call — the full family-by-family action table becomes
distributor-visible). **Default for v1: omit it.** Ship the 4 cards above; revisit once Jerome
picks a direction.

**Digest CSS** (append inside the existing `<style>` block, reuses house-style tokens verbatim —
no new colors):
```css
.digest-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:0 0 20px}
@media(max-width:1100px){.digest-grid{grid-template-columns:1fr 1fr}}
@media(max-width:720px){.digest-grid{grid-template-columns:1fr}}
.dcard{background:var(--surface);border:1px solid var(--line);padding:14px 16px}
.dcard .l{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.dcard .v{font-size:22px;font-weight:700;color:var(--navy);margin-top:3px}
.dcard .n{font-size:12px;color:var(--muted);margin-top:4px;line-height:1.4}
.dcard .chart-wrap.mini{height:46px;margin-top:8px}
```

**Before calling it done (in addition to §7 below):**
- [ ] Runs only inside `if(customer)` — an `internal`-mode DB (e.g. BELGIUM) renders unchanged
- [ ] `os`/`hits`/`leadLab`/`leadPp` re-declared locally, not referencing the IDS room's
      block-scoped consts
- [ ] Sales-analysis chip order verified against `build_sales_analysis.py` before shipping the
      headline as "the" YoY number
- [ ] GPS mini-sparkline respects `L.flags.SHOW_GPS_PCT` exactly like `drawGps()` does — no
      percentage shown where the flag is false
- [ ] Family strategy card intentionally absent, not forgotten

---

## 6. Blacklisted sources — never read these

| File | Why |
|---|---|
| `01_data\00_derived\competitiveness_autodoc_risk.csv` | All 298 rows have `autodoc_min_eur ≤ 2.34` (median exactly 2.34) — the £2.00 "no results" placeholder propagated as a competitor price. Implies engine assemblies face €2.34 competition. |
| `01_data\00_derived\pms_summary_by_db.csv` | Year 2026 only, and CY2026 is Jan–Mar actual against a full-year expected. Understates ~4×. |
| `01_data\00_derived\warranty_fy26_monthly.csv` | 372 bytes, network total only (no DB dimension), USD, and missing Dec-2025. |
| `01_data\raw\sales\*.XLSX` | Never load. Derived only. |
| Any archived `ISUZU_UIO_Overview_2026_vN.xlsx` | Only `06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx` is valid (V19 internally). |

## 7. Before you call it done

- [ ] `src="https://` and `href="https://` → **0**
- [ ] Opens offline, network off, every chart renders
- [ ] No csv/parquet filename in the visible body
- [ ] Every hero chip tooltip carries formula + snapshot + exclusions
- [ ] No GPS % where `SHOW_GPS_PCT` is false
- [ ] No negative or zero-denominator bar anywhere
- [ ] Genuine/BVP shows the whole book, not the paired basket
- [ ] IAM sign convention correct — positive is good
- [ ] "Same-day warehouse" remark only where `verdict_colour` is red
- [ ] Three lanes never summed
- [ ] Nothing labelled "Israel"; no UTI figure in a UMI file or vice versa
- [ ] Contrast: no white on paper, no pale on pale
- [ ] `OPEN_*.cmd` beside the HTML and it works
- [ ] **Open it and look at it** — the blueprint's QA pass catches overflow and repetition that
      reading code never does
