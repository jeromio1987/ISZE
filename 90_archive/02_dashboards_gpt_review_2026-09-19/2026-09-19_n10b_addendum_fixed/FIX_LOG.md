# FIX_LOG — N10B-048 … N10B-061

Patches applied only under  
`02_dashboards\sales\_gpt_review\2026-09-19_n10b_addendum_fixed\`  
Live dashboards were not rebuilt and not overwritten.

## Incident — 2026-09-19 evening (Jerome handoff broken)

**What Jerome saw:** `03_ISZE_PMS_Family_Compare.html` — empty Question / Parts family selects, Chart form “—”, only the static Ireland €389 seed bar, empty mix panel.

**Root cause (file 03):** A bad N10B-055 patch to `bindClicks` left **orphan JavaScript** after the function closed (leftover lines from the old click handler). That is a **syntax error**. The whole app script never ran, so dropdowns never populated and the HTML seed stayed on screen.

**Root cause (files 04–06, found in the same full QA):** N10B-049 / N10B-050 helpers (`applicableIntervalKm`, `formatIntervalCell`, `intervalTipKm`, `periodStats`) were pasted into the **Sales evolution** section render, but called from **Service families**. Browser error: `periodStats is not defined`. Sales evolution still painted; Service families tooltips/interval cells could throw when that section ran.

**What we did:**
1. Restored file 03 from live `02_dashboards\sales\ISZE_PMS_Family_Compare.html`, then re-applied **only** clean N10B-054 (residual scale / 100% mark) and N10B-055 (keyboard on bars) with no orphan remnant. Broken copy kept as `_qa\03_BROKEN_bindClicks_orphan_backup.html`.
2. Moved the N10B-049/050 helper block from `evolution` into the `pms` (Service families) render in files 04, 05, 06. Pre-move backups in `_qa\*_pre_periodStats_move.html`.
3. Full headless QA on **all eight** HTML files; heroes + Service families / residual checks; screenshots image-read.

**Live originals:** untouched. Live Family Compare still works (no JS crash). It does **not** have the N10B-054 “above model” / 100% mark until/unless Jerome says ship.

| ID | Priority | Files | Status | What we did / why deferred |
|---|---|---|---|---|
| **N10B-048** | Blocker | 04, 05, 06 | **Fixed** | Stripped `peerMedians` / `peerGroups` / `peerOrder` to permitted non-thin groups only. ITUK: removed thin `scope:CV` and `region:UK` (kept `pool:CV`, `fleet:m`, `all`). BE/SE: dropped 15 unused median keys each. Hero QA shows ITUK with 3 compare buttons (no thin chips). Per-metric contributor recount after missing values still needs an upstream rebuild if Jerome wants that depth. |
| **N10B-049** | Blocker | 05, 06 (render also 04) | **Fixed** (helpers now in `pms` scope) | Table/captions use applicable interval: LCV schedule → `interval_lcv_km` (Sweden oil/fuel → **20,000 km**); `both_schedules` with differing CV/LCV → **Truck … / pickup …**. Belgium Fuel Filter cell verified: `Truck 40,000 / pickup 20,000 km`. |
| **N10B-050** | Blocker | 04, 05, 06 | **Fixed** (helpers now in `pms` scope) | Tooltips / detail tips for part-year (CY2026) use half of annual `expected_qty_adj`, shortfall = period expectation − H1 actuals, euro = shortfall × avg price. Stored JSON year fields unchanged; display math aligned. |
| **N10B-051** | Material | 04, 05, 06 | **Fixed (label)** | Heat-map note states historical series is **rebased to a constant fleet and schedule**. Did **not** recompute per-year fleet expectations (needs pipeline rebuild). |
| **N10B-052** | Material | 04, 05, 06 | **Fixed** | Trend / “slipping” suppressed unless ≥2 eligible numeric annual cells; caption slope gated the same way. |
| **N10B-053** | Material | 04 | **Fixed** | Firm gap KPI sub/tip become **conditional on unit definition** when any category has `unit_definition_open`. Warning banner retained. |
| **N10B-054** | Material | 03, 04–06 | **Fixed** (03 re-applied cleanly after restore) | File 03 residual: scale ≥100% of expected, `flex-shrink:0`, 100% reference mark, “above model” label. Verified Air Filter → Cyprus **143.3% · above model**. Files 04–06: zero EUR bars no longer force `min-width:3px` (`data-nz`). |
| **N10B-055** | Usability | 03, 04–06, 08 | **Fixed** (03 keyboard bind clean after restore) | Distributor `tip()` adds `tabindex="0"`. File 03 bar rows keyboard (Enter/Space) without orphan JS. File 08 `.ill` KPI labels `tabindex="0"`. |
| **N10B-056** | Usability | 04 (shared 05/06) | **Fixed** | Narrow layout `section{scroll-margin-top:120px}` so sticky header does not cover jumps. |
| **N10B-057** | Usability | 04–06 | **Best-effort** | Print CSS: avoid breaks inside chart rows, notes, banners, table rows; sections may break at subheads. Not full print-pagination QA. |
| **N10B-058** | Usability | 09 | **Fixed** | Print-scope line + checkbox “Print all tabs”. Default remains selected view, labelled; optional `body.print-all` shows every panel. |
| **N10B-059** | Usability | 07 | **Fixed** | Dark-mode CSS forces light fills on SVG text / `#52514e` / `#6b6256` labels. |
| **N10B-060** | Material | 07 | **Fixed** | Section-2 callout **Conditional substitution sensitivity**; chart title + lede + hero mix KPI relabelled as scenario / not proven loss. No invented displacement %. |
| **N10B-061** | Material | 04–06 | **Fixed** | Softened “above 100% means demand too low” in honesty KPI tip and body copy — ratio ≠ cause; lists plausible checks. |

## Deferred / not done

| Item | Why |
|---|---|
| Recompute historic expectations from each year’s fleet (051 full) | Needs builder + authorised rebuild of live packs. |
| Rewrite stored CY2026 `expected_qty_adj` / `unbought_qty` / `gap_eur` in JSON (050 full) | Display/tooltip math fixed; embedded diagnostics still show annual fields if inspected raw. |
| Per-metric contributor counts after exclusions (048 depth) | Group strip is the export-control fix; metric-level recount is pipeline work. |
| File 10 proportional-vs-list geometry change | Addendum treated as design note; added equal-width mobile note only. |
| Files 01–02 | Outside this addendum finding range. |
| Promote copies to live / ship | Waiting for Jerome OK (`rebuild` / `ship`). |

## QA (2026-09-19 re-check after restore)

| File | Paint | JS errors | Notes |
|---|---|---|---|
| 03 Family Compare | **PASS** | none | 15 questions, 18 bars, Chart form filled; residual Air Filter Cyprus above 100% |
| 04 ITUK review | **PASS** | none | 3 compare groups; Service families heat paints |
| 05 Belgium review | **PASS** | none | Interval Truck/pickup on Fuel Filter |
| 06 Sweden review | **PASS** | none | Fuel Filter interval **20,000 km** |
| 07 MD pack | **PASS** | none | Hero KPIs + stacked wallet chart |
| 08 UIO V19/V20 | **PASS** | none | Slope chart paints |
| 09 GPS dashboard | **PASS** | none | Network bars + table |
| 10 OS console | **PASS** | none | Hero KPIs + loop diagram |

Evidence: `_qa\*_hero.png`, `_qa\*_pms_section.png`, `_qa\review03_residual_air.png`, `_qa\full_qa_results.json`.  
Screenshots taken: 8 heroes + 3 PMS sections + 1 residual = **12**; all **12 image-read** in the repair session.
