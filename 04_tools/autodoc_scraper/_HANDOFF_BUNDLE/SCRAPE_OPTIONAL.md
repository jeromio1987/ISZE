# Scraper data (optional)

The BI **does not depend** on live scraping. PMS lost sales and multi-DB capture use **v3, PMS Calc, PRISM, and dealer sales** — not Autodoc/KS/Mekonomen CSVs.

Scraper CSVs only feed:

- **Brand league** / competitor price columns when present  
- IAM views in parent folder / `isze_executive_iam.html`

If you already have `autodoc_results.csv` (etc.) in the bundle, the app uses them. **No need to re-run scrapers** for PMS work.

## If you ever refresh (manual, rare)

1. Run scrapers from parent `autodoc_scraper/` when you choose.  
2. Optionally copy CSVs: `sync_scrape_results.bat`  
3. Restart Streamlit.

No Task Scheduler or monthly cadence is required for this audit closure.

**Update 2026-07-10:** a weekly Windows Task Scheduler job (`ISZE_PMS_IAM_Refresh`, Mondays 07:00)
was added at Jerome's request — parent `run_refresh_scheduled.bat` → `refresh_and_check_drift.py`.
It re-runs the 5 working scrapers, snapshots + diffs prices, appends to
`_snapshots/drift_history.csv`, and rebuilds the executive/bridge/trend HTML. This is still
optional context only — it does not feed PMS actuals or change anything in this bundle.
