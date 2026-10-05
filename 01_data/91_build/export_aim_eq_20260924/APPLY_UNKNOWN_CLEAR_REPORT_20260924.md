# Unknown-marker clear for the IE40 price list — STOPPED before any write

**Date:** 2026-09-24 · **Agent:** cursor (AIM unknown-clear pass)
**Verdict: nothing was written. The brief's count of 819 does not come off the master. The master
gives 845 on this price list, and the brief tells me to stop and report when my number differs.**

Jerome's authority, in his words: *clear the marker on all 819 and let the rules take what they
can.* That authorises the change to the marker. It does not authorise me to pick a different set
from the one measured, or to reconcile a 26-row gap by assuming. So I stopped at the first guard
and am reporting instead.

My pass wrote nothing, and the two files were untouched by me. That is asserted by hash, below.
**Read section 9 first: a parallel agent changed both files at 16:20:54, while this pass was still
measuring.** Everything in sections 1 to 6 describes the state I measured and stopped on.

---

## 1. What I measured, and the one thing that does not line up

Reading the master as it stands right now, and taking the 1,097 part numbers with no family from
the queue:

| Group | Measured | The brief says |
|---|---:|---:|
| Carrying the marker (`Unknown` / `Unknown Review`) on the master | **845** | 819 |
| Master row, family genuinely blank | **209** | 235 |
| No master row at all | **43** | 43 |
| Total | **1,097** | 1,097 |

Both splits add to 1,097. The difference is entirely in the first two lines: 845 against 819, and
209 against 235. The gap is exactly 26 rows, moving from one side of the split to the other.

I did not guess at these. `open_parts_classified.csv` — the brief's own reference file — reports
the marker group as 845. Every one of the fourteen earlier saved states of the master, back to
2026-09-18, also gives 845 on this list. It has never been 819.

## 2. Where 819 actually comes from

819 is the same set read off the *other* file. The classification overlay
(`aim_pn_classification_20260920.csv`) carries a marker in `aim_l1_fixed` for exactly **819** of
those 845 rows. I verified the difference both ways:

- marker on the master but **not** on the overlay: **26** rows
- marker on the overlay but **not** on the master: **0** rows

So 819 is a strict subset of 845. The brief has ten "fixed" clear checks for the overlay, so the
819 is consistent with the overlay having been the file that was read.

**And the missing 26 are not "genuinely blank".** They carry the marker on the master in all five
AIM columns (`aim_l1`, `aim_l2`, `aim_l3`, `aim_l1_fixed`, `aim_l2_fixed`), and they are exactly
the 26 that have **no row at all** in the overlay. They are screws, studs, washers, split pins and clips: `PIPE VINYL` `35663000`,
`SCREW; CONT UNIT` `362304120`, `STUD; CRANKCASE` `410108350`, `PIN; SPLIT,STAB ROD` `811250450`,
`WASHER; LK,BRKT TO FRAME` `915108140`, `CLIP; HOSE` `952073100` and eighteen more of the same
kind. All 26 are stamp `aim_source = aim_workbook` with `has_aim = 0`.

That matters, because the brief says the 235 are *"a master row but a genuinely blank family, with
no usable evidence to reason from"* and leaves them alone. The 26 are the opposite: they do carry
a marker, on the master, which the brief says to clear. Treating them as blank would silently
leave 26 markers standing on parts the decision was meant to cover. That is a real difference, not
a rounding.

## 3. The 4,115 arithmetic does not hold either, so I did not use it as the guard

The brief's other number, the 4,115 marker rows that must keep their marker, comes from
4,934 − 819. Measured master-wide:

| Definition | Rows |
|---|---:|
| `aim_l1` carries the marker | **4,934** |
| any AIM column carries the marker | **4,936** |
| the overlay carries the marker in `aim_l*_fixed` | **4,936** |

The brief's 4,934 matches the first reading. Two extra rows carry the marker only underneath
(`aim_l3_fixed`, and one in `aim_l2_fixed`) with `aim_source = aim_workbook|gap_auto_20260918_sst`,
which is why the three figures differ. I am reporting the measured numbers rather than the
assumed ones, and I have not used any of them as a guard because the guard already failed on the
819/845 question.

The rows that must not move, measured: **4,091** master-wide marker rows sit outside this list and
would have to keep their marker. On the brief's arithmetic that figure is 4,115.

## 4. The placement count is also not what the brief expects

Not a reason to stop on its own, but it belongs in the report because the brief says to expect
roughly 228.

Running the placement rule exactly as the two earlier write-backs describe it — one full AIM path
already carried by the exact description, at least three master parts behind it, figure key as a
veto only — applied to the 845 marker rows:

- **104** would be placed
- **741** would remain unplaced
- 0 landed on a residual bucket, 0 on a wording the tiering study held back, and the figure key
  vetoed nothing

The brief's own reference file, `open_why.py`, reports **88** for the same question, and 228 only
if the rule is *relaxed* — that is, allowed to use wordings with fewer than three supporting
parts, to pick a leaf where two are strong, and to stop letting the figure key veto. **This brief
explicitly says to reuse the strict method and not to soften it.** So 228 is not reachable under
the instruction as written, and the two strict readings I can measure (88 and 104) do not agree
with each other either. The difference between them is the overlay: treating the overlay's family
as part of the wording dictionary changes which wordings resolve, and that is the same file-scope
question as section 2.

I am not claiming a placement figure. I am telling you the range and why it is not settled.

## 5. Nothing was written — asserted, not assumed

| File | Size | sha256 | State |
|---|---:|---|---|
| `01_data\00_derived\aim_master_v2.csv` | 28,529,377 | `cd69c50604dbd4ff2ec9a3a46a446f0d4a34230c3ebc3e43628725acef731507` | unchanged — matches the hash the 14:15 fill report published |
| `01_data\00_derived\aim_pn_classification_20260920.csv` | 24,881,175 | `60111c104ddeb466e6c15f084039639d35172056b0fd2ea10225a3c50da610e0` | unchanged |
| `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.csv` | 13,108,965 | `7437b549ad08d4a102c86b39caaccc263f1834f9f379a5e19395f83cfc912280` | unchanged — matches the fill report |
| `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.xlsx` | 9,272,663 | `7316a9b530d32aaab1e48d898f78e5e332567dbf54e057b1c4ef818a0cfa0dc5` | unchanged — matches the fill report |
| `01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260921.csv` | 13,093,140 | `bed9c4a266aa2851c691ba564f92edbc6723ee61cec6bf261c199b3cb4f6a5fb` | untouched, as instructed |

Consequences, stated plainly:

- **No backups were taken**, because no write was prepared. The two backup paths the brief asked
  for (`aim_master_v2.csv.bak_pre_unknown_clear_20260924_<HHMMSS>` and
  `aim_pn_classification_20260920.csv.bak_pre_unknown_clear_20260924_<HHMMSS>`) **do not exist.**
  I am not creating a backup of a file I did not change; that would dress this up as progress.
- **The dated pair was not rebuilt.** The copy to
  `_backup_20260924_pair_before_unknown_clear\` was **not** made either, for the same reason. The
  2026-09-24 pair still holds the 44 and the 162 from this afternoon and nothing else.
- **The 2026-09-21 pair is untouched.**
- **No dashboard was touched. No browser was driven. No EPC or Snap-on lookup was run.**
  `PASTE_INTO_EQ_CONSOLE_EPC_ONLY_20260924.js` and `open_worklist_epc_only_20260924.*` were not
  read, opened or modified.
- **No change-log row was appended to `DELEGATOR_BOARD.md`.** The brief asks for one row per
  completed change; there was no completed change. The board entry for this pass is the stop
  itself, which I have written up here.

## 6. What I did write

Only inside my own working folder, `01_data\91_build\export_aim_unknown_clear_20260924\`:

| File | What it is |
|---|---|
| `candidate_845_master_set.csv` | the 845 part numbers that carry the marker **on the master** — the set the brief's step 1 derives |
| `candidate_819_overlay_set.csv` | the 819 that carry the marker **on the overlay** — a subset of the 845 |
| `candidate_26_not_in_overlay.csv` | the 26 that are in the first set and not the second, with their wording and marker text |
| `measure_rule_on_markers.py` / `candidate_845_decisions.csv` / `candidate_845_summary.json` | what the strict rule would place on the 845, row by row |
| `probe_819.py`, `probe_819_diff.py`, `probe_819_source.py`, `probe_masterwide.py`, `probe_history.py` (+ their `*_run.txt`) | the measurements behind every number above, each re-runnable |
| `write_candidate_lists.py` | the script that wrote the three candidate lists |

Every one is read-only against the shared files.

## 7. The decision I need from you

Two questions, and the first is the only one that blocks:

1. **Which set is the one you decided on — 845 or 819?** If your decision covered "the parts this
   price list is blocked on", that is 845 and the extra 26 screws, studs, washers and clips come
   with it. If it covered "the parts the overlay flags", it is 819 and the 26 are out of scope.
   The 26 have no row in the overlay, so nothing else in the workspace would place them either.

2. **Which version of the rule — strict or relaxed?** Strict places 104 of the 845 (my reading) or
   88 (the reference file's). Relaxed reaches 228 but is the softer rule the brief told me not to
   use. If you want 228, that is a change to the rule and it should be said out loud.

Everything else in the brief is ready to run the moment those two are settled. The backup, the
paired clear across both files and all their fixed columns, the stamp
`unknown_clear_20260924`, the pair rebuild and the six verification checks are all drafted.

## 8. What I could not verify

1. **Why the briefing note itself says 819.** I can show that 819 is the overlay's count and 845
   is the master's, and that the 26 sit in between. I cannot tell you which one the note meant to
   use.
2. **The placement count is a range, not a figure.** 88 and 104 are both defensible readings of
   the same strict rule and I have not reconciled them. I am not quoting either as the answer.
3. **I did not hand-read the 845 or the 819.** I read the 26 difference rows individually, and the
   wording statistics for the rest.
4. **Nothing downstream was re-derived.** Because no write happened, there was nothing to
   re-derive.

Nothing published. No dashboard touched. No browser, no EPC run. No mail.

---

## 9. Superseded part-way through: a parallel agent wrote both files at 16:20:54

While this pass was still measuring, a second agent working the same IE40 queue changed both
files. I did not write them and I did not authorise them. The timestamps, the hashes and the
backup names all say it was one run started at 14:20:51.

| File | Time | Bytes now | sha256 now |
|---|---|---:|---|
| `01_data\00_derived\aim_master_v2.csv` | 16:20:54 | 28,606,117 | `1870dc2ac08e8128c9323a5da14ad46742bb1200f24d3d6faa3ed53576b74af4` |
| `01_data\00_derived\aim_pn_classification_20260920.csv` | 16:20:55 | 24,925,134 | `e5824683806f7b7fdef1…` |

Their own summary is `01_data\91_build\export_aim_eq_20260924\apply_summary.json`, their script is
`apply.py` (16:20:10) and `build_epc_only_worklist.py` (16:21:40), and their backups are named
`…bak_pre_export_aim_eq_20260924_20260924_142051`.

**What they did to the 845.** Re-measured against the 16:20:54 backup, which is the state this
report describes:

| Outcome on the 845 | Rows |
|---|---:|
| Now carry a real family | **800**, all stamped `aim_source = aim_workbook\|export_aim_eq_20260924` |
| Now blank | **0** |
| Still carrying a marker | **45** |

The 45 still marked — `HYDRAULIC UNIT; ANTI LOCK BRK` on `7552357310` and `8982324801`,
`TARGET;AEBS CAMERA AIMIMG`, eleven cooler and brake hoses, `GLASS; BACKLIGHT`, `PIPE VINYL`,
`THERMOMETER UNIT`, and a run of studs, screws, washers, pins and clips. **All 26 rows I flagged in
section 2 are inside that 45.** So the gap I stopped on was real, and the parallel run came out at
the same place from the other direction: it placed the 800 that agree across both files and left
exactly the contested rows alone.

**What they did to the pair. This is the part that needs your eye.** From `apply_summary.json`:

- They rebuilt the **2026-09-21** pair (`AIM_Master_PN_Categories_Figkey_20260921.csv` 13,149,086
  bytes at 16:21:05, `.xlsx` 9,291,457 bytes at 16:21:38) — after backing it up to
  `…bak_pre_export_aim_eq_20260924_20260924_142051`. Their work **is** in that pair: of the 819, it
  now shows a real family for **794** and still `Unknown` for **25**.
- They did **not** rebuild the 2026-09-24 pair. It still sits at 14:09:23 and shows all **819** as
  `Unknown`. So the pair dated today — the one this brief calls the Power BI deliverable — is
  **stale**: it carries none of the 800 (or 794) cleared rows.
- That pair builder wrote its launcher beside **today's** filename:
  `OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd`, now 74 bytes, pointing at
  `AIM_Master_PN_Categories_Figkey_20260921.xlsx`. The launcher name and the file it opens no
  longer match.

So the position is: the master and the overlay are cleared, the 21st pair reflects it, and the
24th pair — the one the brief asked to be rebuilt — does not.

Their `master_unknown_l1_before/after` figures (145,265 → 144,279, a drop of 986) count the text
`Unknown` anywhere in `aim_l1`, which includes placeholder rows far outside this price list, not
the 4,934 marker rows. That is a different measurement from the one in section 3 and the two
should not be compared directly.

**What this means for the brief.** Steps 2, 3, 6 and 7 were carried out by that other run, not by
me, and the set it acted on came out at the measured 845 rather than the 819. Whether that outcome
is the one you decided on is still the question in section 7 — I have not laid a second write on
top of an active one, and I would not. I have left my own candidate lists in place so the two sets
can be compared without re-deriving them.

