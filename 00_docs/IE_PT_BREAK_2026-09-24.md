# Ireland and Portugal: the 2013/14 break in the fleet workbook

24 September 2026. Read-only review. No workbook, UIO file, dashboard or ceiling was changed.

Two terms used throughout. **UIO** (units in operation) means the Isuzu trucks and pickups still in service in a market in a given year; the fleet workbook `06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx` (version 19) holds it by market, class and year on sheet `1.UIO Overview`. **GPS** means parts billed to the distributor as a share of target spend, where target spend is the target spend per truck multiplied by the trucks in service. Spend per truck is parts billed divided by trucks in service. Both depend directly on the fleet figure, which is why a fleet error moves them one for one.

## The verdict

**This is a clean exclusion, not a fix.** Nothing on disk can join the two halves of either row, and nothing on disk can rebuild the left half. The exclusion is defined below.

**The break does not explain the 41.4% Ireland gap.** Both published Irish fleets carry the identical 2013/14 break, and the 2025 figure does not cross it. The gap comes from a later rebuild in June 2026 that replaced 2019-2025, and one file still reads the version from before that rebuild. Section 4 sets this out; the claim in `STATE_PACKET.md` that "Ireland is the 2013/14 splice" should be withdrawn.

**There is a second join at 2018/19** that nobody has recorded, and several published scrap rates cross it.

## 1. What the rows actually hold (verified from the workbook)

Read with openpyxl, read-only, both cached values and formulas. Rows 7-90 hold no formulas at all; every value is a typed constant. Row 2 (Grand Total) and row 5 (MIDI contribution) are the only live rows.

| Year | Ireland row 26 (CV LD) | Portugal row 51 (CV LD) |
|---:|---:|---:|
| 2012 | 2,848 | 17,166 |
| 2013 | 2,390 | 16,605 |
| 2014 | 12 | 23 |
| 2015 | 190 | 96 |
| 2018 | 706 | 909 |
| 2019 | 820 | 1,502 |
| 2025E | 731 | 2,206 |

The one-year falls are 99.5% (Ireland) and 99.9% (Portugal), as stated in the brief.

I compared these rows across every workbook version on disk: v8, v9, v10, v11, v12, v13, v17, v18, the 18 September backup, V19 and V20 candidate c. **1990-2018 are identical in every version.** The June 2026 rebuild that used the national registration files (Ireland from SIMI, the Irish motor industry registration series; Portugal from the Imotors copy of the national register) changed **2019 onward only**. The same holds for Ireland rows 28 (F-Series) and 29 (pickups) and Portugal rows 53 and 54. So each light-truck row is three builds stacked together:

- **1990-2013**: the IML Japan shipment-based estimate. A different population.
- **2014-2018**: an older partial build that starts from almost nothing in 2014. It was not replaced in June.
- **2019-2025**: the registration-based rebuild.

## 2. Why this cannot be fixed from disk

I searched the workspace for Irish and Portuguese registration sources (SIMI, CSO, ACAP, IMT, Matriculas, earlier workbooks, the Imotors study, the May 2026 Ireland comparison, the open parc tables scraped on 22 September). Only two registration sources exist, and both start too late:

- **Ireland**: `01_data\07_UIO\isuzuregdata.xlsx` (SIMI) starts in 2010.
- **Portugal**: `01_data\07_UIO\Matriculas Isuzu SAP.xlsx` starts in 2005.
- The CSO page reached in the 22 September scrape has no Isuzu split. `B6_national_parc_open_tables_2026-09-22.json` marks every open table "not a substitute for Isuzu UIO".

Three facts settle it:

1. **The left half is not the same population.** Portugal's 2013 light-truck figure is 16,605. The register holds 4,096 Isuzu registrations of every kind from 2005 to 2013, pickups included, and 778 N-series trucks. No survival curve turns 778 trucks into 16,605. Ireland's 2013 figure of 2,390 compares with 511 N-series registrations in 2010-2013. The pre-2014 numbers count something else, and the workbook does not say what.
2. **The 2014-2018 segment is not a registration fleet either.** Ireland shows 12 trucks in 2014, but SIMI records 666 N-series registrations in 2010-2014, all young enough to be almost fully alive. Portugal shows 23, against 832 N-series registrations in 2005-2014. The 2014 audit found the Portuguese register rebuild runs 200-675 units above the published row in every year from 2014 to 2018.
3. **Even a perfect method has too little history.** The workbook's truck survival curve (`3. UIO Calculation`, CV developed markets) keeps 5% of a cohort alive at age 15 and none at 16. A complete fleet for year Y therefore needs registrations from Y-15. Portugal's register supports a complete truck fleet only from **2020** (2005+15). Ireland's supports one only from about **2025** (2010+15). No year before 2014 can be rebuilt from what we hold, for either market.

The May 2026 attempt to repair Ireland (`06_uio\Ireland_SIMI_Comparison\Ireland_UIO_GPS_Comparison_2026-05-28_v4.xlsx`, "Hybrid" sheet) confirms the point. It did not remove the break. It moved it to 2009/10, where the total goes from 10,682 to 706.

**What would fix it** is a pre-2010 SIMI extract for Ireland (the May comparison already lists this as review item 7) and a pre-2005 registration series for Portugal from Imotors or the national authority. Neither is on disk. Until one arrives, exclude.

## 3. The exclusion

**Rows and years excluded as fleet levels:**

| Row | Market / class | Excluded years | Why |
|---|---|---|---|
| 26 | Ireland CV LD | 1990-2018 | 1990-2013 is a different population; 2014-2018 is an incomplete build |
| 51 | Portugal CV LD | 1990-2018 | Same |
| 29 | Ireland pickups | 1990-2018 | Shipment-based estimate to 2018 (the May comparison notes it includes pre-D-Max models); falls 1,435 to 870 at 2019 while 124 were registered, a 48% one-year "scrap" |

Trusted window: **2019-2025** on these three rows. The first year-on-year movement that may be used is **2019 to 2020**.

Rows 28, 53 and 54 have no 2013/14 break and were also rebuilt from 2019. Portugal F-Series (row 53) matches the register from 2014 (fit error 7 units) and may keep its full span. For rows 28 and 54, avoid the 2018/19 step for rates; the Irish F-Series shows negative scrappage in 2019.

**What gets a caveat instead of a number:**

- Any fleet level for rows 26, 51 or 29 before 2019, and any Ireland or Portugal market total before 2019 that sums them. Suggested wording: *"Not comparable: earlier estimate, different population; the registration-based fleet starts in 2019."*
- Any growth rate, scrap rate, trend line or compound growth figure for Ireland or Portugal that uses a year before 2019 together with a year from 2019 on.
- Network totals keep their numbers, because the arithmetic is right. Any network trend across 2013/14 gets a footnote. Row 2 falls 170,690 to 158,533 (-7.1%) in 2014. Rows 26 and 51 alone lose 18,960 in that step. With both rows taken out, the rest of the network moves from 151,695 to 158,498 (+4.5%), which is simple arithmetic on the published cells.
- The BVDB Power BI tables already have an empty `fleet_quality_note` column. That column should carry the exclusion text on the affected Ireland and Portugal rows, and those rows should no longer be marked `basis = actual`.

Two caveats apply inside the trusted window and remain even after this exclusion. The Irish light-truck row reproduces 2025 to 0.5 units only as the 7.5 t band with a two-year lag. Before about 2025 it is missing trucks registered before 2010, so 2019-2024 Irish levels are a floor. Portugal's 2,206 for 2025 is "reported, not verified": the best rebuild from the register gives 2,123 (-3.8%).

## 4. The two published Irish fleets

| | GPS file | Ceiling (wallet) file |
|---|---:|---:|
| File | `01_data\00_derived\gps_spu_by_distributor.csv`, 2025 row | `01_data\00_derived\wallet_waterfall.csv`, 2025 row |
| Ireland fleet | 3,056 (LD 1,151, F 101, pickups 1,804) | 2,161 (LD 731, F 92, pickups 1,338) |
| Portugal fleet | 8,176 (2,585 / 292 / 5,299) | 7,208 (2,206 / 269 / 4,733) |
| Ireland target spend | EUR 1,391,176 | EUR 856,195 |
| Ireland GPS | 85.4% | 138.7% |
| Portugal GPS | 48.9% | 70.4% |

3,056 / 2,161 = +41.4% and 8,176 / 7,208 = +13.4%. Both figures confirmed.

**Where 3,056 comes from.** It is the version 17 workbook's 2025 value, which the May 2026 comparison calls "v17 (current)". The GPS file reads it from `01_data\91_build\uio_v18_gps.json` and `uio_v19_gps.json`. Both files carry the v17 numbers even though their names say v18 and v19 and their `source_uio` field points at the current workbook. The 895-unit Irish gap is entirely 2025 values changed by the June rebuild: light trucks -420, F-Series -9, pickups -466. Portugal's 968 splits -379 / -23 / -566. **The 2013/14 break is identical in both vintages and plays no part.** Fixing the break would not close this gap.

**What this does to published figures.** Ireland prints as 85.4% of target in the GPS file and on the GPS dashboard, and as 138.7% in the ceiling file, the Lost Sales page and the Exec paper's cover. Irish spend per truck reads EUR 389 on the Exec paper (3,056 basis) and EUR 549.49 on the OS Hub (2,161 basis), for the same euros. The GPS percentage gap is not all fleet: the GPS file prices every light truck at EUR 739, while the ceiling file splits the row into 3.5 t (EUR 296) and 7.5 t trucks. The GPS file's Irish series is also mixed within itself: 1,796 (2023), 1,951 (2024), 3,056 (2025), 2,778 (2026). Its 2023, 2024 and 2026 rows come from version 19 and only 2025 comes from v17. The spend-per-truck drop from EUR 653 in 2024 to EUR 389 in 2025 is therefore a denominator artefact, not a market signal.

**Which one should stand.** 2,161 reproduces from the registration file and 3,056 does not, so 2,161 is the defensible 2025 Irish fleet and 7,208 the Portuguese one. Re-pointing `gps_spu_by_distributor.csv` is held under the UIO V21 hold (Jerome, 22 September: no re-pointing until V20 is promoted), and this memo does not reopen that. Until the hold lifts, every 2025 Ireland and Portugal figure taken from the GPS file should carry: *"Fleet from the superseded v17 build; the ceiling uses 2,161 (Ireland) / 7,208 (Portugal)."*

**Related, for Jerome's decision only (ceiling held, not acted on).** The Irish 3.5 t share of 0.3089 comes from a population that includes 3.5 t trucks (464 of 1,502 in the May SIMI comparison). It is applied to row 26, which reproduces from the 7.5 t band alone. If the row really is 7.5 t only, the ceiling prices 225.8 Irish trucks at EUR 296 instead of EUR 739, which understates Ireland's target by about EUR 100k (225.8 x 443). I have not verified which reading is right.

## 5. Numbers that are unsafe until this is settled

**Across the 2013/14 break:**
- Row 26 and row 51, 1990-2013, used as fleet levels anywhere, including Ireland 2,390 and Portugal 16,605 for 2013.
- The row 2 network movement 2013 to 2014 (-12,157, -7.1%) and the row 3 growth cell for 2014, unless footnoted.
- BVDB Power BI pack `09_meetings\BVDB_PBI_Data_Upload_2026-09-23\01_UIO\`:
  - `fact_uio_by_class_year.csv` and `fact_uio_by_market_type_year.csv` (Ireland LD 2,390 to 12; Portugal LD 16,605 to 23).
  - `fact_uio_by_distributor_year.csv` (Ireland 5,450 to 2,484; Portugal 17,505 to 1,075).
  - All three are labelled `actual` with no break note. The source table is `01_data\00_derived\uio_by_market_type_year.csv`.
- `02_dashboards\sales\ISZE_PMS_Family_Evolution_v2.html` embeds the Ireland and Portugal fleets for 1990-2030 and labels Portugal's pre-2014 figure `n_series` (16,605 in 2013), calling the old estimate N-series trucks. I did not verify whether the page charts across 2013/14.
- The May 2026 Ireland "Hybrid" timeline, which carries its own break at 2009/10.

**Across the 2018/19 join** (from `01_data\90_INBOX\UIO_DATA_INVENTORY_2026-09-22.md` and its `final.json`):
- Ireland light trucks 14.3% pooled scrap, 2019-2024. Its first year, 2019, is 2.4%.
- Portugal light trucks 4.9% pooled, 2019-2024. 2019 is -28.6%, negative scrappage.
- Irish pickups 19.5% pooled, 2014-2024. 2019 is 48.0%.
- Irish F-Series 5.3% (2019-2024) and 8.5% (2017-2024). 2019 is -8.3%.

**The stale 2025 fleet** (not the break, but the same Ireland question), Ireland 3,056 and Portugal 8,176:
- `gps_spu_by_distributor.csv`, 2025 row: Ireland EUR 388.57 per truck, GPS 85.36% (82.85% without warranty), target EUR 1,391,176. Portugal EUR 209.12, 48.93%, EUR 3,494,069. The same file sits in the BVDB pack under `02_GPS\`.
- Any Ireland or Portugal per-truck trend 2024 to 2025 or 2025 to 2026 from that file.
- The same values in derived files: `aim_gps_matrix.csv` (2025 row), `aim_catalog_db_matrix.csv`, `aim_catalog_focus_filters.csv`, `aim_catalog_other_filter_by_distributor.csv`, `aim_catalog_other_filter_group_by_distributor.csv` (`billed_eur_per_uio` for Ireland and Portugal), `dealer_sellout_gps_2025.csv`, `sellout_aim_network_mix_2025.csv`. Also `02_dashboards\Data\00_derived\pricing_pack_aim_gps_cy2025.csv` and `ids_corr_db_level_2026-08-10.csv` (Portugal).
- Pages opened and confirmed: `02_dashboards\fleet\ISZE_GPS_Dashboard.html` (Ireland 3,056 / EUR 1,391,176; Portugal 8,176 / EUR 3,494,069) and `02_dashboards\sales\ISZE_Exec_Aftersales_Paper.html` (spend per truck: Ireland EUR 389, Portugal EUR 209).
- A text search also finds 3,056 and 8,176, near Ireland and Portugal, in the AIM Parts Atlas pages, the AIM comparison and deep-dive pages, the KPI dashboard, the Leakage Cockpit, the PMS Family Compare and Tonnage pages, and the pricing revision pages. I did not open these one by one.

## 6. Numbers that remain safe from the break

These use only 2019-2025 values. They carry the level caveats in section 3, but the break does not touch them:

- 2025 fleets on the version 19 basis: Ireland 2,161 (731 / 92 / 1,338) and Portugal 7,208 (2,206 / 269 / 4,733).
- `wallet_waterfall.csv`, 2023-2025:
  - Ireland: fleet 1,796 / 1,951 / 2,161; GPS 161.1% / 160.5% / 138.7%.
  - Portugal: fleet 6,091 / 6,903 / 7,208; GPS 65.3% / 65.4% / 70.4%.
  - Network ceiling EUR 54,375,729 and cover 56.6%.
- `gps_spu_by_distributor.csv`, 2023 and 2024 rows only (same fleets as above). Do not trend them into the 2025 row.
- Files on 2,161 and 7,208: `gps_spu_by_family.csv`, `gps_spu_pms.csv`, `lost_sales_market.csv`, `lost_sales_model.csv`, `pms_summary_by_db.csv`, `pms_opportunity_matrix.csv`, `pms_capture_by_family.csv`, `pms_tonnage_model.csv`, `revenue_runway.csv` (2024-2025), `prism\data\uio_by_model_bucket.csv`.
- Warranty per truck: Ireland EUR 3.17 and Portugal EUR 8.61 (`warranty_commercial\warranty_cv_commercial_by_market.csv`).
- OS Hub: Ireland 2,161 and EUR 549.49 per truck.
- Lost Sales page: Ireland 138.7%.
- Scrap rates computed from 2020 onward:
  - Ireland light trucks 16.5% (2020-2024). This is safe from the break but not a clean measurement: it adds all N-series registrations in the same year, while the row counts 7.5 t trucks two years after registration.
  - Portugal light trucks 8.3% (2020-2024).
  - Irish pickups 9.6% (2020-2024).
- `pms_capture_by_db_year.csv` and `pms_opportunity_matrix.csv` apply the 2025 fleet to 2023-2026 flat. That is a separate year-alignment point and not part of this break.

The 2026-2030 forecast columns are outside this memo. They are already under revision in V20.

## 7. The two other workbook defects

**MIDI tag column: confirmed for the 1990s, refuted for current years.**
- Rows 39-41 (France) and 45-47 (Switzerland) carry distributor `MIDI Europe` but tag `ISZE`.
- Rows 2 and 5 test the distributor column (`SUMPRODUCT` / `SUMIF` on column F), so the workbook's own totals are right. Only a filter on the tag column is wrong.
- The size of the error depends on the year. Filtering on the tag understates MIDI by 564 units (34.7%) in 1990, 3,738 (35.1%) in 1995, 5,500 (29.2%) in 2000, 3,260 (10.2%) in 2005, 966 (1.8%) in 2010 and 90 (0.2%) in 2014.
- From 2023 through 2030 the shortfall is **zero**. "About a third" is true only of the 1990s and does not touch any figure in current use.
- The BVDB pack ships no MIDI rows, so it is unaffected.
- One knock-on effect: summary table 2 ("ISZE only, excl. MIDI-served markets") excludes by tag, so it wrongly includes France and Switzerland. In practice these add only a few units (France trucks 3 and 1).

**Summary tables at the foot of sheet 1: the stated defect is refuted as worded, and the real one is worse.**
- Both tables' headers run 2020, 2022, 2024, 2025 and 2026 to 2030, so they are not pinned to 2024.
- They hold no formulas.
- They are a **frozen copy of the version 17 workbook with every column labelled one year late**. In table 1, 267 of the 272 non-empty cells equal the v17 value for the previous year. The column labelled 2025 holds v17's 2024 figures, and the column labelled 2026 holds v17's 2025 figures. Table 2 behaves the same way, with 243 matches.
- Examples: Ireland trucks 1,362 under "2025" is v17 2024 (1,255 + 107), and 1,252 under "2026" is v17 2025 (1,151 + 101).
- The five cells I could not trace are UK trucks 2026-2030, which v17 holds as live links with no stored value.
- As a result, the tables disagree with the main row on almost every cell. Ireland, Portugal, Germany and Israel trucks match no year of the current workbook, because those markets were rebuilt after the tables were written. Grand totals: table 1 reads 254,117 for "2025" against row 2's 258,594, and 265,716 for "2030" against 309,125.
- Nothing should be quoted from either table. Rebuild them from row-level formulas or delete them in the V20 promotion.

## Sources read

`00_docs\agent\STATE_PACKET.md` (UIO sections); `01_data\90_INBOX\UIO_DATA_INVENTORY_2026-09-22.csv` and `.md`, plus `_uio_inventory_20260922\final.json`; `01_data\90_INBOX\UIO_HISTORY_AUDIT_2026-09-22.md`; the V19 workbook (sheets 1 and 3), the v8-v18 archive versions and V20 candidate c; `isuzuregdata.xlsx`; `Matriculas Isuzu SAP.xlsx` (sheet SUM); `Ireland_UIO_GPS_Comparison_2026-05-28_v4.xlsx`; `uio_v18_gps.json` and `uio_v19_gps.json`; `_backsafe_20260922_ceiling\_ceiling_after.json` and `MANIFEST.md`; the derived CSVs and pages named above. No line-level billing was opened.

**Not established:** what population the pre-2014 IML figures count; whether the Irish row should be 7.5 t only or all N-series; whether the unopened pages from the text search print the stale fleet or only embed it.
