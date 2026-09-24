# PR00 IE40 write-back — the 164 that already had a master row with an empty family

**Date:** 2026-09-24 · **Agent:** cursor (AIM master write-back, part 3)
**Verdict: 162 of 164 placed. 2 left unplaced and named below. The row count did not move — this
was a fill, not an append.**

This is the third and last piece of the IE40 write-back. Part 1 (13:55) refused to write anything
because 92 part numbers carry a deliberate `Unknown` in `aim_l1_fixed`. Part 2 (14:05) appended the
44 that had no row on the master at all. This pass fills the family on the 164 that **do** have a
master row but a blank one — the group part 1 called "would land free".

---

## 1. What the 164 actually were

They are not blank rows. Each one already carries its price-list catalogue node, its figure key and
its Japanese codes, and each one is stamped `aim_source = not_classified` with `has_aim = 0`. What
was empty is the AIM side: `aim_l1`, `aim_l2`, `aim_l3`, `aim_l1_fixed`, `aim_l2_fixed`,
`description`, and the two money columns (all `0.0`).

So the join key for these had to be the description on the **export row**, not on the master row —
the same field the 44 were decided on. All 164 export descriptions are non-empty and none of them
conflicts with a master description, because the master side is blank.

## 2. The method, and the one place it had to be read carefully

Same rule as the 44: **the exact description's own AIM path where the evidence agrees on one full
path with at least three supporting parts.** The brief's hard guard was applied in its strict
reading — **the master alone must carry at least three parts on that one path** — and the classified
workbook was used as a cross-check, not as a source. The figure key was a veto only.

Measured on the 162 that were placed:

- Every one cleared the bar on the **master alone**. The minimum support was **3**, the median
  **17**, the maximum **171**. **Zero** needed the workbook to reach three.
- The workbook's **AIM axis** agreed with the chosen path on all 162 where it had anything to say.
- **No figure key contradicted the chosen path.** Two keys (`810-748`, `350-183`) carry no master
  or workbook evidence at all, so the veto simply had nothing to say — those two rest on the
  description, exactly as the ten engine-assembly keys did in part 2.

**The trap I had to avoid.** The classified workbook carries two axes per part: an AIM axis
(`aim_l1_fixed/l2/l3`) and the price list's own catalogue axis (`catalog_l1/l2/l3`). For these 164
the AIM axis is empty and only the catalogue axis is populated. My first run pooled both and read
the catalogue buckets as if they were competing AIM paths, which left 41 of the 164 unplaced. That
was wrong: the catalogue axis is not an AIM path at all. Its seven top-level buckets —
`Repair parts`, `Competitive parts`, `Accident parts`, `Hardware & consumables`,
`High value repair`, `Other / review`, `Comfort parts` — do not appear anywhere in the AIM domain,
while the workbook's AIM axis uses the same 22 family names the master uses. I re-ran with the
catalogue axis separated. That is the whole difference between 123 placed and 162.

## 3. Where the 162 landed

| AIM family (level 1) | parts |
|---|---|
| Accident & Body | 31 |
| Electrical | 23 |
| Chassis Frame | 15 |
| Suspension | 12 |
| Engine | 11 |
| Wheels Hub | 11 |
| Cabin Interior | 11 |
| Transmission | 8 |
| Steering | 8 |
| Intake Exhaust Emission | 6 |
| Fuel System | 6 |
| Brakes | 5 |
| Lighting | 4 |
| Lubrication | 4 |
| Cooling | 4 |
| Driveline Axle | 2 |
| Clutch | 1 |

**No new class name was created.** Every one of the 70 distinct leaves used already existed on the
master.

## 4. The two rows I did not place

| Part number | Description | List EUR | Why |
|---|---|---|---|
| `8976863171` | `BAR; BACK,RR` | 43.40 | The master splits this exact text across two leaves — 7 parts on `Accident & Body > Bumpers > Bumper Assembly` and 4 on `Accident & Body > Panels > Bumper`. Two strong paths, not one. Both families agree it is Accident & Body, but the leaf does not resolve, so I left it out rather than pick. |
| `8976863181` | `BAR; BACK,RR` | 41.16 | Same text, same split. |

The tiering study had marked both as clean Tier A rows (`tierA = True`, `undefendable = False`),
because at the **level-1** cut the description is unanimous. The disagreement only appears at the
leaf. So this is a guard firing, not a study error — and I left both out on the brief's instruction
not to guess to improve the count.

## 5. Four rows worth naming

Four placed rows were assigned to `Lighting` although both the description join and their figure key
point at `Electrical`:

| Part number | Description | Description / key say | Written | Why |
|---|---|---|---|---|
| `8971269752` | `LAMP; LICENSE PLATE` | Electrical (13 parts) | `Lighting > Lighting > Lamp` | The 13 master rows with that text carry `aim_l1` = Electrical but `aim_l1_fixed` = Lighting. The precedent the builder actually uses says Lighting. |
| `7552087070` | `BRACKET; LAMP,RR COMB` | Electrical (4) | `Lighting > Lighting > Lamp` | Same pattern, 5 support rows. |
| `8981928940` | `LENS; HEADER CONSOLE` | Electrical (3) | `Lighting > Lighting > Lens` | Same pattern, 3 support rows. |
| `8983260230` | `HARNESS; HEADLAMP` | Electrical (7) | `Lighting > Lighting > Lamp` | Same pattern, 7 support rows. |

I followed the master's effective convention (the `*_fixed` values) because that is what the master,
its deliverable builder and part 2 all use. If the right answer is `Electrical` for these four, then
the master's own 28 rows for those texts need changing first — that is a decision about the
classification, not about this fill. The four are listed in `apply_fill_summary.json`.

## 6. What was written on each filled row

Only eight columns were touched, on the 162:

| Column | Before | After | Why |
|---|---|---|---|
| `aim_l1`, `aim_l2`, `aim_l3` | empty | the decided path | the point of the fill |
| `aim_l1_fixed`, `aim_l2_fixed` | empty | same as `aim_l1` / `aim_l2` | so the builder's precedence cannot silently drop the label |
| `has_aim` | `0` | `1` | matches the master's own rule (measured: 19,835 rows carry `1` and all of them have a family) |
| `aim_source` | `not_classified` | `export_pr00_20260924` | the stamp |
| `aim_changed` | `0` | `export_pr00_20260924` | the stamp |

Deliberately **not** touched: `description` (the master keeps it blank for these rows — part 2 also
left it blank; filling it would be a different claim and the pair already supplies a description
from the sales file), `cat_l1/l2/l3` (the price-list node was already right), `cat_pms_flag`
(already set, 77 rows at `1`), the figure-key columns, the eight `jp_*` columns, and the two money
columns (which stay `0.0` — the same window check part 2 ran applies, and I did not re-derive it).

The exact stamp on all 162, in both `aim_source` and `aim_changed`: `export_pr00_20260924`.

## 7. The 92 and the 44

- **The 92.** Compared row by row against the pre-fill backup: **not one changed**, and none carries
  the fill stamp. All 92 still carry `aim_l1_fixed` = `Unknown` (87) or `Unknown Review` (5). That
  decision is still yours.
- **The 44.** Compared against the pre-fill backup, which is the state after the part-2 append:
  **all 44 byte-identical**, and all 44 still carry `export_pr00_20260924`. (The pre-append backup
  does not contain them at all — I checked that 44 of 44 are absent from it, so the pre-fill file is
  the correct baseline for that comparison.)

## 8. Files, sizes and hashes

| Item | Path | Size | sha256 |
|---|---|---|---|
| Backup (before) | `01_data\00_derived\aim_master_v2.csv.bak_pre_export_fill_20260924_140856` | 28,516,277 | `8e8f7a9a640be9643fe68740c5dc3ec5b805c882502d050f914769055d659a99` |
| The master (after) | `01_data\00_derived\aim_master_v2.csv` | 28,529,377 | `cd69c50604dbd4ff2ec9a3a46a446f0d4a34230c3ebc3e43628725acef731507` |
| Rebuilt CSV | `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.csv` | 13,108,965 | `7437b549ad08d4a102c86b39caaccc263f1834f9f379a5e19395f83cfc912280` |
| Rebuilt Excel | `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.xlsx` | 9,272,663 | `7316a9b530d32aaab1e48d898f78e5e332567dbf54e057b1c4ef818a0cfa0dc5` |
| Copy of the pair before this rebuild | `01_data\00_derived\_backup_20260924_pair_before_fill\` | 13,103,773 + 9,269,411 | `bd42e160…d92a55` / `2cd4c832…e3f34f` |

Row count 165,257 → **165,257**. 32 columns, same order. UTF-8, no BOM. CRLF only. The 2026-09-21
pair is untouched. Nothing earlier was overwritten or deleted.

## 9. How I know it worked

Every check was run against the written files and the backups, by part number:

| Check | Result |
|---|---|
| Row count unchanged at 165,257 | PASS |
| Header identical, 32 columns, same order | PASS |
| Rows that changed at all == exactly the 162 targets | PASS — 162 |
| No column outside the eight AIM columns changed anywhere | PASS |
| All 162 carry the levels, `has_aim = 1` and the stamp | PASS |
| No duplicate part numbers, still sorted, no BOM, CRLF only | PASS |
| The 92 blocked rows byte-identical to the backup, none stamped | PASS |
| The 44 appended rows byte-identical, all still stamped | PASS |
| Rebuilt CSV carries the new AIM levels for all 162 | PASS |
| Rebuilt CSV still carries the stamp for all 44 | PASS |
| Rebuilt CSV row count equals the master row count | PASS |

The gate inside `apply_export_pr00_fill_20260924.py` runs all of this **before** any backup or
replace and refuses to proceed on a miss, so a bad write cannot have happened quietly.

## 10. What I could not verify, and two things to know

1. **I did not re-derive the tiering.** The 164 are taken from `would_land_free.txt` as instructed,
  and I confirmed the file holds 164 distinct part numbers with no overlap against the 92 or the 44.
2. **I did not hand-check all 162 against the EPC.** No EPC or Snap-on lookup was run, as instructed.
  The placement rests on the description agreement, which is the method the brief specifies.
3. **The rebuilt pair's `aim_source` column is not the master's `aim_source` for these rows.** The
  pair builder prefers the classification overlay's own `aim_source` over the master's. Because all
  160 of these part numbers that appear in the overlay carry `pr00_catalog` there, the pair prints
  `pr00_catalog` even though the master says `export_pr00_20260924`. Only the 2 not in the overlay
  (`280510800`, `36091500`) show the new stamp. The **AIM levels** are correct on all 162 — that is
  what the pair is for. This behaviour is pre-existing and not something I introduced; I am flagging
  it because the brief asked for the stamp to be visible. If the stamp must show in the pair, the
  fix is in `export_aim_pn_categories_figkey_xlsx.py`, and that is a change to a shared builder —
  your call.
4. **One placed row sits on a leaf that reads like a holding pen:**
  `8979050131` `BOX; GLOVE,INST PNL` → `Electrical > Switch Relay Fuse > Review needed`. It is
  correct by the master's own convention — nine rows carry that text and eight of them are on that
  exact leaf. Flagged so it is not a surprise in a later review.
5. **`has_catalogue_node`** on these rows was `1` for 155 and `0` for 7 before the fill, and I left
  it alone. This is the opposite of part 2, where the 44 had no catalogue node at all — which is
  exactly why these 164 landed free and those 44 did not.
6. **The board row repair.** See §11.

## 11. The broken board row

`00_docs\agent\DELEGATOR_BOARD.md`, the row starting `| 2026-09-24 12:50 | cursor (scraper Phase 0)`
carried 9 pipes where the change-log table takes 6 (5 cells). A later fragment had been appended
inside the same line instead of on a new line. Every row under it in that block rendered as part of
one broken row.

Repaired by keeping the first five cells exactly as they were — time, agent, and the substance of
"What changed", "Files touched" and "Next step" — and dropping the two extra fragments that came
after `Eucon password still to change. |` and the duplicated trailing segment. The removed text
described C2 and C5 work on the price ledger, which was already recorded in the 12:20 row below.

Result: every row in that block now has 5 cells, matching the header. One other row in the file
(line 32, the 2026-09-18 21:05 warranty row) has only 3 cells. **That one was already like that and
is outside this brief, so I left it.** Worth someone's attention separately.

Backup of the board before the repair:
`00_docs\agent\DELEGATOR_BOARD.md.bak_pre_row_repair_20260924_141304` (31,181 bytes → 30,114 bytes).

---

## 12. Files

Written by this pass:

- `01_data\91_build\apply_export_pr00_fill_20260924.py` — the fill, with its gate
- `01_data\91_build\export_aim_fill_20260924\derive_paths_164.py` — the decision rule
- `01_data\91_build\export_aim_fill_20260924\decision_164_final.csv` — the 164 with their evidence
- `01_data\91_build\export_aim_fill_20260924\apply_fill_summary.json` — the run summary
- `01_data\91_build\export_aim_fill_20260924\verify_fill.py` — the independent verification
- the read-only probes in the same folder

Read-only inputs: `EXPORT.XLSX` · `would_land_free.txt` · `carried_out_blocked_precedence.txt` ·
`carried_out_not_in_master.txt` · `tierA_audited.csv` · `aim_master_v2.csv` ·
`aim_pn_classification_20260920.csv` · `AIM_Master_PN_Categories_Figkey_20260924.csv` · the part-2
report and script.

Nothing published. No dashboard touched. No browser, no EPC run. No mail.
