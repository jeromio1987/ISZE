# AIM apply double-check — 2026-10-07

**Apply status: complete**

**Verdict: CONFIRM** — Oct4 forward-repair verified. Sample 1878148072 is Engine gasket on master and overlay; all Oct4 groups match release; eng-gasket to Transmission = 0; release vs master both-nonblank AIM differ = 0; DESC 30,653 + EQ 112 still present; DESC-applied hard holds still 0.

Recommendation: safe

As-of (UTC): 2026-10-07T16:51:15.260396+00:00

## Must-PASS re-check (after Oct4 forward-repair)

- **PASS** — 1878148072 Engine gasket on master AND overlay
- **PASS** — eng-gasket to Transmission = 0 on master
- **PASS** — Oct4 gasket/EVRV/antenna/DEF match release on master+overlay
- **PASS** — release vs master both-nonblank AIM differ = 0
- **PASS** — DESC 30653 + EQ 112 still present
- **PASS** — Hard holds 0 on DESC-applied rows
- **PASS** — Hard hold eng-gasket to Transmission = 0

### Sample 1878148072

- release07: `Engine > Gasket & Sealing > Gasket`
- master: `Engine > Gasket & Sealing > Gasket`
- overlay: `Engine > Gasket & Sealing > Gasket`

### Oct4 scorecard

| Group | Release07 | Master | Overlay |
|---|---:|---:|---:|
| D2_engine_gasket_sets | 209/209 | 209/209 | 209/209 |
| D3_evrv_valves | 9/9 | 9/9 | 9/9 |
| D4_antennas | 71/71 | 71/71 | 71/71 |
| D6_def_injectors | 5/5 | 5/5 | 5/5 |

## Coverage / GO piles still present

- Master rows **165,422**, AIM filled **56,197**.
- DESC tags/match: **30,653** / **30,653**.
- EQ tags/on master: **112** / **112** (missing 4 cameras).
- Release vs master both-nonblank AIM differ: **0**.
- Release blank / master has AIM: **2** (info only; not a nonblank conflict).

## Hard holds

DESC-applied (must be 0):
- `cyl_hd_gasket_path_to_transmission` = **0**
- `gasket_set_to_transmission` = **0**
- `trans_asm_to_literature` = **0**
- `air_valve_to_steering` = **0**

Master-wide:
- `cyl_hd_gasket_desc_to_transmission` = **79**
- `gasket_set_to_transmission` = **19**
- `gasket_set_eng_to_transmission` = **0**
- `trans_asm_to_literature` = **38**
- `air_valve_to_steering` = **6**

Note: residual non-zero master-wide holds (cyl-head / non-ENG gasket-set / trans-asm / air-valve) are older labels outside the 4 Oct + DESC_PROVEN GO piles. Eng gasket is 0; DESC-applied holds are 0. They are not leftovers of this forward-repair.

## Absolute paths

- C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases\aim_pn_classification_release_2026-10-07.csv
- C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv
- C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_pn_classification_20260920.csv
- C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_apply_doublecheck_20261007.md
- C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_apply_doublecheck_20261007.json
