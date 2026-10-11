# AIM PBI export deep QA — 2026-10-11

**Verdict: FAIL**
- Better than Sep-21: **True**
- Safe to send Bart (no blockers): **False**
- Started: 2026-10-11T17:44:15.757197+00:00
- Finished: 2026-10-11T17:45:06.740378+00:00

## Coverage
- Rows: 165213 → 165422
- PNs with AIM family: 24470 → 55895
- Filled blank→AIM: 31216
- Lost AIM: 0
- Path changed: 1081
- Export euro AIM cover (pn max): 97.886% → 97.888%
- Sales-fact euro AIM cover: 97.714% → 97.839%

## Hard holds on export
- `eng_gasket_set_to_transmission` = 0
- `cyl_hd_gasket_to_transmission` = 79
- `any_gasket_set_to_transmission` = 20
- `antenna_not_radio` = 6
- `evrv_not_egr` = 0
- `def_injector_misfiled` = 1
- `trans_asm_to_literature` = 38
- `air_valve_to_steering` = 3

## Blockers
- [G_master_alignment] Export vs master AIM differ on 1246 PNs

## Soft fails / notes
- [E_hard_holds_on_export] trans_asm_to_literature = 38 high
- [N_leading_zeros] too few leading-zero PNs

## Section OK flags
- PASS `A_file_identity`
  - CSV sha256 matches release.json export_sha256
  - Internal release sha256 matches meta
  - RELEASES.json APPROVED = 2026-10-07
- PASS `B_load_compare_shape`
  - Duplicate PN rows new=309 old=309 (figure-key grain, may be >0)
- PASS `C_xlsx_vs_csv`
  - xlsx cols match
  - xlsx fingerprint == csv fingerprint (pn|aim|figure_key)
- PASS `D_sep21_vs_oct7_coverage`
  - Euro AIM coverage improved or held: 97.89% -> 97.89%
- FAIL `E_hard_holds_on_export`
  - eng_gasket_set_to_transmission = 0
  - cyl_hd_gasket_to_transmission = 79 residual on export (inspect samples)
  - any_gasket_set_to_transmission = 20 residual on export (inspect samples)
  - antenna_not_radio = 6
  - evrv_not_egr = 0
  - def_injector_misfiled = 1
  - FAIL: trans_asm_to_literature = 38 high
- PASS `E2_known_pn_spot`
  - Eng gasket sets under Transmission cleared: 207 -> 0
- PASS `F_export_vs_class_release`
  - Export AIM differs on 6 PNs (small)
- FAIL `G_master_alignment`
  - FAIL: Export vs master AIM differ on 1246 PNs
- PASS `H_sales_fact_euro_coverage`
  - Sales euro AIM cover 97.714% -> 97.839%
- PASS `I_vocabulary`
- PASS `J_random_desc_vs_family`
  - filled_new: suspects 2/12 (16.7%)
  - changed: suspects 20/48 (41.7%)
  - unchanged_aim: suspects 34/136 (25.0%)
  - top_eur_aim: suspects 12/144 (8.3%)
  - random_aim: suspects 16/60 (26.7%)
- PASS `K_random_dump`
- PASS `L_eq_skipped`
  - EQ skipped 4; in export with AIM=0
- PASS `M_line_kind`
- FAIL `N_leading_zeros`
  - FAIL: too few leading-zero PNs

## Absolute paths
- C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\AIM_Master_PN_Categories_Figkey_release_2026-10-07.csv
- C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\AIM_Master_PN_Categories_Figkey_release_2026-10-07.xlsx
- C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_pbi_export_deep_qa_20261011.json
- C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_pbi_export_deep_qa_20261011.md
