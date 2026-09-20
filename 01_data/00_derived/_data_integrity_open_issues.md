# Data integrity — open issues

**Updated:** 2026-09-19
Pipeline verification: **green** (see `_verification_report.md`). Items below are **source gaps** or **known limitations**, not build failures.

Jerome warranty rule locked **2026-07-27** (`01_data/90_INBOX/warranty_audit_2026-07-27/SANITY.md`): skip PARTNBR `0` / `0000000000` (labour, not parts); do not chase price-map for no-PN rows; no multi-month blackout on high-volume DBs → not “data missing” for GPS CY2025 parts warranty.

## Cannot fix without new source data

| ID | Issue | Period | Impact | Action owner |
|---|---|---|---|---|
| **LCV-DEC** | `Warranty_LCV_2025.xlsx` last claim month is **November 2025** (IUK 2024-11 → 2025-11; Portugal LCV 2025-01 → 2025-11) | **December 2025 onward** | Full-CY LCV from *this* file is incomplete by one month at the end. GPS CY2025 used the extract as-is. | Next LCV claim-assessment export |
| **SPU-PARTIAL** | `gps_spu_by_distributor.csv` current-year (2026) rows carry **partial-year `total_sales_eur` against a full-year `max_spend_eur`**. The file therefore set `gps_capture_vs_max` ≈ 0.10–0.30 and `traffic_light_v9 = red` for **every** distributor, and comparing `spend_per_unit_eur` across years reads as a **~43% collapse** that did not happen (H1-2026 parts are **+12%** vs H1-2025 on `sales_fact`). **Contained 2026-09-15**: rows now flagged `period_basis=partial_year`, the false capture % and traffic light are blanked, 2023–2025 untouched. **Still open:** the true end date of the 2026 sales column is not reconcilable to a clean quarter from `sales_fact` (Q1 9.99M / Q2 8.72M vs row sum 9.18M), so the 2026 basis remains **unverified**. Fixer: `01_data/91_build/fix_gps_spu_partial_year_rows.py` (reversible from `.csv.pre_partial_year_fix.bak`). | 2026 rows | Blocked a false "network decline" reading | Rebuild 2026 row from a dated extract, or drop the year from the file |
| **CR/RE-FY26** | **SaTy CR/RE exclusion for Apr–Jun 2026 is sign-based only, and cannot be verified.** `Q1FY2027.XLSX` carries **no SaTy column**, so `is_credit_note` for that quarter falls back to `net_sales_value < 0`. A probe on 2026-09-17 returned **zero** SaTy CR/RE rows for Apr–Jun 2026 against 266 rows / €1,458,105 for 2023–Q1 2026 — consistent with the missing column, **not** with clean billing. Effect on the parts base: an unknown positive-value CR/RE amount for one quarter may be un-netted. `FACTS.md` flag H already records this as a judgment call; the quarter-specific consequence is logged here. | 2026 Apr–Jun | Parts base and GPS for FY26 Q2 carry an unverifiable netting basis | Next SAP extract that includes the SaTy column |
| **VIN-IL** | **ISRAEL (UTI) is absent from the JP VIN register** — `01_data\07_UIO\vin\VIN_register.parquet` holds **3,238 VINs across seven markets only (BE, CY, DE, GR, IE, MT, PT)** and deliberately excludes **ITUK (UK) and UTI (Israel)**, the two largest aftersales books. The exclusion is marked by the column `scope_cv_ex_ituk_uti` (built in `build_vin_register.py`, `SCOPE_EXCLUDE_DB = {"ITUK","UK","UTI","UMI"}`). **Consequence:** this register is the only UIO (vehicles in service) age layer for CV shipments, so for Israel there is **no vehicle age and no model / weight-class detail** — any per-market Israel age figure would be invented. **Waiting on Jerome to supply the Israel VINs.** | As-of 2026-07-27 register | No UIO (vehicles in service) age or model mix derivable for Israel from the register | **Jerome** — supply UTI VIN pack |
| **VIN-ITUK** | **ITUK (UK) VIN source located and read; the mileage gap it was meant to close is still open.** Duncan Young's mail (Parts Director, Isuzu Truck UK, 23 July 2026) was found and its VIN list loaded — **29,935 VINs** with model label and registration date. Recorded at `01_data\90_INBOX\_ituk_vins_from_duncan_mail.md`. **The file carries no odometer or mileage column of any kind**, so it cannot produce a km/year figure, and UK remains excluded from `VIN_register.parquet` (`scope_cv_ex_ituk_uti`). The UK mileage question therefore rests on the CV warranty odometer measurement plus Duncan's own 50,000 km/yr statement, which those odometers contradict (measured 16,688 all classes / 35,478 for N75). **Draft mail to Duncan asking for the parc's average annual mileage: `09_meetings\ITUK_MILEAGE_QUESTION_2026-09-18.md` — not sent.** | Located 2026-07-23; reviewed 2026-09-18 | UK register-based age / model mix still blocked; UK mileage assumption unconfirmed | **Jerome** — send the mileage question |
| **WARR-NO-MAINT** | **The warranty claim files contain no maintenance work, so wear-part replacement intervals cannot be measured from them.** CV: oil filter **8 lines**, air cleaner element **0**, fuel filter 10, brake pad **0**, brake rotor **0** out of 33,416 lines. D-Max: oil filter 2, air element 2, brake pad 33, rotor 48 out of 20,383. A consumable replaced at a scheduled service is not a defect and is not claimed. **Consequence:** the `air_filter: 0.5` interval factor and any measured service interval must come from dealer repair-order data or an actual parts-sales basket by part number. This closes the question — do not re-open it by searching the claim files again. Full verdict: `01_data\90_INBOX\_warranty_data_what_else_it_carries_20260918.md` §1. | Established 2026-09-18 | Blocks any measured-interval replacement of the assumed 40,000 km service and the 0.5 air factor | **Jerome** — source dealer RO data or a parts basket if measured intervals are wanted |
| **WARR-SAMPLE** | **Part-number coverage in the warranty claim files is uneven by market by an order of magnitude, so part-level euro rankings are thinner in some books than others.** Share of claim lines carrying **no real part number**: Czech 95%, Switzerland 90%, Italy 87%, France 83%, Spain 74%, UK 63% — against Israel 23%, Germany 23%, Portugal 17%, Ireland 8%. Cause is not established; it may be claim-recording practice or the export format per distributor system. **Consequence:** any part-number ranking built from these files is weakest in the German-owned markets. State the coverage on the face of any such output. | Whole claim file, Dec 2023 → Mar 2026 (CV) | Part-level rankings carry a market-bias that is not currently disclosed anywhere | Establish the cause with the claim owners, or disclose per-market coverage on every use |
| **CV-CURRENCY** | **The CV (truck) claim file is in three currencies and its `CRNCY` column is a two-token trap.** `EUR EUR` = EUR (Israel, Portugal, Ireland, Germany, Cyprus, Malta, Greece); **`EUR GBP` = pounds** (UK — 11,956 lines, the largest book in the file); **`JPY EUR` = yen** (Italy, Spain, France, Switzerland, Hungary, Poland, Czech, Romania, Croatia, Serbia, Slovakia, Bosnia, Makedonija). Confirmed two ways: the token string, and the file's own `JPY_PARTSTTL ÷ PARTAMT1` ratio, ~1.00 on the JPY rows and ~170 on the EUR-flagged ones. **Summing `PARTAMT1` raw mixes three currencies.** An analysis on 2026-09-18 did exactly that and produced a €93.8M Italian figure that was really ¥93.8M. **Corrected and now auditable:** `01_data/00_derived/warranty_commercial/` normalises first (EUR as-is, GBP ×1.12, JPY ÷163.7) and `warranty_cv_currency_audit.csv` states the rate applied per market. | Whole CV claim file | Every raw-summed truck euro figure is wrong — corrected totals: parts turnover €4,655,881, emissions €2,838,570 (61%) | Closed for the new datasets; **any older CV euro figure in the workspace needs re-checking against the audit file** |
| **LD-LABEL** | **The UIO "LD" label is not a weight class, and one market's target wallet depended on reading it correctly.** `LD` means 6.5/7.5 t in Israel and 3.5 t in most of Europe, but both mapped to one rate. **Israel corrected to no-op**: its row holds no 3.5 t truck (CV claim VINs: NPR75/FRR90/FSR90, zero NLR; ministry table starts at 6.5–7.5 t), so €739 — the 7.5 t rate — is already right. **Six other markets were genuinely mispriced** and are now split per market: Portugal ×0.801, Malta ×0.895, Ireland ×0.979, Belgium ×0.981, Germany ×0.982, Cyprus ×0.993 on 2025E target wallet. `V20_SPEC` §Problem 6 listed Germany and Malta as "0% — no change"; Germany is **22%** on the workbook's own Helwig parc bands. | Corrected 2026-09-18 | Was understating six markets' GPS % (Portugal by about a quarter); Israel and the UK were unaffected | Done — `DECISIONS.md` 2026-09-18, `03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv` |
| **N35-SHARE** | **Two markets' 3.5 t shares were sourced from the wrong file, and two more rest on a misread chassis code. Supersedes the Ireland / Belgium / Portugal / Malta / Cyprus figures in `LD-LABEL` above.** Audited every row of `03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv` against the basis it names, then corrected 2026-09-18: **IRELAND 0.063 → 0.3089.** The row was tagged `simi_bands` but carried the **JP VIN register** number (36 of 570; the old note even flagged "JP VIN shipments read 5.6%"). The SIMI parc basis is N35 **464** of N35+N75 **1,502** = 0.3089 (SIMI registrations 2010-2025 from `01_data/07_UIO/isuzuregdata.xlsx` sheet `Sheet2`, convolved against the scrap-adjusted CV curve, read at 2025 from `06_uio/Ireland_SIMI_Comparison/Ireland_UIO_GPS_Comparison_2026-05-28_v4.xlsx`). Flow basis for reference: 663/1,963 = 0.3377. **BELGIUM 0.918 → 0.8571** (register destination BE holds NLR 42 of 49, not 45). **PORTUGAL 0.620 → 0.6899** (1,299 NLR of 1,883 **N-series**; the old row divided by all 2,111 register rows including 228 F-series). **MALTA and CYPRUS are now marked `unmeasured` with their rates held** — both rested on reading **NMR88 as an N35**, but NMR88 is a 9.5 t truck and Cyprus holds **zero** 3.5 t in the register. GERMANY (153/697 = 0.2195), GREECE (4 NPR/NMR, no 3.5 t), ITUK (live workbook 10,900/21,584) and UTI (zero NLR in 2,360 claim VINs) all confirmed sound, and ITUK's rate is unchanged at 0.7526, so its PRISM-lane fixture band still holds. Effect on expected demand, cv slice only: ITUK unchanged, **IRELAND +6.5%**, Portugal +12.8%, Malta +4.9%, Belgium +0.5% — the whole-figure scaling bug did **not** reappear (Belgium's LCV block is immovable). Realised 2025 cover moves: Ireland 81.7% → 76.7%, Portugal 27.5% → 24.4%, Malta 25.5% → 24.3%. Target wallet computed but **not applied**: Ireland €935,912 → €856,281, Portugal €2,446,187 → €2,377,877, network −0.46%; `wallet_waterfall.csv` is locked and was not rebuilt. `pms_capture_by_db_year.parquet` was stale against the CSV (1,176 rows) and has been re-synced. | Corrected 2026-09-18 | Ireland was understated by 24 points of N35 share, so its truck service rate was too low | Done — `uio_ld_n35_share.csv`, `n35_share_audit_20260918.csv`; verifier 143 pass / 0 fail |
| **VIN-GVW** | **The JP VIN register read the chassis number as a tonnage.** `GVW_FROM_CODE` mapped `90 → 9.0 t`, so FRR90 (11–12 t) and FSR90 (13.5 t) were both recorded at 9.0 t, and NLR 3.5 t trucks at 8.5–8.8 t. The register's fleet tonnage read **26,689 t / 8.24 t average** when it is **19,545 t / 6.04 t**. GVW now comes from the ISZJ series, with a new `gvw_t_source` column. Feeds PRISM page 22 (Parc Cohorts). | Corrected 2026-09-18 | Register understated 3.5 t trucks and mislabelled the F-series; fed PRISM page 22 | Done — `01_data/07_UIO/vin/build_vin_register.py`, register rebuilt |
| **UIO-FCAST** | **The UIO (vehicles in service) forecast for 2026–2030 is overstated because it scraps ~3%/yr while the 1990–2025 history uses a survival curve implying ~10.2%/yr (CV) and ~12.3%/yr (LCV).** In `06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx` sheet `1.UIO Overview` the same row therefore changes method at the 2025/2026 boundary. Verified 2026-09-16 by projecting every row forward on the same buried registration inputs at the curve rates: V19's Grand Total is **+9% (2026) → +59% (2030)** too high, or **+45% at 2030** if 2030 registrations are carried forward at the 2029 rate (the sheet publishes no 2030 registration column). Market-level error is far worse than the total: by 2030 the LCV rows run **Poland +102%, UK (IUK row 25) +55%, Israel (UMI) +53%, Hungary +52%, Norway +51%, Germany +49%**. Corrections above apply to every row except UK CV (ITUK rows 22/24), which already uses the Sheet 4 survival model. **Independently, Israel (UTI) CV rows 7–8 are ~25% LOW in every year** — 10,336 modelled for 2025 against 13,881 actually registered (UTI / Israeli Ministry of Transport, via UTI's July 2026 parts pack), a gap of 3,545 that barely moves 2020–2026. **Consequence:** every 2026–2030 UIO figure that divides into parts spend — GPS (spend per unit), capture vs max, the FY27 GPS extended target and the growth plan — runs on an overstated denominator, while Israel's denominator is understated at the same time. **Do not quote 2026–2030 UIO to anyone until rebuilt.** Note also the Grand Total 2025E of 258,594 is on `MIDI Filter: Include` (cell B4); a forecast quoted off an `Include` total carries ~103k of MIDI LCVs that the 18-db GPS base does not. Method, three independent checks, per-row error table and the corrected series: `06_uio\_CURRENT\V20_SPEC.md` (the spec's headline "7.8% → 37.7%" endpoint pair was not reproduced exactly under any scope tested here — the closest single scope is UK CV at +7% → +37%; the direction and the accelerating pattern both confirm). | **2026–2030** (every market except UK CV; Israel all years) | Overstates every forecast UIO denominator + understates Israel → GPS %, capture and FY27 growth plan all suspect | UIO model owner — V20 rebuild per `06_uio\_CURRENT\V20_SPEC.md` |
| **ITUK-MILEAGE** | **ITUK's annual distance is an unconfirmed input, and it governs the published oil-filter cover — a swing of 35 percentage points.** The IML v7 deck assumes **50,000 km/yr** for the whole 22,389-vehicle N-series (`iml_v7_ituk_cy2025.yaml`, `mileage_km_yr: 50000`), which is what makes 40,000 ÷ 50,000 = 1.25 filter visits a year and the 35.1% oil-filter cover. The only measured source contradicts it: **CV warranty odometer deltas over elapsed time give UK N35 (Grafter) 12,891 km/yr and N75 35,478 km/yr** (`01_data/00_derived/warranty_cv_km_age_by_market.csv`; all classes 16,688). Duncan's VIN list carries **no odometer column**, so it cannot arbitrate. **Why it matters now:** expected demand is `fleet × (km ÷ interval) × factor`. With the two factory intervals (N35 20,000 km, N75 40,000 km, both from Duncan slide 14 and René GIDSS) the corrected ITUK oil-filter expectation is **40,605 on the interval ratio alone → cover 24.2%**, but **16,502 once measured mileage is applied → cover 59.5%**. The two rationales point in **opposite** directions and disagree by 35 points, so ITUK's headline cannot be settled until the distance is. The PRISM lane currently reads 0.7526 (`0.5 × (1 + 0.5051)`), which lands within 1.6% of the measured-mileage answer by coincidence — its derivation assumes equal mileage and is not defensible on its own. **Draft mail to Duncan asking for the parc's average annual mileage: `09_meetings\ITUK_MILEAGE_QUESTION_2026-09-18.md` — not sent.** Note also that GIDSS intervals are **indicator-driven** ("the light illuminates at a maximum of 40,000 km"), not fixed schedules, so the interval is a ceiling rather than a frequency. | Whole ITUK book; every year; both lanes | ITUK oil-filter cover is quotable only as "on an unconfirmed 50,000 km/yr"; correct value sits between 24% and 60% | **Jerome** — ask Duncan for the measured average annual mileage, then re-base |

## A canvas that reads 0x0 is not a blank chart — read the composited pixels

**Added 2026-09-19 after a false alarm on the family-evolution page.** Verifying that page's
rebuilt forms, a probe concluded that **form 8's five small-multiple panels were empty shells**,
because after `setForm('f8')` every `sml_*` canvas reported `width=0, height=0`. That conclusion was
**wrong**, and the panels are drawn. The same trap will catch the next agent who checks this page.

| Item | Value |
|---|---|
| What the canvas attribute said | `sml_0..4` = `0x0`, `style width/height: 0px` — after a form switch, and identical on a double switch |
| What the pixels said | **11,597** pixels in the page's own bar colours inside `#smlGrid`; per panel 86–4,030 navy and 65–3,705 terracotta. A titled empty box cannot produce those |
| Mechanism | Chart.js resets the canvas bitmap on a switch and the resize observer has not run when a headless probe reads it immediately. The composited PNG is correct |
| Why the first probe misled | It read `canvas.width`, not the composited page. A later ink measurement also misled: the panel chart areas carry 5–35% ink, but that ink includes the panel title and percentage caption, so ink alone cannot tell a drawn chart from a titled empty box |
| What settled it | Counting pixels in the page's own bar colours (`#15233c`, `#c0552d`) inside the chart region, on a screenshot |
| Durable check | `02_dashboards/sales/_build/qa_forms_painted_v2.py` — one Chrome run per form, bar-colour pixels per region, exits 1 if a form draws none. Current result: f2 37,390 (main chart), f8 11,597 (small-multiple grid), f10 33,209 (table) |
| Where the intermediate probe files went | Deleted, so they cannot be mistaken for a shipped gate |

**Rule:** for a canvas page, prove the mark by its colour on the composited screenshot. Do not read
`canvas.width`/`canvas.height` from headless Chrome, and do not treat a region's ink share as proof
that a chart drew.

## A capability was reported missing without testing it

**Added 2026-09-19.** Told Jerome *"I cannot open Excel on this machine"*, which is **false**. He had
said "Excel file does not work" three times earlier the same day, so the lesson was in front of me
when I repeated its shape: a capability claim that was never tested. The check used was
`shutil.which("EXCEL.EXE")`, which returns `None` for an Office **ClickToRun** install because the
program files are not on PATH. Read the registry instead.

| Item | Value |
|---|---|
| Excel present | **Yes** — Office 16 ClickToRun, `16.0.20326.20144` |
| Program path | `C:\Program Files\Microsoft Office\Root\Office16\EXCEL.EXE` (via `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe`) |
| Wrong test | `shutil.which("EXCEL.EXE")` → `None` → read as "not installed" |
| What works with no Excel at all | Open the workbook, read any cell or sheet, structural render checks, export — the excel connector reads the file itself |
| What does need Excel | Driving COM to recalculate (`EXCEL_ENABLE_COM=true`, currently off) |
| Found because of this | **Corrupted dashes in E11's text** — the em-dash was UTF-8 read as cp1252 and re-saved, showing as `â€"`. Repaired; scan `_fix_register_mojibake.py` now returns zero |
| Register entry | **E28** (High) + counter measure **CM27** in `ISZE_Agent_Error_Register_2026-09-18_19_v2.xlsx` |

**Consequence for how work is reported:** a workbook I hand over is read back through the connector
cell by cell before I describe it, not only parsed with openpyxl. Do not quote a capability limit
without naming the check that produced it.

## A count answered from memory — and a counter that inflated it

**Added 2026-09-19.** Asked how many times he had raised the fleet-denominator point, the reply said
**four** and listed the four from 10:47 onward. Counted from the transcript it is **nine** over two
days, and the first is the day before: 18 Sep 21:42. The measurement script that feeds the register's
own *Times raised* column (`_count_raises.py`) also has the flaw that produced the wrong number: it
counts agent-written subagent briefs as if they were Jerome's turns, and those briefs quote him. On
this theme it read **26** hits against his **9** turns. The 11:23 hit it counted is a 5,506-character
agent brief in a forked chat.

| Item | Value |
|---|---|
| His turns on the fleet-denominator point, 18–19 Sep | **9** (18 Sep 21:42; 19 Sep 10:47, 10:50, 11:00, 11:04, 11:22, 11:58, 14:57, 15:00) |
| What the reply quoted | 4 |
| Hits the old counter reported (his turns + agent briefs) | 26 |
| Counting script (separates his turns) | `01_data/90_INBOX/_count_denominator_raises.py` |
| Register entry | **E27** (Critical) + root cause **R9** in `ISZE_Agent_Error_Register_2026-09-18_19_v2.xlsx` |

**Is the denominator itself a gate?** Partly. The v2 family builder refuses to write a page where no
vehicle type's fleet moves on the comparison pair (lines 636–647) and refuses a worked example that
divides one customer's euro by the all-market fleet (lines 544–552). Those two assertions are live,
but reachable only by running that one builder. The standalone validator written at 11:28 —
`qa_uio_year_denominator.py`, which renders the page and asserts the default denominator is the
period's own fleet — is called from nothing in the repo and targets
`ISZE_PMS_Family_Evolution_Deep.html`, which has since been retired. `ship_gate_check.ps1` runs four
verify scripts and does not call it. So the arithmetic is guarded on one page; the wiring is missing.

## A rate is not sourced just because it has a comment

**Added 2026-09-19 after four separate defects of the same shape were found in one day.** A factor in
`pms_capture_config.py` or `pms_capture_assumptions.yaml` whose line carries a *reason* — "aligned to
oil and fuel", "kept at the old unsourced 0.5 guess deliberately", "PROVISIONAL — confirm with IML" —
reads like a sourced value and is not one. Nothing in the pipeline distinguishes the two, so an
unsourced factor sits indefinitely and is only discovered when a number looks wrong.

Each case below was found by accident during another task, not by any check:

| Factor | What was wrong | Effect | Status |
|---|---|---|---|
| `urea_filter` | `1.0` — one per service visit, the same as an oil filter. René's GIDSS gives the AdBlue **filter** at **200,000 km** (N-series) and **80,000 km** (F-series 4HK1-TCH). | Demand overstated about fivefold on N-series. ITUK AdBlue cover 7.63% → 37.06%; network urea gap €3,814,134 → €2,036,143 | **Fixed 2026-09-19** — `00_docs/PMS_UREA_INTERVAL_FIX_20260919.md` |
| `air_filter` | `0.5`, marked "PROVISIONAL — confirm with IML" since 2026-07-02 | Unquantified | **Still provisional** |
| `brake_pad` / `brake_shoe` global | `0.5`; the file itself says "kept at the old unsourced 0.5 guess deliberately" | Unquantified | **Unsourced by its own admission** |
| `brake_rotor` | `0.25`, "PROVISIONAL, not confirmed by the 2026-07-14 IML slide" | Unquantified | **Still provisional** |
| N35 visit rate | Derived from an interval **ratio** with the mileage cancelled out, which assumes N35 and N75 cover equal distance. The measured mileage gap (2.75×) is wider than the interval gap (2×). | See ITUK-MILEAGE above | **Method not defensible; result coincidentally close** |

`annual_km_yr: 20000` in `pms_capture_assumptions.yaml` is the extreme case: **it is read by nothing.**
Editing it changes no number in the pipeline — already recorded in
`01_data\90_INBOX\_assumption_reversibility_spec.md`. It is a published-looking constant with no
consumer.

**Partial closure (2026-09-18).** The only independent source of true wear-part intervals — the
warranty claim files — **cannot supply them**: CV holds 8 oil-filter lines, 0 air-cleaner and 0
brake-pad lines out of 33,416; a consumable replaced at a scheduled service is not a defect and is
not claimed. See **WARR-NO-MAINT** above. So a measured replacement for the assumed 40,000 km service
and the 0.5 air factor must come from dealer repair-order data or an actual parts basket by part
number, not from claims.

**What would stop this recurring:** every factor carries a **value, a source and a status**, and a
pipeline check fails while any status is `unconfirmed`. The labels already exist in the files and
achieve nothing, because nothing fails on them. Counted today: **9 factors and conventions carrying
an assumption label**, of which 1 is now fixed.

## Closed — do not re-open as GPS gaps

| ID | What it looked like | What it actually is | Period |
|---|---|---|---|
| **UMI-WARR** | Israel LCV absent from `Warranty_LCV_2025.xlsx` | **Resolved 2026-07-03.** Dedicated file `UMI warranty data 202301 - 202605 (1).xlsx` spans **2022-12-18 → 2026-05-17**; CY2025 Jan–Dec continuous (€1,791,020). Do not use the LCV workbook for UMI. | CY2025 complete |
| **CV-BLANK** | Sheet4 €314k “blank country” | **Parse artifact (2026-07-27).** PARTNBR `0` sorts before real PNs under each country. Line-level 3,083 blank-PN rows = labour (PARTAMT €0, LBRAMT €110,995). Skip. Find the euros on `DATA WITHOUT MIDI`, valid PN only. | CY2025 BILLYMD; Nov–Dec 2025 CV in sister `CV Warranty.xlsx` sheet `10_25-12_2025` (2025-09-18 → 2025-12-17) |
| **IRE-CV / PT-CV** | 82% / 52% price-map | Not missing claims. Optional valuation — 1 Ireland + 42 Portugal **real** PNs unpriced (labour/no-PN skip). | CY2025 CV |
| **PT-GAP** | Portugal missing six consecutive months (2025-03 → 2025-08, €0.7–0.9M of CY2025 absent) | **Not a gap — identifier change (closed 2026-09-16).** Portugal's `sold_to` switched from code **519** to code **92** for 2025-02 → 2025-10, then to the customer **name** with no code in `sold_to` for 2026-04 onward; `sold_to_sap` stayed **519** throughout. Filtering on **519 alone** leaves Mar–Aug 2025 empty. Grouping both codes + the name route, `sales_fact` has **all 42 months** 2023-01 → 2026-06, min month €81.5k, no month below 61% of the €135.2k median. CY totals **€1.368M (2023) / €1.557M (2024) / €1.713M (2025)**, +13.8% then +10.0%; H1-2026 **€0.975M is genuinely +19.6% YoY**. Portugal YoY is valid. Same code-split exists for ISD (601 + 2516) and Danmark (2027 + 2751) and must be added up as one distributor — no other network distributor has a real gap. | 2023-01 → 2026-06 complete |

## Out of PMS/GPS exercise scope (by design)

| Market | Why |
|---|---|
| UKRAINE, ARMENIA, KAZAKHSTAN, PALESTINE | Bill parts but not in 18-db GPS-base / PMS parc config |
| MIDI (FR, IT, ES…) | LCV warranty in file but not separate GPS calculator rows |

## Dashboard / feed staleness (monitor)

| Item | Status |
|---|---|
| `tender_data.json` | Refresh via `04_tools/ISZE_Tender_Monitor_Install/publish_tender.ps1` when tenders needed |
| `metrics_snapshot.json` | Run `build_metrics_snapshot.py` after pipeline post-verify |
| Competitiveness IAM scrape | No data-as-of stamp — scrape may be stale. PartsPool Autodoc DE/NO is 2026-03-29, not Eucon UK 2023. |
| Streamlit `pages/2_GPS.py` | Live calc without warranty toggle — use GPS v9 HTML or Evidence `/gps` |
| Streamlit `pages/10_Data_Integrity.py` | **DI-2 / DI-8 refreshed 2026-08-18** — canonical UIO is v19; AIM CY2026 dashboard shipped 2026-07-02. Duplicate-path cross-check and country-pack vintage labels remain. |

## Fixed this session

- GPS warranty wired into `gps_spu_by_distributor.csv` + `isze_data.json`
- PMS per-DB summary for 18 distributors
- Broken `v11` UIO links → `v18`
- Superseded GPS HTML → redirect to v9
- UIO v17 → redirect to v18 (full file in `Dashboards/_archive/`)
