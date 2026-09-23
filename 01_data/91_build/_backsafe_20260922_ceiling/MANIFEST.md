# Backup + change manifest — target-spend ceiling correction

**Created:** 2026-09-22, late evening
**Folder:** `01_data\91_build\_backsafe_20260922_ceiling\`
**Workspace root:** `C:\Users\jerom\Desktop\claude\ISZE`

Read this section first. It reports a mistake, not only a success.

---

## 1. READ THIS — a mistake in this session, and what it cost

`restore.ps1` works and is proven. But **15 of the 48 files in scope cannot be put back
byte-for-byte**, and that is my fault, not a property of the files.

What happened. `_take_backup.py` copies the live file over `.\original\`. I ran it a second time
after the ceiling rebuild and after the dashboard regen, and — correctly, from its own point of
view — it refreshed every backup copy to the *new* bytes and rewrote `_before.json` to the new
hashes. So for those files the only copy of the pre-change bytes inside this folder is gone, and
`restore.ps1 -Verify` reported "matches" on files it could no longer undo. **That is worse than
having no backup, because it looks like one.**

What I then did:

1. Put a guard in `_take_backup.py` so it **refuses** to overwrite a backup copy whose live file no
   longer matches the manifest. Tested: it now exits with
   `REFUSING to overwrite the backup copy of 01_data/00_derived/wallet_waterfall.csv`.
2. Searched the whole workspace for byte-identical copies. **6 files recovered exactly** — their
   pre-change bytes survive in the `PPT_GPT_commercial_pack_2026-09-19` pack and in the
   `07_deploy` mirror.
3. Checked `git show HEAD:<path>` for the remaining 15. **None matched** — the working copies
   carried uncommitted edits, so `HEAD` is not the state I measured. Three are not tracked at all.
4. Marked those 15 as `revertible: false` in `_before.json`, so `restore.ps1 -Verify` now prints
   `NOT-REVERTIBLE` for them instead of a false `matches`.

What that means in practice. **All 15 are generated outputs, and all 15 have a runnable builder.**
The one file that everything derives from — `wallet_waterfall.csv` — *is* byte-for-byte revertible
and was proven by round-trip. So the honest statement of reversibility is:

| | count | how it is reversed |
|---|---:|---|
| Byte-for-byte revertible | **33** | `restore.ps1` |
| Revertible by re-running a builder | **15** | restore `wallet_waterfall.csv`, then re-run that file's builder |

If a full reversal is ever needed: `restore.ps1` first (the 33), then re-run the 15 builders listed
in §5. I have **not** left anything in a state where the numbers are wrong — the 15 are consistent
with the current ceiling; what is lost is only the ability to put a few of them back byte-for-byte
without rebuilding.

---

## 2. Restore commands

One file:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_ceiling\restore.ps1" `
  -File "01_data/00_derived/wallet_waterfall.csv"
```

Everything revertible:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  "C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_ceiling\restore.ps1"
```

Read-only check (exits non-zero if anything differs, and names the not-revertible files):

```powershell
...\restore.ps1 -WhatIf
...\restore.ps1 -Verify
```

**This exact command was run for real.** `_test_restore_roundtrip.py probe` appended a marker line
to `wallet_waterfall.csv`; `restore.ps1 -File 01_data/00_derived/wallet_waterfall.csv` put it back;
`_test_restore_roundtrip.py check` returned `MATCH` against
`e9c13fbcde9adcddae5d3dea9e49445d57bb2a4c09593019eb7b352eed1cc905`. The ceiling rebuild was then
re-applied and returned the identical file hash `5905ee6140c808f9`, so the rebuild is deterministic.

---

## 3. What changed, and why

| # | File | Change |
|---|------|--------|
| 1 | `01_data/00_derived/wallet_waterfall.csv` | **Rebuilt.** `build_wallet_waterfall.py` run unmodified. Six markets now carry the measured 3.5 t share their light-truck row was missing. Network ceiling 55,253,312 → **54,375,729**. Parts billed unchanged. |
| 2 | `01_data/00_derived/lost_sales_model.csv` + `lost_sales_market.csv` + `.meta.json` | Rebuilt by `build_lost_sales_model.py`, which consumes the ceiling. |
| 3 | `01_data/00_derived/metrics_snapshot.json` | Rebuilt. `waterfall.network.wallet_eur_2025` 54,375,729; `gps_pct_2025` 56.6. |
| 4 | `01_data/00_derived/_verification_report.json` / `.md` | Rewritten by `verify_derived_pipeline.py`. 164 pass, 1 warn, 0 fail — the same warn as before (DENMARK 2012/2013). |
| 5 | `03_analytics/Isuzu/prism/data/facts_anchor.yaml` | `waterfall.network.gps_pct_2025` 55.7 → **56.6**, with the mechanism and the stale-not-wrong distinction written into the comment. |
| 6 | `02_dashboards/sales/ISZE_KPI_Dashboard.html` | Rebuilt. Network ceiling 54,375,729. |
| 7 | `02_dashboards/ops/ISZE_OS_Console.html` | Rebuilt. Ceiling, cover, uncaptured and the placeholder share all read from the file at build time. |
| 8 | `02_dashboards/hub/ISZE_OS_Hub.html` | Rebuilt. Same. |
| 9 | `02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html` | Rebuilt. **Plus a builder fix:** the league table's per-market cover column was hardcoded literals, which is why correcting the ceiling left Ireland at 124.2% and Portugal at 56.0%. It now reads them from the ceiling file. |
| 10 | `02_dashboards/_build/build_exec_aftersales_paper.py` | **Builder fix** (the hardcoded cover column). |
| 11 | `01_data/14_dashboards/isze_data.json`, `isze_data.preload.js`, `viz/risk_cockpit.json`, `02_dashboards/sales/risk_cockpit.data.js` | Rebuilt. `addressable_gap_eur` 24,727,686 → **23,950,221**. |
| 12 | `09_meetings/Business_Performance_Review_2026/_bpr_numbers.json` + `.pptx` + `charts_out/_ceiling_strip.png` | Rebuilt. Slide 17 now 54,375,729 / 56.6%. |
| 13 | `09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/target_spend_waterfall.csv` | Rebuilt from the corrected ceiling, with `ceiling_basis` and `ceiling_as_of` added (22 → 24 columns). |
| 14 | `09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/HOW_TO.md` | New section 5 disclosure: the ceiling's basis, its as-of date, and what moved. |
| 15 | `09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/MANIFEST.csv` | Row for the ceiling table updated (cols 22 → 24). |
| 16 | `09_meetings/BVDB_PBI_Data_Upload_2026-09-23_HANDOVER_20260922.zip` | **New.** The archive to hand over. |
| 17 | `09_meetings/BVDB_PBI_Data_Upload_2026-09-23_corrected_GPS-PARTIAL-YEAR_ONLY_superseded_20260922.zip` | **Renamed, not deleted,** from `..._corrected_20260922.zip`. |

### Deliberately not changed

- `BVDB_PBI_Data_Upload_2026-09-23.zip` — the original. Asserted untouched before and after.
- `03_analytics\Isuzu\prism\data\uio_ld_n35_share.csv` — backed up only, to prove it did not drift.
- `01_data\00_derived\revenue_runway.csv` — backed up only. It reads the ceiling for a **capture
  percentage**, not for a level, so the ceiling correction does not move it. Verified: hash
  unchanged after the rebuild.
- `verification_fixtures.yaml`, `modules\freshness.py`, `modules\schema_guard.py`,
  `scripts\verify_derived_pipeline.py` — read only.
- `01_data\90_INBOX\GPT_tonnage_pack_20260920\` — another agent's folder, untouched.

---

## 4. The zip decision

Three copies were in circulation and only one was any good.

| Archive | What it holds | Action |
|---|---|---|
| `..._2026-09-23.zip` | 28 members, 2026-09-22 20:10. GPS part-year correction absent, ceiling stale. | **Not touched.** It is the dated record of what was built at 20:10. |
| `..._corrected_20260922.zip` | 28 members, 21:38. GPS part-year correction **present**; ceiling **stale**. Its name implied it was the fixed pack, which it was not. | **Renamed** to `..._corrected_GPS-PARTIAL-YEAR_ONLY_superseded_20260922.zip`, which says what it actually contains. Not deleted; its bytes are unchanged (asserted). |
| `..._HANDOVER_20260922.zip` | 28 members. GPS part-year correction **and** the corrected ceiling, with the basis and the date on the face of the table. | **New file, this is the one to hand over.** |

Why rename rather than rebuild under the old name: the old name claimed a fix it did not contain,
and overwriting it would have destroyed the only archive carrying the GPS part-year correction in
its original form. A new name that describes the contents fixes the misleading label without
losing anything.

---

## 5. The 15 files that are revertible only by rebuilding

For each: restore `wallet_waterfall.csv` first, then re-run the builder.

| File | Builder |
|---|---|
| `01_data/00_derived/lost_sales_model.csv`, `lost_sales_market.csv`, `lost_sales_model.meta.json` | `03_analytics/Isuzu/prism/scripts/build_lost_sales_model.py` |
| `01_data/00_derived/metrics_snapshot.json` | `03_analytics/Isuzu/prism/scripts/build_metrics_snapshot.py` |
| `01_data/00_derived/_verification_report.json` / `.md` | `03_analytics/Isuzu/prism/scripts/verify_derived_pipeline.py` |
| `03_analytics/Isuzu/prism/data/facts_anchor.yaml` | hand edit — the comment above `waterfall.network.gps_pct_2025` |
| `02_dashboards/sales/ISZE_KPI_Dashboard.html` | `02_dashboards/_build/build_kpi_dashboard.py` |
| `02_dashboards/ops/ISZE_OS_Console.html` | `02_dashboards/ops/build_os_console.py` |
| `02_dashboards/hub/ISZE_OS_Hub.html` | `02_dashboards/_build/build_isze_os_hub.py` |
| `02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html` | `02_dashboards/_build/build_exec_aftersales_paper.py` |
| `01_data/14_dashboards/{isze_data.json, isze_data.preload.js, viz/risk_cockpit.json}` | `build_isze_dashboard_json.py`, then `build_risk_cockpit_viz.py` |
| `09_meetings/Business_Performance_Review_2026/_bpr_numbers.json`, `.pptx` | `build_numbers.py` → `build_core_charts.py` → `build_bpr_deck.py` |
| `09_meetings/BVDB_PBI_Data_Upload_2026-09-23/{02_GPS/target_spend_waterfall.csv, 00_START_HERE/{HOW_TO.md,MANIFEST.csv}}` | `_refresh_pack_and_new_zip.py` in this folder |

`_refresh_pack_and_new_zip.py` is in this folder rather than a workspace builder because the pack's
own builder (`09_meetings\_build_bvdb_pbi_pack_20260923.py`) starts with `shutil.rmtree(OUT)` and
would erase the earlier session's corrections. Running it is not safe.

---

## 6. Helper scripts in this folder

| File | Purpose |
|---|---|
| `restore.ps1` | Put files back. `-File`, `-WhatIf`, `-Verify`. Honours `revertible: false`. |
| `_take_backup.py` | Byte-for-byte backup + manifest. **Now refuses to overwrite a live diff.** |
| `_recover_originals.py` | Search the workspace for surviving pre-change copies; mark the rest not revertible. |
| `_recover_from_git.py` | Check `git show HEAD:<path>` for the same. (None matched.) |
| `_test_restore_roundtrip.py` | The real corruption → restore → compare test. |
| `_ceiling_fingerprint.py` | Per-market ceiling / billed / cover, and the file hash. `before` and `after` runs. |
| `_run_builder_to_temp.py` | Run `build_wallet_waterfall.py` unchanged but into a temp file, diff it, then `os.replace` on `--install`. Works around the truncating-write failure. |
| `_diff_temp_vs_live.py` | Cell-by-cell diff, with the six markets and the captured columns called out. |
| `_recompute_placeholder_share.py` | Re-derive the flat-placeholder share from the live file. |
| `_placeholder_disclosure_audit.py` | Where the disclosure text lives and what each place now says. |
| `_find_stale_share.py` | Pull every `40.3` out of the pages with its context. |
| `_refresh_pack_and_new_zip.py` | Refresh the pack's ceiling table, disclosure and manifest; rename the misleading zip; build the hand-over zip. |
| `_verify_handover_zip_from_archive.py` | Extract the new zip and re-read the ceiling table, the disclosure and a sample **from the archive**. |
| `_kpi_two_basis_probe.py` | Show each market's ceiling against its fleet, and where the two files disagree. |
| `_per_market_dashboard_probe.py` | Where each per-market ledger carries its ceiling. |
| `_exec_paper_table_probe.py` | Read the exec paper's league table back out of the built HTML. |
| `_exec_paper_gate_compare.py` | Whether a gate failure pre-existed the rebuild or was caused by it. |
| `_ceiling_before.json` / `_ceiling_after.json` | Per-market ceiling state either side. |
| `_placeholder_share.json` | Recomputed share, all three years. |

---

## 7. Main unresolved item

`01_data\00_derived\gps_spu_by_distributor.csv` and `wallet_waterfall.csv` disagree on five markets
(Portugal, Ireland, Germany, ITUK, Belgium) by a net EUR 105,748, because they sit on different
fleet vintages. The rebuilt KPI dashboard still takes `ceiling` from one file and `maxSpend` from
the other **inside the same market row**. This is the separate different-basis defect, and it
cannot be resolved without deciding which basis the KPI layer owns. It is reported, not invented
around.
