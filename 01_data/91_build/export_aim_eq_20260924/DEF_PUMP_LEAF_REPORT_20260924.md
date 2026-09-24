# DEF Pump leaf correction — 7552710010

Date: 2026-09-24
Scope: one part, one cell. A shelf change inside one family, no family move, no money move.

## 1. Master state before the write (moved or not)

| Check | Value |
|---|---|
| Path | `01_data/00_derived/aim_master_v2.csv` |
| mtime | 2026-09-24 17:01:53 (matches the 17:01:53 the brief expected) |
| size | 28,611,807 bytes (matches the brief exactly) |
| sha256 before | `eaeb51bea3fe61b3af3ca7d0290f2e071bb480053c76b76198b26451b5a30283` |
| rows before | 165,289 |
| columns | 32, original order |

The master had **not** moved since 17:01:53. The 19-dashboard rebuild was already finished.

## 2. Leaf spelling, read off the master (not invented)

Distinct `aim_l3` values under `aim_l1 = 'Intake Exhaust Emission'` and `aim_l2 = 'DEF System'`:

| aim_l3 | rows |
|---|---|
| `DEF Tank` | 100 |
| `DEF Sensor` | 9 |
| `DEF Pump` | 5 |

Exactly **one** plausible spelling exists, so no choice was needed and no new leaf was created.

The five supporting parts on `DEF Pump`, with the value each carries:

| part_number | description | aim_l3 |
|---|---|---|
| 8975077751 | PUMP ASM; DEF,DCM SPLY | `DEF Pump` |
| 8978325590 | PUMP ASM; DEF,DCM SPLY | `DEF Pump` |
| 8978325591 | PUMP ASM; DEF,DCM SPLY | `DEF Pump` |
| 8982688120 | PUMP ASM; DEF,DCM SPLY | `DEF Pump` |
| 8982688122 | PUMP ASM; DEF,DCM SPLY | `DEF Pump` |

The target row before the write:

```
7552710010,PUMP KIT,Intake Exhaust Emission,DEF System,DEF Tank,,,,,,0,146-190,146,190,,export_aim_eq_20260924,1,0,0,0.0,0.0,Intake Exhaust Emission,DEF System,export_aim_eq_20260924,,,,,,,,
```

## 3. Backup

| Item | Value |
|---|---|
| Backup path | `01_data/00_derived/aim_master_v2.csv.bak_pre_def_pump_leaf_20260924_182731` |
| Backup size | 28,611,807 bytes |
| Backup sha256 | `eaeb51bea3fe61b3af3ca7d0290f2e071bb480053c76b76198b26451b5a30283` (identical to the pre-write master) |

## 4. The write

One row, one cell. The target row after the write:

```
7552710010,PUMP KIT,Intake Exhaust Emission,DEF System,DEF Pump,,,,,,0,146-190,146,190,,export_aim_eq_20260924,1,0,0,0.0,0.0,Intake Exhaust Emission,DEF System,export_aim_eq_20260924,,,,,,,,
```

`aim_l1`, `aim_l2` and every other column are untouched. `aim_source` was deliberately **not**
restamped, because the family-level decision did not change and restamping would have thrown away
the provenance of where the classification came from.

Write method: the frame was built in memory, written to a temporary file in the same folder, then
`os.replace()` moved it onto the live path, so no reader could see a half-written file.

| Master after | Value |
|---|---|
| size | 28,611,807 bytes (unchanged) |
| sha256 after | `0105a5c4ac93ad9f1d17f781f6fdd567a7f5a04f0897c6ad184aba585af9f6d1` |

## 5. Rebuild of the dated pair

Pre-rebuild copies of today's pair and its launcher were made first into
`01_data/00_derived/_backup_20260924_pair_before_def_pump/`
(csv 13,153,014 bytes sha256 `c43a23ac225891a6...`, xlsx 9,294,122 bytes sha256 `62975fc383e628fd...`).

The builder `01_data\91_build\export_aim_pn_categories_figkey_xlsx.py` was run as written. It derives
its names from today's date, so it wrote the 2026-09-24 pair and overwrote today's pair, which is the
intended behaviour. It reported `rows=165289 with_desc=33849 with_fig=161503 with_aim=25180`.

| Rebuilt file | Size | sha256 |
|---|---|---|
| `AIM_Master_PN_Categories_Figkey_20260924.csv` | 13,153,014 | `c6b1aaf36639e76bed386b98ac34981f558c9d61e81c5afdf54063e2ab94acb7` |
| `AIM_Master_PN_Categories_Figkey_20260924.xlsx` | 9,294,124 | `ffc2102d600260f2348c47ca7e151f0369fb08ed658d37327a30f602529566ac` |

The overlay `aim_pn_classification_20260920.csv` carries no row for 7552710010, so nothing masked the
master edit on the way through the builder. That was checked before the write, not assumed.

Launcher `01_data/00_derived/OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd` verified on disk:
74 bytes, `@echo off` + `start "" "%~dp0AIM_Master_PN_Categories_Figkey_20260924.xlsx"`, CRLF on both
lines, no bare LF. It points at the 2026-09-24 Excel.

## 6. Verification

| Check | Result |
|---|---|
| (a) master row count unchanged | PASS — 165,289 before and after |
| (b) exactly one row changed `aim_l3`; no other cell in any row changed | PASS — full cell-by-cell compare of all 165,290 rows (header included) and all 32 columns against the backup: **1 differing cell**, row 42843, column `aim_l3`, `DEF Tank` to `DEF Pump`. Row-length mismatches: 0 |
| (c) 7552710010 now reads the DEF Pump leaf | PASS — `Intake Exhaust Emission / DEF System / DEF Pump`, `aim_source` still `export_aim_eq_20260924` |
| (d) rebuilt csv and xlsx both show that leaf | PASS — csv `aim_level_3 = DEF Pump`; xlsx sheet `AIM_PN` `aim_level_3 = DEF Pump`; sheets `AIM_PN, Coverage, Description_sources` |
| (d2) rebuilt csv vs its pre-run backup | PASS — 1 differing cell only: row 23066, `aim_level_3`, `DEF Tank` to `DEF Pump`, part 7552710010 |
| (e) 2026-09-21 pair unchanged | PASS — csv sha256 `bed9c4a266aa2851...` and xlsx sha256 `8376812d5702a89f...`, both identical to the pre-run hashes |

## 7. What this changes, and what it does not

This is a **shelf change only**. No family changed. No money changed. `l12m_billed_eur` and `eur` for
this part are 0.0 and were not touched. Nothing was excluded, added or removed from the master.

## 8. Note for the next rebuild

The master builder does not read the master as an input, so this move is a direct edit on the master
and a full spine rebuild would drop it. Same open point the 17:35 orphan append raised.
