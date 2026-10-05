# AIM classification — full audit

**Prepared:** 2026-09-17 · **Internal** · read-only (nothing changed in the classifier, pipeline, or any pack)
**Window:** 2025-01-01 → 2026-06-30 (the last sales data on disk; `sales_fact.parquet` max billing_date = 2026-06-30)
**Subject:** `01_data/00_derived/aim_pn_classification.csv` (164,667 rows), its sources, and its consumers
**Basis note:** every euro figure below is stated on the basis measured. This audit window is 18 months and gross. It is **not** the 12-month in-scope base used in `aim_catalog_breakdown_NOTES.md`, so the two must not be mixed.

---

## Verdict

The classification file is **mechanically clean and semantically mixed**. Keys, hierarchy, and join rates pass. The taxonomy does not: one Level-1 column carries **two different classification systems at once**, and the source precedence runs the opposite way from what the label implies. As a management axis today it is not safe to quote without stating which vocabulary is in play.

| # | Finding | Severity | Check |
|---|---|---|---|
| 1 | Two incompatible Level-1 vocabularies in one column in the workbook-sourced layer | **P0** | FAIL |
| 2 | Source precedence inverted — `aim_workbook` owns the money, `pr00_catalog` the label | **P0** | FAIL |
| 3 | Description matching non-deterministic (71 descriptions → >1 L1) | P1 | FAIL |
| 4 | Coverage gaps in the window: 4.71% euro on PNs absent, 1.96% placeholder, 0.34% blank | P1 | FAIL |
| 5 | Non-part lines (rebate, transport, lubricant) bill inside the same parts base | P1 | FAIL |
| 6 | Key integrity: 164,667 rows, 0 duplicates, all 10 characters | — | PASS |
| 7 | Hierarchy integrity: no L2/L3 without L1 on either scheme | — | PASS |
| 8 | Brake semantics reproduce, including the `ROTOR` false-positive trap | — | PASS (with caveat) |

---

## 1. Two Level-1 vocabularies in one column — P0

`aim_l1` holds **30 distinct values**, and they are not one taxonomy. Measured on the file (164,667 rows):

| Axis kind | Rows | Values |
|---|---:|---|
| Posture (catalogue-style) | 147,978 | Competitive parts, Repair parts, Accident parts, High value repair, Comfort parts, Hardware & consumables, Other / review |
| **System-named (a different axis)** | **15,959** | Body Exterior 3,743 · Chassis Frame 1,964 · Electrical 1,896 · Transmission 1,205 · Wheels Hub 989 · Cabin Interior 918 · Intake Exhaust Emission 826 · Fuel System 698 · Engine 664 · Brakes 521 · Maintenance Service 518 · Suspension 446 · Cooling 378 · Steering 329 · Driveline Axle 325 · Lubrication 212 · Fluids Chemicals 127 · Tools Equipment 94 · Clutch 47 · Literature Marketing 37 · Logistics Packaging 22 |
| Placeholder | 730 | Unknown 599 · Unknown Review 131 |

`catalog_l1` by contrast has **8 values** and is a different axis entirely: Repair / Competitive / Accident / Hardware / High value repair / Other / review / Comfort.

**Weighted by euro in the audit window** (2025-01-01 → 2026-06-30, gross, total €52,414,408):

| Axis on `aim_l1` | Euro | Rows | Share |
|---|---:|---:|---:|
| System-named (different axis) | €41,618,619 | 164,056 | **79.40%** |
| Posture (catalogue-style) | €7,115,421 | 50,706 | 13.58% |
| PN not in the classification file | €2,471,070 | 6,081 | 4.71% |
| Placeholder | €1,029,341 | 5,601 | 1.96% |
| Blank `aim_l1` | €179,955 | 142 | 0.34% |

So roughly **four fifths of the billed euro in the window sits on `aim_l1` values drawn from the other taxonomy**. `Intake Exhaust Emission` alone is €7.52M in the window and `Body Exterior` €8.36M — larger than the entire posture layer under it.

**What breaks because of it:** any pack that groups by `aim_l1` produces a chart whose rows come from two different taxonomies, so "Repair parts" and "Engine" appear as peers when they are not. The 17 Sep note already flagged this as "the real classification-scheme conflict" and left it unfixed by decision. This audit confirms it is not cosmetic — it is the majority of the money.

## 2. Source precedence is inverted — P0

`aim_source` reads as a provenance flag for `aim_l1`. Measured in the window:

| `aim_source` | Rows in file | Window euro | Window rows |
|---|---:|---:|---:|
| `pr00_catalog` | 139,410 | €7,017,834 | 50,687 |
| `aim_workbook` | 16,499 | **€42,435,425** | 167,708 |
| (blank) | 8,562 | €2,651,026 | 6,223 |
| `gap_suggestion` | 196 | €310,123 | 1,968 |

The source with **13% of the part numbers carries 81% of the euro** — and it is the coarse workbook taxonomy. The catalogue layer, which the management case treats as the eye-level tree, wins the label on most rows but not the money.

This is the mechanism behind the 17 Sep warning that restricting to `aim_source == 'pr00_catalog'` collapses the answer to 13.5% of euro. It is worse than a reporting trap: it means **the layer we are proposing to adopt is not currently the layer that governs most of the billed value.**

## 3. Description matching is non-deterministic — P1

71 of 5,820 distinct normalised descriptions map to **more than one** `aim_l1` value. The workbook join is by description, so the same part description can land in two different Level 1s. Small in row terms, but it is a correctness defect, not a rounding issue: it means the classifier is not a function of the part.

## 4. Coverage in the window — P1

- **4.71% of window euro (€2.47M, 6,081 rows) is on part numbers absent from the classification file.** At PN level the coverage is 97.95% (399 of 19,421 window PNs missing), which is why a count-based check looks healthier than the euro-based one. State the basis.
- **1.96% placeholder** (`Unknown` / `Unknown Review`) — €1.03M.
- **0.34% blank** `aim_l1` — €180k.
- Independently confirmed on the file: `aim_l1` populated 156,105 / 164,667 (94.8%), `catalog_l1` populated 164,610 / 164,667 (100.0%).

## 5. Non-part lines sit in the parts base — P1

Top part numbers by window euro include lines that are not parts:

| PN | Window euro | Description | Classification |
|---|---:|---|---|
| `REBATE` | €895,030 | Rebate Material | none (correct) |
| `550047337` | €587,819 | Rim R4L 15W40 | none (correct — lubricant) |
| `TRANSPORT` | €540,258 | Transporting Cost | none (correct) |

They are correctly unclassified, but they are inside the same billed base, so any family share expressed in euro carries them in the denominator. Today that is handled by naming them; it must stay named.

## 6–8. What passed

- **Key integrity — PASS.** 164,667 rows, **0 duplicate part numbers**, **0 keys not exactly 10 characters**. Join rate to billed lines 99.84% of rows / 97.72% of euro (from `aim_catalog_breakdown_meta.json`).
- **Hierarchy — PASS.** Zero rows on either scheme carry L2 or L3 without L1.
- **Brake semantics — PASS with the known caveat.** In the window, `Brake parts` holds €5.30M across 11,989 rows; brake-like content outside that family is €241k (4.6%). The `ROTOR` false positives (`ROTOR; SENSOR`, `SENSOR; PM`) reproduce — they are sensors, not brakes, exactly as the 17 Sep note warned. Largest genuine brake lines classify correctly: `8983767550 ROTOR; DISC BRK,FRT` €998,989 → Competitive parts > Brake parts > Brake disc.
- **Top-PN sanity.** The largest non-part-number-coupled lines are real and land sensibly: `7552348290 STEERING UNIT` €1,239,369 → Competitive parts > Steering > Steering gear / unit; `8982878080 FILTER ASM` €460,315 → Competitive parts > Filters > Other filter (the residual bucket, as documented).

---

## What is still UNKNOWN (not checked, not claimed)

1. Whether the two `aim_l1` axes can be reconciled at all, or whether one must be retired.
2. Whether `catalog_l1`'s `Other / review` (9,856 rows in file) is complete or a waiting list.
3. CY2026 basis integrity — flagged separately in `_data_integrity_open_issues.md` (SPU-PARTIAL: the true end date of the 2026 sales column is not reconcilable to a clean quarter; CR/RE-FY26: SaTy netting for Apr–Jun 2026 is sign-based only, unverifiable). This audit did not resolve either.
4. Which downstream packs group by `aim_l1` in a way that mixes the two axes. Consumer sweep not completed.

---

## Recommendation before AIM goes outside ISZE

1. **Settle the Level-1 axis in the file.** One column, one vocabulary. Either drop the 21 system-named values or move them to their own column. Until then, state the axis on every chart.
2. **Fix or relabel the precedence.** If `pr00_catalog` is meant to be the commercial tree, it must actually win on the money; today it does not.
3. **Make the description join deterministic** (71 contested descriptions).
4. **Keep the named residual visible** (placeholder 1.96%, absent PNs 4.71%, non-parts lines).
5. Do **not** present the current `aim_l1` mix to management as one taxonomy. The separation into posture vs system is the difference between a tree and a pile.

---

## Method and reproducibility

- File audit: full-key pass on `aim_pn_classification.csv` (no sampling).
- Euro weighting: join to `sales_fact.parquet` on 10-character part number, window 2025-01-01 → 2026-06-30, `net_sales_value` gross.
- Semantic checks: brake token test against `catalog_l2`, top-10 PN inspection with description.
- Independent recomputation: coverage counts, match rates, and tie-out figures were recomputed, not copied. Cross-checked against `aim_catalog_breakdown_meta.json` and `aim_catalog_breakdown_NOTES.md`.

Sources:
`01_data/00_derived/aim_pn_classification.csv` ·
`01_data/00_derived/sales_fact.parquet` ·
`01_data/00_derived/aim_exposure_by_db_year.csv` ·
`01_data/00_derived/aim_catalog_breakdown_meta.json` ·
`03_analytics/Isuzu/prism/docs/aim_classification_gap_report.md` ·
`01_data/00_derived/_data_integrity_open_issues.md` ·
`03_analytics/Isuzu/prism/modules/aim_pn_classifier.py`
