# Audit — Pricing Revision AIM Source (2026-09-17)

Independent read-only check. Prior "verified" claims and existing check-files were not trusted; numbers were recomputed or recalculated where possible. Nothing was rebuilt.

## 1. Verdict

**Ship with caveats.** The Excel and the HTML both tie out to the published price-revision headline (step euro and weighted %), open cleanly, and keep Israel as two distributors. They are usable. A reader who drills into "Not held" on the roll-up views will under-see that euro; use Checks / PN data / the coverage chips for the real Not held total.

## 2. What was checked

**Excel** (`Pricing_Revision_AIM_Source_Analysis.xlsx`)

- Recalculated through Excel COM (`verify_pricing_analysis_xlsx.ps1`): Checks sheet, network row on DB summary, formula-error scan across the workbook.
- `python 04_tools/excel_pre_delivery_check.py` on the workbook.
- Structural pass via `audit_pricing_deliverables.py` (sheets, 48,653 PN data rows, launcher).
- Live formulas on Checks and DB summary inspected with openpyxl (references into `'PN data'!…`).
- Israel rows, TH/JP / Not held labels, AIM L3 gap buckets, freeze panes and filters.
- Spot-check ITUK / UTI / IUK / UMI against `price_bp_weighted_compare_customer.csv` and `pricing_aim_source_lines.parquet`.

**HTML** (`ISZE_Pricing_Revision_AIM_Source.html`)

- Self-containment and published totals via `audit_pricing_deliverables.py`.
- Fresh headless Chrome (clean profile): network default KPIs, UTI selection, Thailand restrict, Brakes to Hydraulic drill, reset.
- Screenshots taken this session: **9**. Image-read by this auditor: **5** (`live_01_network_top.png`, `live_02_network_full.png`, `live_03_uti_thailand.png`, `live_05_drilled_l2.png`, `shot_01_network.png`). The other four were taken for the interaction trail and not each opened as images.
- Coverage % recomputed from `pricing_aim_source_meta.json` and from the lines file.
- Cross-check of the AIM-spine air-filter split against the catalogue-tree handoff brief (same 40 part numbers).

## 3. Numbers that tie out

| Check | Expected | Observed |
|---|---|---|
| Step euro | EUR 1,652,140.71 | Excel Checks after COM: 1.652.140,71; difference 0,00. HTML published + KPI: EUR 1,652,141 (display rounding). |
| Weighted % | 5.9616% | Excel Checks difference 0,0000 pp. HTML 5.96% on network. |
| Formula errors | none | COM: 0 error cells workbook-wide; DB x AIM L3: 0. |
| Excel pre-delivery | pass | OK, issues=0. |
| HTML self-contained | no CDN / no sibling JSON fetch | Pass (Chart.js inlined; data in payload script). |
| AIM spine share | ~80.3% of in-scope euro | Meta and UI: 80.33% / 80.3%. Recomputed: EUR 28,109,901.68 / EUR 34,993,609.39 = 80.33%. |
| L3 filled | ~80.3% | Same figure (80.33%). |
| Source held | ~93.6% | Meta and UI: 93.62% / 93.6%. Recomputed: (EUR 34,993,609.39 - EUR 2,233,055.91) / EUR 34,993,609.39 = 93.62%. |
| ITUK | billed EUR 6,637,851.40; step EUR 355,797.80; 6.6695% | Matches customer file, meta, parquet, Excel DB row, HTML when ITUK selected. |
| UTI | billed EUR 3,475,697.94; step EUR 180,312.25; 5.5808% | Same. |
| IUK | billed EUR 6,531,640.70; step EUR 316,797.07; 5.9443% | Same. |
| UMI | billed EUR 3,080,200.59; step EUR 124,532.59; 5.637% | Same; separate from UTI everywhere checked. |
| Air-filter 40 PNs on AIM spine | 28 under Maintenance Service > Air Filter (EUR 671,831.60) + 12 under Fluids Chemicals > Cleaning Chemicals > Cleaner (EUR 124,951.56) | Parquet confirms both buckets and euros exactly. |

Excel Checks formulas sum `'PN data'` for step, weighted %, spine, L3, and source held. DB summary euro columns are SUMIFS into `'PN data'`; the weighted % on each DB row is prior to new from those live sums.

## 4. Defects found

### Caveats (not ship-blockers)

1. **"Not held" is thin on the roll-up views.**
   Line data and the Checks sheet carry the full EUR 2,233,055.91 Not held across 20 distributors. The derived cube only keeps Not held keys that also have a price on both sides — that is 2 keys (IUK, Sverige), about EUR 1,329 priced. The Excel TH-JP source sheet and the HTML Not held filter inherit that cube, so a reader who filters there will not see UMI's ~EUR 646k Not held (or ITUK's ~EUR 339k, and so on). Network coverage 93.6% and Checks remain correct. PN data still has every Not held line.

2. **League chart label when one distributor is selected.**
   With UTI selected, the "which distributor" chart drew a single bar labeled CIS-KTK while the KPI correctly showed UTI at 5.58%. Network view (all 22) labels correctly, including UMI and UTI as separate bars. Cosmetic when filtered; do not read the single-bar label in isolation.

3. **HTML KPI "Parts billed" is the priced book (EUR 32.6M), not the full in-scope EUR 35.0M.**
   The footer states both populations clearly (48,653 lines / EUR 34,993,609 in scope; 47,617 priced). The chip itself does not say "priced only." Easy to misread if you stop at the chips.

4. **Coverage chips stay at network 80.3% / 93.6% after distributor or source filters.**
   They are book-level completeness, not the selection. Fine once you know; slightly easy to misread next to filtered step/%.

5. **HTML does not name the catalogue tree.**
   It says AIM families and greys "Not on AIM spine." It does not claim the catalogue-tree air-filter total (EUR 796,783.16). Excel Read me is clearer: catalogue sits beside AIM and is not the axis. A reader comparing this pack to the air-filter handoff brief still needs that brief (or the Excel Read me) to understand the two trees.

### Cosmetic / minor

- Checks displays weighted % as 5,96% under a Dutch Excel locale; the difference cell is still 0,0000.
- COUNTIFS with an odd `"><"` criteria on some Lines columns; COM reported no formula errors and the sheet recalculated.
- Freeze panes and AutoFilter are on PN data and the main roll-ups. No real clipping found in the HTML screenshots that were image-read; Excel layout was not screenshot-QA'd beyond structure.

### Blockers

**None.** Files open, calculate, and match the published revision.

## 5. Caveats the reader must keep

1. **Two trees.** This pack is the AIM spine. The air-filter handoff brief is the catalogue tree. Same ~40 air-filter part numbers: catalogue keeps them together at EUR 796,783.16; AIM splits ~28 / ~12 (EUR 671,831.60 + EUR 124,951.56). Neither figure is wrong; do not mix them in one table without saying which tree.

2. **Distributor is not dealer.** Rows are trading entities / sold-to accounts used for the revision. Billing has no dealer key. "Customer" here is not a dealer panel.

3. **Source of supply is not country of origin.** J = Japan through IML, T = Thailand through IMIT. A Japan-supplied part can still be made elsewhere. "Not held" means the supply flag is missing, not that the line was deleted from the euro totals at network level.

4. **Weighted % is a base-price move on billed quantities**, not revenue, margin, or demand response. Both artefacts say this; keep it when quoting the 5.96%.

5. **For Not held by distributor, trust PN data / Checks / meta, not the TH-JP roll-up or the HTML Not held filter alone.**

## 6. Absolute paths

**Excel**

- `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\Pricing_Revision_AIM_Source_Analysis.xlsx`
- Launcher: `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\OPEN_Pricing_Revision_AIM_Source_Analysis.cmd`

**HTML**

- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.html`
- Launcher: `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\OPEN_Pricing_Revision_AIM_Source.cmd`

**This note**

- `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\AUDIT_Pricing_Revision_AIM_Source_20260917.md`
