# PR00 IE40 price extract — AIM master write-back: STOPPED at the precedence check

**Date:** 2026-09-24 · **Agent:** cursor (data write-back task)
**Verdict: nothing was written. The master was not modified, no backup was made, the builder was not run.**

Step 1 — the precedence check the brief asked for — tripped. The brief says that if the
`*_fixed` columns are populated for these part numbers, stop and report instead of writing.
They are populated, for 92 of the 300, and the effect is proven below against the live
deliverable, not just against the source code.

---

## 1. What was measured (before any write)

Source of the 300: `01_data/91_build/export_aim_tiering_20260924/tierA_audited.csv`.

- 316 rows are flagged `tierA`.
- 3 rows are flagged `undefendable` (`GASKET SET; ENG OVERHAUL` ×2, `GASKET; CYL HD` ×1).
- 12 rows are flagged `convention` (the lamp rows, `PUMP ASM; OIL,P/S`, `CYLINDER ASM; CLUTCH MASTER`).
- 15 rows are either, 0 are both → **301 rows / 300 unique part numbers / EUR 59,274.59**.
  One part number, `8974922881` (`STARTER ASM`), appears twice.
- This matches the brief's stated defensible set of 301 rows / 300 part numbers / EUR 59,275.
  Note the brief described the flags as one `convention` column; there are two
  (`undefendable`, `convention`) and they partition the 15.

### Master: `01_data/00_derived/aim_master_v2.csv`

- 165,213 rows (165,214 CRLF line endings = 1 header + 165,213).
- 256 of the 300 are present. 44 are not on the master at all.
- `aim_l1_fixed` is **non-empty for 92** of the 256. Every one of those 92 says
  `Unknown` (87) or `Unknown Review` (5).
- `aim_l2_fixed` is non-empty for the same 92: `Unknown` (87), `Unclassified` (5).
- `aim_l3_fixed` **does not exist as a column** on the master.
- Current `aim_l1` on the 256: empty 164, `Unknown` 87, `Unknown Review` 5.

### Classification overlay: `01_data/00_derived/aim_pn_classification_20260920.csv`

- 164,907 rows. 252 of the 300 are present (48 absent).
- `aim_l1_fixed` non-empty for 90: `Unknown` 85, `Unknown Review` 5.
- `aim_l2_fixed` non-empty for 90: `Unknown` 85, `Unclassified` 5.
- `aim_l3_fixed` non-empty for 90: `Unknown` 85, `To Review` 5.
- The overlay has no `aim_l1` / `aim_l2` / `aim_l3` columns; it carries the `*_fixed` names only.

So: **92 of the 300 carry a non-empty `aim_l1_fixed` today, and the value is `Unknown` or
`Unknown Review` in every case.**

---

## 2. Why that stops the write

`01_data/91_build/export_aim_pn_categories_figkey_xlsx.py` builds the deliverable in this order:

- line 190–192 — `aim_l1` / `aim_l2` are already the `*_fixed` value **where one exists**,
  otherwise the plain `aim_l1` / `aim_l2`.
- lines 200–209 — then the classification overlay's `aim_l1_fixed` / `aim_l2_fixed` /
  `aim_l3_fixed` are laid over the top and **win** wherever they are non-empty.
- line 192 — `aim_l3` comes from the plain master `aim_l3` column at that point.

Our write goes into `aim_l1` / `aim_l2` / `aim_l3`. Those sit at the *bottom* of both
precedence chains. The `_fixed` value is non-empty on the 92 rows, so it wins.

Simulated, and then confirmed on the file: if a real family were written to all 256 rows,
the deliverable would show the real family on **164 rows** and keep `Unknown` / `Unknown Review`
on **92 rows** — that is 31% of the write silently discarded, EUR 11,256.93 of the EUR 59,275.

### Confirmed against the delivered file, not only the code

`01_data/00_derived/AIM_Master_PN_Categories_Figkey_20260921.csv` (13,093,140 bytes) already
prints exactly that for these part numbers:

- rows for the 300: 256 — `aim_level_1` = empty 164, `Unknown` 87, `Unknown Review` 5.
- the blocked 92 rows: `Unknown` 87, `Unknown Review` 5.

So the trap is live in the file Jerome opens today, not a hypothetical.

---

## 3. The split of the 300 (measured)

| Group | part numbers | list price EUR | what would happen |
|---|---|---|---|
| On master, `aim_l1_fixed` empty | 164 | 29,181.94 | the write would land |
| On master, `aim_l1_fixed` populated | 92 | 11,256.93 | the write would be silently overridden |
| Not on the master at all | 44 | 18,835.72 | the write is impossible — no row to write to |
| **Total** | **300** | **59,274.59** | |

The three groups are disjoint; the counts sum to 300.

### Why the 92 say `Unknown`

All 92 carry `aim_source = aim_workbook`, `aim_changed = 0`, `has_aim = 0`,
`desc_ambiguous = 0`. So `aim_l1_fixed = 'Unknown'` is a deliberate "we could not place this"
marker copied from the AIM workbook, not a mislabel. The same value sits on 4,936 rows master-wide
(`Unknown` 4,273 + `Unknown Review` 663). The other 164 rows carry `aim_source = not_classified`.

That run did not fail because of the *order* of front-end and overlay precedence. It failed because
the AIM workbook itself carries `Unknown` under `aim_l1_fixed` and that value is a deliberate marker
that the extractor treats as authoritative.

---

## 4. The other thing the check found

**44 of the 300 are not on the AIM master.** All 44 are genuinely absent — not a leading-zero,
formatting or length difference (checked: all 44 are 10 characters; master holds 163,583 of 10
characters, plus 1,461 of 9 and shorter). The tiering file's own `on_master` column agrees:
257 of the 301 defensible rows are `on_master = True`, 44 are `False`.

`01_data/EXPORT.XLSX` holds 1,318 unique P/Ns and the 44 are in `queue.csv`, but only 37 of them
appear in `EXPORT.XLSX`. They are almost new part numbers: `8981422000` (`ENGINE ASM`, EUR 8,693.31,
the largest ticket on the queue), `7552319201` / `7552319211` (`DISPLAY; MULTI`), `8982703783`
(`HEAD ASM; CYL`), four `SPRING ASM; LEAF,FRT` rows, `8975339040` (`CONTROLLER; ABS`).

On a spine read from `aim_master_v2.csv`, these 44 cannot be given a family by writing to the
master at all. That is a scope fact worth having before the EPC run is trimmed: the real
"decidable from the row" saving is **256 rows, not 300**, and EUR 40,439 rather than EUR 59,275
against the prices that can actually be written.

---

## 5. What was not done

- No backup was taken. Step 3 was never reached. `aim_master_v2.csv` is untouched:
  28,508,322 bytes, sha256 `4c904357563f611a3421793f17dd424e97d432a8d92d928a04f829a1ff459a6d`,
  mtime 2026-09-20 07:24:12. No BOM, CRLF line endings (165,214), no bare LF.
- No rows were changed. No `aim_source` stamp was applied. The `*_fixed` columns were not touched.
- The builder `python 01_data\91_build\export_aim_pn_categories_figkey_xlsx.py` was **not** run,
  so **no new dated pair exists**. The newest pair on disk is still
  `AIM_Master_PN_Categories_Figkey_20260921.csv` (13,093,140 bytes) and
  `AIM_Master_PN_Categories_Figkey_20260921.xlsx` (9,281,799 bytes). No earlier pair was
  overwritten or deleted.
- No row was appended to the board for the write. The board row records this stop instead
  (`00_docs/agent/DELEGATOR_BOARD.md`, line 98, 5 cells — verified).

### One thing I found on the board but did not touch

Line 22 of the board (the 2026-09-24 12:50 scraper Phase 0 row) carries 9 pipes where the table
takes 6, so it renders as a broken row and everything after it in that block is malformed. That
row was written by another agent before this task started. The brief says not to rewrite existing
rows, so I left it exactly as it was. It needs a one-line repair by whoever owns the scraper
workstream.

---

## 6. What I would do next — Jerome's call

Nothing here is a data fault on the 164 free rows. The question is what to do about the 92.

1. **Clear the 92 markers first, then write.** Set `aim_l1_fixed` / `aim_l2_fixed` on the 92 to
   empty (and the matching 90 in the classification overlay) so the derivation is the only thing
   left standing, then run the write as specified. That would land all 256 at once. It also means
   editing 92 rows that currently say "we could not place this" and have said so since the workbook
   — a deliberate decision, not a cleanup.
2. **Write the 164 only, and leave the 92 carrying `Unknown`.** Safe and honest, but the deliverable
   then still shows `Unknown` on 92 parts that this analysis can place, which is exactly the
   outcome the write-back was meant to remove.
3. **Fix the precedence so `aim_level_1` resolves `Unknown`-as-empty.** Smallest edit, but it touches
   the builder in `01_data/91_build/`, used by every AIM pack — it deserves its own review, not a
   side effect of this task.

I did not choose between these, because each one decides something about the master that is
Jerome's to decide.

Two separate things still waiting on the EPC lookup either way:

- the 44 part numbers that are not on the master, and
- the 15 carved-out rows (`undefendable` + `convention`, EUR 3,420) — lamps, the power-steering
  pump, the clutch master cylinder and the three gasket rows.

The remaining queue after the 300 is 1,003 part numbers; the tiering finding put Tier B at
995 rows / 988 part numbers, and the balance is the 15 carved-out rows.

## 7. Not verified

- I did not re-derive the tiering. The 300 are taken from `tierA_audited.csv` as instructed.
- I did not confirm the `Value` column's arithmetic in `EXPORT.XLSX` (the tiering finding already
  flags this).
- I did not read the 300 part numbers by hand. The step 2 path derivation
  (level 1 → level 2 → level 3 by modal full path, ≥3 agreeing master rows) was never run,
  because the precedence guard stopped the task before it.
- `aim_master_v2.csv` holds `aim_changed = 0` on the blocked 92; I read that as "not yet changed",
  which is what the column name implies, but I did not find the code that writes it.

## Measured evidence

Scripts (read-only) and the carried-out lists:
`01_data/91_build/_tmp_apply_export_pr00_20260924/`

- `probe_precedence.py` … `probe_precedence5.py`, `lock_evidence.py`
- `would_land_free.txt` — the 164 part numbers the write would have reached
- `carried_out_blocked_precedence.txt` — the 92 blocked by `*_fixed`
- `carried_out_not_in_master.txt` — the 44 with no master row

## Files referenced

- `01_data/EXPORT.XLSX` — the PR00 IE40 extract (1,318 rows, 1,318 unique P/Ns)
- `01_data/91_build/export_aim_eq_20260924/queue.csv` — 1,311 rows, 1,303 unique part numbers
- `01_data/91_build/export_aim_tiering_20260924/tierA_audited.csv`, `FINDING.md`
- `01_data/00_derived/aim_master_v2.csv` — untouched
- `01_data/00_derived/aim_pn_classification_20260920.csv`
- `01_data/00_derived/AIM_Master_PN_Categories_Figkey_20260921.csv` / `.xlsx` — unchanged
- `01_data/91_build/export_aim_pn_categories_figkey_xlsx.py` — the builder, read only
