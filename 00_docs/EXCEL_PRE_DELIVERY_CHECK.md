# Excel pre-delivery check — ISZE (all projects)

**Purpose:** Mandatory gate before any Excel file is sent to Jerome. Run these checks in the agent session **before** saying “done” — avoids rework, wrong files, and wasted tokens.

**Companion files:**
| Scope | Doc / script |
|-------|----------------|
| **This file** | Universal formatting + logic rules, project index |
| IDS 2026 result reports | [`../04_tools/ids_dealer_ranking/IDS_2026_LOGIC_CHECK.md`](../04_tools/ids_dealer_ranking/IDS_2026_LOGIC_CHECK.md) + `ids_logic_check.py` |
| GPS / billing studies | [`../04_tools/isze-gps-auditor/SKILL.md`](../04_tools/isze-gps-auditor/SKILL.md) — data audit **before** building |
| Agent behaviour | [`../AGENTS.md`](../AGENTS.md) — never bury material caveats inside the file |

**Reference location (Jerome):** `09_meetings/Preparation Meetings/` — meeting prep workbooks; same rules apply.

---

## Agent workflow (every Excel deliverable)

```
1. Build from template or script (not hand-edited layout)
2. Run automated checks (see below)
3. Open in Excel / report COM results — merge, wrap, overflow, % caps
4. Post issues in CHAT if anything fails (GPS auditor Rule 1–3)
5. Only then deliver the file path to Jerome
```

**Do not** ship `_Delta`, `~$*`, or `* - Copy.*` variants unless explicitly requested.

---

## Quick automated run

From `ISZE/04_tools/`:

```powershell
# Universal: merges, wrap flags, column widths, freeze panes (openpyxl .xlsx)
python excel_pre_delivery_check.py path\to\file.xlsx

# Optional: compare merge count to a template
python excel_pre_delivery_check.py output.xlsx --template template.xlsx

# IDS 2026 country reports (.xls) — layout + score logic (all countries)
cd ids_dealer_ranking
python ids_logic_check.py
```

`.xls` (BIFF / xlutils clone): use **IDS** scripts or Excel COM for formula evaluation; `excel_pre_delivery_check.py` is primarily for `.xlsx`.

---

## A. Formatting — merge, wrap, extend

These are the errors that forced IDS rebuilds and meeting-prep rework. **Template-clone projects must not rebuild layout from scratch.**

### A1. Merged cells

| Check | Pass | Fail |
|-------|------|------|
| **A1.1** Merge count vs template | Same count as master (e.g. DK IDS: **13** merges) | Fewer merges → titles/sections broken |
| **A1.2** Value in merged range | Only **top-left** cell has content | Text written to non-anchor cell → invisible in Excel |
| **A1.3** No new accidental merges | Merges match template map | Script added merges over data columns |
| **A1.4** Horizontal merges for banners | Section titles span intended cols (e.g. `A4:J4`) | Title truncated in one narrow cell |

**How to verify:** `excel_pre_delivery_check.py` or `len(sh.merged_cells)` in xlrd with `formatting_info=True`.

**IDS rule:** Clone `2026 IDS Evaluation Result Report_DK.xls` via `xlutils.copy`; write dealers from column **D** only; never wipe cols A–C layout.

---

### A2. Wrap text

| Check | Pass | Fail |
|-------|------|------|
| **A2.1** Long labels (col B / descriptions) | `wrap_text=True` on question/description columns | `#####` or text spilling into neighbour columns |
| **A2.2** Headers / banners | Center + wrap where template uses it | One-line headers cut off |
| **A2.3** Row height | Tall enough for wrapped lines (or Excel auto-height after open) | Row 1–2 line text clipped vertically |

**How to verify:** Open file → inspect rows with long text (IDS row 17+ col B, GPS section titles). `excel_pre_delivery_check.py` flags description columns without wrap on openpyxl files.

---

### A3. Extend — column width & row height

| Check | Pass | Fail |
|-------|------|------|
| **A3.1** Column width | No `####` for numbers; names readable | Default width 8.43 on wide content |
| **A3.2** Dealer / ID columns | Wide enough for longest dealer name | Names truncated in print/PDF |
| **A3.3** Freeze panes | Match template (IDS: rows **1–12**, cols **A–C**) | Scroll loses headers |
| **A3.4** Print area | No broken `#REF!` print area warnings | Harmless warnings in openpyxl OK if QA passes |

**How to verify:** Scroll right/down in Excel; check last dealer column and bottom sections.

---

### A4. Colours & styles (template clones)

| Check | Pass | Fail |
|-------|------|------|
| **A4.1** Row band colours | Category/question rows keep DK banding | Flat white after `write()` |
| **A4.2** Category row sample | Row 15 col A background matches DK (pattern **56** on IDS) | Wrong band → “wrong file” impression |
| **A4.3** Styled writes only | `_styled_write` / copy xf from template | Raw xlwt write strips format |

---

## B. Logic — numbers & percentages

### B1. Universal rules

| Check | Rule |
|-------|------|
| **B1.1** No % > 100% | Any “%” or “Ave. %” column ≤ 1.0 (or ≤ 100 if %-formatted) |
| **B1.2** Scores ≤ max | Dealer score ≤ col C max for that row |
| **B1.3** Section = sum(children) | Sub-section rows = SUM(question rows); sections = SUM(sub-sections) |
| **B1.4** Totals reconcile | Grand total = sum of sections (or documented override) |
| **B1.5** Formulas vs constants | Section/total rows use **formulas** where template does (IDS row 13/15/16) |
| **B1.6** GPS% | Run GPS auditor first; flag GPS% > 95% before shipping ([`isze-gps-auditor`](../04_tools/isze-gps-auditor/SKILL.md)) |

### B2. Integer vs fraction trap

| Input | Max | Correct |
|-------|-----|---------|
| `0.5` | 2 | 1 point (50% of max) |
| `1` (integer) | 3 | **1 point**, not 100% |
| `4` in French rubric col | 1 | Rubric/priority code — **not** 4 points |

---

## C. Project index — what to run before delivery

| Project | Output (typical) | Build script | Pre-delivery checks |
|---------|------------------|--------------|---------------------|
| **IDS 2026 result reports** | `01_data/90_INBOX/IDS_2026/reports/evaluation_result/*.xls` | `04_tools/ids_dealer_ranking/run_ids_result_reports.py` | `ids_logic_check.py` + `ids_report_qa.py`; open `.xls` not `_delta` |
| **IDS rankings** | `IDS_2026/rankings/*.xlsx` | `build_country_ranking.py`, `combine_all_rankings.py` | `excel_pre_delivery_check.py`; freeze `A2`; % in charts vs sheet |
| **IDS language workbook** | `build_language_workbook.py` output | same | wrap col D; freeze panes |
| **GPS Kosha / v5** | `04_tools/build_gps_v5.py`, `03_analytics/build_gps_kosha*.py` | same | merges on banners; GPS auditor on source data; no GPS% > 100% without caveat |
| **GPS v8/v9 builds** | `01_data/91_build/build_gps_v*.py` | same | template merge map; waterfall reconciles |
| **UIO overview** | `06_uio/_CURRENT/*.xlsx` | `06_uio/_Scripts/build_isuzu_uio.py` | **Ask Jerome** before changing formulas; spot-check totals |
| **Ireland SIMI / GPS calc** | `06_uio/Ireland_SIMI_Comparison/*.xlsx` | `build_*` in folder | tab names; no broken refs; merge on title rows |
| **PMS / pricing basket** | `Projects/Isuzu/pms-pilot/`, `01_data/` | various | PRISM verify; no list prices without source |
| **NOx SPA optimizer export** | Streamlit export / `isze-tools` | `5_NOx_SPA_Optimizer.py` | merge `A1:V1`; freeze `A4` |
| **Autodoc / AIM enrich** | `04_tools/autodoc_scraper/*.xlsx` | enrich scripts | freeze `A2`; wrap on long URLs |
| **Meeting prep (UTI/EU_Conf26)** | `09_meetings/Preparation Meetings/**` | `_build/*.py`, deck fix scripts | overflow scripts run; no clipped shapes (see `fix_slide8_overflow.py` for PPT; same discipline for Excel) |
| **Action plan / KPI targets** | `02_dashboards/Data/11_planning/_build/` | `build_kpi_targets.py` | % columns; named sheets |

**Not Excel but same gate:** HTML dashboards → `02_dashboards/sync_to_deploys.ps1` after edit; PRISM KPIs → green `_verification_report.json` first.

---

## D. IDS 2026 — summary pointer

Full detail: [`IDS_2026_LOGIC_CHECK.md`](../04_tools/ids_dealer_ranking/IDS_2026_LOGIC_CHECK.md)

| Topic | Rule |
|-------|------|
| Files | Deliver `*.xls` from `evaluation_result/` |
| Row 18 / A.1-2 % | Ave. % ≤ 1.0; `MIN(avg/max,1)` |
| Rows 15–16 | Formulas `=SUM(...)` / `=D16+D39+D44`, not static totals |
| Col C | Max points only — never dealer data |
| Countries | 13 built; Denmark/MIDI excluded |
| Error register | E01–E11 in IDS doc |
| Map / geo / Mode A UI | §6b in IDS doc + `.cursor/rules/isze-ids-delivery.mdc`; `build_ids_dashboard.py` geo sanity |

```powershell
cd ISZE\04_tools\ids_dealer_ranking
python ids_logic_check.py
python ids_report_qa.py "..\..\01_data\90_INBOX\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_BE.xls"
python build_ids_dashboard.py   # geo sanity + heatmap QA before HTML write
```

---

## E. Error register (cross-project)

| ID | Symptom | Cause | Prevention |
|----|---------|-------|------------|
| X01 | % > 100% in Ave. column | Outlier score / wrong parser | Cap scores; `MIN(avg/max,1)`; rubric fallback |
| X02 | Totals ~10–15 pts high | `1` = 100% when max > 1 | `_coerce_score`: fraction only if `0 < v < 1` |
| X03 | Layout “wrong file” | Rebuilt workbook vs clone | xlutils.copy + write D+ only |
| X04 | Colours missing | Unstyled write | `_styled_write` + row xf snapshot |
| X05 | Merges lost | New workbook from scratch | Compare `len(merged_cells)` to template |
| X06 | Text clipped | No wrap / narrow cols | `wrap_text=True`; set column width |
| X07 | Section totals don’t update | Static values not formulas | DK-style `SUM` / `+` formulas |
| X08 | User opened Delta xlsx | Wrong deliverable | `_delta/` subfolder; state in chat |
| X09 | Duplicate dashboard count | ` - Copy.xls` | Exclude copies in discover |
| X10 | GPS trend wrong | YoY parquet inconsistency | GPS auditor CHECK 4 |
| X11 | Delivered with known bug | Caveat only in footnote | Stop in chat first (GPS auditor Rule 1–3) |

---

## F. Sign-off template (per file)

Copy for each delivery:

```markdown
## Pre-delivery sign-off — [filename]

- [ ] A1 Merges OK (count: ___ vs template ___)
- [ ] A2 Wrap OK on description/long-text columns
- [ ] A3 Column widths / freeze panes OK
- [ ] A4 Colours/styles OK (if template clone)
- [ ] B1 No % > 100%; scores ≤ max
- [ ] B2 Section arithmetic / formulas OK
- [ ] Project-specific script passed: ___
- [ ] Issues surfaced in chat (not only in file): N/A or [list]

**Path:** 
**Built by:** 
**Date:**
```

---

## G. Adding a new Excel project

1. Add a row to **section C** in this file.
2. If repeatable: add checks to `excel_pre_delivery_check.py` or a project `*_qa.py`.
3. Log new failure modes in **section E**.
4. Reference this file from the project README or `05_memory/projects/*.md`.
