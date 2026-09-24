# Parts classification release: recommendation

**Date:** 23 September 2026
**Status:** recommendation for Jerome to approve. Nothing has been decided, and no classification file was changed.

## Recommendation

Pin `01_data\00_derived\aim_pn_classification_20260920.csv` as the one release every Universe example reads from.

- **Version name:** classification release 2026-09-20
- **Built:** 20 September 2026, 20:46, by `01_data\91_build\build_aim_classification_20260920.py`
- **Size:** 164,907 rows, one row per part number, no duplicate keys
- **Checksum (SHA-256):** `60111c104ddeb466e6c15f084039639d35172056b0fd2ea10225a3c50da610e0`

The data supports this recommendation, with the four open items listed at the end of this memo.

## Why this file

1. **It is the only candidate that carries everything a family view needs.** It holds the catalogue tree (family, group, detailed type), the AIM functional family, the product form (element, assembly, kit), a flag that marks freight, rebate and lubricant lines as non-parts, and a flag on every row whose label differs from the master.
2. **Its catalogue labels can be reproduced.** They match, row for row, the catalogue source as committed on 20 September (git `c813330f`): zero differences.
3. **It keeps the 17 and 18 September corrections.** The air-cleaner filters are filed under Filters. The DEF tanks, common rails, king pins and bumper bars are also in their correct groups.
4. **It covers every part billed in 2025.** Its AIM family labels match the 21 September master export on every billed part.

**The live files went backwards on 21 September.** A pipeline re-run at 12:35 and 12:36 rebuilt `pr00_classification.csv` and `aim_pn_classification.csv` from the price file, which undid those corrections. Engine air filters now sit under "Air conditioning" again in both live files. Anyone who re-reads either file today gets the old error back. The live check report still points at `aim_pn_classification_v2.csv`, so it did not catch this.

## What changes for users, compared with the other candidates

Basis: parts billed in calendar 2025, taken from `01_data\00_derived\sales_fact.parquet` (the derived billing parquet, not the raw extracts). Parts total €32,286,946. Freight, rebates and interest are excluded (€1,420,628).

| Candidate | Built / modified | Rows | Billed parts labelled differently from the recommended file (2025) |
|---|---|---:|---|
| `pr00_classification.csv` (live catalogue source) | 21 Sep 12:35 | 164,795 | 265 parts, €2,245,588 |
| `aim_pn_classification.csv` (live, combined) | 21 Sep 12:36 | 164,783 | same as the line above; the two files are identical on the catalogue tree |
| `aim_master_v2.csv` (catalogue columns) | 20 Sep 09:24 | 165,213 (306 duplicate keys) | 738 parts, €2,432,983 |
| `aim_pn_classification_v2.csv` | 18 Sep build, 20 Sep 20:47 sync | 164,667 | 240 parts, €148,947, mostly lubricant lines left blank |
| `AIM_Master_PN_Categories_Figkey_20260921.csv` (AIM families only) | 22 Sep 19:18 | 165,213 (306 duplicate keys) | 0 |
| `aim_master_v2.csv` (AIM family columns) | 20 Sep 09:24 | 165,213 | 96 parts, €9,248 |

Compared with the live files, the family totals move. For 2025, Filters would read €858k lower and Air conditioning €691k higher. "Review needed" would hold €904k more, Body parts €432k less and Steering €268k less.

**The two drift figures in the paper cannot be reconciled because they count different things.** The 1,618 figure (27 August) compares figure keys in the catalogue with the SAP price file; it does not count family labels. The 2,728 figure (20 September) compares the master's copy with its own source on that day. Neither measures movement between releases. The paper should drop both and quote the release comparison above.

## The three white-paper examples

- **Isuzu Truck UK brake pads (€347,389.58 to €302,366.25): the example reproduces.** The figure comes from the source category and reproduces to the cent. Its three part numbers sit in the brake-pad group in every candidate. Measured on the brake-pad group itself, the recommended file reads €357,044.75 to €304,257.91, and the live files read €352,670.75 to €302,549.55. The difference comes from front pad kits that the source category does not tag, plus one guide pin misfiled as a pad. The story does not change.
- **Portugal clutch kits (€29,959.87 to €31,702.47): the "kits" label does not hold in any candidate.** The source category holds 37 part numbers: pressure plates, clutch discs, release bearings and shift blocks. Only €8,234.32 (47 units) in 2024 and €11,824.10 (69 units) in 2025 are actual clutch kits. The "462 to 461 kits" figure counts all clutch components, not kits. This is true whichever file is chosen. The Genuine against Best Value point may still hold, but the example needs to be relabelled as clutch components or re-cut.
- **Ranked periodic-maintenance family view: the rank order does not depend on the release.** That view is keyed on a separate maintenance tag in `parts_catalog_dimension.csv`, not on any candidate. In the recommended file, 23 of the 25 families sit at least 95% in a single group (96.3% weighted by euro). In the live files, 18% of air-filter euro sits under Air conditioning. Two faults in the tag itself show up whichever file is chosen. The "leaf spring" family includes €95k of front bumper bars in 2025 (the recommended file correctly puts those under bumpers). The "clutch kit" family is a mix of components.

## Top five disagreements by euro (parts billed in 2025)

| Part | Description | 2025 € | Recommended file | Live files and master |
|---|---|---:|---|---|
| 8974995480 | FILTER; ACL | 255,235 | Filters > Air filter | Air conditioning > Other A/C |
| 8972746690 | TANK ASM; DEF | 116,501 | Exhaust > Aftertreatment | Review needed |
| 8984890180 | RAIL; COMMON | 115,065 | Fuel system > Other fuel system | Review needed |
| 1876101132 | FILTER; ACL | 88,054 | Filters > Air filter | Air conditioning > Other A/C |
| 5876100201 | ELEMENT; AIR CLEANER | 85,417 | Filters > Air filter | Air system > Other air system |

In all five, the recommended file matches the part description, and the other files show the state before the corrections.

## Still open

1. **Check result is 17 of 18.** The recommended file has 177 detailed types against 176 approved, because it adds "Filters > Filter element". That leaf needs to be approved or removed before the release is frozen.
2. **The live files regressed on 21 September.** Someone needs to decide whether to restore them from the recommended release or to change the rebuild so that the corrections survive it. Until then, no family label should be read from `pr00_classification.csv` or `aim_pn_classification.csv`.
3. **Known faults in the recommended file.** Four Shell lubricant part numbers carry "Wheels Hub > Wheel Rim" in the AIM family columns. They are flagged as non-parts, but they must stay out of any distributor view. One guide pin (8980475290) sits in the brake-pad group. 9,634 rows (5.8%) sit in "Other / review", and 115 rows have no catalogue source row.
4. **Two changes to the paper.** The Portugal example needs rewording, and the leaf-spring tag needs cleaning, before either goes to a distributor.

Working scripts and outputs (not deliverables): `C:\Users\jerom\AppData\Local\Temp\claude\cls\`.

## Update 24 September 2026

**Overwrite incident:** On 24 September at 16:20, another agent wrote into `01_data\00_derived\aim_pn_classification_20260920.csv` from an EXPORT.XLSX source, changing 1,197 rows. The file's SHA-256 hash changed from `60111c104ddeb466e6c15f084039639d35172056b0fd2ea10225a3c50da610e0` to `e5824683806f7b7fdef17517dac2bc7a653e739b4c493ffba9a6dbb4e513e015`. Both files now contain 164,908 rows.

**Frozen copy:** The exact recommended version survives as `01_data\00_derived\_releases\aim_pn_classification_release_2026-09-20.csv` (read-only, hash verified, stored at 24 September 16:24). A release guard has been installed:

- **Guard location:** `01_data\00_derived\_releases\` folder
- **Manifest:** `RELEASES.json` lists two candidates with hashes and row counts:
  - `2026-09-20`: PENDING_APPROVAL, frozen copy, hash `60111c104...`
  - `2026-09-24-candidate`: NOT_RELEASED, live file with EXPORT.XLSX changes, hash `e5824683...`
- **Checker script:** `check_classification_release.py` verifies the approved release's hash at build time. It exits non-zero if the file does not match or status is not APPROVED.

**Decision now open:** 

1. **Freeze 2026-09-20?** Keep the stable recommended release, which passes the three white-paper examples (pending re-test for item 2 above).
2. **Re-test and freeze 2026-09-24-candidate?** Accept the EXPORT.XLSX classifications added on 24 Sep (1,197 rows changed), re-run the three white-paper examples, and freeze that version instead.

Once Jerome approves a release, the status in RELEASES.json will be set to APPROVED, and the build guard will accept only that file. No further pipeline changes will go undetected.
