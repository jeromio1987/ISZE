# Universe AIM accuracy sample — restored 7 Oct 2026

## Verdict

The 50-part family agreement sample the Universe board expects is back on disk at the path the builder hardcodes. Board accuracy is no longer forced to 0 for a missing file. Family agreement is **47 of 50 = 94%** (bar 90%), so the accuracy condition scores **1**.

## Method (honest, not re-invented)

This is the **24 Sep 2026** measure, restored from `_scratch`, not a new human re-read on 7 Oct.

1. **Draw.** Fifty classified part numbers, probability proportional to L12M billed euro, fixed seed `20260924`. Window = twelve months to the max billing date in the parts base (then 2025-09-01 → 2026-08-31). Script: `_aim_accuracy_sample_20260924.py`.
2. **Judgement.** A named reader compared each part’s billed description to the AIM family / group / leaf it carries, using the part’s figure key and figure-key siblings as a second read. Verdicts filled by `_aim_sample_verdicts_20260924.py`. Nothing on the master was adjusted.
3. **Contract the board reads.** Columns include `agree_l1`, `agree_l2`, `agree_l3` (`Y`/`N`), plus part number, description, euro, AIM L1–L3, figure key, and a note on disagreements.

Full write-up of the original measure: `00_docs/AIM_COVERAGE_MEASURE_2026-09-24.md` §5.

## Results (n = 50)

| Level | Agree | Rate |
|---|---|---|
| Family (L1) | 47 of 50 | **94%** |
| Group (L2) | 43 of 50 | 86% |
| Leaf (L3) | 41 of 50 | 82% |

**Three family-level disagreements (agree_l1 = N):**

| Part | Description (as billed) | Carried family | Why N |
|---|---|---|---|
| 8981455011 | OVERHAUL KIT; SUPPLY PUMP | Transmission | Supply-pump overhaul kit; figure key labelled Pump — engine/fuel, not transmission |
| 8973665260 | SLEEVE & HUB ASM; TOP-4TH,OD | Wheels Hub | Fourth-gear mainshaft hub sleeve; figure key “Review needed”, no corroboration |
| 8980432054 | PUMP ASM; OIL,P/S | Fuel System | Power-steering pump; figure key labelled Steering pump |

## Absolute paths

| Role | Path |
|---|---|
| Sample CSV (board input) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_accuracy_sample_20260924.csv` |
| Draw script | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_accuracy_sample_20260924.py` |
| Verdict filler | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_sample_verdicts_20260924.py` |
| Scratch originals (source of restore) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_scratch\_aim_accuracy_sample_20260924.csv` (and sibling `.py` / verdicts) |
| Coverage measure JSON (also restored; board reads it) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_aim_coverage_measure_20260924.json` |
| Board HTML | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\ISZE_UNIVERSE_BOARD.html` |
| Board state JSON | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\universe_board_state.json` |
| Launcher | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\OPEN_ISZE_UNIVERSE_BOARD.cmd` |

## Board after rebuild (7 Oct 2026)

| Measure | Before (missing sample) | After |
|---|---|---|
| Accuracy condition | 0 (file missing) | **1** (47/50 = 94%) |
| AIM pillar | 40% (4/10) | **60% (6/10)** |
| Groundwork | 43% (26/60) | **48% (29/60)** |

Stale banner turned off (`SHOW_STALE_BOARD_BANNER = False`) because this was a deliberate re-score with the sample restored.

## What is still UNKNOWN

- **These verdicts were not re-read on 7 Oct.** Restoring the filled CSV is honest about the 24 Sep judgement; it is not a fresh independent sample against today’s master. If the master moved on those 50 part numbers, agreement could change — that was not re-checked row-by-row today.
- **Not a random sample of the catalogue.** Weighted to billed euro among classified parts. Says nothing about ~144k master rows with no family.
- **L2 / L3 have no pass bar** on the board; only L1 ≥ 90% scores the condition.
- **Other AIM conditions** (approved release half-credit, one-distributor page half-credit, gate leaf-count fail) are unchanged by this restore.
