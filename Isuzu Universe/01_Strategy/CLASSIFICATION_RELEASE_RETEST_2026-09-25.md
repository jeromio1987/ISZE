# Parts classification release: re-test of the 24 September candidate

**Date:** 25 September 2026
**Task:** Cursor work order block D, `04_tools\delegation\CURSOR_WORK_ORDER_UNIVERSE_2026-09-24.md`
**Status:** recommendation. Nothing approved, nothing edited, `RELEASES.json` untouched.
**Read-only throughout.** No classification file, master, workbook or release file was written.

---

## 1. Verdict

**Re-test the candidate, and re-freeze it as a new release of its own. Do not pass it off as the
20 September file, and do not simply keep the frozen one.**

Everything the three examples were worried about is unchanged in the candidate. There is one clear
gain: **1,147 part numbers that previously read a placeholder now read a real family**, carrying
**EUR 736,530** of billing in the twelve months to June 2026, using labels that already exist in
the frozen file. There are no invented names. Three small items have to be settled first (section
6). None of them is a reason to refuse the file.

The one thing that must not happen is the file being read by anything that expects the approved
20 September release. The two are provably different files: the release guard returns exit 0 on
the frozen copy and exit 1 on this one.

---

## 2. What I tested, and on what basis

| Item | Value |
|---|---|
| Billing source | `01_data\00_derived\sales_fact.parquet`, calendar 2024 and 2025 |
| Non-part rows excluded | yes, `line_kind == "part"` on the frozen release |
| Parts billed, 2025 | EUR 32,210,451.69 (all lines EUR 33,707,573.78) |
| Parts billed, 2024 | EUR 32,938,586.46 |
| Frozen release | `01_data\00_derived\_releases\aim_pn_classification_release_2026-09-20.csv`, sha256 `60111c104dde…`, 164,907 rows, guard **exit 0** (re-verified today) |
| Candidate | `01_data\00_derived\aim_pn_classification_20260920.csv`, sha256 `092e981518ef…`, 164,907 rows, guard **exit 1** |
| Script and raw output | `01_data\90_INBOX\_cls_retest_20260925\` |

A warning about the candidate's provenance that is not in the brief. The candidate is no longer
the file the 24 September decision memo describes (hash `e5824683…`). Two things happened after
that memo was written, both recorded in `01_data\91_build\export_aim_eq_20260924\`:

- **16:20:54** — the EXPORT.XLSX classification write (`apply_summary.json`), making `e5824683…`.
- **19:21:15** — the cab-assembly class applied to the same file, 19 rows, 135 cells
  (`cab_class_overlay_summary.json`), making today's `092e9815…`.

So the candidate is the right thing to re-test, but it is one revision further on than the brief
assumes, and it needs its own release entry.

---

## 3. The three white-paper examples

### (a) Isuzu Truck UK brake pads: reproduces, and is identical in both files

| | 2024 | 2025 | Move |
|---|---:|---:|---:|
| Brake-pad group, frozen release | EUR 357,044.75 | EUR 304,257.91 | **-14.78%** |
| Brake-pad group, candidate | EUR 357,044.75 | EUR 304,257.91 | -14.78% |

Both figures match the decision memo's numbers for the recommended file to the cent, so the
example reproduces. **The two files are bit-identical on this test** - not one euro moves.

The memo's explanation for the gap against the white paper's EUR 347,389.58 holds up on the
evidence: inside the ITUK brake-pad group the euro is dominated by three caliper pad kits
(`8982447940` EUR 438,742, `8982169210` EUR 128,585, `8982169220` EUR 82,429, 2024+2025), and the
guide pin `8980475290` **is** still filed inside the brake-pad group at EUR 6,082 (section 5).

### (b) Portugal clutch: the "kits" wording does not hold, and is unchanged

Portugal clutch parts, frozen release, EUR:

| Leaf | 2024 | 2025 |
|---|---:|---:|
| Clutch disc | 18,596.03 | 22,830.70 |
| Pressure plate / cover | 16,799.32 | 20,317.36 |
| **Clutch kit** | **8,316.87** | **11,824.10** |
| Other clutch | 6,329.43 | 8,336.88 |
| Clutch cylinder | 4,294.57 | 4,361.79 |
| Release bearing | 2,861.96 | 4,242.49 |
| Clutch booster | 1,466.62 | 1,310.05 |
| Clutch linkage / cable | 117.11 | 94.39 |

The candidate gives the same table, cell for cell. A genuine "Clutch kit" leaf exists on this file
(82 part numbers across the network), and on it Portugal reads **EUR 8,316.87 / 62 units in 2024**
and **EUR 11,824.10 / 69 units in 2025** - which reproduces the memo's EUR 8,234.32 / 47 units and
EUR 11,824.10 / 69 units. Only SAP code **519** carries these lines; code 92 has none in 2024.

The conclusion therefore still stands and is not a release question: **the white paper's "462 to
461 kits" counts all clutch components, not kits.** Relabel the example as clutch components, or
re-cut it on the Clutch kit leaf.

### (c) Air filter under Air conditioning: not quite zero, and unchanged

| | Air-cleaner rows, 2025 | Of which under Air conditioning |
|---|---:|---:|
| Frozen release | EUR 815,200.67 | EUR 2,794.95 (**0.34%**) |
| Candidate | EUR 815,200.67 | EUR 2,794.95 (0.34%) |

The memo says this should be **0**. On the file it is not: **121 part numbers carry an air-cleaner
description, and exactly one of them** - `8980913940`, "FILTER; ACL", EUR 2,795 billed in 2025 and
EUR 3,103 in 2024 - **still sits under Competitive parts / Air conditioning / Other A/C.** The other
120 sit under Filters / Air filter. This is a one-row correction, not a taxonomy problem, and it is
identical in both files.

Ranked-view faults behave as the memo says and are not release-dependent: the separate maintenance
tag in `parts_catalog_dimension.csv` reads 1,803 rows as `leaf_spring` and 178 as `clutch_kit`, and
the guide pin `8980475290` carries **no** maintenance tag at all.

---

## 4. What actually changed between the two files

Catalogue axis, AIM axis and the non-part flag, compared row by row on all 164,907 keys:

| Block of columns | Rows differing |
|---|---:|
| `catalog_l1` / `catalog_l2` / `catalog_l3` | **0** |
| `catalog_residual`, `catalog_node_present` | 0 |
| `line_kind` (the non-part flag) | 0 |
| `filter_part_role` | 0 |
| `aim_l1_fixed` / `aim_l2_fixed` / `aim_l3_fixed` | **1,159** |
| `aim_source` | 1,161 |

**The whole change is on the AIM family columns. Not one part moved between catalogue groups.**

And it is a clean move, not a reshuffle:

| | Frozen | Candidate |
|---|---:|---:|
| Rows on a placeholder (`Unknown`) | 4,273 | 3,604 |
| Rows on a placeholder (`Unknown Review`) | 663 | 531 |
| Rows with no AIM family at all | 140,458 | 140,112 |
| **Rows given a real family** | - | **1,147** |
| Rows that **left** a real family for another real family | - | **12** |

Every one of the 1,159 moved rows now reads a real family. **Zero rows fell back onto a
placeholder.** The vocabulary is safe: the candidate introduces **no new first-level family**, one
new second level (`Disc & Drum`) and one new third level (`Cab Assembly`), and both already exist
in the file's own `aim_l2_fixed` / `aim_l3_fixed` columns.

Value and shape of the move, on the file's own `l12m_billed_eur` column. That column name is a legacy abbreviation and does not mean twelve months: the window it holds is January 2025 to June 2026. The figure is used here only to rank the families against each other.

| AIM family taken | Part numbers | Billing on the file's own column (EUR) |
|---|---:|---:|
| Accident & Body | 212 | 181,050 |
| Cabin Interior | 136 | 79,263 |
| Driveline Axle | 52 | 78,373 |
| Intake Exhaust Emission | 85 | 63,432 |
| Engine | 97 | 58,805 |
| Brakes | 92 | 56,077 |
| Steering | 62 | 47,559 |
| Electrical | 118 | 44,578 |
| Cooling | 63 | 35,625 |
| Transmission | 105 | 26,630 |
| Clutch | 32 | 20,798 |
| Suspension | 35 | 17,209 |
| Fuel System | 26 | 13,701 |
| Chassis Frame | 23 | 11,096 |
| Tools Equipment | 4 | 1,222 |
| Wheels Hub | 8 | 1,043 |
| Lubrication | 2 | 67 |
| Maintenance Service | 6 | 0 |
| Fluids Chemicals | 1 | 0 |
| **Total** | **1,159** | **736,530** |

The 12 rows that moved between two real families are all the same shape: eleven cab parts that
read `Accident & Body / Panels / Panel` and now read `Accident & Body / Complete Assembly / Cab
Assembly` (`7551847570`, `7552044930`, `7552612100`, `7552625790`, `7552824860`, `7553142130`,
`8974877720`, `8980115942`, `8980115951`, `8980425220`, and the side-sill pair `8980554611` /
`8980554621`). The cab assemblies belong on the new leaf. **The two side-sill panels are the ones
to look at** - a side sill is a body panel, and it has been swept into the cab-assembly class with
the rest. That is a judgement call, made by another agent on 24 September, worth a second look.

---

## 5. The known faults: where they actually live

The decision memo lists four defects as belonging to the recommended file. Three of them cannot be
reproduced on either release, and the reason is that they belong to a different file.

| Fault as written | What the two release files actually hold |
|---|---|
| Four Shell lubricant part numbers carry "Wheels Hub > Wheel Rim" | **0 rows** beginning `5500` in either file. The check was run the wrong way round: the four Shell rows are not in the classification release at all, so no family label of theirs can be read from it. The fault belongs to `aim_master_v2.csv`. |
| Leaf-spring family carries EUR 95k of front bumper bars | **0 rows** under `Suspension / Leaf / suspension spring` have "bumper" in the description, on either file. The 1,608-row leaf-spring list is clean. The EUR 95k belongs to the separate maintenance tag in `parts_catalog_dimension.csv`, where `leaf_spring` holds 1,803 rows. |
| Guide pin `8980475290` sits in the brake-pad group | **Confirmed on both files.** Competitive parts / Brake parts / Brake pad, EUR 6,082 in ITUK 2024+2025. |
| 9,634 rows (5.8%) in "Other / review" | **Confirmed on both files:** 9,634 rows, **EUR 3,241,257** on the file's own `l12m_billed_eur` column, 5.84% of the file - inside the 8% the gate allows. |

Correcting this matters for whoever acts next: two of those four "known faults" are not a reason
to hold this release, because this file never had them.

---

## 6. Open items before the candidate is frozen

1. **The 18th leaf is one empty row, and it is a data-cleaning question, not a taxonomy one.**
   `Filters / Filter element` holds exactly **one** part number, `5864052180`, with no description
   and **no billing in 2023, 2024, 2025 or 2026**. The rule is that a new leaf is a taxonomy
   decision, so it needs an explicit yes, or the row should not sit there. Do not let 177-versus-176
   block a decision about a part that has never been sold.
2. **The gate result on disk is stale.** `aim_pn_classification_20260920.gate.json` was run on
   20 September at 14:42 UTC: 17 passed, 1 failed, verdict FAIL, and the single failure is
   `drift_vs_previous_run` - the leaf baseline (27 groups, 177 leaves against an approved 176).
   That is item 1 wearing a different hat. It has not been re-run against today's file.
3. **The side-sill pair** in section 4.
4. **The candidate needs its own release entry.** It is a different file from `e5824683…` and from
   `60111c104dde…`. A new `release_id` with its own hash, status `PENDING_APPROVAL`. Nothing about
   the frozen 2026-09-20 entry should change - it is correctly approved and it still guards.
5. **The blocked-marker decision is still open and its numbers have moved.** The 24 September memo
   put 92 part numbers behind an `Unknown` marker that overrides any write to the base column. The
   candidate has since moved 1,147 rows off a placeholder, so the count of rows that still read a
   marker is now **4,135** (`Unknown` 3,604 + `Unknown Review` 531) against 4,936 before. Any pass
   that acts on that decision should re-measure rather than take the 92 from the memo; the same
   applies to the counts in `00_docs\agent\OPUS55_PROMPT2_AFTERMARKET_20260924.md`.

---

## 7. Recommendation

**Accept the candidate's AIM family work and re-freeze it as a new release.** The catalogue axis -
the thing the family views are actually read on - is untouched, the gain is real and measured, the
vocabulary is the file's own, and not one row fell back to a placeholder. The three examples are
unaffected in both directions.

Then, in this order: settle the empty 177th leaf, re-run the classification gate, fix the one
air-cleaner row under Air conditioning and the two side-sill panels, and add the new release entry
with its own hash. Only after the gate is re-run and green should the new file be set to APPROVED.

**Not done, and deliberately:** nothing was approved, no file was written, no release entry was
created, and no other agent's work was corrected. The frozen 2026-09-20 release remains the
approved one, and the guard still refuses the live file.