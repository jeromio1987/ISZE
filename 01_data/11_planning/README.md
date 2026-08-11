# Planning / KPI (`11_planning/`)

## VPACC FY2027 Action Plan

| File | Role |
|------|------|
| `Action plan FY2027 VPACC_July update.xlsx` | ★ newest (July) — git-allowlisted |
| `Action plan FY2027 VPACC_April update.xlsx` | Prior monthly (local; folder mostly off-git) |

**Sheets:** `Action Plan VP` · `Action Plan ACC` · `Sheet1` (orders) · `2018` (misnamed monthly EUR by DB).

**Derived (git):** `01_data/00_derived/vpacc_fy2027_action_plan_july.parquet` (+ orders / monthly / `.meta.json`).

**Rebuild:** `python 01_data/91_build/build_vpacc_fy2027_action_plan.py`

**Join fields for later work:** `pic` (owner), `progress_status` / `progress_filled`, `stream` (`VP`|`ACC`), `objective`, `action_point`, `deadline` (ACC).

**Memory:** `05_memory/projects/action-plan-fy2027.md`
