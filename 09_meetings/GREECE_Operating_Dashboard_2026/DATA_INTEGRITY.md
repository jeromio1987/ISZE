# DATA_INTEGRITY — GREECE operating dashboard

**TARGET_DB** GREECE · sold_to **[66]** · Petros Petropoulos · Greece · MIXED
**AS_OF** 2026-08-19 · **audience** ISZE internal
Holes for **this distributor only**. Nothing copied from UMI, IUK, Ireland, or any other pack.

## PMS capture audit (complete CY, this sold-to)

- File: `pms_capture_by_db_year.csv`
- Filter: `distributor_code == 'GREECE' AND line_type == 'total' AND year == 2025`
- sold_to SAP: **[66]**
- expected qty: **24390.9**
- sold qty (actual): **9824.0**
- capture %: **9824.0 sold ÷ 24390.9 expected = 40.28%**
- network: 282796.0 sold ÷ 996890.1 expected = 28.3678%
- Ireland sold-to 76 in this slice? **True** (True = Ireland is NOT in this pack)
- ITUK sold-to 2575 in this slice? **True** (True = ITUK is NOT in this pack)

## BVP mix audit (whole book — not the paired basket)

- BVP €40665.05 / 49 PNs of book €523358.45 / 2545 PNs = 7.77%
- Genuine: €482693.4 / 2496 PNs
- BVP: €40665.05 / 49 PNs
- Book: €523358.45 / 2545 PNs
- Definition: part_number in genuine_bvp_crossref.bvp_pn · complete CY · credits out · whole book
- Paired-basket trap (do **not** show as mix): 43.3% BVP on 20.7% of book euros

## GPS publish rules

- Skip incomplete: FY2023 — FY2023 is a partial year. It is not published — a partial bar would be read as growth.
- Publish years: [2024, 2025, 2026]
- CY GPS% toggle: **off**. The locked GPS workbook is fiscal-year only. No published calendar-year GPS% exists for this distributor. A CY GPS% will not be invented from the wallet file (different rate, different basket).

## Open issues on the dashboard

| Lane | n | Source |
|---|---|---|
| Mail | 5 | Business review 6 August 2026 |
| Minutes / follow-ups | 2 | Review follow-ups |

## Holes that belong to this distributor

### 1. Billing name on the GPS extract is not South Africa

Sold-to 66 is Petros. The GPS extract still labels that payer with an RSA tag. Never join warranty or GPS files on that name — it collides with Norway. This pack filters sold-to 66 only.

### 2. Dealer-standard OS is visit triage, not a sales forecast

v0.4 hit list has 12 dealers. Do not claim a higher dealer-standard score moves GPS or PMS.

### Shared bans (apply here, not copied numbers)

- Do not read the AutoDoc risk file (GBP 2.00 placeholder as a competitor price).
- Do not read the partial-year PMS-by-DB summary (calendar 2026 vs a full-year expected).
- Do not load raw sales workbooks into this pack.
- Three lost-sales lanes are never added.
- UMI 1797 is not UTI 1799. Turkey and MIDI are not ISZE distributors.

Generated from the GREECE ledger. Do not paste another distributor's pings into this file.
