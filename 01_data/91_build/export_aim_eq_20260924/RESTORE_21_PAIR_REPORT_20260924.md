# Restore of the 2026-09-21 AIM export pair

Date: 2026-09-24. Agent: cursor (AIM 20260921 pair restore).

## Why this was needed

The pair `AIM_Master_PN_Categories_Figkey_20260921.csv` and `.xlsx` should hold the AIM
catalogue as it stood on 21 September. A script hardcodes those two 21 September filenames while
the builder names its output from the current date, so a run on 24 September at 16:21 wrote
today's content onto the 21 September names. The result: the 21 September name carried the 24th's
data, and a duplicate of today's content existed under two dates.

## 1. Starting state (measured before any change)

| File | Bytes | mtime | sha256 |
|---|---:|---|---|
| `AIM_Master_PN_Categories_Figkey_20260921.csv` | 13,149,086 | 2026-09-24 16:21:05 | `2AF850571E5CEAE20E38D6B960DEEAC562EF8CCC2708BAC2988DD9C54D9A8B81` |
| `AIM_Master_PN_Categories_Figkey_20260921.xlsx` | 9,291,457 | 2026-09-24 16:21:38 | `1DC529E3046B12D3AF918E6F3F83DE78B70C75B076AFCF1654704C99F49C2974` |
| `AIM_Master_PN_Categories_Figkey_20260921.csv.bak_pre_export_aim_eq_20260924_20260924_142051` | 13,093,140 | 2026-09-22 19:18:00 | `BED9C4A266AA2851C691BA564F92EDBC6723EE61CEC6BF261C199B3CB4F6A5FB` |
| `AIM_Master_PN_Categories_Figkey_20260921.xlsx.bak_pre_export_aim_eq_20260924_20260924_142051` | 9,281,799 | 2026-09-22 19:19:50 | `8376812D5702A89F08EC434678C708674AF45B0E1C09CC270E886A3E3125AC54` |

For reference, the 2026-09-24 pair at first measurement:

| File | Bytes | mtime | sha256 |
|---|---:|---|---|
| `AIM_Master_PN_Categories_Figkey_20260924.csv` | 13,149,086 | 2026-09-24 16:30:42 | `2AF850571E5CEAE20E38D6B960DEEAC562EF8CCC2708BAC2988DD9C54D9A8B81` |
| `AIM_Master_PN_Categories_Figkey_20260924.xlsx` | 9,291,457 | 2026-09-24 16:31:08 | `399D5EC78F1E7A7A0B8D261B7C85571DDB849E98F0A7EC984F6099774F359781` |

The size and hash point is already decisive: the 21 September CSV was byte-identical to the 24
September CSV (`2AF85057...`), which is what a same-content-under-two-dates mix-up looks like.
The backup's CSV hash is different (`BED9C4A2...`).

## 2. Confirmation the backup really is the older content

Not assumed. A full read-and-compare of every row by part number:

- Backup: 165,213 rows. Today's wrongly-named CSV: 165,257 rows.
- Rows whose family/group/type/label differed, or that were new: **2,579**.
- Spot-check of part numbers the backup left unclassified: the backup shows
  `Unknown|Unknown|Unknown` for `8983930170`, `8982263280`, `7551936010`, `8975065311`; today's
  file has a real family on each (`Driveline Axle|Axle Shaft|Drive Shaft`,
  `Intake Exhaust Emission|Emission Control|Catalyst`, `Engine|Mounting|Engine Mount`,
  `Cabin Interior|Seat|Seat Cushion`). Today's run did the classifying; the backup predates it.
- The backup is therefore the 21st's genuine content, as the task described.

## 3. Source used for the restore, and why

Two byte-identical sources exist:

- the pre-write backups in `01_data/00_derived/` (16:21 run's own safety copies), and
- `Pricing revision\AIM_Master_PN_Categories_Figkey_20260921.csv` / `.xlsx`.

Both hash `BED9C4A2...` (CSV) and `8376812D...` (XLSX). The `Pricing revision` copies were chosen
because they are **provably untouched**: mtime `2026-09-22 19:18:02` and `19:19:50`, two days
before today's incident. The backups share those very mtimes and sizes, but they live inside
`01_data/00_derived/`, the folder today's script writes into. Outside that folder nothing could
have rewritten them this morning, so the `Pricing revision` copy is the one with an unbroken
provenance. Bytes are what is being restored, and the two sources are the same bytes.

## 4. Preservation step (done before the restore)

Today's wrongly-named content was copied, byte for byte, to:

- `01_data/00_derived/_backup_20260924_pair_before_restore21/AIM_Master_PN_Categories_Figkey_20260921.csv`
  — 13,149,086 bytes, sha256 `2AF850571E5CEAE20E38D6B960DEEAC562EF8CCC2708BAC2988DD9C54D9A8B81`
- `01_data/00_derived/_backup_20260924_pair_before_restore21/AIM_Master_PN_Categories_Figkey_20260921.xlsx`
  — 9,291,457 bytes, sha256 `1DC529E3046B12D3AF918E6F3F83DE78B70C75B076AFCF1654704C99F49C2974`

Those two hashes equal the starting-state hashes of the pair, so the preserved copy is exactly what
was on disk before the restore.

## 5. The restore

Method: `[System.IO.File]::Copy` with overwrite — a raw byte copy. The CSV was not parsed or
reformatted, the XLSX was not opened in any library, no encoding or BOM was touched.

| File | Bytes after | mtime after | sha256 after | Matches source |
|---|---:|---|---|---|
| `AIM_Master_PN_Categories_Figkey_20260921.csv` | 13,093,140 | 2026-09-22 19:18:02 | `BED9C4A266AA2851C691BA564F92EDBC6723EE61CEC6BF261C199B3CB4F6A5FB` | yes, byte-identical |
| `AIM_Master_PN_Categories_Figkey_20260921.xlsx` | 9,281,799 | 2026-09-22 19:19:50 | `8376812D5702A89F08EC434678C708674AF45B0E1C09CC270E886A3E3125AC54` | yes, byte-identical |

Content spot-check after the restore (on the live 21 September file): `8983930170`,
`8982263280`, `7551936010`, `8975065311` are back to `Unknown|Unknown|Unknown`. Today's
classifications no longer sit on the 21 September name.

## 6. Launcher state

`01_data/00_derived/OPEN_AIM_Master_PN_Categories_Figkey_20260921.cmd` — 74 bytes, unchanged.
Content (exact):

```
@echo off
start "" "%~dp0AIM_Master_PN_Categories_Figkey_20260921.xlsx"
```

Line endings: CRLF on both lines (verified from the raw bytes: `0D 0A` after `echo off` and after
the `start` line). The launcher opens the 2026-09-21 XLSX, matching its own name. It was already
correct, so nothing was changed.

## 7. The 2026-09-24 pair — measured, not controlled

Another agent owns that pair. It was already at mtime `16:30:42` (CSV) and `16:31:08` (XLSX) when
I first measured it, before I restored anything. At my re-check after the restore its size, mtime
and hashes were unchanged from that first reading, so in my window it did not move again — but the
16:30/16:31 write was that agent's, not mine, and I cannot speak for what it does next. Its CSV
hash (`2AF85057...`) equals the preserved pre-restore 21 September CSV, which is consistent with
the pair-repair agent's own note that today's content is the same in both.

I did not read, write, or touch `_backup_20260924_pair_repair/`, `AIM_Master_PN_Categories_Figkey_20260924.*`,
the 20260924 launcher, `aim_master_v2.csv`, `aim_pn_classification_20260920.csv`, or any dashboard.

## 8. Verification summary

- (a) Restored CSV and XLSX hash identical to the source: **yes** (`BED9C4A2...`, `8376812D...`).
- (b) Launcher opens the file matching its own name: **yes** (2026-09-21 XLSX), CRLF confirmed.
- (c) The 21 September pair no longer carries today's classifications where the backup did not:
  **yes**, 2,579 rows reverted; spot-checks show `Unknown` again.
- (d) The preserved copy holds what was there before: **yes**, hashes equal the starting state.

## 9. Not verified / open

- I could not confirm *who* ran the 16:21 script or why; only that its output is dated today and
  sits under the 21 September name.
- The 2026-09-24 pair is outside my control; I report its measured state only.
- No other untouched 21 September copy was found outside `01_data/00_derived/` and `Pricing revision/`;
  the two are byte-identical in any case.
