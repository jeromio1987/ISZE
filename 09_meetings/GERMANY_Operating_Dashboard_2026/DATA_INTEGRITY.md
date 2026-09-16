# DATA_INTEGRITY — GERMANY operating dashboard

**TARGET_DB** GERMANY · sold_to **[2516, 601]** · Isuzu Sales Deutschland · Germany · MIXED
**AS_OF** 2026-08-14 · **audience** ISZE internal
Holes for **this distributor only**. Nothing copied from UMI, IUK, Ireland, or any other pack.

## PMS capture audit (complete CY, this sold-to)

- File: `pms_capture_by_db_year.csv`
- Filter: `distributor_code == 'GERMANY' AND line_type == 'total' AND year == 2025`
- sold_to SAP: **[2516, 601]**
- expected qty: **87898.3**
- sold qty (actual): **12259.0**
- capture %: **12259.0 sold ÷ 87898.3 expected = 13.95%**
- network: 282796.0 sold ÷ 996890.1 expected = 28.3678%
- Ireland sold-to 76 in this slice? **True** (True = Ireland is NOT in this pack)
- ITUK sold-to 2575 in this slice? **True** (True = ITUK is NOT in this pack)

## BVP mix audit (whole book — not the paired basket)

- BVP €17796.68 / 28 PNs of book €2543905.15 / 4129 PNs = 0.7%
- Genuine: €2526108.47 / 4101 PNs
- BVP: €17796.68 / 28 PNs
- Book: €2543905.15 / 4129 PNs
- Definition: part_number in genuine_bvp_crossref.bvp_pn · complete CY · credits out · whole book
- Paired-basket trap (do **not** show as mix): 26.4% BVP on 7.9% of book euros

## GPS publish rules

- Skip incomplete: FY2023 — FY2023 is a partial year. It is not published — a partial bar would be read as growth.
- Publish years: [2024, 2025, 2026]
- CY GPS% toggle: **off**. The locked GPS workbook is fiscal-year only. No published calendar-year GPS% exists for this distributor. A CY GPS% will not be invented from the wallet file (different rate, different basket).

## Open issues on the dashboard

| Lane | n | Source |
|---|---|---|
| Mail | 4 | ISD / Sebastian Müller / Fabian Thiel (astara.com, isuzu-sales.de). Not Harris Ireland. |
| Minutes / follow-ups | 6 | ISD business review 5 Aug 2026 |

## Holes that belong to this distributor

### 1. No dealer-standard pack

No IDS country pack for this distributor.

### 2. Sales-to-dealer is not on file as a filed series

The #1 ask stands. Do not treat another distributor's extract as this one.

### Shared bans (apply here, not copied numbers)

- Do not read the AutoDoc risk file (GBP 2.00 placeholder as a competitor price).
- Do not read the partial-year PMS-by-DB summary (calendar 2026 vs a full-year expected).
- Do not load raw sales workbooks into this pack.
- Three lost-sales lanes are never added.
- UMI 1797 is not UTI 1799. Turkey and MIDI are not ISZE distributors.

Generated from the GERMANY ledger. Do not paste another distributor's pings into this file.
