# Dashboard UX — readable without horizontal scroll

**Rule:** default tables show **≤7 columns** and **≤15–18 rows**. Charts carry the pattern; tables carry the drill-down. Full raw exports stay in Excel/CSV sources.

## Four surfaces

| # | Surface | Launch | Audience |
|---|---------|--------|----------|
| 1 | **PMS Intelligence** (Streamlit) | `_HANDOFF_BUNDLE\run_bi.bat` | **Start on `PMS results` tab** — not raw Excel grids |
| 2 | **IAM Lookup Lab** (Streamlit) | `run_dashboard.bat` | Scraped AM threat on ~300 PNs only |
| 3 | **Executive HTML — PMS** | `build_executive_dashboard.py --variant pms` | Static share-out, PMS + multi-DB |
| 4 | **Executive HTML — IAM** | same, `--variant iam` | Static share-out, substitution model |

## What belongs on screen vs in expanders

### Tab order (PMS app)

1. **PMS results** — default; KPIs, Plotly charts, PRISM, model mix  
2. **Competitor prices** — optional scraper layer  
3. **Data lineage** — source health + parsed workbook insights (not Cover-sheet dumps)

### PMS app (`bi_shell.py` → PMS results)

| View | On screen (default) | Expander / filter |
|------|---------------------|-------------------|
| Category lost GP | Bar chart + **6-col** category table | — |
| Top PNs | **6-col** table (PN, desc, category, actual, lost GP, AM min) | Search + category filter; cap 100 rows |
| PRISM distributors | KPIs + bar + **top 18** ranked (6–7 cols) | Per-distributor category breakdown |
| Model mix | Bar top 12 + **8-col** model summary | Model × category detail |
| Source files | **6-col** sheet preview | Full sheet only if needed |

**Do not** put on default table: every month column, all site price columns, `expected_qty` alongside engine potential, raw dicts from engine.

### IAM app (`autodoc_dashboard.py`)

| Tab | On screen | Expander |
|-----|-----------|----------|
| PMS Lost Sales | Chart + **6-col** category + **7-col** top PNs | “Top PMS PNs (detail)” |
| Brand League | Chart + **6-col** brand table | — |
| Category heatmap | **Plotly heatmap** (not wide pivot table) | **4-col** top categories |
| PN Deep Dive | **Metrics + cards** per selected PN | Price stack (4 cols) |
| Data quality | **5-col** source status | Long disclosure text |
| Methodology | Narrative | CSV lookup tables |

### HTML exports

Same slim formatters as Streamlit (`bi_display` / `iam_display`). Tables capped at **12–15 rows**, **7 columns**, ellipsis CSS for overflow.

## Column cheat sheet (keep these)

**PMS category row:** Category · Lost GP (€) · Capture % · Actual · Potential · PNs  

**PMS PN row:** PN · Description · Category · Lost GP (€) · Capture % · AM (€)  

**PRISM distributor:** Distributor · Expected · Actual · Capture % · Lost GP (€) · UIO  

**IAM brand:** Brand · Tier · PNs · Expected loss (€) · Rev exposed (€)  

**IAM PN:** PN · Description · Quadrant · Threat brand · Expected loss (€) · Action · AM price (€)  

## What we removed from default tables

- Duplicate € columns (lost revenue + lost GP on same row)
- All scraper site columns (AD_UK, MEK, KS, …) — use PN Deep Dive for one PN
- AIM + Class + 10 scoring fields on one grid
- Full distributor list (100+ rows) without chart
- Methodology CSVs inline (moved to expanders in IAM app)

## If something still scrolls

1. Narrow browser zoom or widen window — Streamlit still needs ~1100px for 7 columns.
2. Use the **chart** on that tab first; open **expander** only for export-style detail.
3. For PRISM, compare **top 18** distributors; do not merge with ITUK engine totals on one table.

## Rebuild static HTML after code changes

```bat
cd C:\Users\jerom\Desktop\claude\ISZE\04_tools\autodoc_scraper
python build_executive_dashboard.py --variant all
```

Open `_html_previews\isze_executive_pms.html` and `isze_executive_iam.html`.
