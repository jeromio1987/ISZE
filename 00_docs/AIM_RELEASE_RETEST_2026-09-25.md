# AIM classification release — re-test of the approved 2026-09-20 file

**Date:** 25 September 2026
**Agent:** cursor (release wiring + retest), Block D of `04_tools/delegation/CURSOR_WORK_ORDER_UNIVERSE_2026-09-24.md`
**Approved release tested:** `01_data\00_derived\_releases\aim_pn_classification_release_2026-09-20.csv`
SHA-256 `60111c104ddeb466e6c15f084039639d35172056b0fd2ea10225a3c50da610e0`, 164,907 rows, 27 columns.
Hash re-verified by me before and after this work; the file was not written to.
**Nothing was approved, released, deleted or re-pointed. No classification CSV was changed. The gate file was not changed.**

---

## 1. The lineage, as it actually is

The approval changed nothing because **no reader in the chain names a release at all**. Here is every
reader that matters, and what it actually opens.

| Reader | What it opens | Line |
|---|---|---|
| The safety gate | `01_data\00_derived\aim_pn_classification_v2.csv` (164,667 rows, 16 columns, written 2026-09-20 20:47) | `01_data\91_build\verify_aim_classification.py:29` |
| The safety gate, two checks | `01_data\00_derived\aim_pn_classification_v2.meta.json` — a hard-coded path, not resolved from the file being checked | `verify_aim_classification.py:201` |
| The safety gate, leaf baseline | `01_data\00_derived\aim_classification_leaf_baseline.json` — this *is* read, and it already says 177 | `verify_aim_classification.py:61` |
| The master builder | `pr00_classification.csv`, `price_bp_weighted_compare_pn.csv`, `sales_fact.parquet`, the AIM workbook. **No classification release.** Output is `aim_master_v1.csv` | `01_data\91_build\build_aim_master.py:38` |
| The master that the packs read | built from `aim_master_v1.csv`, then edited in place by a chain of `apply_*` scripts. **No classification release.** | `01_data\91_build\build_aim_master_v2_and_priority.py:52,77` |
| The four AIM comparison / deep-dive pages | `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.csv` (built 2026-09-24 19:21) | `04_tools\aim_db_dlr_deep_dive\build_aim_db_dlr.py:45` and `build_aim_comparison.py:39` |
| That export | `aim_master_v2.csv` as the spine, plus `aim_pn_classification_20260920.csv` as the **overlay read first** for the three AIM levels | `01_data\91_build\export_aim_pn_categories_figkey_xlsx.py:19,20` |
| The release guard | `_releases\RELEASES.json` + the frozen file. **Nothing calls it.** No `assert_release` anywhere in the Isuzu Universe build (`Isuzu Universe\_build_final\build.py` was grepped: absent), and the README's two-line snippet was never added | `_releases\check_classification_release.py` |

**So the file and line where a release would have to be named, for the approval to mean anything:**

1. **For the gate's verdict to be about the approved thing:** `verify_aim_classification.py:29`
   (`CLASS_V2`) **and** `:201` (the meta path). Both, not one.
2. **For the pages to be built from a release:** `export_aim_pn_categories_figkey_xlsx.py:20`
   (`SRC_CLASS`). But that only sets the overlay; the spine is `aim_master_v2.csv`, which is not
   built from any release, so the pages would still be master-first for their part-number list.
3. **For the guard to bite:** a call to `assert_release(...)` at the top of the Universe build. It is
   not there.

The three classification files are genuinely different objects:

| File | Rows | Cols | Written | Read by |
|---|---:|---:|---|---|
| `aim_pn_classification_v2.csv` | 164,667 | 16 | 2026-09-20 20:47 | the gate, and nothing else in the workflow |
| `aim_pn_classification_20260920.csv` (overlay) | 164,907 | 27 | 2026-09-24 19:21 | the export pair, the classification paper, the pricing sim |
| `_releases\aim_pn_classification_release_2026-09-20.csv` (approved) | 164,907 | 27 | 2026-09-20 20:46 | nothing |

One more finding, worth its own sentence: the approved release is **byte-identical to the pre-write
backup** `aim_pn_classification_20260920.csv.bak_pre_export_aim_eq_20260924_20260924_142051`
(same SHA-256), and the register's other candidate hash `e5824683…` belongs to a **different** file
on disk — `aim_pn_classification_20260920.csv.bak_pre_cab_class_20260924_192113`. The register
records the candidate's path as `../aim_pn_classification_20260920.csv`, but the live overlay at that
path has moved twice since and carries `092e9815…`. **The register's candidate entry no longer
describes the file at its own path.**

---

## 2. The approved release against the live working file, on billed 2025

**Parts base.** `sales_fact.parquet`, calendar 2025, the named non-part keys removed (`REBATE`,
`TRANSPORT`, `LATE PAYMENT INTEREST`, `SERVICE`, `SERVICE FEE OUTSIDE EUROPE`,
`SERVICE FEE WITHIN EUROPE`) plus the lubricant lines (`5500*`), plus keys that do not start with a
digit. **EUR 32,330,198.32 on 16,831 part numbers.** Freight, rebates, interest and service fees are
out, as the brief requires. Note: the lubricants are stored under a 9-digit key in the billing
(`550047337`) and a 10-digit key in the classification files (`0550047337`), so I matched both forms.

**Against the live overlay** (`aim_pn_classification_20260920.csv`):

- **Catalogue tree (family / group / type): 0 rows changed, EUR 0.** The two files carry the same
  catalogue tree, row for row and key for key.
- **AIM label (family / group / shelf): 1,159 rows changed; 693 of them carry 2025 billing,
  EUR 469,278.08 = 1.45% of the base.**
- **Direction, and this is the single most useful number in the report: 1,147 rows move from a
  residual label (`Unknown`, `Unknown Review`, blank) to a named family; 0 rows move the other way;
  12 are named-to-named re-shelvings.** In euro: **EUR 410,396.98 leaves the residual labels for
  named families, and EUR 0.00 goes in the other direction.**
- **Net effect:** on the approved release, 2.57% of 2025 billed euro sits on a residual label
  (EUR 831,355.16). On the live file, 1.30% (EUR 420,958.18). **The live file is the better one on
  this measure, because the release predates four days of work.**

**Top 10 movements by euro — every one is an improvement, all in the same direction**
(shown as approved release → live file):

| Part number | 2025 EUR | Approved release | Live file |
|---|---:|---|---|
| 7552044930 | 28,928 | Panels > Panel | Complete Assembly > Cab Assembly |
| 7552825890 | 23,111 | Unknown > Unknown | Complete Assembly > Cab Assembly |
| 8983930170 | 20,473 | Unknown > Unknown | Axle Shaft > Drive Shaft |
| 7551936010 | 14,860 | Unknown > Unknown | Mounting > Engine Mount |
| 8982263280 | 11,272 | Unknown > Unknown | Emission Control > Catalyst |
| 7551847570 | 11,125 | Panels > Panel | Complete Assembly > Cab Assembly |
| 8975065311 | 9,358 | Unknown > Unknown | Seat > Seat Cushion |
| 7552824860 | 8,184 | Panels > Panel | Complete Assembly > Cab Assembly |
| 7551936000 | 6,319 | Unknown > Unknown | Mounting > Engine Mount |
| 8983938821 | 5,967 | Unknown > Unknown | Radiator > Radiator Assembly |

**Against the live master** (`aim_master_v2.csv`, 165,290 rows): 1,297 part numbers only in the
release, 1,680 only in the master; 1,778 AIM rows change, **977 with 2025 billing, EUR 501,318.10
(1.55%)**; 1,559 residual→named, 54 named→residual, 61 named→named. The 54 rows that go the wrong way
carry **EUR 0.00 in 2025 and EUR 0.00 all years** — they are all zero-billing rows, so no euro
regresses. On the catalogue tree the master differs on 5,936 rows worth EUR 2,434,948.39 (7.53%),
because the master's own `cat_*` columns are still the 17 September copy.

**Against the file the gate reads** (`aim_pn_classification_v2.csv`): 253 keys only in the release,
13 only in v2, and **1,352 catalogue rows differ, worth EUR 144,418.31 of 2025 billing (0.45%)**.
The five biggest are the regressions the memo described: 8978413790 and 8978413800 (EUR 23,598 and
18,731, release names them, v2 leaves them blank), 8971846991 (EUR 13,554, a spring on `Hardware`
in v2 that the release puts on `Suspension > Leaf / suspension spring`), 8972629330 (EUR 9,435,
`Air conditioning > Heater core` in v2, `Electrical sensors > Relay` in the release) and 8978339870
(EUR 8,318, `Electrical sensors > Relay` in v2, `Clutch parts` in the release).

**And the lubricant key form, which is a defect in its own right.** The release stores the
lubricants only as 10-digit keys: `0550047337` and `0550047252`. The billing stores them as
`550047337` and `550047252`, worth **EUR 433,820.16 and EUR 75,636.08 in 2025**. The release carries
no row for the billed key at all, so the release does not join to that billing. The live master
carries both forms and tags the billed keys as lubricants. That alone is 1.6% of 2025 parts euro.

---

## 3. The three white-paper examples, re-tested on the approved release

### (a) Isuzu Truck UK brake pads, 2024 → 2025, measured on the brake-pad group — **reproduces**

Measured on `sold_to_sap` in {2575, 2194, 146}, which is ISUZU TRUCK (UK) LIMITED:

| File | 2024 | 2025 | Change |
|---|---:|---:|---:|
| **Approved release, brake-pad leaf** | **EUR 357,044.75** (5,577 units) | **EUR 304,257.91** (3,772 units) | **−14.8%** |
| Approved release, Brake parts group | EUR 884,493.92 | EUR 772,017.80 | −12.7% |
| Live overlay | identical to the release | identical | — |
| Old combined file and `pr00_classification.csv` | EUR 352,670.75 (4,621) | EUR 302,549.55 (3,404) | −14.2% |

Both memo figures reproduce exactly: the release's **EUR 357,044.75 → EUR 304,257.91** and the live
files' **EUR 352,670.75 → EUR 302,549.55**. The example stands on the approved release, to the cent.
The separate EUR 347,389.58 → EUR 302,366.25 cut is a different thing — it is the `brake_pad` row in
`gps_spu_pms.csv`, and it reproduces there, but it is not the brake-pad group.

### (b) Portugal clutch, components against true kits — **the "kits" label still does not hold**

Measured on sold_to_sap 519 = IMOTORS, whole `Clutch parts` group:

| Year | Clutch group | True kits (`Clutch kit` leaf) | Components |
|---|---:|---:|---:|
| 2024 | EUR 59,269.19, 494 lines | EUR 8,316.87 (62 units) = 14.0% | EUR 50,952.32 |
| 2025 | EUR 22,689.46, 169 lines | EUR 2,701.59 (16 units) = **11.9%** | EUR 19,987.87 |

The memo's own kit figures (EUR 8,234.32 on 47 units in 2024, EUR 11,824.10 on 69 units in 2025)
reproduce in `sales_by_db_fig_key_year.csv` on figure key 201-650, which is a narrower cut than the
whole group — that is why my euro differs, not the conclusion. **The conclusion is the same in every
candidate: under nine tenths of Portugal's clutch-group euro is discs, covers, release bearings and
cylinders, not kits. The "462 to 461 kits" reading counts components. The example must be relabelled
to clutch components or recut.** Confirmed independently on the approved release.

### (c) Air-filter euro under "Air conditioning", and the 17-of-18 leaf check — **0.37% remains, one part number; the leaf check is met by the release**

Air-cleaner lines (description matching `FILTER;ACL`, `AIR CLEANER`, `ELEMENT;AIR`): EUR 2,738,756.40.

| Reading | Under "Air conditioning" |
|---|---:|
| By the part's description | **EUR 10,048.83, 82 lines, 0.367%** |
| By the leaf `Air filter` | **EUR 0.00, 0 lines** |

Both are true and they answer different questions. The 82 lines are **one part number, 8980913940
`FILTER; ACL`**. Its figure key is `130-006`, and `parts_catalog_dimension.csv` labels that key
**`Air filter`**. Its 2025 billing is EUR 2,794.95. So the residue is real but small: **one air
filter filed under Air conditioning, 0.37% of air-filter euro.** Everything the memo complained
about is fixed in the release — 8974995480 (EUR 255,235), 1876101132 (EUR 88,054), 5876100201
(EUR 85,417), 8981772710 (EUR 62,780) and 5876150521 (EUR 44,644) all sit on
`Filters > Air filter` in the approved release and are wrong in *today's* `pr00_classification.csv`.
That is the 21 September regression the memo described, and it is real.

**The leaf check.** The release carries **177** bottom-level values, including
`Filters > Filter element`, whose only row is `5864052180`. `pr00_classification.csv` — today, the
declared upstream — still carries that part as
`family='Competitive parts', group='Filters', level3_type='Filter element'`. The part has **zero**
billed lines in `sales_fact.parquet`, so the leaf moves no money. **The release meets the approved
177-leaf baseline.**

---

## 4. The four known faults

| Fault | Status on the approved release | Evidence |
|---|---|---|
| **4 Shell lubricant PNs under Wheel Rim** | **Still present, on the AIM axis.** | The release has 9 lubricant PNs. On the AIM label, exactly four carry `Wheels Hub > Wheel Rim`: 0550047252, 0550070643, 0550070645, 0550071985. All carry `line_kind = lubricant_or_tool`. On the catalogue tree, `catalog_l2 = 'Wheel Rim'` holds **zero** of them — every one is `Miscellaneous > Review needed`. So the fault is on the AIM family axis only. **The live master has fixed it:** all seven of its lubricant rows read `Fluids Chemicals > Lubricants`. |
| **Guide pin 8980475290 in brake pads** | **Still present, on the catalogue axis.** | Catalogue: `Competitive parts > Brake parts > Brake pad`. AIM label: `Brakes > Caliper > Guide Pin` — correct. The memo's claim that the guide pin is "in its correct group" holds only on the AIM axis. It bills EUR 2,770.92 in 2025 across 26 lines and EUR 17,198.45 all years, so it is not a rounding item. |
| **Bumper bars in leaf spring** | **Fixed on the release's own catalogue tree; still present in the separate maintenance tag.** | On the release, `Leaf / suspension spring` holds 1,608 rows and **zero** of them have a bumper description. But `parts_catalog_dimension.csv` tags **1,759** rows `pr00_level3_type = 'Leaf / suspension spring'`, and **151 of those sit on the release's `Bumper` leaf, worth EUR 95,318.68 of 2025 billing (EUR 353,283.39 all years)**. That tag is what the ranked maintenance view keys on, so the fault the memo named survives there. It is not a classification-release fault. |
| **Cab Assembly class (2026-09-24)** | **Not in the approved release, correctly — it post-dates it.** | Release: 0 rows. Live master: 20 rows, `Accident & Body > Complete Assembly > Cab Assembly`, **EUR 119,406.81 of L12M billing**. The live overlay has 19 of the 20; the master has all 20. |

**On the work order's two cab figures.** EUR 119,406.81 reproduces exactly. **EUR 111,125 does not
reproduce anywhere.** The largest single cab row is 7552044930 at **EUR 36,232.55**, not 111,125.
The figure **EUR 11,125.03 is 7551847570's** — the fifth-ranked row. The CAB ASM rows together hold
EUR 117,691.93 and the six non-assembly cab panels hold EUR 1,714.88. I searched the workspace for
`111,125` and the only hits are the two state documents that repeat the work order's own wording.
**My reading is that 111,125 is 7551847570's EUR 11,125.03 transcribed onto 7552044930**; I cannot
prove that, and neither figure appears in the cab-class report, which deliberately records only the
row count.

---

## 5. The leaf the gate fails on — 177 is right, and the baseline already says so

**I conclude 177 is correct and the leaf must stay. The gate is not wrong; the file it checks is
stale. Do not change `aim_classification_leaf_baseline.json`, and do not add a leaf.**

The evidence:

1. **The approved count is already 177, not 176.** `aim_classification_leaf_baseline.json` top-level
   reads `axis_a_l3_approved: 177`, with a history entry dated 2026-09-20, revision
   `catalog_symbolic_leaf_20260920`, `released_by_jerome: true`, `added_leaves: ["Filters / Filter
   element"]`, and the evidence naming part 5864052180. The gate loads that number (`:61`), and its
   own failure text already says "approved 177" (visible in the recorded check note on
   `axis_a_l3_count`). **So the mechanical fix the failure message suggests — "update EXPECT
   axis_a_l3_approved" — is already done. The message is out of date, not the baseline.**
2. **The leaf is legitimate.** Its only row, 5864052180, sits at
   `Competitive parts > Filters > Filter element` in the approved release and in the live overlay, on
   the word of `pr00_classification.csv`, which still carries it that way today.
3. **It carries no money.** 5864052180 has zero billed lines in `sales_fact.parquet` at any date.
   Removing it would change a count and nothing else.
4. **The 176 is the stale reading.** `aim_pn_classification_v2.csv` — the file the gate opens — was
   built 2026-09-20 20:47 from the older combined file and puts that part on `Filters > Fuel filter`.
   It is the only file of the three that lacks the leaf. Nothing in the workflow except the gate
   reads it.

**If a person cannot take my word for it, the file to check is
`01_data\00_derived\pr00_classification.csv`** — the row for `pn_norm = 5864052180`, column
`level3_type`. It reads `Filter element` today. If someone ever re-runs the 21 September pipeline
over pr00 again, that leaf can silently disappear again, and no gate will catch it because the gate
reads the other file.

---

## 6. What improved, what regressed

**Improved, against the file the gate actually reads (`aim_pn_classification_v2.csv`):**

- 253 more part numbers present; 1,352 catalogue rows re-pointed, EUR 144,418.31 of 2025 billing.
- The five large air-filter / aftertreatment / common-rail corrections (EUR 840,000 of 2025 billing)
  are right in the release and wrong in v2.
- The `Filters > Filter element` leaf is present, so the approved 177-leaf baseline is met.
- The guide pin is on `Brakes > Caliper` on the AIM axis.

**Improved, against the file the pages read and today's source of record:** the catalogue tree of the
approved release matches committed `pr00` as at 20 September on every row, and differs from today's
`pr00` on 1,660 rows worth EUR 2,245,499.86 of 2025 billing — in the release's favour on every large
row. The memo's "265 parts / EUR 2,245,588" reconciles to my **264 parts / EUR 2,245,499.86** (the
part count differs by one because one of the unequal keys does not join).

**Regressed, against the live working files:**

- The release is four days old. It carries **none** of the 24 September work: the Cab Assembly class
  (20 rows, EUR 119,406.81 of L12M billing), the 32 appended orphan parts, the DEF Pump leaf.
- Its AIM label axis leaves **EUR 469,278.08** of 2025 billing on a residual label that the live
  overlay has since named. Residual 2.57% of euro against the live 1.30%.
- It does not join the lubricant billing at all (EUR 509,456.24 of 2025 billing, key form).
- Against the master on the catalogue tree: 5,936 rows, EUR 2,434,948.39 (7.53%).

**Three corrections to earlier documents that this re-test establishes:**

1. **The board's reading of the gate — "the one rule that punishes the improvement itself" — is
   wrong.** The leaf rule is correct and the baseline already says 177. The gate fails because it
   checks `aim_pn_classification_v2.csv`, which is 240 rows and 253 keys behind and is read by
   nothing else. (`02_dashboards\hub\_review\PILLAR_BOARD_ATTACK_2026-09-24.md:61`,
   `01_data\00_derived\universe_board_state.json:49`.)
2. **"EUR 111,125 of it on 7552044930" does not reproduce.** See section 4.
3. **`_releases\RELEASES.json`'s `2026-09-24-candidate` entry no longer describes the file at its own
   recorded path.** Its hash belongs to `…bak_pre_cab_class_20260924_192113`; the live overlay at
   `../aim_pn_classification_20260920.csv` now carries `092e9815…`.

---

## 7. Recommendation

**The approved 2026-09-20 release is sound as a catalogue-tree reference, and it is the right file
for the three white-paper examples, which reproduce against it. It is not sound — today — as "the
file the workspace builds from", and I would not repoint anything at it as it stands.**

The reason is narrow and concrete, not a judgement about quality. On the axis the release wins
(catalogue tree) the live overlay is already identical, so wiring the release in buys nothing there.
On the axis that has moved (AIM family labels) and on the part-list (keys) and the lubricant key
form, the release is behind and repointing at it would silently drop four days of work: the Cab
Assembly class, 32 orphan appends, and EUR 469,278.08 of named families. It would also drop the
lubricant rows out of every view that groups by family.

**What I would do instead, and what it needs from Jerome:**

1. **Keep the approval as it stands.** It is correct for what it was approved to be — a frozen,
   reproducible catalogue tree, and the reference the white-paper examples are quoted against.
2. **Do not repoint the pages.** Make it a deliberate decision, not a drive-by, because it would
   change what the four deep-dive pages mean.
3. **Fix the gate's file before anything else**, because right now the workspace's only safety check
   on classification quality is looking at a file no one reads. That change is section 8 and it is
   four lines.
4. **If a single build-from release is wanted** (which is what the pillar board's condition 3 asks
   for), it has to be **a new release cut**, built from the settled `aim_master_v2.csv` plus this
   release's catalogue tree, with the lubricant keys stored both ways. That is a new `release_id`
   and it is Jerome's call, not mine.

---

## 8. Wiring it in: what I did, and why I stopped

**I stopped. I did not repoint the gate.** The work order's own condition — "if it would change which
rows the gate inspects in a way that alters its meaning, STOP" — is met, and I proved it with a
read-only simulation (`01_data\91_build\_blockD_gate_sim_20260925.py`, output
`01_data\91_build\_blockD_gate_sim_release.json`): with the two constants changed to the release, the
verdict is **12 of 15**, and two of the three new failures are artefacts of the repoint rather than
findings:

| Check | With the gate pointed at the release | Why |
|---|---|---|
| `pr00_copy_integrity` | **FAIL, measured `None`** | The check reads `aim_pn_classification_v2.meta.json` by a hard-coded path. The release's meta has no copy-integrity block, so the check reports failure although nothing is known to be wrong. |
| `two_axes_contract` | **FAIL, "meta lacks the axis_b wording"** | Same cause. The release's meta states Axis A identity and a commercial score not being a parent, but never uses the literal string `axis_b`, which is what the check greps for. |
| `drift_vs_previous_run` | **FAIL, three drifts** | The baseline report was written about a different file, so the first run after the repoint compares release measures against v2 measures and trips the 1% rule on three checks. |

That is exactly the failure mode the work order names. The gate would go from "17 of 18, failing on a
bookkeeping rule that is actually right" to "12 of 15, failing for two reasons that are not real",
and it would be **certifying the approved release using the other file's evidence** — the opposite of
what the approval was for.

**The narrowest correct change, for whoever does it next — four edits, and none of them mine to make
without Jerome's word:**

1. `verify_aim_classification.py:29` — make `CLASS_V2` resolve to the approved release through
   `_releases\check_classification_release.py` rather than the literal `aim_pn_classification_v2.csv`.
2. `verify_aim_classification.py:201` — resolve the meta **from the file being checked**
   (`Path(CLASS_V2).with_suffix(".meta.json")` and the release's own name), not from a fixed path.
   Until this is done, `--file <release>` silently reports v2's copy-integrity number as the
   release's. I verified that: the `--file` run prints 99.3597 and passes, and that number is v2's.
3. Write the gate report's drift baseline **per approved file** (store
   `_releases\aim_pn_classification_release_2026-09-20.gate.json`), so the first run after the switch
   does not compare two different files.
4. Leave `aim_classification_leaf_baseline.json` alone. It already reads 177 and it is right.

Do those four, and the gate's verdict is about the approved release, honestly, and it passes. Do only
the first, and the gate starts certifying the release with the wrong file's evidence, which is worse
than the state it is in now.

---

## 9. What I could not establish

- **The EUR 111,125 cab figure.** Unreproducible on any reading of the master, the overlay or the
  billing. See section 4 for what I think it is and why I cannot prove it.
- **The memo's EUR 1,420,628 exclusion.** I get EUR 852,641.10 (the named non-part lines) plus
  EUR 524,734.36 (lubricants) = EUR 1,377,375.46, and my parts base is EUR 32,330,198.32 against the
  memo's EUR 32,286,946 — the same gap of about **EUR 43,250** on both sides of the sum. I could not
  close it from the data. The memo's working folder survives at
  `C:\Users\jerom\AppData\Local\Temp\claude\cls\` and I read its scripts; its own `compare.py` notes
  a padding rule but its exclusion list is not in a form I could re-run to the euro. **A person
  should check that folder, or the memo's author should restate the exclusion list.**
- **Which of the 251 remaining UK light-commercial 3.5 t share assumptions** belongs to the Ireland
  question — out of scope here, and flagged elsewhere; I did not touch it.
- **Whether the register's `2026-09-24-candidate` was ever meant to be the live overlay.** Its
  recorded path says yes, its recorded hash says a backup file. That is a decision for Jerome, not a
  measurement I can make.
- **The `.gate.json` history of the gate.** `aim_pn_classification_20260920.gate.json` exists from
  2026-09-20 16:42 and I did not open it to compare, because the work order's question was about the
  live gate and the approved release, and I did not want to add a third file's numbers to the drift
  story after measuring two.
- **Nothing about the newer candidate was tested.** I did not re-test the 2026-09-24 candidate
  against the white-paper examples; the work order does not ask for it and its hash is already stale
  against its own path.

---

## 10. Method, and what was not touched

Every number above is measured by me on disk today, from
`01_data\00_derived\sales_fact.parquet` and the five classification files named in section 1, with
the readers listed. The probe scripts are all under `01_data\91_build\_blockD_*_20260925.py` and
write only to `_blockD_*.json` / `.txt` / `.out.txt` beside themselves.

**Written to: nothing, except the scripts above and this file.**
Not changed: `aim_pn_classification_v2.csv`, `aim_pn_classification_20260920.csv`,
`aim_pn_classification.csv`, the frozen release, `aim_master_v2.csv`, the export pair,
`RELEASES.json`, `verify_aim_classification.py`, `aim_classification_leaf_baseline.json`,
`aim_classification_gate.json`, `build_aim_master.py`, `build_aim_master_v2_and_priority.py`,
`export_aim_pn_categories_figkey_xlsx.py`, any AIM page, any IDS page, PRISM, the pillar board, the
tender digest. No classification CSV was written, deleted or replaced.

**Hashes before and after this session, unchanged:**
`aim_classification_gate.json` `4adebc19720f6f13…`, `RELEASES.json` `0e45fea0141a1939…`, the frozen
release `60111c104ddeb466…`, the live overlay `092e981518efc544…`,
`aim_pn_classification_v2.csv` `371b6c212c69a671…`, `aim_master_v2.csv` `8add555669baf1f7…`.
