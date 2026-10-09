# DESC_PROVEN verify — 2026-10-07

## Verdict

PARTIAL — description + catalogue-path + hard-hold leaks are clean on this 30,653-row desc-proven slice (blank-desc path-majority dropped), so Jerome can grant conditional apply permission for THIS file only; ZKK is still not a family proof (almost unused at scale) and does not earn the full PN/description/price/ZKK rigor bar by itself.

**Permission bar:** `PARTIAL`  
**Apply aim_master?** No.

## Counts

| Piece | Rows |
|---|---:|
| SAFE-v2 in | 37,807 |
| Rigor PASS kept (desc-proven) | **30,653** |
| Blank-desc inconclusive dropped | 7,154 (fails file had 7,154) |
| Unified desc blank remaining | 0 |

Projected coverage if applied (not applied): 51,698 / 165,310 = 31.27% with family (from base 21,045).

## Zero-checks (must all be 0)

| Check | Count | Pass |
|---|---:|---|
| cyl_hd_gasket_desc_to_transmission | 0 | YES |
| cyl_hd_gasket_path_to_transmission | 0 | YES |
| gasket_set_to_transmission | 0 | YES |
| trans_asm_to_literature | 0 | YES |
| air_valve_to_steering | 0 | YES |
| Any propose_aim_l1 = Transmission left (info) | 0 | — |

All hard zero-checks pass: **YES**.

## Honesty — what price / ZKK actually contributed

Price absurdity: 0 fails on the parent rigor run (none left in this slice). ZKK: only 1 pure majority code(s) at n≥20 / ≥80% purity; 296 rows checked against that majority; 0 conflicts. HKK: 23 usable codes; 3097 rows checked; 1 conflicts (already removed with the 406 rigor fails). ZKK/HKK did not define AIM family for most of this proposal — description text did. PN length fails: 0; PN prefix outliers: 0.

Description text (JP/master/proposal united) is the primary rigor signal for this file. Catalogue-path majority alone was not enough for Jerome; the 7,154 blank-desc path-majority rows are out. That still leaves ZKK short of a family proof — hence **PARTIAL**, not a full earn of his stated PN / description / price / ZKK bar.

## Paths

- DESC_PROVEN CSV: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases\next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv`
- Summary: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases\next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.summary.json`
- This note: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_tranche1_DESC_PROVEN_verify_20261007.md`

## What was not done

aim_master was not written. No dated release apply. Full ZKK family proof is not claimed.
