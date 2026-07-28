# ISZE AIM CLASSIFICATION REFRESH — 2026-07-26

Report-only check per `isze-aim-classification-refresh` (AUTOMATION_REGISTER).
No classification was auto-applied.

## CLASSIFICATION STATUS (from memory)

Last confirmed rate: ~98% of revenue classified (2026-07-02 fix); residual unclassified **1.6% CY2024 / 1.8% CY2025**
Older figures still in memory (93.5% count CY2024 / ~87% rev CY2025 workbook) are superseded for residual-gap talk — use the 2026-07-02 gap report.
Target: 100%
Gap: ~1.6–1.8% revenue (~EUR1.12M over 2024+2025, 635 PNs — not auto-applied)

## LATEST WORKING FILE

- `01_data/00_derived/aim_pn_classification.csv` — last modified **2026-07-26 12:21** (already rebuilt today before this session)
- Gap report: `03_analytics/Isuzu/prism/docs/aim_classification_gap_report.md` — **2026-07-02**
- Workbook: `01_data/01_Pricing/ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx` — **2026-04-29** (stale vs derived CSV)

## NEW SALES DATA DETECTED THIS MONTH

- `01_data/00_derived/sales_fact.parquet` and related PRISM sales exports refreshed within the last 35 days
- Price revision workbook in `01_data/` (CY2026 price revision)
- No new full CY2026/CY2027 SAP master export that would force a classification rebuild beyond today's already-fresh `aim_pn_classification.csv`

## OUTSTANDING GAPS (from memory + gap report)

1. Honest residual EUR1.12M / 635 PNs (wiper blades, stereo, transfer asm, power chambers, …) — proposals in gap report, NOT auto-applied
2. Register open item: post-reorg paths for `ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx` still flagged by live-state audit
3. VKWRT / older 100%-target notes in skill text are historical; current blocker is the residual PN list, not missing CY2024 ingest

## ACTIONS THIS MONTH

1. Optional: Jerome reviews top residual PNs in `aim_classification_gap_report.md` if classification must move past ~98%
2. Rebuilt tonight: `python scripts/build_aim_pn_classification.py` -> 164,667 PNs (aim_l1 94.8% / catalog_l1 100%; sources pr00_catalog 139,410 / aim_workbook 16,499 / gap_suggestion 196)
3. Mekonomen IAM scrape failed this evening (Playwright browser missing under Cursor temp) — IAM price coverage for Mekonomen stays on 2026-07-16 backup until `playwright install` / browser path is fixed

## PATH PREFLIGHT

- OK `05_memory/projects/aftermarket-intelligence.md`
- OK `01_data/`
- OK `03_analytics/Isuzu/data/`
