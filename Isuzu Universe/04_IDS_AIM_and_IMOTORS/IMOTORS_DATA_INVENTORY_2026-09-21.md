# Imotors (Portugal) — what is actually on disk

Built 2026-09-21 · internal · inventory only, nothing rebuilt, every file below already existed.

Purpose: one page listing the Portugal data that exists, with its path, its grain and its figures,
so the same set can be handed to an assistant without hunting the tree. Where a number was not read
on this date, it says so.

---

## 1. The short answer to three questions

| Question | Answer |
|---|---|
| Has Imotors sent sales-to-dealer data? | **Yes, once** — 3 September 2026, from Nuno Machado (Astara). One workbook, CY2025 + CY2026 to August. Quantity per part number per month, **no dealer names**. |
| Is there IDS data for Portugal? | **Yes** — a scored round of **16 dealers**, plus a per-dealer feedback workbook and a DB rollup. |
| Is there a car park / fleet figure? | **Yes** — a measured parc, and it is one of the better ones in the network. See §4. |

---

## 2. Sales to dealer (DB → dealer)

**Raw, as received (immutable):**
`01_data\12_raw\dealer_sales\PORTUGAL\PORTUGAL_Sales_to_Dealer_2025_2026YTD_Aug.xlsx`
- Inbox copy: `01_data\90_INBOX\nuno_machado_sales_to_dealer_20260903\PORTUGAL_Sales_to_Dealer_2025-26_from_NunoMachado_20260903_1258.xlsx`
- Registry row: `01_data\12_raw\dealer_sales\_registry.yaml` (line 121)
- Source note: `01_data\12_raw\dealer_sales\PORTUGAL\SOURCE.md`
- Sheets: `2025` (full year) and `2026` (January–August)
- Columns: invoice date, `Referencia` (part number), quantity
- Grain: **network × part number × month. No dealer dimension. Quantity only, no euro.**
- What it is: Imotors selling on to its dealers. **Not** ISZE billing Portugal.

**Normalised:**
| File | Rows | Part numbers | Units |
|---|---:|---:|---:|
| `01_data\00_derived\dealer_sellout_long_PORTUGAL_CY2025.csv` | 21,636 | 5,712 | **51,363** |
| `01_data\00_derived\dealer_sellout_long_PORTUGAL_CY2026YTD.csv` | 15,789 | 4,747 | **39,790** |

Monthly rows and the roll-up row agree exactly in both files, so neither double-counts.

**Adapter:** `01_data\91_build\normalize_dealer_sellout_portugal.py`

**Valued at ISZE's own billed prices per part number** (`build_dealer_sellout_aim_gps.py`):
- `01_data\00_derived\dealer_sellout_gps_2025.csv` — Portugal (network aggregate) row:
  **€1,439,188** total, **€176.03 per truck**, 8.19% of units have no ISZE price and therefore count as zero.
- `01_data\00_derived\dealer_sellout_aim_mix_2025.csv` — the same row with the parts mix.

**The one thing that does not exist for Portugal:** any dealer name. The other six markets with
sales-to-dealer data (ITUK, IUK, Ireland, Greece, UTI, Romania) are the same — **only ITUK's CY2025
file has dealer names**, and only ITUK's.

---

## 3. What Portugal orders — the family picture (CY2025, sales to dealer, valued)

Source: `01_data\00_derived\sellout_aim_by_aim_l1_2025.csv`, layer `sellout_db_dlr`, distributor
`PORTUGAL`. 51,363 units, €1,439,188.

| Family (AIM L1) | Units | € | BVP € | Contested genuine € |
|---|---:|---:|---:|---:|
| Body Exterior | 5,295 | 215,764 | 0 | 0 |
| Intake Exhaust Emission | 1,328 | 174,062 | 0 | 0 |
| Competitive parts | 4,011 | 153,429 | 16,736 | 12,940 |
| Brakes | 2,145 | 122,880 | 8,148 | 14,387 |
| Fuel System | 1,816 | 93,858 | 563 | 0 |
| Electrical | 1,903 | 71,043 | 251 | 0 |
| Wheels Hub | 4,711 | 69,681 | 1,235 | 1,420 |
| Maintenance Service | 7,193 | 61,809 | 28,682 | 285 |
| High value repair | 923 | 57,179 | 25 | 50 |
| Transmission | 2,680 | 56,479 | 41 | 37 |
| Steering | 283 | 54,563 | 0 | 0 |
| Repair parts | 1,610 | 54,253 | 2,050 | 70 |

Service-family view (`...\sellout_aim_by_pms_2025.csv`, top rows): `brake_pad` €61,816;
`fuel_filter` €27,164; `brake_rotor` €26,677; `clutch_kit` €25,365; `air_filter` €24,348;
`oil_filter` €17,429; `blower_filter` €15,774.

**Two limits of that table, both measured here.** In `sellout_aim_by_pms_2025.csv`,
**€1,167,262 of the €1,439,188 — 81% — sits in `(unclassified)`**, meaning those units have no service
category attached. The AIM L1 table above is the one to use for family totals; the service-category
table covers only the classified fifth. This is not a Portugal defect, it is how much of the network's
part numbers carry a service-category mapping.

And the `aim_bucket` column in `sellout_aim_by_aim_l1_2025.csv` cannot be read with `eur_total` to
separate BVP from genuine — the same total repeats on every bucket row of a family. The BVP and
contested columns above were read from a separate pass over `sellout_aim_by_pms_2025.csv` and
`sellout_aim_by_subgroup_2025.csv`; a re-run should take them from `aim_bucket` against `valued_eur` in
`dealer_sellout_gps_2025.csv`, which is the file built for that purpose.

---

## 4. Fleet / car park

**The measured parc** — `01_data\08_Distributor\Imotors_Portugal_UIO_GPS_PMS_Study.xlsx`
- Built from official I-Motors registrations (`Matriculas Isuzu SAP.xlsx`) convolved with the UIO V19
  survival curve. Sheets: `SAP_Raw_Registrations`, `Survival_Curves`, `UIO_Rebuild`, `UIO_Compare`,
  `GPS_Recalc`.
- 2025 parc: **N35 1,521.31 + N75/N50/N62 869.00 = 2,390.31** N-series → **light share 0.6364 (63.6%)**.
  2024 gives 0.6386.
- **This replaces the 0.690** that earlier papers carried: that was a Japanese **shipment** mix
  (NLR 1,299 of 1,883), not a parc share. Corrected in `DECISIONS.md` and `ISZE_ROADMAP.md` on 19/09.
- The workbook's own `GPS_Recalc` sheet: target spend €2,480,298 on its rebuilt split against
  €3,052,087 on the current basis (its figures, reported not re-derived).

**The fleet base actually in use** — `01_data\00_derived\gps_spu_by_distributor.csv`, PORTUGAL rows:

| Year | Parts billed € | Warranty parts € | Trucks in service | € per truck | Target € | Capture |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 1,363,633 | — | 6,091 | 223.88 | — | — |
| 2024 | 1,536,814 | — | 6,903 | 222.63 | — | — |
| 2025 | **1,709,794** | 130,588 | **8,176** | **209.12** | 3,494,069 | **48.9%** (ex-warranty 193.15 / 45.2%) |
| 2026 YTD | 509,806 | — | 8,444 | 60.37 | 4,093,046 | partial year, do not read a capture % |

**Open decision, not resolved here:** the workbook's rebuilt N-series stock (2,390) against the LD row
the UIO workbook uses (2,206), and against the GPS denominator of 8,176. Which becomes the fleet base
is a fleet-base decision, recorded as open in `DECISIONS.md` (D09).

**Mileage** — `01_data\08_Distributor\Portugal_annual_km_mileage.md`
- **22,742 km/yr**, from an IMG LCV / D-Max VIN sample of 1,596 vehicles (Jul 2026).
- It is an **LCV** figure. The **N75 truck has no measured annual distance for Portugal** and still runs
  on the 20,000 km/yr default in `pms_capture_assumptions.yaml`. Any per-vehicle expected-demand
  statement for Portugal inherits that assumption.

---

## 5. IDS 2026 — Portugal

**Scored round: 16 dealers.** Rank, name, points achieved %, items scored %:

| Rank | Dealer | Points % | Items % |
|---:|---|---:|---:|
| 1 | AMATOSCAR EVORA | 99.29 | 100.00 |
| 2 | AUTO RENO MINHO POVOA | 96.43 | 96.43 |
| 3 | AUTO RENO MINHO VIANA | 96.43 | 96.43 |
| 4 | AUTO RENO PAÇOS FERREIRA | 96.43 | 96.43 |
| 5 | AUTO RENO PENAFIEL | 94.29 | 94.39 |
| 6 | AMATOSCAR PORTALEGRE | 92.86 | 94.90 |
| 7 | AUTO INDUSTRIAL LEIRIA | 91.43 | 95.92 |
| 8 | ROLMAX | 90.71 | 96.43 |
| 9 | AUTO IMPERIAL | 86.43 | 95.41 |
| 10 | SOCARROS CALDAS | 82.50 | 93.37 |
| 11 | ASTARA RETAIL LISBOA | 78.93 | 85.71 |
| 12 | MSCAR | 77.86 | 87.24 |
| 13 | SOTERMÁQUINAS | 77.86 | 86.73 |
| 14 | XANAUTO | 77.86 | 85.20 |
| 15 | ASTARA RETAIL CASCAIS | 76.79 | 83.16 |
| 16 | AMATOSCAR BEJA | 74.64 | 85.71 |

Source: `01_data\08_Distributor\IDS_2026\rankings\Portugal_dealer_ranking.xlsx`.
Four of the sixteen are Astara's own retail sites, the rest are independent dealers.

**Supporting files:**
| What | Path |
|---|---|
| Per-dealer self-audit workbooks (232-row detail, 18 dealer columns) | `01_data\08_Distributor\IDS_2026\Portugal\IDS Evaluation 2026 - PORTUGAL - FINAL\` |
| Combined evaluation result (Portugal26 + Mechanic Info + Service Advisor Info + Score) | `01_data\08_Distributor\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_Portugal.xls` |
| Year-on-year delta | `...\reports\evaluation_result\_delta\2026 IDS Evaluation Result Report_Portugal_Delta.xlsx` |
| Per-dealer feedback sheets (16 files) | `09_meetings\IDS_2026_DB_Feedback_Sheet_v0.4\Portugal\dealers\` |
| DB roll-up (network overview, hit list, incomplete lane, next steps, pull scorecard) | `...\Portugal\IDS_2026_DB_Rollup_Portugal_v0.4.xlsx` |
| SharePoint drop copy of both | `09_meetings\IDS_2026_SharePoint_drop\IDS_dealer_sheets\Portugal\` |
| Dealer comparison page | `09_meetings\Imotors_Portugal_IDS_2026\IDS_2026_dealer_compare_Portugal.html` (+ `02_dashboards\ids\` copy, + `OPEN_*.cmd`) |
| Dealer map page | `09_meetings\Imotors_Portugal_IDS_2026\IDS_2026_Portugal_dealer_map.html` (+ copies) |
| Country pack zip | `09_meetings\IDS_2026_Country_Packs_v1.5\IDS_2026_Portugal_v1.5.zip` |
| **City and address are blank** for all 16 in the consolidated network file | `01_data\00_derived\ids_dealer_network.csv` (city blank on 495 of 519 network-wide, address blank on all) |

**Do not build a dealer-level link from IDS to sales.** No Portugal file connects a dealer name to a
billing account or to a purchase history, the same position the ITUK work reached: 16 of 44 UK names
matched exactly and roughly 20–26 did not. For Portugal nothing analogous has been attempted.

---

## 6. Earlier Portugal analysis already on disk

| File | What it is |
|---|---|
| `09_meetings\Imotors_Portugal_IDS_2026\ISZE_Imotors_H1_Parts_Analysis_Jul2026.xlsx` | H1 2026 vs H1 2025 ISZE → Portugal billing, 5,087 part numbers, plus 27-row category summary and top movers |
| `...\ISZE_Imotors_H1_Parts_Analysis_Jul2026_ITC.xlsx` | Same with the ITC layer |
| `09_meetings\PORTUGAL_Sales_Review_2026\ISZE_PORTUGAL_Q12026_Parts_Analysis.xlsx` | Q1 2026 parts analysis |
| `09_meetings\PORTUGAL_Sales_Review_2026\MINUTES_ISZE_Astara_Portugal_2026-07-29.md` / `.docx` | Meeting minutes |
| `09_meetings\PORTUGAL_Operating_Dashboard_2026\PORTUGAL_Operating_Dashboard.html` | Operating dashboard (1.3 MB, 17/09) + `OPEN_*.cmd` |
| `09_meetings\Preparation Meetings\Imotors_UMI_Sales_Study\` | Deep studies V2, V3, V3.1, V4 (html/xlsx/pdf/json) |
| `09_meetings\Preparation Meetings\DB_Sales_Order_Study\deep_v4\` | Imotors deep study V4 + `packs\PORTUGAL.json` |
| `01_data\08_Distributor\Imotors_Portugal_UIO_GPS_PMS_Study.xlsx` | The parc rebuild (§4) |
| `02_dashboards\pricing\ISZE_IAM_Quality_Positioning_Engine_IMOTORS.html` | Price positioning engine, Imotors |

---

## 7. What GPT already has, and what it does not

**Built and sitting on disk ready to upload:**

`08_gpt\atlas_pack_2026-09-20\` — 14 files (start-here, atlas concept, data inventory, platform and
access, readable data tables, dealer count and coverage, business context, custom instructions,
inventory CSV, machine-readable tables CSV 8.1 MB, dealer geography CSV, dealer scores CSV, upload
guide, review brief). **The car park is in here** as the table `trucks_in_service` (1,279 rows,
distributor × market × class × model type × year, source `ISUZU_UIO_Overview_2026.xlsx` sheet
`1.UIO Overview`), plus `trucks_in_service_light_share` (9 markets, Portugal 0.6364),
`measured_mileage_by_market_class`, the 519 IDS scores and the 564-row dealer geography.

`01_data\15_gpt_safe\gpt_pack_2026-09-20\` — billing ISZE → distributor (514,037 rows), warranty
(62,059 rows), **sales to dealer for all seven markets including Portugal** (334,182 rows),
GPS spend per truck, service-gap matrix, service capture by market and family, trucks-in-service
light share, wallet waterfall, part classification, genuine/BVP mix, network percentiles.
Confirmed by reading the file: POR**TUGAL 2025 = 21,636 rows, PORTUGAL 2026 = 15,789 rows.**

`01_data\15_gpt_safe\gpt_review_3_big_2026-09-20\` — pricing, parts family, aftersales ceiling and the
combined data tables.

`08_gpt\data-analysis-assistant.skill` and the other skill files.

**What is not confirmed:** whether the September packs have actually been uploaded.
`08_gpt\UPLOAD_STATUS.md` still records the last upload as **2026-05-12, v1.0 context pack**, and says
the next upload is due the first working Monday of the month. The packs on disk are newer than that
record. Whether they are inside the assistant is something only the assistant's file list can settle.

**What GPT does not have anywhere:** part numbers tied to a named Portugal dealer. It has Portugal at
national grain, and it has no per-dealer fleet for any market.

---

## 8. Stop line

Nothing was rebuilt, regenerated, moved or deleted to produce this page. Every file named above was
read as it stood. The two limits noted above — the 81% of Portugal's units that carry no service
category (§3), and the blank IDS city and address (§5) — are reported, not fixed.
