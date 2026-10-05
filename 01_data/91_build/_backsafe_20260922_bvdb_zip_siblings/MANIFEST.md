# Backup + change manifest — BVDB delivery zip and three sibling files

**Created:** 2026-09-22, late evening session
**Folder:** `01_data\91_build\_backsafe_20260922_bvdb_zip_siblings\`
**Workspace root:** `C:\Users\jerom\Desktop\claude\ISZE`
**Extends:** `01_data\91_build\_backsafe_20260922_partial_year\` (the earlier pass, untouched)

Everything below is reversible. The originals are in `.\original\`, byte-for-byte, and
`.\restore.ps1` puts any one of them back and verifies the hash. The restore was exercised for
real: a file was deliberately corrupted, restored, and the hash confirmed against `_before.json`.

---

## The delivery zip

| | Original | Corrected |
|---|---|---|
| File | `09_meetings\BVDB_PBI_Data_Upload_2026-09-23.zip` | `09_meetings\BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip` |
| Bytes | 402,816 | 410,550 |
| Members | 28 | 28 |
| Member layout | flat, no wrapper folder | flat, matching |
| Written | 2026-09-22 20:10 | 2026-09-22 21:38 |
| sha256 | `ffc74d1b5b8c1eac…` | `f11155380a46addf…` |

**The original was not overwritten.** A new file was written beside it, named so the correction
is visible and it sorts next to the original. The build script asserts the original's hash before
and after and reports `original_zip_untouched`.

Inside the corrected archive, read from the archive rather than the folder:

- `02_GPS/gps_spu_by_distributor.csv` — **21 columns**, `period_basis` and `coverage_note` present;
  2026 rows carry **0** capture percentages and **22** `unknown` traffic lights.
- `02_GPS/gps_spu_by_family.csv` — **11 columns**, `period_basis` present, 306 2026 rows annotated.
- `02_GPS/gps_spu_pms.csv` — **11 columns**, `period_basis` present, 504 2026 rows annotated.
- `03_PMS/pms_opportunity_matrix.csv` — **17 columns**; `period_basis`, `coverage_note`,
  `year_coverage_pct` and `gap_eur_like_for_like` present. Every one of the 13 pre-existing
  columns is text-identical to the original; `gap_eur_like_for_like` equals `revenue_gap_eur` on
  all 756 full-year rows.
- `00_START_HERE/HOW_TO.md` — part-year caveat, the non-parts exclusion note, and the category-gap
  note in section 6.
- `00_START_HERE/_pack_meta.json` — 28 members, 400.9 KB, 23 data files.

Member-by-member diff against the original: **7 changed, 21 identical, none added, none removed.**

---

## Files changed

| # | File | Reason |
|---|------|--------|
| 1 | `09_meetings\BVDB_PBI_Data_Upload_2026-09-23.zip` | **NOT changed.** Kept as the dated record of what was built at 20:10. |
| 2 | `09_meetings\BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip` | **New.** Corrected hand-over archive. |
| 3 | `01_data\00_derived\gps_spu_by_family.csv` | Added `period_basis` / `coverage_note`. `spu_eur` deliberately untouched. |
| 4 | `01_data\00_derived\gps_spu_pms.csv` | Same. |
| 5 | `09_meetings\…\02_GPS\gps_spu_by_family.csv` | Pack copy of #3. |
| 6 | `09_meetings\…\02_GPS\gps_spu_pms.csv` | Pack copy of #4. |
| 7 | `09_meetings\…\00_START_HERE\MANIFEST.csv` | cols 9→11 on the two GPS rows; purposes now say the 8-month rate is correct and to filter `period_basis`. |
| 8 | `09_meetings\…\00_START_HERE\HOW_TO.md` | Disclosure: family / PMS / AIM period basis added to the top caveat and to section 5. |
| 9 | `09_meetings\…\00_START_HERE\_pack_meta.json` | Real member count (28) and size (393.2 KB) instead of 23 / 388.2. |
| 10 | `03_analytics\Isuzu\prism\scripts\build_bvp_p4_p5.py` | **Builder patch.** Emits the two columns on the family and PMS slices. |
| 11 | `03_analytics\Isuzu\prism\scripts\build_aim_gps_matrix.py` | Docstring only. Records the part-year re-check and why the labels are left alone. |
| 12 | `01_data\00_derived\_data_integrity_open_issues.md` | New `SPU-PARTIAL-SIBLINGS` and `SPU-PARTIAL-GAP` entries, both closed. |
| 13 | `01_data\00_derived\pms_opportunity_matrix.csv` | Builder rebuild: 4 columns added. All 13 pre-existing columns text-identical. |
| 14 | `09_meetings\…\03_PMS\pms_opportunity_matrix.csv` | Pack copy of #13. |
| 15 | `03_analytics\Isuzu\prism\scripts\build_pms_opportunity_matrix.py` | **Builder patch.** Emits the four columns; refuses to write if a full-year row moves; gains `--out` / `--compare-to`. |

### Deliberately NOT changed

- `01_data\00_derived\aim_gps_matrix.csv`, `.parquet`, and the pack copy — the 2026 quadrant labels
  are sound. Evidence: within-year medians on both axes, and scaling the GPS axis ×8/12 and ×12/8
  leaves all six 2026 `priority_target` markets unchanged. So does scaling **both** axes.
- `revenue_gap_eur` on every row of the opportunity matrix — it is the honest gap against the year's
  full expectation. The like-for-like comparator was **added beside it**, not substituted for it.
- `09_meetings\_build_bvdb_pbi_pack_20260923.py` — the reason the pack lost the two columns is that
  it copies files wholesale; once the source files carry the columns the pack carries them too. No
  change was needed, and changing it was not asked for.
- `wallet_waterfall.csv` and everything in the lost-sales / pricing chain — locked.
- `verification_fixtures.yaml`, `modules\freshness.py`, `modules\schema_guard.py`,
  `scripts\verify_derived_pipeline.py` — read only.
- `03_analytics\Isuzu\prism\data\uio_ld_n35_share.csv` — not touched.

---

## Restore

One file:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_bvdb_zip_siblings\restore.ps1" `
  -File "01_data/00_derived/gps_spu_by_family.csv"
```

Everything in this set:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_bvdb_zip_siblings\restore.ps1"
```

Check without writing, and verify the current state:

```powershell
...\restore.ps1 -WhatIf
...\restore.ps1 -Verify
```

`-Verify` exits non-zero if any file differs from its recorded original. Result at the end of this
session: **12 changed, 6 matching, 0 failed** — the 12 being the files edited here. The restore was
exercised for real after the set grew to 18 files: a file was corrupted, restored, and the hash
confirmed.

To reverse the zip work specifically: restore the pack files and the two source files, then delete
the corrected archive. The original zip never needs restoring, because it was never written to.

---

## Why a splice and not a rebuild

`build_bvp_p4_p5.py` round-trips its whole output through pandas, which re-renders existing float
cells at one unit in the last place. The earlier pass measured this: `195.14028776978415` became
`195.14028776978412` in four 2023–2024 cells. Task 3 requires the pre-2026 rows to stay
byte-identical, so `_add_period_columns.py` keeps every original byte and appends only the two new
fields, preserving the CRLF endings, the absence of a BOM and the trailing newline.

**The byte-identity is therefore achieved by the splice, not by the builder alone.** The proof used
here is a strip round-trip: remove the two new columns from the changed file and the result is
byte-identical to the backup — 84,615 and 140,895 bytes respectively, exact.

`_add_period_columns.py` is safe to re-run; it refuses to write if a single line's prefix would
change.

---

## Helper scripts in this folder

| File | Purpose |
|------|---------|
| `restore.ps1` | Put files back, with `-File`, `-WhatIf` and `-Verify`. |
| `_take_backup.py` | Byte-for-byte backup into `.\original\`, plus `_before.json`. |
| `_build_corrected_zip.py` | First zip build; refreshes MANIFEST and `_pack_meta.json`. |
| `_refresh_pack_and_rezip.py` | Copies the two corrected files into the pack, refreshes the manifest, rebuilds the zip. |
| `_add_period_columns.py` | The two-column splice for the family and PMS files, with `--dry-run`. |
| `_add_opportunity_columns.py` | The five-column splice variant for the opportunity matrix. **Superseded in practice** — the adopted change came from the patched builder instead, because rebuilding plus a full text comparison is a stronger proof than splicing. Kept because it refuses to write if a full-year row would move. |
| `_adopt_opportunity.py` | Rebuilds, asserts every old column is text-identical and no full-year row moved, then adopts the result. |
| `_test_opportunity_rebuild.py` | Per-year numeric comparison of a rebuild against the live file. |
| `_test_opportunity_bytewise.py` | Strict text comparison — numeric equality is not enough. |
| `_probe5_gap_magnitude.py` | First, **wrong**, attempt at the gap. It scaled a difference instead of a level. Kept as a record of the error, not as evidence. |
| `_probe6_gap_correct.py` | The corrected magnitude: €21.98M printed vs €13.45M like-for-like for 2026. |
| `_probe7_identity.py` | Tests an algebraic shortcut that turned out to be inexact (±€40 on `capture_rate` rounding), which is why the like-for-like comes from the builder and not from the published file. |
| `_zip_probe.py` | Reads every member of a zip and re-reads the GPS file **from the archive**. |
| `_zip_diff.py` | Member-by-member archive diff, normalising the wrapper-folder difference. |
| `_zip_matches_folder.py` | Proves the archive is a faithful copy of the folder, member by member. |
| `_sibling_evidence.py`, `_probe2.py`, `_probe3.py` | Read-only evidence behind the sibling decisions. |
| `_verify_siblings.py` | Strip round-trip identity, schema, and the in-zip state. |
| `_final_state.py` | Per-file final state against the right reference. |
| `_test_builder_patch.py` | Proves the patched builder emits the same columns and the same wording. |
| `_test_restore.py` | The real restore round-trip. |
| `_verifier_roundtrip.py` | Snapshots the verifier outputs before and after, and diffs check statuses. |
| `_show_checks.py` | Prints the schema and GPS checks from the report. |
| `_zip_build_log.json` | Every zip build, with hashes and the original-untouched assertion. |
| `_before.json` | sha256 of every original. |
| `verifier_before\`, `verifier_after\` | The three verifier outputs either side of the check run. |

---

## Verification summary

`python scripts/verify_derived_pipeline.py` from `03_analytics\Isuzu\prism`:

```
Verification: 164 pass, 1 warn, 0 fail
```

- **1 warn:** `uio_year.historical_gaps` — DENMARK 2012 and 2013 holes in the workbook, left
  unfilled. Pre-existing and unrelated.
- **No check changed status.** 165 checks before and after, none added, none removed.
- `schema.gps_spu_by_distributor.csv`: all 10 declared columns present, 21 in the file — the
  21-column schema is intact.
- The report says `ok: true`. That is not being used as evidence for any figure; it is reported
  because the brief asked for the summary line and every non-pass check.

The full pipeline was **not** run.
