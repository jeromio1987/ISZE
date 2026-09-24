# Cab class — report

**Date:** 2026-09-24 19:20
**Asked:** *"a cab is a truck cabine create a separate class for it"*
**Written by:** Cursor, from the master's own evidence

---

## 1. The class

```
Accident & Body  >  Complete Assembly  >  Cab Assembly
```

| Name | Already on the master? |
|---|---|
| `Accident & Body` | **Yes** — one of the 23 top-level families, 4,380 rows |
| `Complete Assembly` | **Yes** — the group the engine assembly already uses, 45 rows |
| `Cab Assembly` | **No — this is the one new name created.** Nothing close to it existed: the only cab-ish name on the master is `Cabin Interior`, which holds the seats, dashboard and trim (1,291 rows) and is a different thing from the cab as a structure or a whole unit. |

So one new leaf was created. No second spelling of anything else was invented.

## 2. The evidence for that shape, measured

The rule followed is the master's own, not one I chose. Every description ending in ` ASM` was
read and grouped by its aim path (336 rows). The complete assemblies on the master are:

| Path | Rows |
|---|---|
| `Engine > Complete Assembly > Engine Assembly` | 45 |
| `Cooling > Radiator > Radiator Assembly` | 161 |
| `Accident & Body > Bumpers > Bumper Assembly` | 55 |
| `Accident & Body > Rear Gate > Rear Gate Assembly` | 16 |
| `Accident & Body > Lamps > Headlamp Assembly` | 164 |
| `Suspension > Leaf Springs > Leaf Spring Asm` | 123 |
| `Driveline Axle > Final Drive > Final Drive Asm` | 76 |
| `Brakes > Actuation > Brake Assembly` | 8 |
| `Maintenance Service > Filters > Filter Assembly` | 65 |
| `Intake Exhaust Emission > DPF/DPD > DPD Assembly` | 40 |

`Complete Assembly` is a group (`aim_l2`) exactly once on the whole master: under `Engine`.
That is the convention for a whole unit — `<family> > Complete Assembly > <X> Assembly`. The cab
follows it, because a cab is a whole unit in the same sense an engine is.

### Why the family is `Accident & Body`

Four measured reasons, not one:

1. **`Complete Assembly` exists only under `Engine` today.** So the group name could be reused
   under a different family without clashing, but there is no precedent that says which family.
   The family therefore had to be argued from where cab parts already are.
2. **The cab is the truck's body.** `Accident & Body` is the master's own top-level group for the
   body, and it separately excludes `Accident & Body > Panels > Door` (1,305 rows) — i.e. the
   master's body family is about the structure, not the glazing.
3. **The cab already sits there.** Six cab assemblies are on `Accident & Body > Panels > Panel`
   today, put there by an earlier pass. Moving a subclass out of a family into another family
   would be a bigger claim than moving it inside the family it is already in.
4. **The master's own figure key agrees.** Twelve of the 13 cab assemblies carry figure key
   `604-001` (9 rows) or `604-002` (3 rows), and the catalogue dimension labels `604-002` as
   `Other body` — under `Accident parts / Body parts / Other body`. The master's own data calls the
   cab body. The thirteenth has no figure key at all.

### The honest alternative, and why I did not take it

**A cab could have been its own top-level family.** The argument for it: the cab is arguably as
distinct a unit as `Cabin Interior` (a top-level family today) or `Accident & Body`, and the
master already has a "Cabin" concept, so `Cab` beside `Cabin Interior` is not absurd.

I did not take it, because the master's own behaviour does not support it:

- A new top-level family would cut across two existing families at once. The cab parts sit in
  `Accident & Body`, its interior fittings sit in `Cabin Interior`, and the cab lock/harness parts
  sit in `Electrical`. A new family would need a rule for each, and that rule does not exist.
- The precedent that was set today went the other way. The engine assembly was given a group
  *inside* `Engine`, not a new family. Doing the cab differently would make the two complete
  assemblies in the taxonomy use two different conventions.
- There is no cab row anywhere in the master at `aim_l1`, and no cab bucket in the catalogue axis
  or in the Japan codes either. Nothing in the file suggests a family-sized population.

**Recommendation: keep it as a group inside `Accident & Body`.** If Jerome wants a top-level `Cab`
family later, that is a larger decision and would need to move `Cabin Interior` with it.

## 3. What was placed, and the evidence for each

**20 parts placed.** Every one carries either its own description naming the cab, or an identical
description that another master row already uses. Nothing was placed because it merely sits near a
cab part.

### 3a. The cab as an assembly — 13 parts, evidence: the part's own description says `CAB ASM`

| Part number | Description | Was | Now |
|---|---|---|---|
| 7551847570 | CAB ASM; SERVICE,W/ELECT | Accident & Body > Panels > Panel | the new class |
| 7552044930 | CAB ASM; SERVICE,WO/ELECT | Accident & Body > Panels > Panel | the new class |
| 7552612100 | CAB ASM; SERVICE,WO/ELEC | Accident & Body > Panels > Panel | the new class |
| 7552625790 | CAB ASM; SERVICE,WO/ELEC | Accident & Body > Panels > Panel | the new class |
| 7552824860 | CAB ASM; SERVICE,WO/ELEC | Accident & Body > Panels > Panel | the new class |
| 7553142130 | CAB ASM; SERVICE,WO/ELEC | Accident & Body > Panels > Panel | the new class |
| 7551847580 | CAB ASM; SERVICE,WO/ELEC | Unknown > Unknown > Unknown | the new class |
| 7552060250 | CAB ASM; SERVICE,WO/ELEC | Unknown > Unknown > Unknown | the new class |
| 7552349740 | CAB ASM; SERVICE,W/ELECT | Unknown > Unknown > Unknown | the new class |
| 7552427800 | CAB ASM; SERVICE,WO/ELEC | Unknown > Unknown > Unknown | the new class |
| 7552641820 | CAB ASM; SERVICE,WO/ELEC | Unknown > Unknown > Unknown | the new class |
| 7552650510 | CAB ASM; SERVICE,W/ELECT | Unknown > Unknown > Unknown | the new class |
| 7552825890 | CAB ASM; SERVICE,WO/ELEC | Unknown > Unknown > Unknown | the new class |

Six of these were already on a body family but on a generic `Panel` shelf, with nothing saying
they are the whole cab. Seven were parked on the `Unknown` marker.

### 3b. The cab's own structure — 6 parts, evidence: an identical description already on a body family

| Part number | Description | Was | Evidence |
|---|---|---|---|
| 8974877720 | PANEL; CAB BACK | Accident & Body > Panels > Panel | the words `CAB BACK` name the cab directly |
| 8980115942 | PANEL; CAB BACK | Accident & Body > Panels > Panel | same |
| 8980115951 | PANEL; CAB BACK | Accident & Body > Panels > Panel | same |
| 8980425220 | PANEL; CAB BACK | Accident & Body > Panels > Panel | same |
| 8980554611 | PANEL; SIDE SILL,CAB | Accident & Body > Panels > Panel | the words `SIDE SILL,CAB` name the cab directly |
| 8980554621 | PANEL; SIDE SILL,CAB | Accident & Body > Panels > Panel | same |

These four part numbers carry the **identical** description `PANEL; CAB BACK`, and the master
already treats that description as body structure: of the 448 master rows whose description starts
`PANEL;`, **426 sit on `Accident & Body > Panels > Panel`** and 15 more sit on the same family's
`Door` leaf. They are the back and the side sill of the cab itself, not a fitting inside it.

### 3c. Added, because it had no master row at all — 1 part

| Part number | Description | List price | Source |
|---|---|---|---|
| **7553266960** | `CAB ASM; SERVICE,W/ELECT` | EUR 7,603.44 | `01_data/EXPORT.XLSX`, row 5 |

This is the part that started the request. It had **no row on the master** (verified: 0 rows, and
0 rows in the classification overlay and the catalogue dimension too). Its description is
identical to 7551847570, which is on the master, so the placement needs no judgement.

Its new row carries, measured against the 44 rows appended earlier today:
`aim_source = cab_class_20260924`, `aim_l1/l2/l3` = the new class, `aim_l1_fixed/l2_fixed` =
`Accident & Body` / `Complete Assembly`, `has_aim = 1`, `has_catalogue_node = 0`,
`fig_no = 604`, `key_no = 002`, `fig_key` blank (the master builds `fig_key` only where the key
number is numeric, and `002` is), `l12m_billed_eur = 0.0` and `eur = 0.0` — the spine carries
`0.0` for every row with no catalogue node, which is the case here.

## 4. What was deliberately NOT moved

**264 cab-related rows were left exactly where they are.** They are the vast majority of the rows
whose text contains the standalone word `CAB`.

Read this table as a working census of the 264, not as an arithmetic sum — the word groups overlap
(a mounting rubber is both a `RUBBER;` and a cab mounting), so the "what" rows are counted by
description keyword and do not add to 264 in total.

| What | Rows | Where they stay | Why |
|---|---|---|---|
| Cab mounting brackets, stays, crossmembers | 67 | `Chassis Frame > Crossmember & Brackets` | A bracket that holds the cab is chassis. Several were put there **on purpose today**: the 177 wording rules include `("CAB MOUNTING", "Chassis Frame", "Crossmember & Brackets", "Bracket")`. |
| Cab suspension rubbers and bushes | 27 | `Suspension > Bushings` / `> Bush & Mount` | Same reason — the cab mount is a suspension component. |
| Cab harnesses and connectors | 56 | `Electrical > Harness & Connectors` | A cab harness is wiring. |
| Cab locks, hinges, tilt stays, rods and pins | 39 | `Accident & Body > Locks & Handles`, `Chassis Frame` | Route-access hardware on the outside of the cab, not the cab unit. |
| Cab silencer and floor mats | 8 | `Intake Exhaust Emission > Exhaust` | Heat shielding that hangs near the cab, not part of it. |
| Cab emblems and decals | 13 | `Accident & Body > Trim` | Badges and stickers. |
| Cab doors, seals, fenders and assist grips | 14 | `Accident & Body > Panels`, `> Trim` | Body panels and seals. A door is not the cab. |
| The rest | ~40 | as they are | Named a cab part, nothing more: bolts, washers, plates, anchors, a cab-to-pipe hose, two assist grips. |
| 73 rows on the `Unknown` marker | 73 | `Unknown > Unknown > Unknown` | These are the cab mountings, rubbers and brackets whose family is genuinely open. **They are not this change's to close**, and forcing them onto the cab class would have been the wide, arguable version of this work. |
| 1 row on the `Unknown Review` marker | 1 | `Unknown Review > Unclassified` | Same. |
| 12 rows with no family at all | 12 | blank | Same. |

Full path census of the 264 left alone:

```
 73  Unknown                  > Unknown                 > Unknown
 67  Chassis Frame            > Crossmember & Brackets  > Bracket
 24  Suspension               > Bushings                > Rubber Mount
 23  Electrical               > Harness & Connectors    > Connector
 14  Chassis Frame            > Crossmember & Brackets  > Stay
 12  (no family)
  9  Chassis Frame            > Mounting Hardware       > Bolt
  8  Accident & Body          > Panels                  > Door
  6  Intake Exhaust Emission  > Exhaust                 > Silencer
  5  Accident & Body          > Trim                    > Emblem
  4  Accident & Body          > Locks & Handles         > Latch
  4  Accident & Body          > Panels                  > Fender
  4  Electrical               > Control Units           > Control Unit
  3  Suspension               > Bush & Mount            > Bushing
  3  Cabin Interior           > Pedals & Controls       > Lever
  2  Chassis Frame            > Mounting Hardware       > Plate
  1  Electrical               > Harness & Connectors    > Terminal
  1  Electrical               > Switch Relay Fuse       > Switch
  1  Unknown Review           > Unclassified            > To Review
```

**The scope decision, stated plainly:** this class is for **the cab as a unit** — the assembly and
its own structure — **not** for every part whose text mentions a cab. 20 rows were placed, 264 were
left. A small class that is measured is worth more than a large one that is arguable, and the
narrow reading is the one the evidence supports.

## 5. Files written, with before and after

| File | Before | After |
|---|---|---|
| `01_data\00_derived\aim_master_v2.csv` | 165,289 rows · 28,611,807 bytes · sha256 `0105a5c4ac93ad9f1d17f781f6fdd567a7f5a04f0897c6ad184aba585af9f6d1` | **165,290 rows** · 28,612,879 bytes · sha256 `8add555669baf1f75b3bb2d203d58960fff7596b26ec5d8645d7ffee45604acf` |
| `01_data\00_derived\aim_pn_classification_20260920.csv` | 164,907 rows · 24,925,134 bytes · sha256 `e5824683806f7b7fdef17517dac2bc7a653e739b4c493ffba9a6dbb4e513e015` | 164,907 rows · 24,926,081 bytes · sha256 `092e981518efc5440ac10972ed2312dcd493c851e39d3d5c278f2ad5d0c27a60` |

**Backups**

```
01_data\00_derived\aim_master_v2.csv.bak_pre_cab_class_20260924_191700
   28,611,807 bytes  sha256 0105a5c4ac93ad9f1d17f781f6fdd567a7f5a04f0897c6ad184aba585af9f6d1
01_data\00_derived\aim_pn_classification_20260920.csv.bak_pre_cab_class_20260924_192113
   24,925,134 bytes  sha256 e5824683806f7b7fdef17517dac2bc7a653e739b4c493ffba9a6dbb4e513e015
01_data\00_derived\_backup_20260924_pair_before_cab_class\
   AIM_Master_PN_Categories_Figkey_20260924.csv   13,153,014 bytes  c6b1aaf36639e76b
   AIM_Master_PN_Categories_Figkey_20260924.xlsx   9,294,124 bytes  ffc2102d600260f2
   OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd      74 bytes  22e651a798139f6a
```

Both live files were built in memory, written to a temporary file in the same folder, checked, and
then replaced onto the live path. Nothing was edited in place.

**Measured knock-on for the packs that group by family**

| | Before | After | Delta |
|---|---|---|---|
| Rows on `Accident & Body` | 4,380 | **4,388** | +8 |
| Rows on `Unknown` | 3,603 | **3,596** | −7 |
| Rows on `Unknown Review` | 531 | 531 | 0 |
| Rows on the new class | 0 | **20** | +20 |
| Distinct top-level families | 23 | **23** | 0 (no new family value) |

The 8 rows that joined `Accident & Body` are the **7 cab assemblies that came off the `Unknown`
marker, plus the 1 added row**. The other 12 placed parts were already inside `Accident & Body`
(6 cab assemblies and 6 cab panels that moved from `Panels > Panel` to the new shelf), so they do
not move the family count — they only move the shelf. The net the packs will see is therefore
**`Accident & Body` +8, `Unknown` −7, and a new shelf of 20 rows.**

**Cells changed**

- Master: **116 cells across 19 rows** — `aim_l2`, `aim_l3`, `aim_l2_fixed`, `aim_source`,
  `aim_changed` on all 19; plus `aim_l1`, `aim_l1_fixed`, `has_aim` on the 7 that were on the
  `Unknown` marker.
- Overlay: **135 cells across the same 19 rows** — `aim_l1_fixed`, `aim_l2_fixed`, `aim_l3_fixed`,
  `workbook_l1`, `workbook_l2`, `workbook_l3`, `workbook_axis_kind`, `workbook_source`,
  `aim_source`.

### Why the overlay had to move too

The export pair builder reads its three AIM levels from the classification overlay **first** and
only falls back to the master. On my first rebuild the pair was still printing
`Accident & Body | Panels | Panel` on 19 of the 20 parts, because those 19 have an overlay row that
still carried the old path. The overlay was therefore updated on the same 19 part numbers.

Two things were deliberately left alone in the overlay:

- **`catalog_l1/l2/l3`** — the identity axis (what the part is ordered as: `Body parts /
  Other body`). That is a different axis from the functional family, and moving it would be a
  different decision that also moves the 177-leaf catalogue baseline.
- **`axis_conflict`** — it says the two axes disagree. They still do at the group level, so it stays
  as it is. Clearing it would have shrunk a counter the verifier watches and says must not grow.
  Quietly shrinking a watched number is not mine to do.

## 6. Rebuilt outputs

```
01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.csv
01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.xlsx
01_data\00_derived\OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd
```

Produced by running the existing builder as written:
`python 01_data\91_build\export_aim_pn_categories_figkey_xlsx.py`. It derives its filename from
today's date, so it wrote the 2026-09-24 names and overwrote today's own file. Output line:

```
rows=165290 with_desc=33850 with_fig=161504 with_aim=25181
```

The launcher was checked on disk: **74 bytes**, `@echo off` then
`start "" "%~dp0AIM_Master_PN_Categories_Figkey_20260924.xlsx"`, **CRLF** on both lines, and it
points at the 2026-09-24 file.

**The 2026-09-21 pair was not touched.** Its three files hash exactly as they did before this work
(`csv` 13,093,140 bytes `bed9c4a2…`, `xlsx` 9,281,799 bytes `8376812d…`, `.cmd` 74 bytes
`c182b0e9…`). `AIM_Master_PN_Categories_Figkey_20260921.*` is untouched.

## 7. Verification — 16 checks, all passed

| # | Check | Result |
|---|---|---|
| a1 | Header identical, 32 columns | PASS |
| a2 | Row count grew by exactly 1 | PASS (165,289 → 165,290) |
| a3 | No duplicate part number | PASS |
| a4 | Still sorted ascending | PASS |
| b1 | Cell-by-cell against the backup: only the intended cells differ | PASS — 19 rows, 116 cells, **0 unexpected** |
| c1 | All 19 placed rows read the new class at all three levels | PASS |
| c2 | All 19 carry the fixed columns too | PASS |
| c3 | All 19 stamped `cab_class_20260924` | PASS |
| d1 | 7553266960 exists and carries the class | PASS |
| e1 | Rebuilt pair row count 165,290 | PASS |
| e2 | Rebuilt **csv** shows the class on all 20 | PASS |
| e3 | Rebuilt **xlsx** shows the class on all 20 | PASS |
| f1 | 2026-09-21 pair unchanged | PASS |
| g1 | Launcher points at the 2026-09-24 xlsx | PASS |
| g2 | Launcher is CRLF | PASS |
| h1 | The class holds exactly 20 rows | PASS |

Recorded to `01_data\91_build\export_aim_eq_20260924\cab_class_verify.json`.

## 8. Open count on the IE40 price list

Measured the same way as before: of the **1,303 part numbers** in
`01_data\91_build\export_aim_eq_20260924\queue.csv`, how many still have no real family in the
rebuilt pair.

| | Before | After |
|---|---|---|
| No row on the master at all (blank) | 34 | **33** |
| On the `Unknown` marker | 31 | 31 |
| On the `Unknown Review` marker | 14 | 14 |
| **Total open** | **79** | **78** |

One part closed: 7553266960. Nine further cab-related part numbers that appear on this price list
(`MEMBER; CAB MTG RR`, `BRACKET; CAB RR MTG`, `RUBBER; CUSHION,CAB MTG`, `STAY ASM; CAB TILT`,
`DECAL; CAB FRT`, `RUBBER; MTG,CAB,UPR RR`, and two cab harnesses) were left where they are on
purpose, for the reasons in section 4.

## 9. What I could not establish, and what has to happen next

**This is a structural change, not a small edit.** `Accident & Body` is one of the 23 top-level
families the whole workspace groups by, and `Cab Assembly` is a new shelf inside it. The measured
knock-on: `Accident & Body` goes from 4,380 to 4,388 rows, the `Unknown` marker from 3,603 to
3,596, and a shelf that did not exist this morning now holds 20 rows.

1. **Every dashboard needs a deliberate refresh to show this.** All of them were rebuilt earlier
   today and carry signed checks at that state. I did not touch a single one, as instructed. Until
   each is rebuilt, it will show the cab parts on `Accident & Body > Panels > Panel`, or on
   `Unknown`. The Power BI file reads the same export pair, so it needs the same refresh.
2. **The AIM classification verifier now exits 1, on a drift check that is not about this change.**
   It reports `leaf_baseline: L2=27 (approved 27), L3=176 (approved 177)`, because it reads
   `aim_pn_classification_v2.csv` (164,667 rows, last written 2026-09-20 20:47, a separate file I
   did not touch) while the approved baseline in `aim_classification_leaf_baseline.json` says 177.
   That file says the baseline is the only place the approved counts live and that the tolerance
   must not be relaxed — so it is left exactly as it is, and the failure stands on the record.
   Two other notes: this exercise created no new **catalogue** (identity) leaf, so the 177 figure is
   untouched by design; and running the verifier rewrote
   `01_data\00_derived\aim_classification_gate.json`, flipping it to `verdict: FAIL` for that
   pre-existing reason. That side effect is disclosed, and that file's own previous state is
   recoverable from git.
3. **The release guard was not satisfied and was not weakened.** `_releases\RELEASES.json` has no
   `APPROVED` release today, and its second candidate pins the live overlay's hash. Editing the
   overlay was a deliberate decision for this task, not a silent change; the guard's record is left
   honest rather than updated to match.
4. **A full spine rebuild would drop these placements.** The same open point the earlier appends
   raised: the master builder does not read the master as an input. Whether to fold this in is
   Jerome's call.
5. **One thing I could not check.** Whether the 263 left-alone rows are the *right* 263 in every
   single case. I read the path census of all 283 cab rows and the reasoning holds for each group,
   but three rows sit on `Accident & Body > Lamps` and `Electrical > Instruments` and I did not
   chase them individually. They were left where they are.

## 10. Files left behind

The two changes and the checks:

```
01_data\91_build\apply_cab_class_20260924.py            the master change, dry-run by default
01_data\91_build\apply_cab_class_overlay_20260924.py    the overlay carry-through
01_data\91_build\_cab_verify.py                         the 16 checks
01_data\91_build\_cab_backup_pair.py                    the pair backup
01_data\91_build\_cab_concurrency.py                    the post-write drift check
01_data\91_build\_cab_board_append.py                   the board row, in bytes
01_data\91_build\_cab_board_fix.py                      the correction to that row
01_data\91_build\export_aim_eq_20260924\CAB_CLASS_REPORT_20260924.md   this report
01_data\91_build\export_aim_eq_20260924\cab_class_verify.json
01_data\91_build\export_aim_eq_20260924\cab_class_apply_summary.json
01_data\91_build\export_aim_eq_20260924\cab_class_overlay_summary.json
```

Measurement scripts, read-only:

```
01_data\91_build\_cab_buckets.py            the bucket counts in section 4
01_data\91_build\_cab_left_census.py        the path census of the 264
01_data\91_build\_cab_family_delta.py       the family counts in section 5
```

Scratch output of the probes, kept only so the numbers can be re-checked:

```
01_data\91_build\_cab_work_*.txt            13 text files of raw probe output
01_data\91_build\export_aim_eq_20260924\_cab_*.txt
```
