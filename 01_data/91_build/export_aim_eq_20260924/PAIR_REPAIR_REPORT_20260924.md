# AIM dated-pair repair — 2026-09-24

Author: cursor (pair repair). Scope: rebuild the 2026-09-24 dated pair from the live master, back up
both dated pairs, fix the launcher whose name and target disagreed. Nothing else was touched.

## 1. Starting state (measured before any change)

| File | Bytes | Last write |
|---|---|---|
| `aim_master_v2.csv` | 28,606,117 | 2026-09-24 16:20:54 |
| `aim_pn_classification_20260920.csv` | 24,925,134 | 2026-09-24 16:20:55 |
| `AIM_Master_PN_Categories_Figkey_20260921.csv` | 13,149,086 | 2026-09-24 16:21:05 |
| `AIM_Master_PN_Categories_Figkey_20260921.xlsx` | 9,291,457 | 2026-09-24 16:21:38 |
| `AIM_Master_PN_Categories_Figkey_20260924.csv` | 13,108,965 | 2026-09-24 14:09:23 |
| `AIM_Master_PN_Categories_Figkey_20260924.xlsx` | 9,272,663 | 2026-09-24 14:09:53 |
| `OPEN_AIM_Master_PN_Categories_Figkey_20260921.cmd` | 74 | 2026-09-24 16:22:44 |
| `OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd` | 74 | 2026-09-24 16:21:38 |

Master sha256 at start: `1870DC2AC08E8128C9323A5DA14AD46742BB1200F24D3D6FAA3ED53576B74AF4`

The brief's sizes for the 2026-09-24 pair (13,108,965 and 9,272,663) are confirmed. The brief's
sizes for the 2026-09-21 pair (13,149,086 and 9,291,457) are also confirmed.

## 2. Which pair carried the newest content

The **2026-09-21 pair**. Its write time (16:21:05 / 16:21:38) follows the master's (16:20:54), and
its content agrees with the master:

| Check | 2021 csv | 2024 csv | master |
|---|---|---|---|
| rows | 165,257 | 165,257 | 165,257 |
| `aim_level_1` blank | 140,109 | 140,295 | — |
| `aim_level_1` = `Unknown` | 3,653 | 4,321 | — |

What the parallel run actually changed (proved, not assumed). I diffed the classification overlay
against the copy committed in git (`5d6b98b3`, 2026-09-23) and found **1,008 part numbers that went
from blank or `Unknown` to a real family**. Their two dated pairs disagree:

| part number | newest pair (2021) | stale pair (2024) | master `aim_l1_fixed` |
|---|---|---|---|
| 1090300730 | Electrical | nan | Electrical |
| 1093370270 | Engine | Unknown | Engine |
| 1095890171 | Driveline Axle | nan | Driveline Axle |
| 1096254970 | Transmission | Engine | Transmission |
| 1096255760 | Engine | nan | Engine |
| 1097012360 | Engine | nan | Engine |
| 1097071570 | Intake Exhaust Emission | nan | Intake Exhaust Emission |
| 1097601191 | Transmission | nan | Transmission |
| 1098110022 | Clutch | Unknown | Clutch |
| 1098201170 | Clutch | Unknown | Clutch |
| 1099841410 | Steering | nan | Steering |
| 1099871410 | Cabin Interior | nan | Cabin Interior |
| 1125280060 | Engine | Suspension | Engine |
| 1136741600 | Cooling | Unknown | Cooling |
| 1312211360 | Clutch | nan | Clutch |
| 1313423350 | Clutch | Unknown | Clutch |

So the 2026-09-21 pair is the better of the two on content, and it still differs from the master on
at least one row (`1096254970`: Engine there, Transmission on the master). It was therefore a useful
fallback, not a substitute for rebuilding.

The cause of the wrong date is in the builder itself, read and confirmed rather than taken from the
brief: `01_data/91_build/export_aim_pn_categories_figkey_xlsx.py` line 17 sets
`STAMP = date.today().strftime('%Y%m%d')`. It derives the filename from today's date, so it writes a
`_20260924` name today. The parallel run at 16:20..16:21 did not use it as written: its
`apply.py` (lines 31-33) **hardcodes** the 2026-09-21 names into the module before calling it.
That is why the live master landed under a 21 September filename.

## 3. Re-check of the master before writing

Master at 16:26 and at the end of the run (16:32+):

* 28,606,117 bytes, 2026-09-24 16:20:54, sha256
  `1870DC2AC08E8128C9323A5DA14AD46742BB1200F24D3D6FAA3ED53576B74AF4` — unchanged.
* Overlay also unchanged: 24,925,134 bytes, 2026-09-24 16:20:55.

The master did not move during this run, so nothing of the other writer's was overwritten. The
master was read only; this task wrote no data file.

## 4. Backups taken (before any change)

Folder: `01_data\00_derived\_backup_20260924_pair_repair\`

`newest_content_2021_named\` (the pair that carried the newest content)
* `AIM_Master_PN_Categories_Figkey_20260921.csv` — 13,149,086 bytes, 16:21:05
* `AIM_Master_PN_Categories_Figkey_20260921.xlsx` — 9,291,457 bytes, 16:21:38
* `OPEN_AIM_Master_PN_Categories_Figkey_20260921.cmd` — 74 bytes

`stale_content_2024_named\` (the pair that carried the 14:09 content)
* `AIM_Master_PN_Categories_Figkey_20260924.csv` — 13,108,965 bytes, 14:09:23
* `AIM_Master_PN_Categories_Figkey_20260924.xlsx` — 9,272,663 bytes, 14:09:53
* `OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd` — 74 bytes

Both launchers were also backed up, so the broken text (74 bytes, pointing at the 2021 xlsx) is
recoverable.

## 5. Rebuild — rebuild, not copy

The builder was run as written:

```
python 01_data\91_build\export_aim_pn_categories_figkey_xlsx.py
```

It exited 0 and reported:

```
rows=165257 with_desc=33817 with_fig=161471 with_aim=25148
csv=...\AIM_Master_PN_Categories_Figkey_20260924.csv size_mb=13.15
xlsx=...\AIM_Master_PN_Categories_Figkey_20260924.xlsx size_mb=9.29
```

Python reports today as `20260924`, so `STAMP` behaved as the script says and produced the
2026-09-24 names. **It also rewrote the sibling `OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd`**
(the same script writes the launcher from `STAMP`, lines 312-317), and it wrote that launcher
correctly — pointing at the 2026-09-24 xlsx, two lines, CRLF. So the launcher was fixed as a
by-product of the rebuild and needed no hand edit.

The copy route in the brief was not needed, and was not used. Had it been needed it would have been
the weaker answer, because the 2026-09-21 pair already differed from the master on part number
`1096254970`.

The builder does not print the `Unknown` count or write a hash, so the checks below are mine.

## 6. Verification

**Rows.** master 165,257 / rebuilt CSV 2026-09-24 165,257 / rebuilt 2021 CSV 165,257. Identical.

**Spot check.** The 16 part numbers above, read from the rebuilt CSV and from the `AIM_PN` sheet of
the rebuilt Excel. All 16 print the same real family in both files, and the same value the master
holds in `aim_l1_fixed`. 16 of 16 pass. Full list of the 1,008 newly classified numbers:
`_pair_repair_newly_classified_20260924.txt` in this folder.

**Whole-file comparison.** The rebuilt 2026-09-24 CSV is 13,149,086 bytes and sha256
`2AF850571E5CEAE20E38D6B960DEEAC562EF8CCC2708BAC2988DD9C54D9A8B81` — byte-identical to the
2026-09-21 CSV. Both were built from the same live master and overlay by the same script, so
identical content is expected. The two Excel files are the same size but differ in bytes:
2026-09-24 sha256 `399D5EC78F1E7A7A0B8D261B7C85571DDB849E98F0A7EC984F6099774F359781` against
2026-09-21 `1DC529E3046B12D3AF918E6F3F83DE78B70C75B076AFCF1654704C99F49C2974` — openpyxl stamps
creation time into the workbook, so a byte difference there is not a content difference.

**Coverage sheet.** The rebuilt Excel reports `as_of = 20260924`, 165,257 part numbers, 33,817 with
a description, 161,471 with a figure key, 25,148 with `aim_level_1`, and names the CSV as
`AIM_Master_PN_Categories_Figkey_20260924.csv` — i.e. the Excel points at its own dated CSV.

**Left as-is.** 3,653 rows still print `Unknown` in `aim_level_1`. These were not touched: clearing
the marker is a separate decision already sitting with Jerome on the board (16:40 row).

**Launcher, bytes on disk.**

`OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd`, 74 bytes:

```
40 65 63 68 6F 20 6F 66 66 0D 0A 73 74 61 72 74 20 22 22 20 22 25 7E 64 70 30 41 49 4D 5F 4D 61 73 74 65 72 5F 50 4E 5F 43 61 74 65 67 6F 72 69 65 73 5F 46 69 67 6B 65 79 5F 32 30 32 36 30 39 32 34 2E 78 6C 73 78 22 0D 0A
```

Two lines. `40 65 63 68 6F 20 6F 66 66` = `@echo off`, `0D 0A` = CRLF, and the target string ends
`32 30 32 36 30 39 32 34` = `20260924`. Body is exactly the two required lines. Line endings are
CRLF, no trailing spaces, no BOM, no final line without a terminator.

`OPEN_AIM_Master_PN_Categories_Figkey_20260921.cmd`, 74 bytes: `@echo off` CRLF, then
`start "" "%~dp0AIM_Master_PN_Categories_Figkey_20260921.xlsx"` CRLF. It points at its own 2021 file
and was left alone.

**Master unchanged.** sha256 at the end of the run is
`1870DC2AC08E8128C9323A5DA14AD46742BB1200F24D3D6FAA3ED53576B74AF4`, identical to the start.

**Not verified.** The rebuilt Excel was read back row by row for the spot-check only; I did not
open it in Excel, so I cannot say what it looks like on screen. I did not run a diff of every one of
the 165,257 rows between the rebuilt pair and the master — the byte-level match against the 2021
pair, which was itself built from the same master, is the evidence used instead.

## 7. What should happen to the 2026-09-21 pair

Today that pair holds today's content under 21 September's name. Three options, with what each
costs:

1. **Leave it.** The newest content stays readable in the ISZE folder, and the `Pricing revision`
   copy still holds genuine 21 September content. The cost: two files with different dates and the
   same content, so the date in the filename stops meaning anything. That is the habit that
   produced this defect.
2. **Restore it** so the 2021 name goes back to the 21st's content, from the backup taken by the
   parallel run: `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260921.csv.bak_pre_export_aim_eq_20260924_20260924_142051`
   (13,093,140 bytes) and the matching `.xlsx` (9,281,799 bytes). That copy hashes identical to
   `Pricing revision\AIM_Master_PN_Categories_Figkey_20260921.csv` and its `.xlsx`, so there is a
   clean, unambiguous restore source. Cost: none to the live content, since the 2026-09-24 pair now
   carries it.
3. **Delete it.** Nothing else in `01_data` refers to it as a live input; its only dependent is its
   own launcher in this folder, plus one duplicate launcher under `Pricing revision\` and generated
   dashboards that recorded a source line. Cost: a date disappears.

**Recommendation: option 2, and stop writing the pair through a hardcoded filename.** The real fault
is not the stale date on a file, it is that a run today is allowed to publish today's numbers under
yesterday's name. The builder derives its name from the date, which is correct; the apply script
overrides that. Fix option 2 so the 21st's file says the 21st, then either let the apply script use
the builder's own names or have it take the target date as an explicit argument so a mismatch cannot
happen quietly. I have not acted on any of this.

## 8. Open items not established

* Why the 16:21 run wrote a 2026-09-21 pair at all. I can see the hardcoded names and their effect;
  the intent behind them is in that agent's brief, not in anything on disk I read.
* Whether the two `_20260924`-named launchers elsewhere (none found) or the duplicate launcher under
  `Pricing revision\` need the same treatment. The `Pricing revision` copy points at its own folder's
  2021 file and is consistent with itself; I left it alone.
* The 3,653 rows still marked `Unknown`, unchanged and still Jerome's call.
