# Backup + change manifest — partial-year (SPU-PARTIAL) correction

**Created:** 2026-09-22, afternoon/evening session
**Folder:** `01_data\91_build\_backsafe_20260922_partial_year\`
**Workspace root:** `C:\Users\jerom\Desktop\claude\ISZE`

Everything below is reversible. The originals are in `.\original\`, byte-for-byte, and
`.\restore.ps1` puts any one of them back and verifies the hash.

---

## Restore commands

One file:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_partial_year\restore.ps1" `
  -File "01_data/00_derived/gps_spu_by_distributor.csv"
```

Everything in this set:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_partial_year\restore.ps1"
```

Check without writing, and verify what is on disk now:

```powershell
...\restore.ps1 -WhatIf
...\restore.ps1 -Verify
```

`-Verify` exits non-zero if any file differs from its recorded original.

---

## Files changed

| # | File | sha256 before | sha256 after | Reason |
|---|------|---------------|--------------|--------|
| 1 | `03_analytics/Isuzu/prism/scripts/enrich_gps_spu_v9.py` | `802eee392c7f5730…` | `ec338298c510dd30…` | Task 2 — partial-year guard in the writer, so a part-year numerator is never divided by a full-year target, plus a refusal to write if any partial-year row still carries a percentage or a colour. |
| 2 | `01_data/00_derived/gps_spu_by_distributor.csv` | `0bdb8a2623e8adb1…` | `01293886b10f1f59…` | Task 3 — builder output with the four derived columns blank/unknown on 22 partial-year rows. 2023–2025 left byte-identical (see the splice note below). |
| 3 | `01_data/15_gpt_safe/gps_spu_by_distributor.csv` | `2170d9c2aa02ff16…` | `c27fced51e010d42…` | Task 3 — re-annotated (`period_basis`, `coverage_note` added) then contained: 18 capture cells blanked, 18 light cells `unknown`. |
| 4 | `03_analytics/Isuzu/prism/evidence-app/data/derived/gps_spu_by_distributor.csv` | `f5d59a6e350c1116…` | `1f3e6043e15edbb7…` | Task 3 — same as #3. |
| 5 | `09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/gps_spu_by_distributor.csv` | `eb95f18c6ac42869…` | `16a051fb3b6d3c64…` | Task 3 — same as #3; this is the copy that goes into the hand-over zip. |
| 6 | `09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/HOW_TO.md` | `36885181a4eb7795…` | `373f253345fcfffe…` | Task 5 — plain period-basis disclosure, a `period_basis` note on the relationship and refresh sections, the like-for-like instruction on visual 2, a full-years-only DAX filter, and the non-parts exclusion note. |
| 7 | `09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/MANIFEST.csv` | `08257b8c08a406f1…` | `f3690da38c836c79…` | Task 5 — period-basis note on the GPS, PMS and AIM rows; `period_basis` added to the GPS join keys; column count 19 → 21. |
| 8 | `01_data/00_derived/network_percentile.csv` | `89eb2100168a3c75…` | unchanged | Task 4 — backed up for reversibility, **not changed** (see the decision below). |
| 9 | `01_data/00_derived/aim_gps_matrix.csv` | `4f8a42c83917dac2…` | unchanged | Task 4 — backed up for reversibility, **not changed**. |

Full 64-character hashes for every file: `_before.json` (original state) and `_after.json`
(final state). Those two files are the machine-readable version of this table.

**Timestamp of the change:** 2026-09-22, between 20:10 and 21:0x local. Each file's mtime on
disk is the authoritative record.

---

## Task 4 decision — the `2026 UNMAPPED` row

**Decision: the exclusion is correct on the merits and the row was NOT reinstated. Disclosure
was added instead, in `HOW_TO.md` and in the pack's `dim_distributor.csv` note.**

**Why.** The EUR 178,452.56 was four billing lines, all non-parts: three service-fee payments on
sold-to 146 and one payment of EUR 160,492.56 on sold-to 373, plus a EUR 360 demurrage line —
EUR 160,492.56 + 2 × EUR 8,800 + EUR 360. The pack's own `01_UIO/dim_distributor.csv` already
classifies sold-to 146, 373 and 2970 as `excluded_non_parts` ("Non-parts billing only (service fee
/ demurrage) — audit Check 1 exclusion"). A parts-spend measure should not carry them, so
reinstating the row would put non-parts money back into a parts measure. That is the opposite of
correct.

**What the earlier report got wrong, and I verified rather than followed.** The brief states that
deleting the row moved four published percentiles and IUK's 2026 `gps_spu` percentile from 11.76 to
27.45. **It did not.** Holding the raw values constant and toggling only the row:

- The `UNMAPPED` row's own `gps_spu` was blank (`raw_value` empty), so it did not enter the ranking.
- Percentile is computed over non-null values only, so the pool size stayed 18 and no market's rank
  changed.
- 2026 `network_median` is **EUR 119.9965 with the row and EUR 119.9965 without it**;
  `n_distributors` is 18 either way.

**No percentile moved when the row was dropped. Zero markets.**

**What did move them, and this is the real finding:** the 2026 figures were rebuilt on 21 September
on a longer billing window. IUK's `spend_per_unit_eur` went from **EUR 33.51 to EUR 82.24** (still
a part-year rate), and the 2026 median from **EUR 48.35** (as committed) to **EUR 119.9965** (now).
Recomputing the percentile from each vintage of the GPS file with the builder's own formula gives
IUK **11.76 → 11.76** (unchanged) and HUNGARY **5.88 → 0.00**, GREECE **0.00 → 5.88**. Those two
swaps are the 21-Sep sales rebuild, not the row deletion.

So the honest position is: the euro left the parts base **correctly**, and the only defect was that
it left silently — no note told a reader the scope excludes non-parts payments. That is what was
fixed.

---

## Files backing up things I ran, not things I changed

`.\rewritten_by_checks\` holds the three verification outputs as they stood **before** I ran
`verify_derived_pipeline.py`, so a check run is reversible too:

- `01_data/00_derived/_verification_report.json`
- `01_data/00_derived/_verification_report.md`
- `01_data/00_derived/metrics_snapshot.json`

`metrics_snapshot.json` was not modified by the check run (hash identical before and after). The
two report files were rewritten; their content is equivalent (164 pass / 1 warn / 0 fail before and
after, no check added, removed or changed status).

---

## The splice on file #2, and why the older years are byte-identical

The builder round-trips the whole file through pandas. That silently re-renders four
`spend_per_unit_eur` cells in 2023–2024 at **one unit in the last place** (about 2.8 × 10⁻¹⁴) —
`195.14028776978415` became `195.14028776978412`, and three others like it. The value does not
change and nothing downstream reads it differently, but the text does, and Task 6 asks for
2023–2025 to be byte-identical.

So after the builder ran, `_splice_untouched_years.py` kept the original bytes for every non-2026
line and took only the 22 useful 2026 lines from the builder's output. It refuses to write unless
the values are unchanged (tolerance 1 × 10⁻¹²). Result: **2023–2025 byte-identical to the backup,
and the 2026 rows carry the guard.**

This means the byte-identity is achieved by the splice, **not** by the builder on its own. If the
builder is run again, those four cells drift again and the splice has to be re-run to restore them.
`_splice_untouched_years.py` is safe to re-run at any time.

---

## Guards proven, not assumed

- `_test_guard.py` — the refusal fires on a partial row carrying `gps_capture_vs_max`, on one
  carrying a `traffic_light_v9` colour, and on one carrying `gps_capture_ex_warranty_vs_max`; a
  clean partial row passes, and a full-year row carrying a capture % is untouched.
- `_verify_builder_result.py` — 2026 blank/unknown, annotated, and 2023–2025 byte-identical.
- `_verify_copies.py` — for all three copies: annotation added, 2026 blank/unknown, every
  non-derived column and every protected column unchanged, no row added or removed, encoding intact.
- Restore round-trip exercised for real: the pack copy was restored, confirmed back at its original
  hash with the false numbers and 19 columns, then re-contained.

---

## Not done, and flagged rather than forced

1. **The hand-over zip still contains the uncorrected GPS file and the old `HOW_TO.md`.**
   `09_meetings\BVDB_PBI_Data_Upload_2026-09-23.zip` was last written 2026-09-22 20:10. Its members
   are still `02_GPS/gps_spu_by_distributor.csv` at `eb95f18c6ac42869` (19 columns, the false
   numbers) and `HOW_TO.md` at `36885181a4eb7795` (no disclosure). Re-zipping would overwrite a
   dated hand-over artefact, so I have not done it. **A fresh zip is needed before anything is
   handed over.**
2. **`gps_spu_by_family.csv` and `gps_spu_pms.csv` still carry a part-year 2026 `spu_eur` with no
   period column.** The same class of defect, left alone as out of scope.
3. **`aim_gps_matrix.csv` still describes the part year as an ordinary year** — it carries
   `year_coverage_pct` = 0.6658 and `is_partial_year` = True, but its `quadrant_label` column is
   computed as if 2026 were complete. The pack's own `HOW_TO.md` now warns generally, but the file
   is not corrected and the pack ZIP `_pack_meta.json` still lists 23 files / 388.2 KB while the zip
   is 28 members / ~394 KB.

---

## What was NOT touched, by rule

- `wallet_waterfall.csv` and every pricing deliverable — locked, untouched.
- `run_pipeline_and_verify.ps1` — never run. Only `enrich_gps_spu_v9.py` and
  `verify_derived_pipeline.py`.
- `verification_fixtures.yaml`, `modules\freshness.py`, `modules\schema_guard.py`,
  `scripts\verify_derived_pipeline.py` — read only, not edited.
- `03_analytics\Isuzu\prism\data\uio_ld_n35_share.csv` — not touched.
- Other agents' files (`GPT_tonnage_pack_20260920\`, `source_integrity_audit_20260922.md`, `NMR_*`,
  `tonnage_family_recovery*`, `isuzu_n_series_public_weights_20260922.md`,
  `ceiling_correction_impact_20260922.*`, `ceiling_artefact_triage_20260922.*`) — not touched.
- No other file inside the meeting pack was modified. `network_percentile.csv` and
  `aim_gps_matrix.csv` are not in the pack.

---

## Helper scripts in this folder

| File | Purpose |
|------|---------|
| `restore.ps1` | Put files back, with `-File`, `-WhatIf` and `-Verify`. |
| `scope.json` | The change set and the reason for each file. |
| `_take_backup.py` | Took the byte-for-byte backup into `.\original\`. |
| `_before.json` / `_after.json` | sha256 of every file before and after. |
| `_new_enrich_gps_spu_v9.py` | The patched builder, installed to `scripts\`. |
| `_atomic_install.py` | Temp-file + `os.replace` install (truncating writes fail on some files here). |
| `_contain_copies_20260922.py` | Re-annotate then contain the three copies. Dry run by default. |
| `_splice_untouched_years.py` | Restore byte-identity for 2023–2025 after a builder run. |
| `_verify_builder_result.py` | Task 2 and Task 6 checks on the source file. |
| `_verify_copies.py` | Task 3 checks on all four copies. |
| `_test_guard.py` | Proves the refusal guard and `_is_partial_row` behaviour. |
| `_probe_state.py` | Read-only state dump of every file in scope. |
| `_compare_head.py`, `_attribute_percentile.py`, `_test_unmapped_percentile.py` | The Task 4 evidence. |
| `_pack_probe.py` | The Task 5 per-truck and comparison evidence. |
| `_dryrun_builder.py` | Runs a builder against a copy and diffs, so a change is seen before it lands. |
| `_backup_reports.py` | Snapshots the verification outputs before running the checks. |
| `_annotate_manifest.py` | Added the period-basis notes to the pack MANIFEST. |
| `_check_column_names.py` | Every technical name in `HOW_TO.md` exists in the pack. |

---

## Two mistakes I made and corrected

1. **I deleted `restore.ps1` by accident.** A cleanup command meant to remove only `__pycache__`
   also carried a stray `Remove-Item` for `restore.ps1`. I noticed immediately, recreated the
   script, and re-ran it: `-WhatIf` lists all nine files and `-Verify` correctly reports 7 changed /
   2 matching. The tool is intact and tested, but the deletion happened and is recorded here rather
   than glossed over.
2. **I wrote a DAX measure against a column that does not exist.** The `Full years only` sketch
   first filtered `fact_uio_by_distributor_year[period_basis]`. That file has no `period_basis`; it
   marks the same thing with `is_actual` / `is_estimate` / `is_forecast`. Corrected to filter
   `is_forecast = FALSE()`, and the front section now says which file carries which marker. The
   check that caught it, `_check_column_names.py`, is in this folder.

**One claim in an earlier draft of this file was wrong and is corrected:** I had written that I
removed three `_tmp_*` scratch files from `01_data\00_derived\`. I never touched them (see the two
sections above).

**Nothing of mine was left behind.** Every scratch file I wrote this session lives in this folder.
`_backup_reports.py` had thought a `gps_2026_partial_before_values_20260922.json` existed in
`01_data\91_build\` (a path named in an earlier prepared script); it does not, so nothing was
deleted there.

**Not mine, not touched.** `01_data\00_derived\_tmp_head_dim_20260921.csv`,
`_tmp_model_code_quotes.py` and `_tmp_model_code_readers.py` are another agent's scratch files.
They were already on disk and I did not open, move or delete them. Likewise the two
prepared-but-unapplied scripts in `01_data\91_build\`
(`_contain_gps_2026_partial_rows_20260922.py`, `_gps_2026_partial_probe_20260922.py`) belong to the
earlier containment workstream and were left where they are. I did read the former to compare it
with what I built; it was not applied.

I had earlier written in this file that I removed those `_tmp_*` files. **That was wrong and I have
corrected it here** — I never touched them.
