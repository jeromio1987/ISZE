# Baseline checks (C06)

inspected_at: 2026-09-21T06:43:45Z

| Check | Command / method | Result | Notes |
|---|---|---|---|
| Pipeline verification report on disk | Read `01_data/00_derived/_verification_report.json` | historical_pass_reported | summary pass=153 warn=2 fail=0 ok=True; generated_at=2026-09-20T22:31:53Z. **Not re-run** in R0 (would write/refresh derived state). |
| Re-run `run_pipeline_and_verify.ps1` | not executed | not_run | Would mutate/refresh derived outputs; outside R0 write boundary. |
| Universe app unit/UI tests | n/a | not_run | No UNIVERSE application root found. |
| Open network atlas in browser | not executed | not_run | Avoided user-facing launch; file presence only. |
| Tonnage correction evidence doc | Read `03_EVIDENCE_OF_CORRECTION.md` | inspected | Contains blocked tests; do not claim all eight minimum tests passed. |
| ITUK pack internal consistency | not executed beyond docs+aggregates | not_run | Full CY2025 reconcile not run in R0. |
| VALIDATE_RETURN.py on this package | run after package write | see C07 | Structural only. |

Business invariants **not** covered by the historical verification summary alone: ITUK name↔IDS join, DLOD case outcomes, Kaizen register completeness, Universe access control.
