# HTML dashboards — roadmap & inventory

**Last updated:** 2026-06-13  
**Hub:** [`ISZE_ROADMAP.md`](../../ISZE_ROADMAP.md) · **Routing:** `00_docs/ROUTING.yaml` → `edit_html_dashboard`

---

## Current inventory

| Dashboard | File | Purpose | State |
|---|---|---|---|
| Master Dashboard | `hub/MASTER_DASHBOARD.html` | Top-level ISZE KPI hub | Active |
| AIM Dashboard | `sales/AIM_Dashboard_CY2025.html` | AIM classification CY2025 | Active |
| UIO Dashboard | `_archive/ISUZU_UIO_Dashboard_2026_v17.html` | Vehicle-in-operation tracking | Archived (v17) — confirm replacement |
| Competitiveness Dashboard | `sales/ISZE_Competitiveness_Dashboard.html` | Part price vs market | Active |
| Monthly Sales Tracker | `sales/ISZE_Monthly_Sales_Tracker.html` | YTD revenue vs budget | Active |
| Plan Tracker 2030 | `fleet/ISZE_Plan_Tracker_2030.html` | Kosha / long-range plan | Active |
| SPA Run Rate (UTI) | `sales/ISZE_SPA_RunRate_UTI.html` | SPA run-rate UTI | Active |
| Tender Monitor | `ops/ISZE_Tender_Monitor_v2.html` | Tender alerts | Active |
| ZEV Golden Window | `fleet/ITUK_ZEV_Golden_Window_Dashboard.html` | ICE parc window 2025–2032 | Active |
| Tools Legal Map | `ops/ISZE_Tools_Legal_Map.html` | Tool/data legal compliance | Reference |
| AI Tools Overview | `ops/ISZE_AI_Tools_Overview.html` | AI tool landscape | Reference |

Paths relative to `02_dashboards/`. GPS specs: [`gps.md`](gps.md)

---

## Canonical workflow

`02_dashboards/` is the **single source of truth** for HTML.

1. Edit `*.html` here (themed subfolders: `hub/`, `sales/`, `fleet/`, `ops/`).
2. Run `sync_to_deploys.ps1` → `07_deploy/Master Dashboard/`, `publish-site/`.
3. Publish deploy repos (GitHub Pages / Netlify).

JSON feeds: `01_data/dashboards/*.json` only (not `02_dashboards/*.json`).

**Deploy-side compatibility:** Published HTML loads JSON via `fetch('../Data/dashboards/...')` — intentional GitHub Pages layout. Do not change local source paths to match deploy URLs.

---

## HTML roadmap (V3 / V4)

- **Hygiene:** archive stale UIO v11; monthly sales update protocol
- **V3:** Golden Window overlay, Competitiveness Class C (Autodoc inject), Master ↔ PRISM links
- **V4:** Supabase KPIs, Jarvis widget

Full PRISM + pipeline queue: [`ISZE_ROADMAP.md`](../../ISZE_ROADMAP.md).
