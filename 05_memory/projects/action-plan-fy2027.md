# FY2027 VPACC Action Plan — pointer (internal)

**Status:** Active · July 2026 update on git.

## Canonical files

| Kind | Path | Verified 2026-09-16 |
|------|------|---------------------|
| ★ Workbook (July) | `01_data/11_planning/Action plan FY2027 VPACC_July update.xlsx` | exists |
| August update | `01_data/11_planning/Action plan FY2027 VPACC_August update.xlsx` | exists, **not yet derived** — see gaps below |
| Prior | `01_data/11_planning/Action plan FY2027 VPACC_April update.xlsx` | exists |
| Main actions | `01_data/00_derived/vpacc_fy2027_action_plan_july.parquet` | exists, 121 rows (July edition) |
| Meta | `02_dashboards/Data/00_derived/vpacc_fy2027_action_plan_july.meta.json` | **not in `01_data`** — see gaps below |
| Builder | `02_dashboards/Data/91_build/build_vpacc_fy2027_action_plan.py` | **not in `01_data`** — see gaps below |
| August top-up | `01_data/91_build/_fill_vpacc_action_plan_august.py` | exists (canonical tree) |

## Known gaps (recorded 2026-09-16, not fixed)

- The metadata file and the main builder live in a **second tree** under `02_dashboards/Data/`, while their outputs land in the canonical `01_data/` tree. `01_data/91_build/` does not contain `build_vpacc_fy2027_action_plan.py`. Treat the `02_dashboards/Data/` copies as the working location until they are moved.
- The **August** workbook is on disk but has not been rebuilt into `01_data/00_derived/`. Everything that quotes a status from the derived parquet is therefore quoting the **July** edition. `_fill_vpacc_action_plan_august.py` exists in the canonical tree but was not run in this pass.
- `01_data/11_planning/README.md` (previously named here as a folder map) **does not exist**. The folder contains the workbooks and the `_build/` subfolder.
- There is **no recorded approval step** anywhere for marking a plan action complete. Do not invent one; see `00_docs/FY2027_ACTION_CREDIT_MAP.md` §3.

Field guide, mapping of delivered work to plan actions, and the closure routine: `00_docs/FY2027_ACTION_CREDIT_MAP.md`.

## Streams & join fields

- **VP** / **ACC** in `stream`
- Owner: `pic` (initials, e.g. JVDP, KM, DW)
- Status: `progress_status` (`plan_made` → `completed_and_eval`) + `progress_filled` (0–4)
- ACC also has `deadline`
- Not dealer-keyed — later IDS/sales/pricing joins are by theme/`pic`/stream, not dealer code

## Adjacent live items (not canon)

- **ITUK brake SPA** — customer proposal received 15 Sep 2026 from Duncan Young; being converted to the official SPA request format. Situation note + mode-B review: `01_data/90_INBOX/_ituk_brake_spa_20260915/`. Owner: JVDP.
