# EQ-HIT extract — priority CY2025 (SSOT)

**Status:** SUCCESS for this pass (brake_rotor + fuel_filter seeds) · 2026-09-05  
**Source:** `https://isuzu.snaponepc.com/epc/#/` global Part Number search  
**Output:** `01_data/00_derived/eqhit_extract_priority_cy2025.csv`  
**Schema:** playbook fitment grain (`pull_date`…`notes`) — one row per PN × catalogue edition  
**Skipped:** `oil_filter` / lubricants (per brief)

## Truth counts

| Metric | Value |
|--------|------:|
| Rows | **2311** |
| Unique PNs | **37** |
| Categories covered | clutch_disc · brake_shoe · brake_pad · clutch_pressure_plate · blower_filter · **brake_rotor** · **fuel_filter** |

Append path: `01_data/91_build/_append_eqhit_playbook.py` (+ `_append_eqhit_triples.py`).  
**Do not run** `_append_eqhit_extract.py` — collapses fitment grain.

## This pass — brake_rotor (8/8)

| PN | Fitment rows | EQ-HIT total | Status |
|----|-------------:|-------------:|--------|
| 8983767550 | 28 | 28 | ok |
| 8983767530 | 12 | 12 | ok |
| 8981919560 | 54 | 54 | ok |
| 8982488951 | 43 | 43 | ok |
| 8979488071 | 18 | 18 | ok |
| 8982488930 | 48 | 48 | ok |
| 8982488970 | 81 | 81 | ok |
| 8983767540 | 51 | 51 | ok |

## This pass — fuel_filter (8/8 seeds)

| PN | Fitment rows | EQ-HIT total | Status |
|----|-------------:|-------------:|--------|
| 8981596930 | 204 | 204 | ok |
| 8981941190 | 124 | 124 | ok |
| 8975425400 | 314 | 314 | ok |
| 8980374810 | 121 | 121 | ok |
| 5876150170 | 1 | 0 | partial — zero hits in EPC |
| 5876101570 | 1 | 0 | partial — zero hits in EPC |
| 1876102860 | 1 | 0 | partial — zero hits in EPC |
| 5876150240 | 1 | 0 | partial — zero hits in EPC |

## Still open (later)

- Oil/lubricants: **skip** (locked).
- Next ranking categories beyond rotor/fuel if Jerome asks.
- Session was still logged in (`Logout` visible) at end of this pass.

Engine codes: not in global search grid — blank in CSV.
