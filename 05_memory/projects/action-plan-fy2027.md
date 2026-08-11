# FY2027 VPACC Action Plan — pointer (Mode B)

**Status:** Active · July 2026 update on git.

## Canonical files

| Kind | Path |
|------|------|
| ★ Workbook (July) | `01_data/11_planning/Action plan FY2027 VPACC_July update.xlsx` |
| Prior | `01_data/11_planning/Action plan FY2027 VPACC_April update.xlsx` |
| Folder map | `01_data/11_planning/README.md` |
| Main actions | `01_data/00_derived/vpacc_fy2027_action_plan_july.parquet` |
| Meta | `01_data/00_derived/vpacc_fy2027_action_plan_july.meta.json` |
| Builder | `01_data/91_build/build_vpacc_fy2027_action_plan.py` |

## Streams & join fields

- **VP** / **ACC** in `stream`
- Owner: `pic` (initials, e.g. JVDP, KM, DW)
- Status: `progress_status` (`plan_made` → `completed_and_eval`) + `progress_filled` (0–4)
- ACC also has `deadline`
- Not dealer-keyed — later IDS/sales/pricing joins are by theme/`pic`/stream, not dealer code
