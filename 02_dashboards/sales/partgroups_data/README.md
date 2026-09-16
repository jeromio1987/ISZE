# Part-Groups explorer data

Canonical JSON also lives in `01_data/14_dashboards/partgroups_explorer/`.
This folder is the sibling copy fetched by `ISZE_PartGroups_Sales_Explorer.html`.

## Size budget

| File | Role |
|------|------|
| `partgroups_agg.json` | Sales aggregates (~3.7 MB) — first paint |
| `partgroups_pnyear.json` | PN movers / drill (~12 MB) — lazy |
| `partgroups_competitive.json` | Eucon panel (~140 KB) |
| `partgroups_meta.json` | Stamps |
| `partgroups_gps_pms.json` | Network GPS + PMS total |
| `partgroups_scrape.json` | Live shop scrape summary |

HTML shell must stay under ~500 KB (Plotly via local `_ui/plotly.min.js` copy of `02_dashboards/_ui/plotly.min.js`).

## Open

**Always** double-click `OPEN_PartGroups_Explorer.cmd` (starts HTTP on 8766 and opens the page).
Do **not** open `ISZE_PartGroups_Sales_Explorer.html` via Explorer double-click — multi-MB JSON needs HTTP.

Aftermarket Live Pricing (`02_dashboards/pricing/ISZE_Aftermarket_Live_Pricing_Dashboard.html`) is **self-contained** (scrape JSON embedded) — double-click OK.

## Rebuild

```powershell
python 02_dashboards/sales/_build/build_partgroups_sales_explorer.py
```
