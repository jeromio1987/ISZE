# DATA_INTEGRITY — ITUK operating dashboard

**TARGET_DB** ITUK · sold_to **[2575]** · Isuzu Truck UK · United Kingdom · CV
**AS_OF** 2026-08-19 · **audience** ISZE internal
Holes for **this distributor only**. Nothing copied from UMI, IUK, Ireland, or any other pack.

## PMS capture audit (complete CY, this sold-to)

- File: `pms_capture_by_db_year.csv`
- Filter: `distributor_code == 'ITUK' AND line_type == 'total' AND year == 2025`
- sold_to SAP: **[2575]**
- expected qty: **75337.1**
- sold qty (actual): **49651.0**
- capture %: **49651.0 sold ÷ 75337.1 expected = 65.91%**
- network: 282796.0 sold ÷ 996890.1 expected = 28.3678%
- Ireland sold-to 76 in this slice? **True** (True = Ireland is NOT in this pack)
- ITUK sold-to 2575 in this slice? **False** (True = ITUK is NOT in this pack)

## BVP mix audit (whole book — not the paired basket)

- BVP €148950.85 / 59 PNs of book €5575757.47 / 3809 PNs = 2.67%
- Genuine: €5426806.62 / 3750 PNs
- BVP: €148950.85 / 59 PNs
- Book: €5575757.47 / 3809 PNs
- Definition: part_number in genuine_bvp_crossref.bvp_pn · complete CY · credits out · whole book
- Paired-basket trap (do **not** show as mix): 15.3% BVP on 18.5% of book euros

## GPS publish rules

- Skip incomplete: FY2023 — FY2023 is a partial year. It is not published — a partial bar would be read as growth.
- Publish years: [2024, 2025, 2026]
- CY GPS% toggle: **off**. The locked GPS workbook is fiscal-year only. No published calendar-year GPS% exists for this distributor. A CY GPS% will not be invented from the wallet file (different rate, different basket).

## Open issues on the dashboard

| Lane | n | Source |
|---|---|---|
| Mail | 7 | Open items from mail |
| Minutes / follow-ups | 5 | IML / ITUK follow-ups (no named minutes folder) |

## Holes that belong to this distributor

### 1. No fiscal GPS % series in the locked workbook

This distributor sits on the Dashboard row only (V4 as-presented). The GPS room shows euros and the locked FY27 figures. Nothing is synthesised.

### 2. Two PMS lanes — do not swap them in an ITUK/IML meeting

This room is the network league (same expected-qty model as the other 17). The IML/ITUK signed-off lane is 35.9% cover / EUR 2 038 471 gap on DVLA 22389 at 1.25× filters (oil filter 35.1%). Do not show both as the capture rate.

- Network league on this dashboard: capture 65.91% vs network 28.37%.
- IML signed-off lane: cover 35.9% · oil filter 35.1% · gap EUR 2038471 · DVLA UIO 22389.

### Shared bans (apply here, not copied numbers)

- Do not read the AutoDoc risk file (GBP 2.00 placeholder as a competitor price).
- Do not read the partial-year PMS-by-DB summary (calendar 2026 vs a full-year expected).
- Do not load raw sales workbooks into this pack.
- Three lost-sales lanes are never added.
- UMI 1797 is not UTI 1799. Turkey and MIDI are not ISZE distributors.

Generated from the ITUK ledger. Do not paste another distributor's pings into this file.
