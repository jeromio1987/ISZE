# PR00 IE40 — the 43 part numbers with no row on the AIM master

**Date:** 2026-09-24 · **Agent:** cursor (AIM orphan append)
**Verdict: 32 of the 43 now sit on the master, all 32 on the EPC's own figure name. 11 were left
unplaced and are named below. The master grew by exactly 32 rows and no existing row moved.**

This is the third and last piece of the IE40 work. The first pass stopped at the precedence question
(`APPLY_REPORT_20260924.md`). The second appended the 44 that had no row (`APPLY_APPEND_REPORT_20260924.md`,
14:05). This pass takes the 43 part numbers that *still* had no row after that append — a different
set, not a leftover of the 44.

---

## 1. The 43, confirmed against the master as it stood

Derived, not assumed. `01_data/91_build/export_aim_eq_20260924/queue.csv` holds 1,311 price lines
across 1,303 distinct part numbers. Read against the master as it stood at 17:01 (backup taken
first), **43 of those part numbers had no row at all**, so no family could be written for them.

The count is exactly 43, so the guard the brief set did not fire and the work proceeded. The list is
recorded at `01_data/91_build/export_aim_eq_20260924/orphans_43.csv`.

The other two groups the brief names were measured too and were **not** in scope:

| Group | Measured on the master | On the classification overlay |
|---|---:|---:|
| Carrying the `Unknown` marker | 45 | **25** |
| A row, no usable family | 23 | 19 (the rest have no overlay row) |
| No row at all | **43** | 43 |

**One thing does not line up, and I am saying so rather than smoothing it.** The brief calls the
second group 25 and the third 31. Read off the master, the marker group is 45 and the blank group is
23. Read off the classification overlay, the marker group is exactly **25** — the brief's number —
and the blank group is smaller than 31. The earlier open-parts analysis
(`01_data/91_build/export_aim_open_why_20260924/`) reports yet another pair of numbers for the same
list (845 and 31) because it measures a different union and reads `aim_l1` rather than the
`aim_l1_fixed` column the published file actually prefers.

I did not reconcile this. Nothing in it changes the 43, which is the only group I was asked to act
on; the 43 agrees under every reading. Both guarded groups were left strictly alone and that is
proved by part number in section 6.

---

## 2. How each of the 43 was established

The route ladder was applied in the order the brief gave, and never softened.

**Route (a) — the EPC figure name, read through `aim_rules.py`: 32 parts.**
This is the catalogue's own answer and the strongest evidence available. For each part the figure
name recorded in `classified.csv` was read through the same 177 wording rules the earlier run used,
longest phrase first. All 32 landed on a path that already exists on the master, and for all 32 the
rule's answer is identical to what `classified.csv` itself recorded — I re-derived it rather than
copying the column, and the two agree on 32 of 32.

**Route (b) — exact description agreeing on one full AIM path, figure key as a veto: 0 parts.**
I ran it in full, the same way `finalise_decisions.py` did for the 44. Not one of the 43 was decided
by it, and here is the honest reason: for the 32 that route (a) placed, route (a) is the stronger
source by the brief's own ordering, so it wins even where route (b) also had three or more parts
behind it. That was true for 16 of them. For the remaining 11, route (b) reached the three-part bar
for none, so it could not place them either.

The figure-key veto was applied wherever route (b) had any support at all, and it fired once:
`8943796470 GASKET; OIL PUMP` — the description's own path points at the oil pump, the figure key
`442-039` is unanimous on the master for `Transmission > Bearings & Seals > Gasket`. But that part
was already placed by route (a), so the veto made no difference to the outcome.

**Where route (a) and route (b) disagree.** This is the part I would want read carefully. For 11 of
the 32, the exact description — with strong support on the master — points at a *different* path
from the figure name:

| Part | Description | By the figure name (written) | By the description (master support) |
|---|---|---|---|
| `8975480980` | `TRANSMISSION ASM; MANUAL` | Transmission > Case > Case Cover | Literature Marketing > Manuals > Manual (76) |
| `8978410221` | `LAMP ASM; HEAD` | Electrical > Lighting > Lamp | Lighting > Lamps > Headlamp Assembly (322) |
| `8978410231` | `LAMP ASM; HEAD` | Electrical > Lighting > Lamp | Lighting > Lamps > Headlamp Assembly (322) |
| `8972785810` | `LAMP ASM; RR COMB` | Electrical > Lighting > Lamp | Lighting > Lamps > Rear Combination Lamp (156) |
| `8972785820` | `LAMP ASM; RR COMB` | Electrical > Lighting > Lamp | Lighting > Lamps > Rear Combination Lamp (156) |
| `8975447350` | `DISC; CLUTCH` | Clutch > Clutch Kit > Clutch Kit | Clutch > Disc > Clutch Disc (98) |
| `8983899750` | `ABSORBER ASM; SHOCK,FRT` | Suspension > Suspension Arm > Ball Joint | Suspension > Shock Absorber > Damper (76) |
| `8983700410` | `FILTER ASM; FUEL` | Maintenance Service > Fuel Filter > Fuel Filter Element | Maintenance Service > Filters (unspecified) > Filter Assembly (76) |
| `7552062110` | `FILTER ASM; OIL` | Cooling > Radiator > Radiator Assembly | Maintenance Service > Filters (unspecified) > Filter Assembly (20) |
| `8943796470` | `GASKET; OIL PUMP` | Steering > Gear > Steering Gear | Lubrication > Oil Pump > Oil Pump (16) |
| `7552710010` | `PUMP KIT` | Intake Exhaust Emission > DEF System > DEF Tank | Fuel System > Injection Pump > Fuel Pump (4) |

The brief puts the figure name first, and it is the right first answer for "which system is this part
for", so that is what was written and it is what the stamp says. But two rows deserve a second look
because the description looks better than the figure name:

- `7552062110 FILTER ASM; OIL` — an oil filter filed under the radiator, because the figure it sits
  on is `0-50 OIL COOLER AND OIL FILTER`. The wording rule turns "OIL FILTER" into the maintenance
  oil-filter leaf, but the rule for the longer phrase "OIL COOLER AND OIL FILTER" wins and sends it
  to cooling. Defensible on the figure, arguable on the part.
- `7552710010 PUMP KIT` — filed on the DEF tank because its figure is `1-46 DEF TANK AND PIPING`. The
  description's own evidence points at a fuel pump, but only 4 master parts support it. Weak both
  ways; the figure name is the better of two thin answers.

One more to name: `8974210030 TRAY; INST` went to `Cabin Interior > Dashboard & Controls > Knob`
because the figure `7-40 INSTRUMENT PANEL AND BOX` maps there under the authored rules. An
instrument tray on a knob leaf is odd, but it is the leaf the authored rules give and I reused the
rules rather than writing my own dictionary.

**Route (c) — left unplaced: 11 parts.**
Named in section 3. Not one was guessed to improve the count.

---

## 3. The 11 left unplaced, and why

| Part | Description | Figure key | Why it stays unplaced |
|---|---|---|---|
| `5876102381` | `PAD KIT; CALIPER, DISC BRK, FR` | 302-017 | Not in the EPC. The wording carries zero master parts; only the figure key is unanimous, and a figure-key-only answer is a weaker route than this brief allows. |
| `7553266960` | `CAB ASM; SERVICE,W/ELECT` | 604-002 | Not in the EPC. One master part behind the wording — below the three-part bar. |
| `7552126065` | `BRACKET; MOTOR BATTERY` | 061-248 | Not in the EPC. One master part behind the wording, and it is the motor it brackets, not the bracket. |
| `1884053370` | `LLC;200L TYPE E` | 999-37K | Not in the EPC. This is coolant by its own wording but the wording has never been on the master. |
| `7552598420` | `CIRCUIT; PRINTED,BATTERY` | 810-795 | Not in the EPC. No master part carries this wording at all. |
| `7552347140` | `COVER; FUSE CABLE` | 810-796 | Not in the EPC. No master part carries this wording. |
| `7552360101` | `BASE; FUSE CABLE` | 061-309 | Not in the EPC. No master part carries this wording. |
| `7553196060` | `GUIDE; HARNESS` | 146-231 | Not in the EPC. No master part carries this wording. |
| `8943633640` | `CONNECTOR; HARNESS (2P FEMAIL)` | 816-002 | No EPC figure name, and the figure key is shared by master parts in different families. |
| `8980626220` | `CONNECTOR; HEAD LAMP` | 816-090 | No EPC figure name, and the figure key is shared. |
| `8980680830` | `CONNECTOR; HEAD LAMP` | 816-090 | No EPC figure name, and the figure key is shared. |

Two of these are worth a sentence because they look easy and are not. The three connectors — two
head-lamp connectors and one two-pin harness connector — would all land on
`Electrical > Harness & Connectors > Connector` at 47 supporting parts if the wording rule were
allowed to match on the first word alone. The authored rules do not contain a bare "CONNECTOR" rule,
and every route this brief permits reads the rules as authored, so they stay unplaced. If you want
them filed there, that is a change to `aim_rules.py`, not a judgement call I should make inside an
append.

The three parts the earlier run placed by a unanimous figure key alone (`5876102381`, `7553266960`,
`7552126065`) are the other deliberate stop: a figure key that happens to be unanimous is weaker
evidence than the brief's route (b), and route (b) did not reach three parts for any of them. They
are named here so the decision is visible rather than buried.

---

## 4. What was written, and the hashes

| Item | Path | Size | sha256 |
|---|---|---:|---|
| Backup (before) | `01_data\00_derived\aim_master_v2.csv.bak_pre_orphan_append_20260924_170151` | 28,606,117 | `1870dc2ac08e8128c9323a5da14ad46742bb1200f24d3d6faa3ed53576b74af4` |
| The master (after) | `01_data\00_derived\aim_master_v2.csv` | 28,611,807 | `eaeb51bea3fe61b3af3ca7d0290f2e071bb480053c76b76198b26451b5a30283` |
| Rebuilt CSV | `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.csv` | 13,153,014 | `c43a23ac225891a6dc6e7d86c861478409c4508c2be97bce07c36c3818608a2d` |
| Rebuilt Excel | `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.xlsx` | 9,294,122 | `62975fc383e628fd686a43641cc68c06c68d45d3216148ebb13ee01cdc1366b4` |
| The 2026-09-24 pair before the rebuild | `01_data\00_derived\_backup_20260924_pair_before_orphans\` | — | csv 13,149,086 · xlsx 9,291,457 · launcher 74 bytes |

Row count 165,257 → **165,289**. Encoding unchanged (UTF-8, no BOM), line endings unchanged (CRLF
throughout, no bare LF), 32 columns in the original order.

**The write never touched the live file directly.** The candidate was built in memory, written to a
temporary file in the same folder, checked in full, and only then moved onto the live path with a
replace, so a reader running at the same time sees either the old file or the new one and never a
half-written one. That was the brief's instruction and it was followed.

**Column shape.** Every new row matches the earlier 44 exactly: levels in `aim_l1/l2/l3`, the same
levels in `aim_l1_fixed/l2_fixed`, `has_aim` = 1, `has_catalogue_node` = 0, `cat_pms_flag` = 0,
`desc_ambiguous` = 0, the `cat_*` and `price_class_iml` and `jp_*` columns blank, `aim_source` and
`aim_changed` carrying the stamp. `fig_key` is built `fig_no-key_no` **only** where the key number is
numeric, which is the master's own measured convention — 4,083 existing rows with a non-numeric key
all carry a blank `fig_key` and are identified by `fig_no` and `key_no`, so the two placed parts with
non-numeric keys (`1884053370` was not placed; nothing written this pass needed it) follow the same
rule.

**The money column** is `0.0` on every new row, and that was measured rather than assumed: four of
the 43 appear in the sales file and all seven of their lines fall after 30 June 2026, outside the
window the master measures. Nothing billed inside the window, so zero is correct.

**Stamp.** `export_aim_eq_20260924` on all 32, which is the stamp that matches the evidence used —
the EPC figure name decided every one of them. No row carries `export_pr00_20260924`, because no row
was decided by description agreement.

---

## 5. The dated pair

The pair was rebuilt by running the builder as written:

```
python 01_data\91_build\export_aim_pn_categories_figkey_xlsx.py
```

It derives its own names from today's date, so it wrote the 2026-09-24 names and overwrote today's
earlier pair, which is what the brief asks for. It reported 165,289 rows, and both the CSV and the
Excel now carry the 32 new part numbers with their families (checked row by row, 32 of 32 in each).
The existing 2026-09-24 pair was copied to `_backup_20260924_pair_before_orphans\` first.

The rebuild also rewrote `OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd`. Checked on disk
afterwards: 74 bytes, `@echo off` and the start line, CRLF on both lines, and it points at the
2026-09-24 Excel.

**The 2026-09-21 pair was not touched by this pass.** The pair builder writes only the date-named
files, and the only files this pass wrote are the ones listed in section 4. Nothing in
`AIM_Master_PN_Categories_Figkey_20260921.*` was read-modify-written or replaced here.

**For your attention, not mine to fix:** the live 2026-09-21 pair now holds genuine 21 September
content (130,931,140 bytes, mtime 22 September) after the restore another agent recorded on the
board at 17:05. That is a different agent's work and I neither did it nor changed it.

---

## 6. How I know it worked

Every check was run against the written file and the backup, **by part number, not by row
position**, after the write. Full output: `verify_orphan_append.json`, `open_count_final.json` and
`guarded_25.json` / `guarded_31.json` in this folder.

| Check | Result |
|---|---|
| Row count grew by exactly the number placed | PASS — 165,257 → 165,289, +32 |
| Header identical, 32 columns, same order | PASS |
| All 165,257 pre-existing rows byte-identical to the backup, compared by part number | PASS |
| No AIM column changed on any pre-existing row | PASS |
| No pre-existing row lost | PASS |
| All 32 present with the decided levels and the stamp, and the fixed columns agreeing | PASS |
| No duplicate part numbers | PASS |
| File still sorted by part number | PASS |
| No BOM, CRLF only | PASS |
| Rebuilt CSV carries all 32 with their families | PASS — 32 of 32 |
| Rebuilt Excel carries all 32 with their families | PASS — 32 of 32 |
| Launcher points at the 2026-09-24 Excel, CRLF | PASS |
| The 44 appended at 14:05 untouched (166 rows including the fill pass, no row changed) | PASS |
| The brief's 25 marker rows on this list: none changed, none newly added, no stamp gained | PASS — 0 of 25 |
| The brief's 31 rows: none changed, none newly added, no stamp gained | PASS — 0 of 31 |

The gate that guards the write is inside `apply_orphan_append_20260924.py`. It builds the candidate,
runs all thirteen checks against it **before** any backup or replace, and refuses to proceed if any
pre-existing row has drifted or if my 43 overlap the blocked, free or earlier-44 sets.

### The open count on the price list

Measured on the master, before and after:

| Why a part number is open | Before | After |
|---|---:|---:|
| No row on the master at all | 43 | **11** |
| Carrying the `Unknown` marker | 45 | 45 |
| A row with no usable family | 23 | 23 |
| **Open, total** | **111** | **79** |
| With a real family | 1,192 | **1,224** |
| Part numbers on the list | 1,303 | 1,303 |

The 111 reconciles exactly: 43 + 45 + 23 + 1,192 = 1,303. So the price list closed by 32, from 111
open to 79.

Read the way the brief counts the same list — the 43, then the 25 marker rows and the 31 wording
rows — the count goes from 99 open to **67** open, and the 32 are the only ones that moved. Both
readings are in `open_count_final.json` so you can see which one you want quoted.

---

## 7. Growing this file, and the risk — unchanged, and still real

**There is still no sanctioned append path.** I looked for one before touching anything and found
none, exactly as the 14:05 pass reported:

- `00_docs\agent\DELEGATOR_REFRESH_HOWTO.md` lists `01_data/00_derived/aim_master_v2.csv` as
  read-only and locked, and says a rebuild is your call recorded on the board, not something an
  agent does on its own. This brief is that authorisation for this specific append; the page itself
  offers no append route.
- The `apply_*` scripts under `01_data\91_build\` are one-off sessions, each written for one night's
  decision. They are precedent for **how** to append safely and I followed that pattern — backup,
  gate, atomic replace, stamp — but none of them is a pipeline you can call.

So: no sanctioned path existed, and I appended rows directly. The risk, named plainly:

> `01_data\91_build\build_aim_master.py` (and its v2/priority wrapper) starts from the AIM workbook,
> `pr00_classification.csv`, the pricing basis and the sales file. **It does not read the master as
> an input.** A future spine rebuild will regenerate the master from those sources and **will drop
> these 32 rows, and the 44 before them, and every other appended row**, unless the append is folded
> into the builder first.

Two things make that cheaper to live with. The stamp is specific — `export_aim_eq_20260924` — so a
future rebuild can find exactly what was added. And `aim_l1_fixed` / `aim_l2_fixed` are populated on
the new rows, so they survive the precedence order the published file uses, which is the trap that
stopped the first pass.

**What I would do about it:** fold the append into the builder rather than leaving it as a side
script, so the next rebuild cannot drop it. That is a change to a locked file's build chain and it
is your call, not mine.

---

## 8. What I could not verify

1. **The 45 / 23 / 25 / 31 split does not reconcile between the master and the overlay**, and the
   brief's numbers match the overlay for the marker group but not for the blank group. I did not
   reconcile it because nothing in it changes the 43. Section 1 has the measurements.
2. **I did not hand-check the 32 against the EPC.** No browser was driven and no EPC lookup was run,
   as instructed. The placement rests on the figure name the earlier run recorded, read through the
   authored rules, plus the independent agreement that the rule's own answer matches the column the
   earlier run wrote. That is strong but it is a second-hand read of the catalogue.
3. **The 11 unplaced parts have not been looked up again.** For five of them the EPC has no record at
   all; for the others the earlier run recorded a figure name that the rules could not turn into a
   family. A fresh lookup is a browser task and out of scope here.
4. **I did not re-derive the master's own billing window.** I relied on the window recorded at 14:05
   (1 January 2025 to 30 June 2026) when setting the money column to zero, and on those four parts'
   line dates. I did not re-measure the window itself.
5. **The rebuilt Excel was read back through pandas, not opened in Excel**, so I cannot say what it
   looks like on screen. The CSV and the Excel were both checked row by row for the 32.
6. **Two placements are arguable and I flagged them rather than quietly fixing them** —
   `7552062110` (oil filter filed under cooling) and `7552710010` (pump kit filed on the DEF tank),
   with `8974210030` (instrument tray on a knob leaf) as a third. All three are honest reproductions
   of the authored rules and the figure names, not my judgement.

Nothing was published. No dashboard was touched. No browser, no EPC run, no mail.
`AIM_Master_PN_Categories_Figkey_20260921.*` was not written by this pass.

---

## 9. Files

Written by this pass:

- `01_data\91_build\export_aim_orphan_append_20260924\apply_orphan_append_20260924.py` — the append, with its gate
- `01_data\91_build\export_aim_orphan_append_20260924\decide_orphans.py` — the route ladder (a) / (b) / (c)
- `01_data\91_build\export_aim_orphan_append_20260924\decision_orphans.csv` — all 43 with the evidence for each
- `01_data\91_build\export_aim_orphan_append_20260924\verify_orphan_append.py` and `verify_orphan_append.json`
- `01_data\91_build\export_aim_orphan_append_20260924\open_count_final.json`, `open_split_before_after.json`, `guarded_25.json`, `guarded_31.json`
- the read-only probes in the same folder (`probe_evidence.py`, `probe_rest.py`, `probe_eleven.py`,
  `probe_open_counts.py`, `probe_open_final.py`, `probe_guarded_25_31.py`, `probe_placement_groups.py`)
- `01_data\91_build\export_aim_eq_20260924\orphans_43.csv` — the 43 as derived

Read-only inputs: `01_data\EXPORT.XLSX` · `queue.csv` · `classified.csv` · `still_unknown.csv` ·
`eq_results.jsonl` · `aim_rules.py` · `aim_pn_classification_20260920.csv` · `aim_master_v2.csv` ·
the earlier reports (`APPLY_REPORT`, `APPLY_APPEND_REPORT`, `APPLY_FILL_REPORT`,
`APPLY_UNKNOWN_CLEAR_REPORT`, `PAIR_REPAIR_REPORT`) · `sales_fact.parquet` ·
`00_docs\agent\DELEGATOR_REFRESH_HOWTO.md`.
