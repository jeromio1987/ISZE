---
topic: pms-coverage
read_when: [pms, ituk, pilot, capture, iml]
canonical_metrics: FACTS.md, metric_dictionary.md §PMS, pms_capture_by_db_year.csv
last_validated: 2026-06-13
---

# Project: PMS Coverage

> **PRISM authority:** `pms_capture_by_db_year.csv` after green verify. Expected demand = UIO × **0.5** svc/yr (N75) × **70%** addressable. **Do not** use 1.5× svc/yr or single-PN dealer math vs PRISM.

## Status

Active — ITUK pilot with ISZJ (IML). Targets: Filters +1% retention, Clutch/Brake +3% retention.

## Decisions / clarifications

- **Legacy oil-filter rates (~61% / ~81% or ~10% / ~17%)** — wrong denominators; PRISM + `FACTS.md` win.
- **Cust 2574 = IUK, Cust 2575 = ITUK** — do not conflate in dealer pivots.
- **ITUK UIO:** **22,389** (DVLA Mar 2026) for capture denominator — not Hasegawa-only parc.
- **Cover ratios** (mapped fleet 12,010 vs DVLA 22,389) — different purpose than PRISM capture; state denominator when citing.

## Open questions

- EQ-HIT mapping for PN → service schedule (ITUK validation pending).
- CY2025 full PMS basket gap revalidation pending.

## Pointers (detail lives here — do not duplicate in chat)

| What | Path |
|------|------|
| Capture formulas | `Projects/Isuzu/prism/docs/metric_dictionary.md` |
| Headline capture figures | `FACTS.md`, `metrics_snapshot.json` |
| Calculator / deck | `Isuzu/Divers/ISZE_PMS_Coverage_Calculator.xlsx`, `PMS sales promotion ISZE_ISZJ.pptx` |
| Cover ratio workbook | `Projects/Isuzu/pms-pilot/PMS Parts sales ITUK WS2025(update 260323).xlsx` |
| Competitiveness case | `Dashboards/ISZE_Competitiveness_Dashboard.html` |
| Programme memory | `memory/projects/competitiveness.md` |

## Connections

→ `memory/projects/action-plan-fy2026.md` (PMS campaign workstream)  
→ `memory/projects/uio.md` (ITUK parc methodology)
