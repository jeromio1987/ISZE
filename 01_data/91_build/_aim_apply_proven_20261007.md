# AIM proven apply — 2026-10-07

## Verdict

**Applied: YES (after forward-repair).** Release `2026-10-07` stayed APPROVED. DESC_PROVEN + EQ_PROVEN were already on master/overlay. Oct4 AIM moves (engine gasket sets, EVRV, antennas, DEF) were missing on master/overlay and were forward-repaired from the release (marker `forward_repair_oct4_20261007`). RELEASES.json was not re-stamped.

## Proof (re-verified)

- Sample `1878148072`: master = `Engine > Gasket & Sealing > Gasket`; overlay = `Engine > Gasket & Sealing > Gasket`
- Hard hold gasket_set_eng→Transmission on master: **0**
- Oct4 D2/D3/D4/D6: master and overlay match release (0 bad / 0 missing)
- Release vs master non-blank AIM remain differs: **0**
- DESC tags still: 30653; EQ tags: 112
- Repair stamps: master 622, overlay 505

### Oct4 scorecard (after repair)

| Group | n | Master OK | Overlay OK |
|---|---:|---:|---:|
| D2_engine_gasket_sets | 209 | 209/209 | 209/209 |
| D3_evrv_valves | 10 | 10/10 | 10/10 |
| D4_antennas | 92 | 92/92 | 92/92 |
| D6_def_injectors | 5 | 5/5 | 5/5 |

## Coverage

- Release AIM non-blank: 55,830 / 165,055 rows (unchanged)
- Master AIM non-blank: 55,932 / 165,422 rows (labels corrected in place)
- Overlay: AIM labels corrected in place to match release

## Paths

- Release: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases\aim_pn_classification_release_2026-10-07.csv`
- Master: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv`
- Overlay: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_pn_classification_20260920.csv`
- Repair verify JSON: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_forward_repair_oct4_20261007.json`
- This report: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_apply_proven_20261007.md`

## Honesty

First COMPLETE claim was wrong on Oct4 sync. Independent double-check rejected it (`_aim_apply_doublecheck_20261007.md`). This report is rewritten after repair proof.
