# AIM priority list — handoff for the sales-analysis agent

**Prepared:** 2026-09-17 · internal · one basis only, stated below
**Read this before touching anything in the AIM set.**

---

## 1. The basis — do not mix

| | |
|---|---|
| Source | `01_data/00_derived/price_bp_weighted_compare_pn.csv` |
| Filter | `in_scope == True` |
| Window | **2025-07-01 → 2026-06-30** (L12M) |
| Billed | **€34,993,609.39** |
| Step | **€1,652,140.71** |
| Weighted increase | **5.9616%** |

Both the step and the weighted increase reproduce the published revision exactly. If your work does not reconcile to these two numbers, stop and check the basis before going further.

**There is a second window in this workspace — 2025-01-01 → 2026-06-30 (18 months, gross billing).** It gives different euro for the same families, roughly 30–40% higher. Never mix the two. If you see Brakes at €5.30M you are on the 18-month window; at €3.16M you are on this basis.

---

## 2. Files

| File | What it is |
|---|---|
| `02_dashboards/pricing/AIM_PRIORITY_LIST.csv` | The list. 15,872 part numbers, 22 columns, ranked by step euro |
| `02_dashboards/pricing/AIM_PRIORITY_LIST.xlsx` | Same, plus Top 250 sheet, AIM L1–L2 rollup, taxonomy fixes, Read me |
| `01_data/00_derived/aim_master_v2.csv` | Corrected AIM master, 165,213 rows |
| `01_data/00_derived/aim_taxonomy_fixes_v1.csv` | Every taxonomy change made, with reason and euro |
| `01_data/00_derived/aim_master_v2.meta.json` | Coverage and fix log |

---

## 3. Columns that matter

| Column | Meaning | How to use |
|---|---|---|
| `priority_rank` | 1 = largest step euro | Rank for the revision agenda |
| `step_eur` | Euro impact of the revision on this part | **The priority measure** |
| `delta_pct` | Weighted base-price move on this part | The size of the move |
| `l12m_billed_eur` | Billed euro, this basis | Size of the part |
| `cum_step_share_pct` | Cumulative share of the step | Top 100 = 42.6%, top 250 = 56.8% |
| `aim_l1/l2/l3` | **Corrected** AIM Category | The governed spine |
| `on_aim_spine` | `0` = not on the AIM spine | **Filter or separate — never chart as a class** |
| `cat_l1/l2/l3` | Price-list catalogue | Attribute only. Never the axis |
| `pms_flag` | `1` = catalogue family is PMS/competitive | For the PMS cut |
| `fig_key` | Manufacturer figure key | Structural grouping only. **Never evidence of competition** |
| `distributors` | How many distributors carry the part | Breadth |
| `aim_changed` | `1` = this row's AIM class changed in the fix | Audit trail |

---

## 4. What is on the list

| Corrected AIM L1 | PNs | Billed € | Step € | Step % |
|---|---:|---:|---:|---:|
| Intake Exhaust Emission | 486 | 5,148,968 | 289,255 | 18.0% |
| **UNCLASSIFIED (not on AIM spine)** | 5,620 | 6,883,708 | 274,035 | 17.0% |
| Accident & Body | 2,355 | 4,292,317 | 239,611 | 14.0% |
| Brakes | 347 | 3,156,407 | 215,508 | 13.0% |
| Maintenance Service | 356 | 3,198,973 | 110,552 | 7.0% |
| Electrical | 755 | 1,523,107 | 85,990 | 5.0% |
| Lighting | 697 | 1,692,710 | 82,782 | 5.0% |
| Fuel System | 467 | 1,819,020 | 74,122 | 4.0% |
| Wheels Hub | 606 | 1,156,620 | 61,546 | 4.0% |
| … 15 more classes | | | | |

**PMS split:** flagged €18,865,041 billed / €886,743 step. Not flagged €16,128,568 / €765,397.

**Concentration:** top 10 lines = 19.1% of the step · top 100 = 42.6% · top 250 = 56.8% · top 1,000 = 79.0%.

---

## 5. Head of the list (top 10 by step)

| # | Part | Billed € | Step € | Δ% | Description | AIM |
|---|---|---|---:|---:|---:|---|---|
| 1 | 8982447940 | 342,394 | 81,934 | 24.87 | PAD KIT; CALIPER,DISC BRK,FRT | Brakes > Pads & Shoes |
| 2 | 8978808250 | 808,390 | 44,099 | 7.00 | SENSOR; PM | Intake Exhaust Emission > Sensors |
| 3 | 8983767550 | 703,041 | 39,058 | 7.00 | ROTOR; DISC BRK,FRT | Brakes > Discs & Drums |
| 4 | 8983528481 | 568,853 | 33,449 | 7.00 | SENSOR; NOX | Intake Exhaust Emission > Sensors |
| 5 | 8982705240 | 256,036 | 30,840 | 10.08 | ELEMENT; OIL FILTER | Maintenance Service > Oil Filter |
| 6 | 8978808270 | 544,908 | 29,686 | 7.00 | SENSOR; PM | Intake Exhaust Emission > Sensors |
| 7 | 8975359391 | 305,423 | 16,768 | 7.00 | DPD ASM | Intake Exhaust Emission > DPF/DPD |
| 8 | 8975554500 | 266,865 | 14,932 | 7.00 | FILTER; BLOWER UNIT | Cabin Interior > HVAC Filters |
| 9 | 8974985741 | 240,103 | 13,297 | 7.00 | TURBOCHARGER ASM | Intake Exhaust Emission > Turbo |
| 10 | 8982688122 | 222,965 | 12,202 | 7.00 | PUMP ASM; DEF,DCM SPLY | Intake Exhaust Emission > DEF System |

---

## 6. Taxonomy fixes already applied — and what was deliberately not fixed

### Applied (see `aim_taxonomy_fixes_v1.csv`)

| Fix | Change | Euro moved |
|---|---|---:|
| L1 split | Lighting pulled out of Accident & Body and Electrical into its own class | €2,001,797 + €588,452 |
| L2 merge | `Brakes > Disc & Drum` → `Discs & Drums` (was the same concept twice) | €865,383 |
| L2 rename | `Maintenance Service > Filters` → `Filters (unspecified)` (it is not a parent total) | €1,570,755 |
| L2 merge | `Electrical > Sensors` → `Sensors & Switches` | €4,153 |
| L2 merge | `Electrical > Starting & Charging` → `Charging` | €18,711 |

Accident & Body fell from €8,340,691 to €6,338,894 — a crash class no longer inflated by a service business.

### Flagged, not forced

These need description rules or a human call. Forcing them blind would invent classifications:

1. **Bumpers split.** L2 `Bumpers` and bumper lines sitting inside `Panels`.
2. **Lubricants in two places.** `Fluids Chemicals > Lubricants` versus the separate `Lubrication` L1.
3. **Filters under four L1s.** `Maintenance Service`, `Fuel System > Filtration`, `Cabin Interior > HVAC Filters`, `Lubrication > Oil Filter System`.

---

## 7. Coverage — state it every time

- **Genuine AIM Category: 80.33% of billed euro** (€28,109,902).
- **Not on the AIM spine: 19.67%** (€6,883,708), labelled `UNCLASSIFIED (not on AIM spine)` and fully attributable to catalogue posture.
- **Catalogue node: 100.00%** — by construction, because the pricing base only contains priced parts.

Do not quote an AIM figure without the 80.33% beside it. A reader who re-derives will find the gap, and it is better that you named it first.

---

## 8. Two rules that were broken before and must not be broken again

1. **Never join on description.** Identity is `part_number`. Descriptions are attached from billing text by euro, not matched.
2. **Figure key is structure, never competition.** Two parts under one figure may be left and right, or an assembly. It is not evidence that no competitor exists. A build that used it that way labelled €12.96M as "captive" and had to be corrected.

---

## 9. The EPC

The Isuzu Snapon EPC is open in the browser and can name parts by part number. It is a **targeted** tool, not a bulk source — the existing scraper has a ~12-second delay per part, so full coverage is not feasible in one session. Use it for the ambiguous and unclassified cases, not as a bulk rename.
