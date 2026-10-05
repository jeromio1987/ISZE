# Backup and restore — section 3f reconciliation, 2026-09-22

This folder is the undo path for the **§3f reconciliation pass** made on the evening of
2026-09-22 against the hand-off pack at:

`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920\`

It is separate from the pack's own `.bak_before_v4_20260922` files, which belong to the v4 pass
and were not touched by this one.

## Files backed up, before and after

| File | Before (sha256, first 16) | After (sha256, first 16) | Bytes before → after |
|---|---|---|---|
| `00_READ_ME_FIRST.md` | `eeb18190b0fb3993` | `9a193f446619754a` | 45,163 → 57,757 |
| `01_BRIEF_FOR_THE_MODEL.md` | `e4ddeae56ad73983` | `8c0d04ea7969dad8` | 10,473 → 11,082 |
| `02_CORRECTION_LOG.md` | `ae8103974b96f7e2` | `022b2ef186fc5082` | 25,162 → 36,341 |
| `04_FILE_CATALOG.csv` | `7a0d310327b73b2a` | `c0bda488f6d627db` | 8,682 → 8,976 |

Full hashes are in `_before.json` and `_after.json`. The un-edited fifth document,
`03_EVIDENCE_OF_CORRECTION.md`, was **not** backed up and **not** changed (17,498 bytes, sha256
`751f334243573d95` — unchanged from the v4 pass).

## Line-ending convention preserved

The read-me is **CRLF**; the other three files are **LF**. Each file was written back with its own
convention, so the diffs stay readable. This was verified after the edit: the read-me has 434 CRLF
against 434 LF, and the other three have zero CRLF.

## Restore

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_pack_3f\restore.ps1"
```

Restores all four files from the copies in this folder and prints the sha256 of each restored
file. To restore one file only, pass its name:

```powershell
powershell -ExecutionPolicy Bypass -File "...\restore.ps1" -File 00_READ_ME_FIRST.md
```

To re-apply the correction after a restore, run the four apply scripts in this folder, in order — see
the script table below. `_apply_3f.py` writes the read-me and stops; `_apply_3f_b.py` writes the other
three; the two `_patch_*` scripts then tighten four cells in §3f. Running them against already-corrected
files will fail on their own assertions, which is intended — they are not idempotent, precisely so a
double-apply cannot go unnoticed.

## The restore was tested, not assumed

On 2026-09-22 the full round trip was run for real, on all four files:

1. `restore.ps1` restored all four from the copies here.
2. All four hashed back to their **before** values — `eeb18190b0fb3993`, `e4ddeae56ad73983`,
   `ae8103974b96f7e2`, `7a0d310327b73b2a`.
3. The four apply scripts ran in order.
4. All four hashed to their **after** values — `9a193f446619754a`, `8c0d04ea7969dad8`,
   `022b2ef186fc5082`, `c0bda488f6d627db`.

Both states were confirmed by hash. `_roundtrip.ps1` in this folder is that test; it prints
`ROUND_TRIP_OK` on success and exits non-zero on any mismatch. The pack was re-counted at 20 content
files afterwards.

## What this pass did not touch

- No data file in the pack was edited. The five-family euro total EUR 5,990,933 and every per-family
  euro reproduce exactly from the shipped files.
- No `build_*.py` was run.
- The five `.bak_before_v4_20260922` files in the pack root were left in place, unmoved and
  unmodified. They remain the v4 pass's undo path.
- The version label was not bumped; the pack remains v4, 2026-09-22.

## Scripts in this folder

| Script | What it does |
|---|---|
| `_backup.py` | Copies the four files here and writes `_before.json` with sha256 and byte counts. |
| `_apply_3f.py` | Applies the `00_READ_ME_FIRST.md` corrections (CRLF preserved), then stops. |
| `_apply_3f_b.py` | Applies the `01_BRIEF_FOR_THE_MODEL.md`, `02_CORRECTION_LOG.md` and `04_FILE_CATALOG.csv` corrections (LF preserved). |
| `_patch_3f_readme.py` | Three precision fixes to §3f made after reading the corrected section back: "sixteen a band" becomes "sixteen an EPC reference, seven of them a band"; the commercial paragraph no longer contradicts the table over whether a band-exclusive rotor exists; the route table's first column now reads as a row count with the banded count inside it. |
| `_patch_3f_readme_b.py` | One further §3f fix: the cross-reference counts are stated as reproducing under an undocumented definition (`genuine_pn` only) rather than as unsourceable. |
| `_verify.py` | Confirms the corrected cells are present, the withdrawn ones gone, the catalog parses, and the pack holds 20 content files. Writes `_after.json`. |
| `_roundtrip.ps1` | The tested undo-and-redo: restores all four, checks them against the before hashes, re-applies, checks them against the after hashes, prints `ROUND_TRIP_OK`. |
| `restore.ps1` | Restores from this folder. |

**Re-applying in full after a restore** is four commands, in this order:

```powershell
python "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_pack_3f\_apply_3f.py"
python "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_pack_3f\_apply_3f_b.py"
python "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_pack_3f\_patch_3f_readme.py"
python "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_pack_3f\_patch_3f_readme_b.py"
```

The working notes that produced the corrected figures are `_tmp_pack_3f_reconcile_20260922.py`,
`_tmp_pack_3f_reconcile2_20260922.py`, `_tmp_pack_3f_detail_20260922.py`,
`_tmp_pack_3f_checks_20260922.py`, `_tmp_pack_3f_final_20260922.py` and
`_tmp_pack_3f_last_20260922.py` in `01_data\90_INBOX\`.

