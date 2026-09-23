# Israel - V20 rebuild on government registration data

Prepared 2026-09-22. Read-only pass: the live workbook was opened for reading only and was not modified.

Evidence pack: `rebuild_outputs\` (CSV / JSON), QA renders in `_pdf\`, scripts in this folder.

---

## 1. What the sources actually are

| What | Where | State |
|---|---|---|
| UTI registration flow by GVW band, 1994-2025 | `01_data\90_INBOX\_imie_mail_20260730\UIO ISUZU 2025.xlsx`, sheet `גיליון1`, range `A1:G34` | **Real data file.** Header row 1 (`YEAR / 6.5 TON / 7.5 TON / 10TON / 11 TON / 12 TON / TOTAL`), years 1994-2025 in rows 2-33, totals row 34. 10,715 bytes, mtime 2026-07-04 12:05:19. |
| Israeli Ministry of Transport **parc** by weight band at 30.06.2026 | `C:\Users\jerom\Downloads\מצגת לחלפים בלגיה - אפריל 2026.pdf`, page 14 (title `ISUZU CAR PARK 30.06.2026 - based on MOT data`) and page 15 | **Picture on slides, no data file.** 44-page PDF, 3,593,592 bytes, mtime 2026-07-27 17:42. Page 14's text layer gives `Active fleet: 14,019 Trucks`. The class table is drawn shapes, not text. |
| Ministry parc by year (11,514 / 12,557 / 13,323 / 13,881 / 14,019) and the 1,680 old-tail count | `_CURRENT\V20_SPEC.md` | §Problem 4, lines 283-302, the spec's carry-down of the slide figures. |

The registration flow is a **flow**; the ministry table is a **parc**. Different quantities; the spec already says so (§Problem 9).

Two independent checks that the carried-down class split is the right one:

1. `8,610 + 2,485 + 2,697 + 227 = 14,019` exactly, which is the slide's own total.
2. The flow's `6.5 + 7.5 t` cumulative is `8,905`; the ministry's `6.5-7.5 t` parc is `8,610`, a ratio of `0.967`. That is a normal parc/flow ratio for the largest, youngest-weighted class. Reading `8,610` as anything other than the Isuzu 6.5-7.5 t count makes the ratio meaningless.

Pages 14 and 15 also carry a business annotation `Phase-Out Cycle (1999-2010)` on the chart, which independently confirms the old-tail cohort window.

Slide 15's brand-versus-market comparison columns could **not** be read reliably at any render resolution and are **not used** anywhere in this rebuild.

---

## 2. Rebuilt Israel rows (dated candidate, 2026-09-22)

Row shape matches the workbook so they can be dropped in: row 7 = `CV / LD`, row 8 = `CV / MD`, plus the new 12.1-16 t row that has no home today.

Government figures are used at face value for every year the source quotes. The registration flow sets only the *shape* (the mix between classes and the years the ministry does not quote). It never overrides a government number.

| Year | LD row (6.5-7.5 t) | MD row (7.6-10 + 10.1-12 t) | NEW row (12.1-16 t) | Total | Government | Delta |
|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 8,266 | 3,020 | 228 | **11,514** | 11,514 | 0 |
| 2021 | 8,453 | 3,411 | 222 | 12,086 | *(not on the slide)* | - |
| 2022 | 8,566 | 3,774 | 217 | **12,557** | 12,557 | 0 |
| 2023 | 8,617 | 4,281 | 213 | 13,111 | *(not on the slide)* | - |
| 2024 | 8,501 | 4,613 | 209 | **13,323** | 13,323 | 0 |
| 2025 | 8,636 | 5,033 | 212 | **13,881** | 13,881 | 0 |
| 2026 | 8,610 | 5,182 | 227 | **14,019** | 14,019 | 0 |
| 2027 | 7,960 | 4,962 | 227 | 13,149 | - | - |
| 2028 | 7,276 | 4,704 | 227 | 12,208 | - | - |
| 2029 | 6,572 | 4,409 | 227 | 11,209 | - | - |
| 2030 | 5,851 | 4,072 | 227 | 10,150 | - | - |

Full series 1994-2030: `rebuild_outputs\rebuild_israel_rows_for_v20.csv`.

**Caveats, stated plainly.**

- 2020, 2022, 2024, 2025 and 2026 are government-anchored and exact.
- 2021 and 2023 are interpolated between two government anchors; the ministry's parc total for those years is not quoted on any slide we hold. Slide 17 does show fleet counts for 2020-2025, but reading the 2021/2023 bars would be a chart digitisation, which the brief rules out, so I did not do it.
- 1994-2019 is the registration flow convolved on the IML Emerging curve and scaled to the 2020 anchor. A shape, not a measurement.
- 2027-2030 **falls**, in the LD row especially, because the registration table stops at 2025 and the model rolls the 2025 cohort forward on the survival curve. A shape, not a forecast.
- The 12.1-16 t row is held flat at 227 from 2013 onward and decayed on the developed-market curve before that. It has no registration flow in UTI's table, so no shape exists for it.

---

## 3. Per-class table at 30.06.2026

| Ministry class | Government | Share | Ministry avg age | Market avg age | Our workbook 2026F | Gap gov minus ours | Rebuilt 2026 | Gap gov minus rebuilt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 6.5-7.5 t | 8,610 | 61.4 % | 9.4 | 9.8 | 6,101 | **+2,509** | 8,610 | 0 |
| 7.6-10 t | 2,485 | 17.7 % | 6.2 | 10.7 | 2,215 | **+270** | 2,485 | 0 |
| 10.1-12 t | 2,697 | 19.2 % | 5.9 | 7.3 | 2,444 | **+253** | 2,697 | 0 |
| 12.1-16 t | 227 | 1.6 % | 5.6 | 9.1 | 0 | **+227** | 227 | 0 |
| **Total** | **14,019** | 100 % | | | **10,760** | **+3,259** | **14,019** | **0** |

Our 2026 split is the workbook's own `LD = 6,101` and `MD = 4,659` (V18 already folds the 12 t band into MD), divided across the ministry's medium bands in the flow's own proportion so the two are compared like for like. `6,101 + 4,659 = 10,760` matches the spec's quoted model total.

`rebuild_outputs\per_class_table_2026-06-30.csv`.

---

## 4. Gap decomposition: 14,019 minus 10,760 = 3,259

| Block | Trucks | Share of gap | Basis |
|---|---:|---:|---|
| **A. Unmapped weight classes.** The 12.1-16 t band has no row in our model and no registration flow in UTI's table | **227** | 7.0 % | Measured exactly |
| **B. Over-aggressive scrappage on the old tail.** The ministry says 1,680 trucks first registered 1999-2010 are still on the road; our curve retains 193 of the 2,105 registered in that window | **up to 1,487** | up to 45.6 % | Measured exactly |
| **C. Different population.** Trucks never in UTI's recorded flow (parallel imports, previous importer) | **at least 333** | at least 10.2 % | **Hard floor, proven** |
| **D. Unexplained residual.** Accrual under-count in the 2011-2025 cohorts | **at least 1,212** | at least 37.2 % | Cannot be attributed with the data on hand |

B and C overlap: a truck inside the ministry's 1,680 that was never in UTI's file is counted in both. **Fully attributed: 227 + 333 = 560 trucks (17.2 %).** The floor test below pins B down further.

**Where C's floor comes from.** Every Isuzu truck UTI ever recorded registering, 1994-2025, across all five bands, is **13,686** units. The ministry's parc is **14,019**. So even at 100 % survival of the entire recorded flow the parc is short by **333**. Split: the 12.1-16 t class has a 227-truck parc and *zero* recorded flow; on the three bands UTI does record the parc is 13,792 against 13,686 recorded, a further 106 short. Those 333 trucks were never in UTI's file.

**Where B comes from.** Registrations in UTI's table for 1999-2010, all bands: **2,105**. Ministry: **1,680 still on the road**, which is 11.98 % of 14,019 and matches the "12 % of the fleet" statement. Our IML Emerging curve retains **193**. Implied survival of the recorded block is 79.8 % against our curve's 9.2 %, a shortfall of **1,487**.

**Why D cannot be split.** The independent floor fix, measured on the recorded flow:

| Floor | Fleet at 2026 | 1999-2010 block | vs ministry 1,680 | Still unreachable |
|---|---:|---:|---|---:|
| none (today) | 9,729 | 193 | 9.2 % | 4,290 |
| 50 % from age 15, held to age 40 | 10,674 | 1,052 | 63 % | 3,345 |
| 80 % from age 15, held to age 40 | 11,427 | **1,684** | 100 % | 2,592 |
| 100 % from age 15, held to age 40 | 11,928 | 2,105 | 125 % | 2,091 |
| 90 % from age 19 (Britain's V15 shape) | 10,530 | 978 | 58 % | 3,489 |

Two things fall out of this:

1. The floor must be **held past age 19**. The ministry's old tail sits at ages 16-27, so a floor that reverts to zero at 20, which is what our current curve does, leaves most of the block dead. Extending the floor to age 40 is what makes it bite.
2. **A floor that matches the ministry's own old-tail figure reproduces 1,680 at a level of about 0.80 from age 15**, and the fleet then reaches only **11,422**, leaving **2,597** unreachable. The British V15 shape of 90 % from age 19 adds just **+801** trucks, which is **24.6 %** of the gap.

So the floor alone would close roughly a quarter of the gap, not all of it. The remaining 2,300 to 2,600 sits in the 2011-2025 cohorts, and the ministry publishes no age detail below 2010, so we cannot tell how much of it is our curve still under-counting versus how much is more unrecorded population. **This is the honest stopping point.**

---

## 5. Evidence trail

| Figure used | File | Sheet / page | Range / element | Date read |
|---|---|---|---|---|
| Registration flow 1994-2025 by band | `ISZE\01_data\90_INBOX\_imie_mail_20260730\UIO ISUZU 2025.xlsx` | `גיליון1` | `A1:G34` | 2026-09-22 |
| Ministry parc total 14,019 at 30.06.2026 | `C:\Users\jerom\Downloads\מצגת לחלפים בלגיה - אפריל 2026.pdf` | page 14 | title text `Active fleet: 14,019 Trucks` | 2026-09-22 |
| Ministry parc by band (8,610 / 2,485 / 2,697 / 227) | same PDF | pages 14-15 | drawn table, not text | used as carried in `V20_SPEC.md` §Problem 4, lines 295-305 |
| Ministry parc by year, plus the 1,680 old-tail count | `ISZE\06_uio\_CURRENT\V20_SPEC.md` | §Problem 4 | lines 283-302 | 2026-09-22 |
| Class to segment mapping | live workbook | `Assumptions & Mapping` | row 95 | 2026-09-22 |
| IML Emerging CV survival curve, age 1-20 | live workbook | `3. UIO Calculation` | Section A, rows 6-25, column C | 2026-09-22 |
| Our current Israel rows | live workbook | `1.UIO Overview` | row 7 (LD): 2024 = 6,071 / 2025E = 6,059 / 2026F = 6,101; row 8 (MD): 2024 = 3,978 / 2025E = 4,277 / 2026F = 4,659 | 2026-09-22 |
| Ireland precedent, government source as primary | `ISZE\06_uio\Ireland_SIMI_Comparison\build_ireland_comparison_v4.py` | - | `survive()` plus the hybrid series logic | 2026-09-22 |

QA renders: `_pdf\uti_p14.png` through `uti_p18.png` at 170 dpi, `_pdf\p14_hi.png` through `p18_hi.png` at 400 dpi, plus the per-page embedded images at native size. The table pages carry no text layer, which is why the class figures are taken from the spec's carry-down rather than read off the slide.

---

## 6. What is still blocked

1. **The ministry's class table has no data file behind it.** Slide 15's per-band figures are drawn shapes. A registration-authority extract from the Israeli Ministry of Transport or from UTI would make the class split and the per-year parc machine-checkable instead of carried down by hand. Until then, `2,485` and `227` rest on a single slide plus the spec's consistency check.
2. **The 2021 and 2023 parc totals are unavailable.** They are interpolated between government anchors. Slide 17 shows 2020-2025 fleet counts, but reading the 2021 and 2023 bars is a chart digitisation, which the brief rules out, so I did not do it. A number printed anywhere, in a UTI mail or an MOT extract, would make them exact.
3. **The 2027-2030 series is a shape, not a forecast.** The registration table ends at 2025, so the model rolls the 2025 cohort forward and the fleet visibly decays. A government or distributor view of 2026 onwards registrations is needed before the forward years can be used.
4. **Block D, at least 1,212 trucks and at least 37 % of the gap, is unattributed.** It needs age detail for the 2011-2025 cohorts, which the ministry does not publish.
5. **Our implied average age is below the ministry's own**, 7.3 against 9.4 years for the 6.5-7.5 t class. The rebuilt level reconciles to the government parc by construction, but its age profile is still younger than the ministry's, which is the same old-tail shortfall showing up a second way.
6. **The 12.1-16 t row is inferred.** 227 trucks with no registration flow and no model home; the shape from 2013 onward is my construction and should be labelled as such in the workbook.
