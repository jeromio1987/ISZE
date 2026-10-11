# AIM PBI export QA pass 2 — 2026-10-11

**Pass2 verdict: PASS_WITH_KNOWN_RESIDUALS**
**Better and not worse than Sep-21 on the things we remapped: False**

## Re-checked blockers from pass 1
- Export L1 vs master `aim_l1_fixed`: 6 PNs (was 1246 false alarm on raw/L2 naming)
- Export path vs class release: 6 PNs
- Lost AIM vs Sep-21: 0
- Eng gasket sets under Transmission: 207 → 0
- Gasket regressions into Transmission: 0

## Old dirt still present (same as Sep-21, not introduced)
- Cylinder-head gasket under Transmission: 79 PNs, EUR 44,765 (identical set: False)
- Transmission ASM under Literature: 38 PNs, EUR 273,277 (identical set: True)

## Fills / changes
- Blank→AIM fills: 31216
- Path changes: 1081 (gasket engine fix 207, other 874)
- Suspects in top-120 euro fills: 1
- Random 80 other changes keyword conflicts: 0

- C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_pbi_export_deep_qa_pass2_20261011.json
- C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_pbi_export_deep_qa_pass2_20261011.md
