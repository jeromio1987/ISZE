# IDS 2026 Evaluation Result Reports — Logic Check

> **Workspace gate:** Read [`../../00_docs/EXCEL_PRE_DELIVERY_CHECK.md`](../../00_docs/EXCEL_PRE_DELIVERY_CHECK.md) first — merge, wrap, extend, and cross-project rules apply before every Excel delivery.

Use this document after every rebuild (`run_ids_result_reports.py`) or when investigating a suspicious score. It lists **all known failure modes**, how to detect them, and what “correct” looks like.

**Open for review:** `reports/evaluation_result/2026 IDS Evaluation Result Report_{CC}.xls`  
**Do not use for layout review:** `_delta/*_Delta.xlsx` (plain numbers, no DK formatting or formulas).

Paths are relative to `ISZE/01_data/90_INBOX/IDS_2026/` unless noted.

---

## Quick automated run

From `ISZE/04_tools/ids_dealer_ranking/` (after universal checks in `00_docs/EXCEL_PRE_DELIVERY_CHECK.md`):

```powershell
# Rebuild all countries + layout QA (built into --qa)
python run_ids_result_reports.py

# Layout QA on one file
python ids_report_qa.py "..\..\01_data\90_INBOX\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_BE.xls"

# Logic checks (scores, %, section sums) — all countries
python ids_logic_check.py

# Rebuild offline dashboard after reports change (refuses to write if heatmap empty)
python build_ids_dashboard.py
```

`build_ids_dashboard.py` runs **section-heatmap QA** before writing HTML: it fails (exit 3) if fewer than half of dealers have A–E section pct, or if any non-ITUK country would render an all-grey heatmap. Root cause of that failure mode: category/total cells are Excel formulas without cached values — extract must sum question rows. Override only with `--skip-qa`.

`ids_logic_check.py` implements the **Score & percentage** and **Section arithmetic** sections below. Layout checks stay in `ids_report_qa.py`.

---

## Countries in scope

| Country | Input folder | Report file | Notes |
|---------|--------------|-------------|-------|
| BE | `BE/` | `..._BE.xls` | French/Dutch eval sheets; rubric fallback important |
| NL | `NL/` | `..._NL.xls` | Zelfevaluatie: integer `1` = 1 point, not 100% |
| Poland | `Poland/` | `..._Poland.xls` | |
| Petros | `Petros/` | `..._Petros.xls` | |
| RSA | `RSA/` | `..._RSA.xls` | |
| IUK | `IUK/` | `..._IUK.xls` | |
| ITUK | `ITUK/` | `..._ITUK.xls` | **Totals only** — no A–E detail rows filled |
| Israel | `Israel/` | `..._Israel.xls` | |
| Malta | `Gasanzammit/` | `..._Malta.xls` | |
| Cyprus | `Loutsios/` | `..._Cyprus.xls` | |
| Romania | `Romania/` | `..._Romania.xls` | Skips `ISUZU DEALERS ROMANIA 2025.xlsx` |
| Portugal | `Portugal/` | `..._Portugal.xls` | |
| Hungary | `Hungary/` | `..._Hungary.xls` | Hungarian rubric columns |
| Denmark | — | — | **Not built** — ranking export only |
| MIDI | `MIDI/` | — | **Not built** — consolidated file, no adapter |

---

## 1. Score & percentage logic

### 1.1 No percentage above 100%

| Check | Rule | How to fail |
|-------|------|-------------|
| **Ave. % column** | For every scored row with max points in col C, `Ave. %` ≤ **1.0** (100% when formatted as %) | Outlier dealer score above max; bad self-eval parsing; missing `MIN(...,1)` in formula |
| **Dealer % row (14)** | `Score (One hundred perfect score conversion)` ≤ **1.0** per dealer | Total > 280 |
| **Dealer question scores** | Each question score ≤ **col C max** for that row | Priority/rubric code written as points (e.g. `4` on max-1 item) |

**Typical bug (fixed):** Garage Degroote (BE) had `4` in French auto-évaluation for A.1-2 (max 1). Country average for row 18 showed **105.9%** (`1.059`).

**Fixes in pipeline:**
- Scores capped at `max_points` when writing.
- `Ave. %` formula: `MIN(TotalAverage / MaxPoints, 1)`.
- Self-eval above max → fall back to OUI/NON rubric columns (H–K).

**Manual spot-check (Excel):**
1. Row 12 headers: `Total Average` | `Ave. %`.
2. Pick any question row (e.g. A.1-2, row 18).
3. Confirm **Ave. %** ≤ 1.0 (or ≤ 100% if column is %-formatted).

**When max = 1:** `Total Average` and `Ave. %` show the **same number** (e.g. `0.97`). That is correct — not a duplicate-column bug.

---

### 1.2 Self-evaluation parsing (`_coerce_score`)

| Input in dealer file | Max points | Correct interpretation |
|---------------------|------------|------------------------|
| `0.5` (strictly between 0 and 1) | > 1 | Fraction of max → `0.5 × max` |
| `1` (integer) | 2 or 3 | **1 point**, not 100% |
| `1.0` | 1 | 1 point (100% of that item) |
| `YES` / `OUI` / `JA` | any | Full max |
| `NO` / `NON` / `NEE` | any | 0 |
| Value > max | any | Use rubric columns; else cap at max |

**Typical bug (fixed):** Integer `1` on max-3 questions treated as 100% → inflated totals (~+13 pts average across ~241 dealers on standard templates). Example: Antoretti BE **208** correct, not 232.

---

### 1.3 French / rubric fallback

When auto-évaluation (col L) is invalid (> max or missing):

1. Scan Point 0 / 1 / 2 / 3 columns (H–K) for **OUI / YES / JA**.
2. Use that rubric level as the score (capped at max).
3. Do **not** treat `NON` in the Point-0 description column as a zero score.

**Typical bug (fixed):** First `NON` in Point-0 column forced score `0` instead of reading `OUI` in Point-1.

---

## 2. Section arithmetic (rows 15–16 and totals)

Section rows **should differ per dealer** — they are totals, not constants.

| Row (Excel) | Label | Col C | Dealer columns should be |
|-------------|-------|-------|---------------------------|
| 13 | Score (Original) | 280 | Sum of sections A–E (or override for ITUK) |
| 15 | A. Premises, Facility and Clothing | 46 | `=D16+D39+D44` (sub-sections) |
| 16 | A.1 Premises | 32 | `=SUM(D17:D38)` (all A.1-x questions) |

| Check | Rule |
|-------|------|
| Sub-section = sum of questions | Row 16 dealer value = sum of A.1-1 … A.1-22 for that dealer |
| Section A = sum of sub-sections | Row 15 = A.1 + A.2 + A.3 for that dealer |
| Total = sum of top sections | Row 13 = A + B + C + D + E |
| Row 14 % | `=D13/280` (linked to row 13) |

**Typical bug (fixed):** Static Python totals in section rows instead of DK **formulas** — looked like unrelated “variables” and did not recalc when a question cell was edited.

**Manual spot-check:** Click **D16** → formula bar shows `=SUM(D17:D38)`. Change one question → row 16 updates.

---

## 3. Layout & column rules (DK clone)

Automated: `ids_report_qa.py`

| # | Check | Pass |
|---|-------|------|
| L1 | Main sheet name ends with `26` (e.g. `BE26`) | ✓ |
| L2 | 235 rows, merge count matches DK template | ✓ |
| L3 | Dealers start **column D** (index 3) | ✓ |
| L4 | Col **C** on meta rows (3–11): **empty** | ✓ |
| L5 | Col **C** row 13: **280** | ✓ |
| L6 | Col **C** row 14: **empty** | ✓ |
| L7 | Row 12: `Total Average` / `Ave. %` above score block | ✓ |
| L8 | Row 2: dealer index numbers only — **no** avg labels | ✓ |
| L9 | Col A question refs row 15+ match DK template | ✓ |
| L10 | Col C max points match DK per row | ✓ |
| L11 | Row band colours on dealer columns match DK | ✓ |

**Typical bugs (fixed):**
- Dealer data written in column C.
- Average headers missing (were cleared with dealer columns).
- Row colours lost after `write()` without template styles.

---

## 4. File hygiene

| Check | Rule |
|-------|------|
| F1 | Use `*.xls` in `evaluation_result/` — not `*_Delta.xlsx` for review |
| F2 | Ignore `* - Copy.xls` duplicates (excluded from dashboard) |
| F3 | Close Excel before rebuild — file lock blocks overwrite on Windows |
| F4 | Dashboard reads `evaluation_result/*.xls` only | Expected ~308 dealers (13 countries), not ~563 |

---

## 5. Per-dealer parsing

| Check | Rule |
|-------|------|
| P1 | Every included dealer has a name in row 3 | |
| P2 | Total row 13 matches sum of `question_scores` (± rounding) unless `total_override` (ITUK) | |
| P3 | No dealer score > max on any question row | |
| P4 | Skipped files: `*ranking*`, `*met grafiek*`, `~$*`, Romania 2025 aggregate | |

**ITUK exception:** Detail rows (15+) empty; only row 13 totals populated from consolidated workbook.

---

## 6. Dashboard (`IDS_2026_dealer_compare.html`)

After `build_ids_dashboard.py`:

| Check | Expected |
|-------|----------|
| D1 | Dealer count ~308 (not doubled) | |
| D2 | 13 countries listed | |
| D3 | Section % derived from category rows in `.xls` | |
| D4 | No ` - Copy.xls` files in source folder | |

---

## 7. Error register (history)

Use as regression checklist — if any reappears, treat as **blocker** before sharing reports.

| ID | Symptom | Root cause | Prevention |
|----|---------|------------|------------|
| E01 | Ave. % > 100% (e.g. 105.9% on A.1-2) | Outlier score above max in one dealer file | Cap scores; `MIN(avg/max,1)`; rubric fallback |
| E02 | Totals ~10–15 pts too high | `1` interpreted as 100% when max > 1 | `_coerce_score`: fraction only if `0 < v < 1` |
| E03 | Antoretti 232 vs 208 | Same as E02 | Rebuild after coerce fix |
| E04 | Section rows don’t match questions | Static sums vs Excel | Section rows use `SUM` / `+` formulas like DK |
| E05 | Column C has dealer names/scores | Full sheet rewrite | Clone DK template; write dealers col D+ only |
| E06 | Missing row colours | Unstyled `write()` | `_styled_write` + row style snapshot |
| E07 | Missing `Total Average` / `Ave. %` headers | Cleared with dealer cols | Rewrite row 12 headers after clear |
| E08 | Dashboard 563 dealers | Duplicate ` - Copy.xls` | `discover_result_reports` excludes copies |
| E09 | Degroote A.1-1/A.1-2 = 0 | Rubric: `NON` in Point-0 taken as score | Only `OUI`/`YES` in rubric cols sets score |
| E10 | User opens Delta xlsx | Wrong file type for review | Delta in `_delta/`; docs + this checklist |
| E11 | openpyxl print-area warning | Harmless defined name in dealer files | Ignore; QA still passes |

---

## 8. Per-country sign-off

After rebuild, mark each country when **layout QA** (`ids_report_qa.py`) and **logic check** (`ids_logic_check.py`) pass.

| Country | Layout QA | Logic check | Date | Notes |
|---------|-----------|-------------|------|-------|
| BE | ☐ | ☐ | | |
| NL | ☐ | ☐ | | |
| Poland | ☐ | ☐ | | |
| Petros | ☐ | ☐ | | |
| RSA | ☐ | ☐ | | |
| IUK | ☐ | ☐ | | |
| ITUK | ☐ | ☐ | | totals only |
| Israel | ☐ | ☐ | | |
| Malta | ☐ | ☐ | | |
| Cyprus | ☐ | ☐ | | |
| Romania | ☐ | ☐ | | |
| Portugal | ☐ | ☐ | | |
| Hungary | ☐ | ☐ | | |

---

## 9. Reference — key files

| File | Role |
|------|------|
| `build_ids_result_report.py` | Build `.xls` from dealer workbooks |
| `ids_report_qa.py` | Layout compare vs DK template |
| `ids_logic_check.py` | Score / % / section arithmetic checks |
| `run_ids_result_reports.py` | Batch build 13 countries |
| `ids_report_extract.py` | Extract data for dashboard |
| `build_ids_dashboard.py` | Offline HTML dashboard |
| `ids_paths.py` | Paths and country resolution |
| `reports/_template/2026 IDS Evaluation Result Report_DK.xls` | DK master (sheet `DK26`) |

---

## 10. Escalation

If logic check fails for one dealer but not others:

1. Note **country**, **dealer name**, **question ref** (e.g. A.1-2), **raw value** in source `.xlsx`.
2. Run `parse_dealer_workbook` on that file in isolation (see `build_ids_result_report.py`).
3. Fix parser or add rubric rule; rebuild country; re-run `ids_logic_check.py`.

If layout QA fails: compare row/col indices to DK template — do not patch the `.xls` by hand; fix `build_ids_result_report.py` and rebuild.
