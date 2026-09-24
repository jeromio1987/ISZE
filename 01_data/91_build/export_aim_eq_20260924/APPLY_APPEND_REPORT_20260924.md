# PR00 IE40 write-back — the 44 that were not on the AIM master

**Date:** 2026-09-24 · **Agent:** cursor (AIM master write-back, part 2)
**Verdict: 44 of 44 placed. Nothing left unplaced. The master grew by exactly 44 rows and no existing row moved.**

This is the second half of the work the earlier pass stopped. That pass
(`01_data/91_build/export_aim_eq_20260924/APPLY_REPORT_20260924.md`) correctly refused to write
because 92 part numbers carry a deliberate `Unknown` in `aim_l1_fixed`. Those 92 are still
untouched. This pass takes the 44 that have **no row on the master at all**, which the precedence
question never touched.

---

## 1. The engine assembly

`8981422000`, `ENGINE ASM`, list EUR 8,693.31 — the largest ticket on the whole IE40 queue.

It now sits on **Engine > Complete Assembly > Engine Assembly**.

That path is not invented. It is what the master already says for the exact text `ENGINE ASM`:
**27 existing master part numbers carry that description and all 27 are on that one leaf.** The
separate classified workbook agrees independently: 73 rows read `ENGINE ASM` there and all 73 sit
on the leaf called `Engine assembly`.

**Which leaf I reused.** Two spellings of the same class exist in the workspace and they are not
interchangeable:

| Where | Field | Spelling | The 44 checked against it |
|---|---|---|---|
| The main table `aim_master_v2.csv` | `aim_l3` | `Engine Assembly` | **this is what I used** |
| The classified workbook `aim_pn_classification_20260920.csv` | `catalog_l3` | `Engine assembly` (lower-case a) | its `aim_l3_fixed` column carries `Engine Assembly`, same as the master |

So the leaf the brief asked me to check **does exist** — `catalog_l1/catalog_l2/catalog_l3` =
`Repair parts / Engine parts / Engine assembly`, holding **687 rows** — and it is the lower-case
form of the same leaf. I wrote the master's spelling, `Engine Assembly`, because the master is the
file being written and its own 27 ENGINE ASM rows use exactly that. I did not invent a third form.

Also confirmed: `8981422000` itself is **not** in the classified workbook (0 of the 44 are), so
there was no competing leaf for this specific part number to argue with.

---

## 2. The 44 — placed, all of them

Every one was placed. None was left unplaced. The method was the brief's first preference, and it
was strong enough that I never needed the figure key as a source:

> The exact description already means one AIM path on the master, with at least three part numbers
> behind it. The classified workbook is checked for agreement. The figure key is used **only as a
> veto**, never as the source.

Measured result:

- **44 of 44** had exactly one full AIM path with **≥ 3** supporting parts. Zero had two or more
  competing strong paths.
- **Minimum support was 6** parts. All 44 cleared the bar on the **master alone** — none needed the
  classified workbook to reach three.
- **Zero figure keys disagreed** with the chosen path. Every key either agreed or carried no
  evidence at all, so the veto never fired.

Four of the 44 are worth naming because their figure keys would have mis-filed them if I had let
the key be the source instead of a veto — exactly the traps documented in
`03_analytics/Isuzu/prism/docs/AIM_CLASSIFICATION_AUDIT_2026-09-17.md`:

| Part number | Description | Key | Key's top path | Written path (description) |
|---|---|---|---|---|
| `8982703783` | `HEAD ASM; CYL` | `011-001` | the key's 400 parts read `Cylinder head`, which is right here | `Engine > Cylinder Head > Head Cover` — the master's own leaf for this text |
| `7552973320` | `INJECTOR ASM; DEF DCM` | `146-020` | agrees | `Fuel System > Fuel Control > Injector` |
| `8975339040` | `CONTROLLER; ABS` | `826-158` | key's catalogue hint is `Brake parts > ABS component` | `Electrical > Control Units > Control Unit` — its description family on the master |
| `8981391311` | `CLAMP; BATTERY` | `520-040` | key's catalogue hint sits under lighting | `Lighting > Lighting > Lamp` — the master's own path for `CLAMP; BATTERY`, 9 parts |

The last two are the ones to look at if you want to argue with the result. They are honest
reproductions of the master's existing convention for those exact descriptions, not my judgement.
Two rows are genuinely arguable and I have flagged them rather than quietly "fixing" them:
`8975339040` (an ABS controller is an electrical control unit, but an ABS component reading is
defensible) and `8981391311` (a battery clamp filed under lighting is odd, but that is where all
nine other parts with that description already sit).

Where the 44 landed, grouped:

| AIM path | count |
|---|---|
| Electrical > Harness & Connectors > Connector | 6 |
| Suspension > Leaf Springs > Leaf Spring Asm | 5 |
| Chassis Frame > Crossmember & Brackets > Bracket | 3 |
| Accident & Body > Panels > Panel | 3 |
| Electrical > Instruments > Instrument Cluster | 3 |
| Lighting > Lighting > Lamp | 3 |
| Accident & Body > Panels > Door | 2 |
| Cabin Interior > Pedals & Controls > Cable | 2 |
| Fuel System > Tank & Supply > Fuel Tank | 2 |
| Engine > Complete Assembly > Engine Assembly | 1 |
| Engine > Cylinder Head > Head Cover | 1 |
| Engine > Gasket & Sealing > Oil Seal | 1 |
| Suspension > Bushings > Rubber Mount | 1 |
| Cabin Interior > Seat > Seat Back | 1 |
| Cabin Interior > Seat > Seat Cushion | 1 |
| Cabin Interior > HVAC Filters > HVAC | 1 |
| Accident & Body > Panels > Bumper | 1 |
| Accident & Body > Locks & Handles > Handle | 1 |
| Accident & Body > Wiper & Washer > Wiper Blade | 1 |
| Fuel System > Fuel Control > Injector | 1 |
| Electrical > Switch Relay Fuse > Switch | 1 |
| Electrical > Instruments > Sensor | 1 |
| Electrical > Control Units > Control Unit | 1 |
| Clutch > Pressure Plate > Pressure Plate | 1 |

Every one of those 24 paths already existed on the master. **I did not create a single new class
name.** The engine assembly needed nothing new either — the class was already there.

---

## 3. Columns on each new row

Every row carries `aim_source = export_pr00_20260924` and `aim_changed = export_pr00_20260924`.
Column names and order are unchanged (32 columns, same order as before).

| Column | Value | Why |
|---|---|---|
| `part_number`, `description` | from the price extract | the two facts the row is |
| `aim_l1`, `aim_l2`, `aim_l3` | the decided path | the point of the write |
| `aim_l1_fixed`, `aim_l2_fixed` | same as `aim_l1` / `aim_l2` | so the two routes agree and neither overwrites the other |
| `has_aim` | `1` | the row now has a family |
| `has_catalogue_node` | `0` | none of the 44 has an upstream price-list catalogue row; that is a fact, not a gap I filled |
| `cat_l1/l2/l3` | blank | same reason; flagging them as the residual bucket would have been a different, weaker claim |
| `cat_pms_flag` | `0` | the master's own rule is `1` only when `cat_l2` is a PMS family; with no `cat_l2` it cannot be `1` |
| `fig_key`, `fig_no`, `key_no` | from the price extract | kept in the master's own convention: the key is built `fig_no-key_no` **only** where the key number is numeric. For `001-HAA` the key stays blank and `fig_no` / `key_no` carry it — exactly as the existing 77 `001-HAA` rows do |
| `l12m_billed_eur`, `eur` | `0.0` | measured, not assumed — see below |
| `aim_demand_type`, `aim_core_noncore` | blank | not unanimous across the supporting parts for all 44, so left blank rather than invented; this matches the prior appends |
| `price_class_iml` | blank | these parts are not in the per-distributor pricing basis |
| the eight `jp_*` columns | blank | not populated by this task |

**On the money column.** I set it to zero only after checking. The master's own window is
2025-01-01 to 2026-06-30 (the column name `l12m_billed_eur` is a legacy label for an 18-month
window). **Seven of the 44 appear in the sales file, and every one of those 12 lines falls after
30 June 2026** — the earliest is 8 July 2026 and the latest 28 August 2026. So nothing billed
inside the window the master measures, and `0.0` is correct rather than lazy. Which seven, and
their line counts, are in `apply_append_summary.json`.

---

## 4. The 92, and the 164 — untouched

- **The 92.** Compared row by row against the backup: **not one of them changed**, and not one
  carries my stamp. They still carry `aim_l1_fixed` = `Unknown` (87) or `Unknown Review` (5). That
  decision is still yours.
- **The 164.** Not my scope. Also verified unchanged, no stamp.

---

## 5. What was written, and the hashes

| Item | Path | Size | sha256 |
|---|---|---|---|
| Backup (before) | `01_data\00_derived\aim_master_v2.csv.bak_pre_export_append_20260924_135923` | 28,508,322 | `4c904357563f611a3421793f17dd424e97d432a8d92d928a04f829a1ff459a6d` |
| The master (after) | `01_data\00_derived\aim_master_v2.csv` | 28,516,277 | `8e8f7a9a640be9643fe68740c5dc3ec5b805c882502d050f914769055d659a99` |
| New CSV | `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.csv` | 13,103,773 | `bd42e160f2a2dd17340ff1e47278d7cef32662c03a8e0c970fa51b8bb4d92a55` |
| New Excel | `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.xlsx` | 9,269,411 | `2cd4c8323c331424ed7a82dbd560bbc65f664d6a9f766a46efeaa079e9e3f34f` |

Row count 165,213 → **165,257**. Encoding unchanged (UTF-8, no BOM), line endings unchanged (CRLF
throughout, no bare LF), 32 columns in the original order.

The 2026-09-21 pair is untouched and still on disk. Nothing earlier was overwritten or deleted.
The new pair is dated 2026-09-24 because that is the build date.

---

## 6. How I know it worked (the verification, not the builder saying 0)

Every check was run against the written file and the backup, by part number, after the write:

| Check | Result |
|---|---|
| Row count grew by exactly 44 | PASS — 165,257 |
| Header identical, 32 columns, same order | PASS |
| All 165,213 pre-existing rows byte-identical to the backup | PASS |
| No AIM column changed on any pre-existing row | PASS |
| All 44 present with the decided levels and the stamp | PASS |
| No duplicate part numbers | PASS |
| File still sorted by part number | PASS |
| No BOM introduced | PASS |
| The 44 carry the new labels and the stamp in the new CSV | PASS — 44 of 44 |
| None of the 92 blocked rows changed | PASS |
| None of the 92 or 164 carries my stamp | PASS |

The gate that guards the write is inside `apply_export_pr00_append_20260924.py`. It compares the
candidate file against the original row by row **before** any backup or replace, and it refused to
proceed if any pre-existing row had drifted. It also refuses up front if my set overlaps either of
the two lists I must not touch, and it re-hashes the backup and refuses if it does not match the
original.

---

## 7. Which route exists for growing this file — and the risk

**There is no sanctioned append path.** I looked for one before touching anything:

- `00_docs\agent\DELEGATOR_REFRESH_HOWTO.md` explicitly lists `01_data/00_derived/aim_master_v2.csv`
  as **read-only and locked**, and says a rebuild of it is your call, recorded on the board, not
  something an agent does on its own. This task is your authorisation for this specific append; the
  page itself offers no append route.
- The `apply_*` scripts under `01_data\91_build\` (`apply_eq_hit_session_20260919.py`,
  `apply_not_on_aim_spine_high_20260919.py`, `apply_not_on_aim_4signal_agree2_3_20260919.py`,
  `apply_jp_codes_to_spine_20260920.py`) are one-off sessions, each written for one night's
  decision. They are precedent for **how** to append safely, and I followed that pattern
  (backup → gate → atomic replace → stamp), but none of them is a repeatable pipeline you can call.

So: **no sanctioned path existed. I appended rows directly.** I am saying that plainly, as asked.
The risk is real and I want it named precisely:

> The file that rebuilds this table is `01_data\91_build\build_aim_master.py` (plus its v2/priority
> wrapper `build_aim_master_v2_and_priority.py`). It starts from the AIM workbook, `pr00_classification.csv`,
> the pricing basis and the sales file — **it does not read the master as an input.** So a future
> spine rebuild will regenerate the master from those sources and **will drop these 44 rows and any
> other appended rows**, unless the append is folded into the builder first.

Two things make this cheaper to live with:

- The stamp is specific: `aim_source = export_pr00_20260924`. Any future rebuild can find exactly
  what was added by looking for it, and the decision for each part number is reproducible from the
  exact-description rule (`finalise_decisions.py`, deterministic, no hand-picking).
- `aim_l1_fixed` / `aim_l2_fixed` are populated on the new rows, so they survive the precedence
  order the deliverable builder uses — the same trap that stopped the earlier pass. The 92 are
  blocked precisely because their `*_fixed` says `Unknown`; these 44 say a real family.

**What I would do about it:** make the append part of the builder rather than a side script, so the
next rebuild cannot drop it. That is a change to a locked file's build chain and it is your call,
not mine.

---

## 8. What I could not verify, and one thing I found

Not verified, and not claimed:

1. **I did not re-derive the tiering.** The 44 are taken from `carried_out_not_in_master.txt` as
   instructed, and I confirmed the file holds exactly 44 distinct part numbers.
2. **I did not hand-check all 44 against the EPC.** No EPC or Snap-on lookup was run, as instructed.
   The placement rests on the exact-description agreement, which is the method the brief specifies
   as first preference.
3. **Every part number in the file is new to the master**, so there was no prior row to compare the
   chosen path against. The path is the description's own convention, not a correction of anything.
4. **The `Value` column arithmetic in `EXPORT.XLSX`** is still unreconciled. I used the list price
   (`Price`) only for the one figure quoted in this report, and the earlier finding already flags it.
5. **The two arguable rows** (`8975339040`, `8981391311`) are reproductions of the master's existing
   convention. If you want them somewhere else, that is a decision about the class, not about my
   write.

One thing I found and did not touch, the same as the earlier pass: **line 22 of
`00_docs\agent\DELEGATOR_BOARD.md`** (the 2026-09-24 12:50 scraper row) carries 9 pipes where the
table takes 6, and everything after it in that block renders as one broken row. It was written by a
different agent before this task. The brief says not to rewrite existing rows, so I left it. My own
new row is written on its own line at the end so it is not swallowed by that break.

---

## 9. Files

Written by this pass:

- `01_data\91_build\apply_export_pr00_append_20260924.py` — the append, with its gate
- `01_data\91_build\export_aim_append_20260924\finalise_decisions.py` — the decision rule
- `01_data\91_build\export_aim_append_20260924\verify_append.py` — the step-11 verification
- `01_data\91_build\export_aim_append_20260924\decision_44_final.csv` — the 44 with their evidence
- `01_data\91_build\export_aim_append_20260924\apply_append_summary.json` — the run summary
- the read-only probe scripts in the same folder, which record how each answer was reached

Read-only inputs: `EXPORT.XLSX` · `carried_out_not_in_master.txt` ·
`carried_out_blocked_precedence.txt` · `would_land_free.txt` · `tierA_audited.csv` · `queue_final_tiered.csv` ·
`aim_master_v2.csv` · `aim_pn_classification_20260920.csv` · `sales_fact.parquet` ·
`AIM_CLASSIFICATION_AUDIT_2026-09-17.md`

Nothing published. No dashboard touched. No browser, no EPC run. No mail.
