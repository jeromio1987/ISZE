# SAFE-v2 verify — 2026-10-07

## Verdict

SAFE-v2 is description-clean on the cyl-head / hard-hold leaks (zero checks pass), but 7,154 rows still have no description and ride on catalogue path only — not apply-ready until Jerome re-reads that blank-desc tail (or cuts it).

**Apply permission earned?** No. Apply permission is not earned yet — zero-checks on description leaks pass, but the blank-description path-majority tail still needs Jerome's eyes before any apply.

## Counts

| Piece | Rows |
|---|---:|
| CLEAN in | 38,213 |
| Rigor fails excluded | 406 (file had 406) |
| Extra cyl-head→Transmission beyond those fails | 0 |
| SAFE-v2 out | **37,807** |
| Of which rigor-pass (described / commodity) | 30,653 |
| Of which rigor-inconclusive (blank desc) | 7,154 |

Projected coverage if applied (not applied): 58,852 / 165,310 = 35.6% with family (from base 21,045).

## Zero-checks (must all be 0)

| Check | Count | Pass |
|---|---:|---|
| GASKET; CYL HD / head-gasket / ENG-gasket desc → Transmission | 0 | YES |
| Cylinder head gasket path → Transmission | 0 | YES |
| Gasket set → Transmission | 0 | YES |
| Transmission assembly → Literature Marketing | 0 | YES |
| Air valve → Steering | 0 | YES |
| Any propose_aim_l1 = Transmission left (info) | 0 | — |

All hard zero-checks pass: **YES**.

## Honesty — description vs path

still path-majority for 7,154 rows without description (7,154 rigor-inconclusive kept); 30,653 rows have a description. ZKK is almost useless at this scale (rigor found 1 pure ZKK code at n≥20 / ≥80%), so blank-desc rows are catalogue-path proposals, not commodity-verified.

The earlier rigor run already showed ZKK cannot define AIM family at scale (one pure code). SAFE-v2 does not invent a ZKK fix; it only removes known fails and the cyl-head gasket sibling leak.

## Paths

- SAFE-v2 CSV: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases\next_release_proposal_full_class_tranche1_catmap_SAFE_v2_2026-10-07.csv`
- Summary: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases\next_release_proposal_full_class_tranche1_catmap_SAFE_v2_2026-10-07.summary.json`
- This note: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_tranche1_SAFE_v2_verify_20261007.md`

## What was not done

aim_master was not written. No dated release apply. Jerome's conditional apply permission from the CLEAN rigor FAIL is still not earned for an automatic apply.
