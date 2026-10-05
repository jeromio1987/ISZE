# AIM deep dive: ISZE → distributor and distributor → dealer

**Build spec for DeepSeek.** Written 24 September 2026. Read the whole file before writing code.
Every path below is absolute and exists. If a file is not where this spec says, **stop and report it**. Do not look for a substitute and do not guess.

---

## 0. What you are building, and in which order

An interactive HTML dashboard that compares two sales stages, part number by part number, grouped in the AIM product tree:

| Stage | Meaning | Source |
|---|---|---|
| **ISZE → distributor** (“billed”) | what ISZE invoiced to the distributor | ISZE billing |
| **Distributor → dealer** (“sold to dealer”) | what the distributor sold to its dealer network | the distributor's own sales-to-dealer file |

The drill path is **AIM level 1 → level 2 → level 3 → part number**, the same as the reference dashboard (§1). Every level shows **both stages side by side**, in **quantity** and **price / value**, both as **normal figures** and as **PMS cover %**.

**Build it in two runs, and stop between them:**

1. **Run 1, Portugal only.** Output: `ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html`. Run the checks in §9. **Stop and report** the check results. Do not start run 2 until Jerome has confirmed run 1.
2. **Run 2, all distributors with data** (§3.2). Output: `ISZE_AIM_DB_DLR_Deep_Dive_ALL.html`. Same code, same checks, per distributor.

Both runs use **one build script** with a `--db` argument (`--db PORTUGAL` / `--db ALL`).

| Output | Path |
|---|---|
| Build script | `C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\build_aim_db_dlr.py` |
| Dashboard, run 1 | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html` |
| Dashboard, run 2 | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_DB_DLR_Deep_Dive_ALL.html` |
| Verification report (per run) | `C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\VERIFY_<RUN>.md` + `.json` |
| Double-click opener (per run) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\OPEN_AIM_DB_DLR_<RUN>.cmd` (one line: `start "" "%~dp0ISZE_AIM_DB_DLR_Deep_Dive_<RUN>.html"`) |

---

## 1. Reference dashboard: copy its look and its interaction

`C:\Users\jerom\Desktop\ISZE_Pricing_Revision_AIM_Source.html`

This file is 6.9 MB because its data is inline. **Do not open it whole in an editor or print it to a console.** Read the `<style>` block and the `<script>` logic around the controls. Copy:

- **Style:** the colour tokens (`--navy:#15233c; --terra:#c0552d; --paper:#f7f4ee; …`), Georgia headings, the white control bar with the terracotta left border, and the drill table.
- **Controls pattern:** `<select>` filters + segmented buttons (`data-m="…" class="on"`) + a “Reset” button.
- **Drill table:** level 1 → level 2 → level 3 → part numbers, expand and collapse on click, with a breadcrumb.
- **Charts:** Chart.js, inlined like the reference, so the page works offline. No CDN at run time.

Related existing dashboards. Look, don't copy logic blindly:
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\Dealer_Billed_vs_Sales_to_Dealer_FY2026.html`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DB_DLR_Replenishment_CY2025.html`

---

## 2. Hard rules. Breaking one of these makes the output unusable.

1. **Never** read `C:\Users\jerom\Desktop\claude\ISZE\01_data\raw\sales\*.XLSX` or any other raw line-level billing. Use only the derived files in §3.
2. **Never** use Google Drive. Everything is in the local ISZE folder.
3. **Never** invent a number, a mapping, a target or a price. If something is missing, show “not available” and give the reason on the page.
4. **Lubricants are out of scope.** Drop every part number whose AIM level 1 is `Fluids Chemicals`, and every part number whose `line_kind` ≠ `part` (freight, service fee, rebate, merchandise and so on). Keep AIM level 1 `Lubrication`: those are engine parts (oil pumps, drain plugs), not oils.
5. **Sales to dealer has no prices.** Its euro values are **units × the ISZE price list** (§3.5) and must be labelled “valued at the ISZE price list of 10 Aug 2026”. **Never** call it dealer turnover or the distributor's revenue.
6. **Never add a year or YTD row to month rows** (§4.1). This is the easiest mistake to make and it doubles the units.
7. **Never present PMS cover above 100% without a visible warning**, and never hide a bad denominator. A cover above 100% usually means the demand model or the mapping is wrong for that family.
8. Write new scripts to files and run them. Do not put multi-line Python inside `python -c`.

---

## 3. Input files (all derived, all local)

Root: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\`

### 3.1 ISZE billing (ISZE → distributor)

`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_fact.parquet`

- Columns: `billing_date, sold_to_sap, sold_to, part_number, description, billed_qty, net_sales_value, saty, year, material, fig_key, fig_key_source`
- Range: 3 Jan 2023 to 31 Aug 2026.
- **Exclude** document types `saty` in `CR, RE, DR, ZDR, FD` (credit notes, returns, debit notes, free deliveries). Keep `SOR, VOR, RUSH, PRD, SVOR`. Report the excluded euros per distributor in the verification report.
- Distributor key: **`sold_to_sap` → `distributor_code`** through `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\distributor_dimension.csv`. Read `distributor_dimension.md` next to it. **Join on `sold_to_sap`, never on `payer_code`.** Portugal is **two** sold-to codes (`519` and `92`); add them together.
- Actual billed price per unit = `net_sales_value / billed_qty`, computed on the aggregate (sum of euros ÷ sum of units), never as an average of line prices.

### 3.2 Sales to dealer (distributor → dealer)

Files: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\dealer_sellout_long_<DB>_<PERIOD>.csv`

Columns: `distributor_code, source_file, grain, year, period, period_grain, part_number, part_number_raw, description, qty, dealer_name, vehicle_scope, flags` (the ITUK 2023/2024/2026 files have the same columns in a different order, so read by name).

| Distributor (`distributor_code`) | Files to use | Month coverage | Notes |
|---|---|---|---|
| **PORTUGAL** | `_PORTUGAL_CY2025.csv`, `_PORTUGAL_CY2026YTD.csv` | Jan 2025 – Aug 2026 | network level |
| **IRELAND** | `_IRELAND_CY2025.csv`, `_IRELAND_CY2026YTD.csv` | Jan 2025 – Jul 2026 | network level |
| **ITUK** | `_ITUK_CY2023.csv`, `_ITUK_CY2024.csv`, `_ITUK_network_CY2025.csv`, `_ITUK_CY2026YTD.csv` | Jan 2023 – Aug 2026 | CV only. **Do not use `_ITUK_CY2025.csv` for network totals**; it is the dealer-level file (64 dealers) and is used only for the dealer layer (§6.9). |
| **IUK** | `_IUK_CY2025.csv`, `_IUK_CY2026YTD.csv` | Jan 2025 – Jul 2026 | **D-Max only** (`lcv_dmax`) |
| **UTI** | `_UTI_CY2025.csv`, `_UTI_CY2026YTD.csv` | 2025: **only Jan and Aug–Dec** have month rows; 2026: Jan – Jun | Feb–Jul 2025 are missing at month level (the 2025 year row holds 92,660 units, the month rows 55,570). **Treat Feb–Jul 2025 as “no data”; never fill them from the year row.** |
| **GREECE** | `_GREECE_CY2025.csv` | Jan – Dec 2025 | **D-Max only** |
| ~~ROMANIA~~ | — | — | **Out.** Too thin (688 part numbers). Do not include. |

Billing sold-to codes (from `distributor_dimension.csv`): PORTUGAL 519 + 92 · IRELAND 76 · ITUK 2575 · IUK 2574 · UTI 1799 · GREECE 66. Verify them in the file; do not hard-code anything the file contradicts.

### 3.3 AIM tree (level 1 / 2 / 3)

`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260921.csv`

- Columns: `part_number, description, description_source, aim_level_1, aim_level_2, aim_level_3, figure_key, figure_no, key_no, figure_key_label, line_kind, aim_source, l12m_billed_eur`
- 165,213 part numbers, of which 24,756 carry an AIM level. The rest have no level: put them in a bucket called **“Not classified in AIM”** (all three levels). **Show that bucket's share of units and euros in the KPI strip**; do not drop it silently.

### 3.4 PMS families and PMS demand

- **PMS family per part number:** `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\parts_catalog_dimension.csv`, column `pms_category`. Fold the variants: `brake_pad_front`, `brake_pad_rear` → `brake_pad`; `brake_shoe_front`, `brake_shoe_rear`, `brake_lining_front`, `brake_lining_rear` → `brake_shoe`. The 14 PMS families: `oil_filter, fuel_filter, air_filter, blower_filter, urea_filter, brake_pad, brake_shoe, brake_rotor, clutch_kit, clutch_disc, clutch_pressure_plate, release_bearing, pilot_bearing, clutch_booster`. Anything else in `pms_category` (leaf spring, shock absorber and so on) is **not** PMS for this dashboard.
- **PMS demand (the denominator):** `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_capture_by_db_year.csv`, column `expected_qty` per `year × distributor_code × pms_category`.
  - **Trap:** each combination appears three times (`line_type` = `genuine`, `bvp`, `total`) with the **same** `expected_qty`. Take it **once**, from the `total` row. Adding the three triples demand.
  - It is a **calendar-year** figure. Monthly demand = `expected_qty / 12`. Demand for any selected window = the sum of the monthly demand over the months in the window (so a window across two years uses both years' figures).
- **Portugal only, optional toggle:** “Fleet base: network model | I Motors registrations”. The I Motors deck uses the registration-based FY2026 fleet (7,360 vehicles, scrap-rate model). Its per-family yearly demand comes from `pms_demand_fy2026()` in `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IMotors_FY2027_BPR\merged\_build\sto_compare.py`. Call that function at build time and embed the 14 numbers. Default = network model, so all distributors are measured the same way.
- **Clutch families** (`clutch_kit, clutch_disc, clutch_pressure_plate, release_bearing, pilot_bearing, clutch_booster`): show them, and put this remark next to every clutch PMS % (asterisk + footnote): *“The percentage may not be accurate: we do not know how many vehicles have a manual or an AMT gearbox.”*

### 3.5 Prices

- **Current ISZE price list (use this one):** `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pricing_pr00_ie40.parquet`, built from `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\Price_file_PR00_IE40_20260810.xlsx` (IE40 PR00 list, 10 Aug 2026, newest). Columns: `sales_org, part_number, newest_pn, description, price_condition, sp_eur, currency, valid_start, valid_end, country_of_origin, fig_no, key_no, is_superseded_row, source_file`. A price of `0.00` means **no price**; treat it as missing, not zero.
- Background on which price file is which: `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\PRICING_DATA.md`. Do not use `PRICE_CD_20260910.xlsx` (that is a JPY base-price revision, not the EUR list).

### 3.6 Genuine / BVP flag (optional filter)

`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\bvp_pn_dimension.csv`, column `line_type` (`genuine` | `bvp`), 919 part numbers. Part numbers outside this file are “not in the Genuine/BVP list”.

### 3.7 Source of supply (Japan / Thailand)

Take the same source-of-supply field the reference dashboard uses (its `<select id="src">`). If you cannot trace where the reference gets it, use `country_of_origin` from `pricing_pr00_ie40.parquet` and say so on the page.

---

## 4. Data rules

### 4.1 Period grain in the sales-to-dealer files (critical)

Every file carries **month rows and a total row for the same data**:

- `period_grain = "month"`: `period` like `2025-03`. **Use only these.**
- `period_grain = "year"` (`period` = `2025`) or `"ytd"` (`period` = `2026-YTD`): totals of the month rows. **Drop them.** Checked: in every file except UTI 2025 and the ITUK dealer file, the total row equals the sum of the month rows. Adding both doubles the units (Portugal CY2025: 51,363 on month rows, 102,726 if you add the year row).

### 4.2 Part-number keys

- Normalise every part number the same way on both stages: strip spaces, drop a trailing `.0`, **strip leading zeros**, keep as text.
- **Supersession:** map every part number to its newest number with `part_number → newest_pn` from `pricing_pr00_ie40.parquet`, on **both** stages, before grouping. Then join the AIM tree and the price on the newest number, falling back to the original number when the newest is not in the AIM file or has no price. Put the old numbers in a tooltip on the part-number row.

### 4.3 Value measures

| Measure | Billed | Sold to dealer |
|---|---|---|
| Units | `billed_qty` | `qty` |
| EUR actual | `net_sales_value` | **not available** (grey out) |
| EUR at price list | units × `sp_eur` | units × `sp_eur` |
| Average price | EUR actual ÷ units | not available |
| **Price index** | average actual price ÷ list price (1.00 = at list) | not available |

- **EUR at price list is the default euro measure**, because it is the only one on which the two stages compare like for like.
- Show the share of units without a list price in the KPI strip.

### 4.4 PMS cover

`PMS cover = units in window ÷ PMS demand in window`, per PMS family (and summed over the families for AIM nodes that contain PMS part numbers). The **same demand** is used for both stages. It applies only to the 14 PMS families. For non-PMS nodes show “—”, not 0%.

### 4.5 Stock-movement ratio

`bought ÷ sold = billed units ÷ sold-to-dealer units` over the same window.
Colours: **below 0.95** red (“running stock down”), **0.95–1.15** grey (“in step”), **above 1.15** amber (“building stock”). Show it only when both stages have data for every month of the window.

### 4.6 Vehicle scope

IUK and GREECE sales to dealer are **D-Max only**. Compare their dealer figures only with the LCV part of billing. Put a visible scope badge on those distributors, and do not include them in any network total of truck families.

---

## 5. Dynamic time period: the selector

The data is stored at **month grain** for both stages: `(distributor, stage, month, newest_pn) → units, eur_actual, eur_list`. Every figure on the page is recomputed from the selected month window. Nothing is pre-aggregated by year in the embedded data.

**Selector design:**

1. **Timeline strip** across the top of the page (Jan 2023 → latest month). Small monthly columns, two thin series (billed / sold to dealer, units) for the selected distributor and node, and a **two-handle brush** to drag the window. Months with no data for a stage are **hatched** for that stage.
2. **Preset chips** that set the brush: `CY2025` · `CY2026 YTD` · `FY2026 (Apr 25–Mar 26)` · `FY2027 YTD` · `Last 12 months` · `Last 3 months` · `Custom` (active while dragging).
3. **Compare with:** `none` · `same months last year` · `previous period of equal length`. Every KPI then shows a delta, and charts show the comparison as a lighter series.
4. **Common-window rule.** A comparison between the two stages is only valid over months where **both** stages have data. When the brush covers months where one stage is missing, show a warning bar (“Sales to dealer not available for Feb–Jul 2025 (UTI): figures cover N of M months”) and compute the stage comparison, the ratio and the PMS cover **only on the overlapping months**. Never pro-rate and never fill a gap.
5. A header line that always states the active window, e.g. `Window: Jan 2025 – Aug 2026 · 20 months · billed ✓ 20/20 · sold to dealer ✓ 20/20`.
6. Keep the window in the URL hash (`#db=PORTUGAL&from=2025-01&to=2026-08&cmp=ly`) so a view can be shared.

---

## 6. Page layout and charts (in this order)

**Controls bar** (same style as the reference): Distributor · Stage (`Billed` | `Sold to dealer` | **`Side by side`**, default) · Measure (`Units` | `EUR at price list` | `EUR actual` | `Average price` | `Price index` | `PMS cover %` | `Bought ÷ sold`) · Source of supply · `PMS families only` toggle · Genuine / BVP filter · Reset. The timeline selector (§5) sits directly under it.

1. **KPI strip** for the selection: units billed / sold · EUR at list billed / sold · bought ÷ sold · PMS cover billed / sold · price index · share not classified in AIM · share without list price.
2. **Level-1 side-by-side bars.** Horizontal bars per AIM level 1, billed next to sold. Click a bar to drill (level 1 → 2 → 3 → part number) with a breadcrumb. This is the main navigation.
3. **Treemap** of the current level, sized by sold-to-dealer units (or billed when a distributor has no dealer data) and coloured by bought ÷ sold (§4.5 colours). Stock build and run-down are visible at a glance. (`chartjs-chart-treemap`, inlined.)
4. **Monthly line** for the selected node: billed units against sold units per month, plus a **cumulative gap** line (running sum of billed − sold, the stock effect). Brush-aware.
5. **PMS cover bars:** the 14 PMS families, cover on billing next to cover on sales to dealer, same denominator. Clutch families carry the asterisk and footnote (§3.4). A cover above 100% gets a warning marker (§2.7).
6. **Price-volume scatter** at part-number level: x = price index (or change in list price against the comparison window), y = change in sold-to-dealer units against the comparison window, bubble = EUR at list. It shows where price may be holding volume back, for SPA candidates.
7. **Pareto** of part numbers inside the selected node: bars = the gap (sold − billed, or PMS demand − sold) per part number, line = cumulative %. It answers how few part numbers carry the gap.
8. **Heatmap, distributor × AIM level 1** (run 2 only), value = PMS cover on sales to dealer or bought ÷ sold (switchable). Network comparison in one view.
9. **Dealer layer (ITUK only, CY2025 only):** dealer × AIM level 1 table from `dealer_sellout_long_ITUK_CY2025.csv` (month rows only, `dealer_name`). For every other distributor show the section greyed out with “No dealer-level data from this distributor”.
10. **Drill table** (like the reference): level 1 → 2 → 3 → part number, columns = units billed · units sold · bought ÷ sold · EUR at list billed · EUR at list sold · avg actual price · list price · price index · PMS family · PMS cover billed · PMS cover sold. Sortable, with a search box for part number or description, and CSV export of the visible rows.
11. **Data coverage panel** (always visible, not a footnote) per distributor: month range per stage, missing months, scope (CV / D-Max / mixed), share not in AIM, share without list price, excluded billing euros (§3.1).

Footer: sources with full paths and the build date. No other file names in the body text.

---

## 7. Embedded data format

- One JSON object inlined in a `<script type="application/json" id="data">` tag.
- Facts at month grain, keyed by integer ids (a lookup table for part numbers, AIM nodes, months and distributors) to keep the file small. Target under 15 MB for run 2. If it is larger, drop part numbers with zero units in both stages over the whole range first, then report the size.
- Dimensions: part number → AIM L1/L2/L3, PMS family, Genuine/BVP, source of supply, list price, description, old numbers.
- PMS demand: `distributor × pms_family × year → expected_qty` (plus the Portugal registration variant).
- Coverage metadata per distributor and stage.

---

## 8. Build script behaviour

- `python build_aim_db_dlr.py --db PORTUGAL` / `--db ALL`.
- Reads only the files in §3. Prints a short log per step with row counts.
- Fails loudly (non-zero exit, clear message) when a file is missing, a column is missing, or a check in §9 fails. It never writes a half-built HTML.
- Writes the verification report (§9) next to itself.

---

## 9. Verification: must pass before you report

Put every check with expected vs actual in `VERIFY_<RUN>.md` / `.json`.

**Portugal (run 1).** These figures come from the I Motors review deck and must reproduce exactly with the rules above (PMS family from `parts_catalog_dimension.csv`, billing excluding `CR, RE, DR, ZDR, FD`, sold-to 519 + 92):

| Check | Expected |
|---|---|
| Sold-to-dealer units, month rows, Jan–Dec 2025 | **51,363** |
| Sold-to-dealer units, month rows, Jan–Aug 2026 | **39,790** |
| Billed units FY2026 (Apr 2025 – Mar 2026), brake pad | **1,370** |
| Billed units FY2026, oil filter | **2,743** |
| Billed units FY2026, brake shoe | **348** |
| Sold-to-dealer units FY2026, brake pad | **994** |
| Sold-to-dealer units FY2026, oil filter | **3,694** |
| Sold-to-dealer units FY2027 Apr–Aug, brake pad | **406** |

Note: these use the part numbers **before** supersession mapping. Run the checks with the mapping switched off, then report how much the mapping moves them.

**Every distributor (run 2):**
- Sum of month rows per file = total row (report the UTI 2025 and ITUK dealer-file exceptions).
- Billed units and euros per calendar year reconcile to `sales_fact.parquet` for that distributor's sold-to codes, after exclusions, to the unit.
- No PMS cover above 100% without a warning in the page.
- Share of units not in AIM and without a list price, per stage.
- File size of the HTML.

**Visual check:** open the HTML in a browser (desktop and 390 px wide), take screenshots of the top of the page, the drill at level 3, and the part-number table. Report anything clipped or overlapping.

---

## 10. What to report back

1. Paths of the files written.
2. The verification table (§9) with pass / fail.
3. Anything you could not do, and why. No workarounds you invented.
4. Open questions. Do not decide them yourself.
