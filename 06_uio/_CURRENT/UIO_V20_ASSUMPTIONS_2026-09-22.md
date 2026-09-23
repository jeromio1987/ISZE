# UIO V20 — assumptions log

**Candidate:** `C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx`  
**Generated:** 2026-09-22  
**Applies to:** `ISUZU_UIO_Overview_2026.xlsx` (V19, 18 Jun 2026) — read-only reference, not modified

## 1. Purpose and authority

The live V19 file carries a split method: 1990–2025 is built with a survival curve, 2026–2030 with a flat 3 %/yr scrap rule (`UIO × 0.97 + new registrations`). The flat rule implies a 33.3-year vehicle life; the curve used everywhere else implies 9.85 years (CV) and 8.13 years (LCV). This candidate removes the flat rule and applies the same survival curve to 2026–2030.

This is a **dated candidate**, not a promotion of the live file. V19 remains canonical until someone promotes this candidate.

## 2. The method

For every in-scope row:

```
UIO(t) = SUM_v [ R_v × S(t − v + 1) ]  +  R_t × S(1)
```

- `R_v` = new-registration cohort for year *v*.
- `S` = survival curve by vehicle age.
- `R_1990–2025` is recovered by recursive decomposition of V19's **own** historical series (`R_t = UIO(t) − Σ_{v<t} R_v × S(t−v+1)`). The reconstruction therefore reproduces 1990–2025 exactly by construction, so there is **no step at the 2025/2026 boundary**.
- `R_2026–2030` is taken from the new-registration inputs V19 already buried in its roll-forward (`regs(t) = UIO(t) − UIO(t−1) × 0.97`), then 3-point smoothed with the five-year level preserved exactly.

### Curves used (unchanged from V19 sheet `3. UIO Calculation`)

| Curve | Applies to | Ages | Average life | Implied scrap/yr | Source |
|---|---|---|---|---|---|
| CV developed, 16-yr | LD, MD, F-Series | 1–16 | 9.85 yr | 10.15 % | Sheet 3 Section A / IML |
| LCV, 12-yr | LCV | 1–12 | 8.13 yr | 12.30 % | Sheet 3 Section A / IMIT Nov-2025 |
| CV emerging, 20-yr | not used in V20 forecast (see §8) | 1–20 | 12.15 yr | 8.23 % | Sheet 3 Section A |
| Flat 3 % rule (V19 forecast) | V19 2026–2030 only | n/a | 33.33 yr | 3.00 % | V19 build step 6 |

**Why the LCV curve is the `age-12 = 0.00` variant.** Sheet `3. UIO Calculation` row 18 shows age 12 = 0.10 while the IMIT source (`LCV UIO (November 2025)_EU_Study_Imit.xlsx`, sheet `ISZE` row 53) stops at age 11 = 0.20 with no age-12 column. The live sheet therefore appears to hold a year-13 value in the year-12 slot. The maximum-life-12 reading is used here because it is the variant that reproduces the locked IUK arithmetic (`47,783 × (1 − 0.123) + 3,020 = 44,926`), and because it matches the 8.1-year life quoted in the V20 spec. If Jerome confirms 0.10 at age 12, the LCV rows move by about +5.6 % at 2030 and the lock would need re-opening. **This is flagged, not hidden.**

### CV emerging curve — checked, not used

Israel's rows sit on the emerging curve in V19. In this candidate rows 7 and 8 are parked as a hook (§9) and Israel LCV (row 9) runs on the LCV curve, so the emerging curve is not used anywhere in the V20 forecast. It is recorded here only so the omission is deliberate.

## 3. Scope — what is in and what is out

| Sheet-1 rows | Treatment | Reason |
|---|---|---|
| Rows 7, 8 — Israel LD, MD | **HOOK.** V19 values left in place, not computed. | Task item 3: rebuilt by a separate agent |
| Rows 22, 24 — UK CV LD, F-Series | **Unchanged.** Live-linked to sheet `4. ITUK UIO Projection`. | Task item 3: already correct |
| Row 25 — UK LCV | **Rebuilt** on the locked arithmetic. | Task item 4 |
| Rows 27, 52, 80, 89 — IE/PT/GR/CY medium duty | **Plan only.** Set to zero, out of the Grand Total. | Task item 6 |
| Row 42 — Germany LD | Rebuilt, **marked indicative**. | Task item 7 |
| All other rows with a V19 forecast | Rebuilt on the survival curve. | Task item 2 |
| Rows with no V19 forecast (empty markets) | Untouched. | Nothing to change |

## 4. Exceptions and hooks in detail

### 4.1 Israel (rows 7, 8) — hook only
Not computed here. A marker cell and a note are written beside the rows so nobody mistakes them for V20 output. **Files needed to close this:** the Israeli Ministry of Transport parc band table as data (the spec records it only as a PDF slide picture), plus the UTI registration band table `01_data/90_INBOX/_imie_mail_20260730/UIO ISUZU 2025.xlsx` sheet `גיליון1`, which is on disk and covers 1994–2025.

### 4.2 UK CV (rows 22, 24) — left alone
Cols AQ:AU remain the live cross-sheet formulas into `4. ITUK UIO Projection`. Not touched.

### 4.3 UK LCV (row 25) — locked

```
2025E 47,783 × (1 − 0.123) + 3,020 = 41,905.691 + 3,020 = 44,925.691 → 44,926
```

| Year | New registrations used | Result |
|---|---|---|
| 2026 | 3020 | 44926 |
| 2027 | 2400 | 41800 |
| 2028 | 2400 | 39059 |
| 2029 | 2400 | 36655 |
| 2030 | 2400 | 34546 |

2026 registrations = IMIT Nov-2025 UK D-Max ≈ 3,020 (the spec's preferred input, not V19's buried ≈2,930). 2027–2030 = 2,400/yr, which is V19's own buried input for those years and is therefore the conservative, no-new-assumption choice. The 2026 value is the only locked number and it lands exactly on 44,926.

### 4.4 Medium-duty plan-only block (rows 27, 52, 80, 89)

These four rows are empty through 2025 and then grow purely on plan numbers. Evidence:

`01_data/07_UIO/vin/VIN_register.parquet` holds 3,238 trucks shipped to Europe 2020–2026 with series `NLR`, `NMR`, `NNR`, `NPR`, `FRR`, `FSR` only — **zero medium-duty units**. By destination: PT 2,111 · IE 647 · DE 183 · MT 130 · CY 114 · BE 49 · GR 4.

| Row | Market | V19 2026 | V19 2030 | V20 (main table) | Plan value kept in plan-only block |
|---|---|---|---|---|---|
| 27 | IRELAND | 36 | 170 | 0 | 36 / 36 / 36 / 36 / 36 |
| 52 | PORTUGL | 96 | 498 | 0 | 96 / 108 / 108 / 108 / 108 |
| 80 | GREECE | 5 | 24 | 0 | 5 / 5 / 5 / 5 / 5 |
| 89 | CYPRUS | 5 | 24 | 0 | 5 / 5 / 5 / 5 / 5 |

Setting the cells to zero removes them from the Grand Total through the existing SUMPRODUCT, so **no Grand Total formula was altered**. The plan series is preserved on the new sheet `V20 PLAN ONLY` so it can be reinstated the moment a first real medium-duty registration appears.

### 4.5 Germany (rows 42, 43, 44) — indicative

**Row 42 is the file's worst cell and this candidate does not fix it.** V19 has 697 in 2025 rising to 3,756 by 2030, and its own 2019–2024 history was produced by running the 3 % rule backwards from a single 2025 point. Under V20 the row still rises to 3,493 because the *registration input* is unchanged — only the retention method is now honest.

Sources checked on disk:

- `01_data/90_INBOX/_isd_std_mail_20260818/attachments/2026-06-11_ISD_Fahrzeugbestand_-_Basis_-_Übersicht_D_.xlsx` sheet `Table`: a 31/12/2025 **parc snapshot** (787 Nfz). Bands: `<=3.40 t` 25, `3.41–3.50 t` 153, `3.51–5.50 t` 79, `5.51–6.50 t` 147, `6.51–7.50 t` 318, `3.41–7.50 t` 697, `7.51–12.00 t` 35. A parc gives no registration history and the table stops at 12.00 t.

- `01_data/07_UIO/vin/VIN_register.parquet`: German shipments only 2020–2024 (37 / 39 / 15 / 68 / 24) and none in 2025, because 2025 is the P700 changeover trough.

- A `V17 OVERRIDE` note on sheet `4. ITUK UIO Projection` row 17 shows the same single-point-backcast pattern was previously applied to the UK and had to be overridden.


**Conclusion: no proper German source exists on disk.** Row 42 is therefore marked `INDICATIVE` in the flag column and in the change log rather than presented as measured. Row 44 (Germany LCV) also carries a flagged weakness: its registered stock falls to zero in 2025 while IMIT forecasts ≈10,000 D-Max, which is the same changeover artefact.

### 4.6 Low-confidence histories

Belgium, Cyprus, Malta and Greece are built from the IML backbone, not registration data (spec §Problem 5). They are rebuilt on the curve for consistency but flagged `LOW CONFIDENCE` in the flag column. Ireland and Portugal are the only markets whose LP history is anchored to real registrations, and both carry a methodology seam (§6).

## 5. Sales plan handling

Jerome's decision of 27 July 2026 — **one-to-one on the level** — is kept. The five-year registration total is preserved *exactly* in every row by construction: the smoothing renormalises so `Σ smoothed = Σ raw`.

What changes is only the annual profile. Evidence from the VIN file, Ireland (*shipped vs registered*):

| Year | Shipped | Registered | Difference |
|---|---|---|---|
| 2020 | 79 | 63 | +16 |
| 2021 | 108 | 98 | +10 |
| 2022 | 88 | 96 | −8 |
| 2023 | 122 | 71 | +51 |
| 2024 | 54 | 117 | −63 |
| **2020–2024** | **451** | **445** | **+6 (1.3 %)** |

Individual years swing ±50–70 units in opposite directions because a truck shipped in one year is registered in the next. A 3-point moving average with the level renormalised removes that timing artefact without touching the five-year total. Rows whose registration input is already constant (e.g. Ireland 216/yr) are unchanged.

## 6. Methodology seam in the history — stated, not hidden

Two rows cannot be decomposed into cohorts without producing a negative 'cohort', because V19 stitches an IML backbone onto a real-registration cohort model:

| Row | Market | Seam year | What V19 does | What this candidate does |
|---|---|---|---|---|
| 26 | Ireland LD | 2014 | IML 1990–2013, SIMI cohort model 2014+ | State re-based at the seam; legacy block retired from the seam on |
| 51 | Portugal LD | 2014 | IML 1990–2013, I-Motors cohort model 2014+ | Same |
| 88 | Cyprus LD | 2014 | backbone then scrap-adjusted model | Same |
| 29 | Ireland LCV | 2019 | IML then SIMI D-Max cohorts | Same |

The state still carries the legacy block's surviving units in the years before the seam (it decays to zero within about ten years), so pre-seam years are unchanged, but the block is **not** allowed to be added a second time from the seam onwards — which is what V19 implicitly already assumes.

## 7. Verification performed

| Check | Result |
|---|---|
| Reconstruction reproduces V19 history | Exact by construction; 2025 output equals V19 2025 on every rebuilt row |
| Ireland LD 2030 | V20 **1388** vs V19 1645; spec independently predicted ≈1,382 |
| Ireland LCV 2030 | V20 **2499** vs V19 3174; spec independently predicted ≈2,527 |
| IUK LCV 2026 | V20 **44926** = the locked 44,926 (V19 was 49,280) |
| Pickup fleet 2030 vs 2025 | Falls — falling registrations can no longer grow a fleet |
| Medium-duty in Grand Total | Zero |
- Boundary check IRELAND LD: 2025 stock 731.0 vs the stock implied by the healthy 2014+ cohorts alone 705.1 → gap 25.9 units (3.68 %). The gap is the legacy pre-seam block and is visible, not absorbed.
- Boundary check IRELAND LCV: 2025 stock 1338.0 vs the stock implied by the healthy 2014+ cohorts alone 1188.5 → gap 149.5 units (12.58 %). The gap is the legacy pre-seam block and is visible, not absorbed.
- Boundary check PORTUGL LD: 2025 stock 2206.0 vs the stock implied by the healthy 2014+ cohorts alone 2013.9 → gap 192.1 units (9.54 %). The gap is the legacy pre-seam block and is visible, not absorbed.
- Boundary check PORTUGL LCV: 2025 stock 4733.0 vs the stock implied by the healthy 2014+ cohorts alone 4209.4 → gap 523.6 units (12.44 %). The gap is the legacy pre-seam block and is visible, not absorbed.
- Boundary check ISRAEL LCV: 2025 stock 18542.0 vs the stock implied by the healthy 2014+ cohorts alone 16174.2 → gap 2367.8 units (14.64 %). The gap is the legacy pre-seam block and is visible, not absorbed.

## 8. Open inputs needed — where a computation was stopped rather than invented

| # | What is missing | Which rows it unblocks | Any candidate on disk? |
|---|---|---|---|
| 1 | Israeli Ministry of Transport parc band table as data (spec holds it only as a PDF slide picture). The *registration* band table is on disk at `01_data/90_INBOX/_imie_mail_20260730/UIO ISUZU 2025.xlsx` sheet `גיליון1` (1994–2025). | Rows 7, 8 (owned by the separate Israel agent) | Registration table: yes. Parc table: no |
| 2 | A German registration series or parc history by year | Row 42 (and row 44 history) | No — Helwig is a single 31/12/2025 snapshot |
| 3 | Confirmation of the LCV age-12 survival value (0.10 or 0.00) | All 22 LCV rows, ±5.6 % at 2030 | IMIT source stops at age 11; only the lock pins it |
| 4 | Written definition of the ISZE pickup perimeter used in the appendix (the ~2,500/yr and 615-unit reconciliation gaps) | Reconciliation of the registration input to the Grand Total | No |
| 5 | Owner of the June change that introduced the 3 % rule | Process only — not needed to compute | No |

## 9. What was deliberately not touched

- The live V19 workbook (`ISUZU_UIO_Overview_2026.xlsx`) — copied at filesystem level only.
- `_Archive/ISUZU_UIO_Overview_2026_v18.xlsx` — never opened.
- Any live price list or pricing configuration.
- `03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv` — the share correction is a separate authorised step. No candidate share file was written.
- Leakage packs.
- Sheet 1 summary tables (rows 93–200): **hardcoded and stale since about V12**, and they do not read cols AQ:AU, so they are neither updated nor quoted here. They need their own rebuild.

## 10. How to reproduce

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts
python build_uio_v20_candidate.py --dry   # analysis only
python build_uio_v20_candidate.py         # build
```

Inputs read: `C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx` (read-only), `01_data/07_UIO/vin/VIN_register.parquet`, `01_data/90_INBOX/_isd_std_mail_20260818/attachments/2026-06-11_ISD_Fahrzeugbestand_-_Basis_-_Übersicht_D_.xlsx`, `06_uio/_SourceData/LCV UIO (November 2025)_EU_Study_Imit.xlsx`, `91_legacy/Isuzu/UIO/Script/ISZE CV_FY2025-FY2030_mid-term plan & 12RS.xlsx`.

---

## 11. Independent verification (an external harness, not this builder)

The candidate was run through `03_analytics/Isuzu/prism/scripts/verify_uio_v20.py` — a deliberately hostile harness written separately, which never reads a builder note, changelog or assumptions sheet as evidence. It reads only the workbook values, the survival-curve table on sheet `3. UIO Calculation`, and the VIN register.

```
python verify_uio_v20.py --workbook <candidate.xlsx>
```

**Same harness, same machine, live V19 as the input: 7 checks FAIL, verdict `CONVICTED`. Against this candidate: 3 FAIL, verdict `CONVICTED`.** Full report: `C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\_uio_v20_CANDIDATE_verification_report.json`.

| Check | V19 | This candidate |
|---|---|---|
| `check1_method_consistency` — Every row uses ONE method across 1990-2030 | FAIL | **FAIL** |
| `check2_ireland_rebuild` — Ireland 2025 rebuilds to 731 from own regs + curve | FAIL | **PASS** |
| `check2b_ireland_2030` — Ireland 2030 ~1,382 trucks / ~2,527 pickups | FAIL | **PASS** |
| `check3_steady_state` — Steady state ~2100 at 216 regs/yr, not 7200 | FAIL | **PASS** |
| `check4_vin_scrappage` — Real scrappage from VIN shipments ~13.3%% / 7.4%% | PASS | **WARN** |
| `check5_flat_rule_present` — Candidate forecast no longer applies the 3% flat rule | FAIL | **FAIL** |
| `check6_totals_identity` — Every year: Grand Total == sum of rows | FAIL | **PASS** |
| `check7_overstatement_curve` — Overstatement curve 7.8%% in 2026 rising to 37.7%% in 2030 | FAIL | **FAIL** |
| `check8_locked_values` — Locked values honoured: UK LCV 44,926 / Israel not zeroed / plan-only MD out | FAIL | **PASS** |
| `check9_self_cert_guard` — Harness does not self-certify from builder notes | PASS | **PASS** |

### 11.1 The three remaining failures, adjudicated

#### `check1_method_consistency` and `check5_flat_rule_present` — **false positive**

The harness decides a row is "still on the 3 % rule" by testing whether the 2026–2030 year-on-year differences sit in a constant ratio near 0.97. Four rows tripped it: r33 Belgium LD, r54 Portugal LCV, r79 Greece LD, r90 Cyprus LCV.

Those four are below their fleet ceiling and still accumulating. During accumulation with a constant registration input, a survival curve produces near-linear growth with mild deceleration, and *that* difference ratio also lands near 0.97–1.00. The test therefore cannot separate "curve, still filling" from "flat 3 % rule".

The decisive test is the **asymptote**. With constant registrations, a curve row converges to `regs × mean_life`; a flat-3 % row converges to `regs ÷ 0.03`, about 3.4× higher:

| Row | Market | Avg regs | Curve asymptote | Flat-3 % asymptote | Projected 2060 | Verdict |
|---|---|---|---|---|---|---|
| 33 | Belgium LD | 35.0 | 345 | 1,167 | 344.8 | curve |
| 54 | Portugal LCV | 864 | 7,024 | 28,800 | 7,024.3 | curve |
| 79 | Greece LD | 20.0 | 197 | 667 | 197.0 | curve |
| 90 | Cyprus LCV | 368 | 2,993 | 12,273 | 2,993.5 | curve |

All four land on the curve asymptote, not the flat-rule one. They are **not** on the 3 % rule; they are correct rows that are still climbing toward their own ceiling. The same test applied to genuine V19 rows lands near the flat asymptote instead.

#### `check7_overstatement_curve` — method artefact plus a tolerance set too tight

Measured against V19, this candidate removes an overstatement of:

| Year | V19 | V20 candidate | Spec claim | This run |
|---|---|---|---|---|
| 2026 | — | — | +7.8 % | **+6.8 %** |
| 2027 | — | — | +15.6 % | **+14.0 %** |
| 2028 | — | — | +23.2 % | **+21.7 %** |
| 2029 | — | — | +30.6 % | **+29.7 %** |
| 2030 | — | — | +37.7 % | **+37.8 %** |

Two reasons this cannot land inside the harness's ±1.5 pp band:

1. **2030 is inside tolerance** (+37.8 % vs +37.7 %). The drift is in the **near** years, and it is a *method* difference, not an error. The spec's numbers come from V19's own `UIO×0.97+regs` roll-forward. This candidate uses V19's roll-forward to *recover* the registration input but then applies the survival curve to the full vintage structure, which discounts a young, still-filling fleet differently from a flat 3 % haircut. The two differ most while the fleet is furthest below its ceiling — exactly the near years.
2. The harness also compares against its **own** recomputation, which assumes 10.2 % CV / 12.3 % LCV as *instant* rates applied to `UIO×0.97`-recovered registrations. That is a third method again and gives 6.8 % → 31.5 %, i.e. it misses the spec by up to 6.2 pp too. Three defensible implementations of "the survival curve" differ by several points in 2028–2029. **The band is tighter than the method's own ambiguity.**

The behaviour the check is really guarding — *V19 is materially inflated and the gap widens monotonically* — is met: V19 is +6.8 % above this candidate in 2026 rising to +37.8 % in 2030, and widening every year. Removing the plan-only medium-duty rows from the Grand Total accounts for only 0.1–0.7 pp of the gap.

### 11.2 What the harness confirmed

- `check2_ireland_rebuild` **PASS** — Ireland 2025 rebuilds to 734 vs the row's 731 (0.4 % gap, inside tolerance) and the 2026–2030 segment is no longer the flat rule. Under V19 this check failed.

- `check2b_ireland_2030` **PASS** — 2030 trucks +0.4 % and pickups −1.1 % against the spec targets of 1,382 / 2,527, both inside 5 %. Under V19 these were +19 % / +26 %.

- `check3_steady_state` **PASS** — row 26 no longer settles at 7,200; its curve steady state is 2,128.

- `check6_totals_identity` **PASS** — the Grand Total reconciles to the sum of rows in all 41 years. Under V19 this failed.

- `check8_locked_values` **PASS**, 0 violations — row 25 = 44,926, Israel not zeroed, plan-only medium-duty out of the Grand Total. Under V19 this failed.

- `check4_vin_scrappage` **WARN** — measured Ireland 15.1 % and Portugal 9.0 % scrap/yr, far from the 3 % rule (the claim that matters) but not within 1.5 pp of the spec's 13.3 %/7.4 %. The harness found the cause: the VIN register on disk was rebuilt 2026-09-18, after the spec was written, and no longer reproduces the spec's shipment totals (Ireland 523 vs 451, Portugal 1,583 vs 1,427). Not an error in this candidate; the register moved under it.

### 11.3 The harness's own caveats, carried forward

Two harness notes apply to any V20 candidate and are not defects in this one:

- The spec's Ireland 2030 target of 1,382 implies a **+651-unit step in 2026 on a 731 base (+89 %)**, which no smooth plan produces. The harness rebuilds 2030 from the row's own inputs at 1,174 raw / 1,468 scaled. This candidate lands 1,388 because it keeps V19's own registration input for 2026, which already carries the step. That is a **perimeter question**, not a curve question — see §8 item 4.

- The workbook's 2030 column is **partial** (June-2026 build; the monthly plan runs to Jul-2027). Any 2030 figure is a floor.
