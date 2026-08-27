# HTML dashboards — roadmap & inventory

**Last updated:** 2026-08-26
**Hub:** [`ISZE_ROADMAP.md`](../ISZE_ROADMAP.md) · **Routing:** `00_docs/ROUTING.yaml` → `edit_html_dashboard`
**Mode:** everything here is **Mode A** (outside-facing language rules apply) unless the row says Mode B / internal.

---

## Canonical workflow

`02_dashboards/` is the **single source of truth** for HTML. `07_deploy/` is generated — never edit it.

1. Edit `*.html` in the themed subfolder (`hub/`, `sales/`, `fleet/`, `ops/`, `pricing/`, `bi/`, `ids/`).
2. Rebuild if the page has a builder (`02_dashboards/_build/`, `01_data/91_build/`).
3. Run `02_dashboards/_build/ship_gate_check.ps1` — must print `SHIP_GATE_OK`. Exit 0 is not done; paint evidence is required (`.cursor/rules/isze-verify-rendered-output.mdc`).
4. Run `02_dashboards/sync_to_deploys.ps1` → `07_deploy/Master Dashboard/`, `publish-site/`.
5. Publish the deploy repos (GitHub Pages / Netlify) — **ask Jerome first**.

JSON feeds come from `01_data/14_dashboards/*.json` (alias `01_data/dashboards/`) only — never from `02_dashboards/*.json`.

**Deploy-side compatibility:** published HTML loads JSON via `fetch('../Data/dashboards/...')`. That is the intentional GitHub Pages layout — do not rewrite local source paths to match deploy URLs.

---

## Inventory

### Hub

| Dashboard | File | State |
|---|---|---|
| Master Dashboard | `hub/MASTER_DASHBOARD.html` | Active — top-level KPI hub |
| Project hub / index | `hub/PROJECT_HUB.html` · `hub/index.html` | Active — single home, no dead links (2026-08) |
| BI packs index | `hub/BI_PACKS.html` | Active — entry to `bi/` twins |
| AI Operations Explorer | `hub/AI_Operations_Explorer.html` | Reference |

### Sales

| Dashboard | File | State |
|---|---|---|
| **Aftermarket BI Command Center** | `sales/ISZE_Aftermarket_BI_Command_Center.html` | Active — SSR build-time (0.41 MB), 2026-08-19 |
| DB→DLR replenishment CY2025 | `sales/ISZE_DB_DLR_Replenishment_CY2025.html` | Active — multi-DB, 2026-08-19 |
| AIM Dashboard CY2026 | `sales/AIM_Dashboard_CY2026.html` | Active — billing-only, CY+FY windows |
| Risk Cockpit | `sales/ISZE_Risk_Cockpit.html` | Active · `viz/risk_cockpit.json` |
| Competitiveness | `sales/ISZE_Competitiveness_Dashboard.html` | Active — competitor **vintages unlabelled** until B10 |
| Monthly Sales Tracker | `sales/ISZE_Monthly_Sales_Tracker.html` | Active |
| Dealer sell-out (AIM/GPS · UTI vs ITUK) | `sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` · `sales/Dealer_Sellout_UTI_vs_ITUK.html` | Active — **UTI ≠ UMI · IUK ≠ ITUK · IRELAND ≠ IUK** |
| Part Groups explorer | `sales/ISZE_PartGroups_Sales_Explorer.html` | Active |
| SPA Run Rate (UTI) · UTI replenishment H2 2025 | `sales/ISZE_SPA_RunRate_UTI.html` · `sales/ISZE_UTI_Replenishment_H2_2025.html` | Active |

### Fleet

| Dashboard | File | State |
|---|---|---|
| UIO Dashboard | `fleet/ISUZU_UIO_Dashboard_2026.html` | Active — canonical name; workbook **v19** in `06_uio/_CURRENT/` |
| GPS Dashboard | `fleet/ISZE_GPS_Dashboard.html` | Active — canonical; `_v9` is a redirect only |
| Plan Tracker 2030 | `fleet/ISZE_Plan_Tracker_2030.html` | Active — Kosha long-range |
| ZEV Golden Window | `fleet/ITUK_ZEV_Golden_Window_Dashboard.html` | Active — ICE parc window 2025–2032 |
| FY2026 year-end review | `fleet/ISZE_FY2026_YearEnd_Review.html` | Active |

### Ops

| Dashboard | File | State |
|---|---|---|
| **Action Ledger** (P8) | `ops/ISZE_Action_Ledger.html` + `_Hub.html` | Active **Mode B** — mixed-basis stakes, never one wallet |
| OS data map | `ops/ISZE_OS_Data_Map.html` | Internal planning — YAML `00_docs/ISZE_OS_DATA_MAP.yaml`, rebuild `ops/build_os_data_map.py` |
| Tender Monitor | `ops/ISZE_Tender_Monitor_v2.html` | Active — feed `01_data/14_dashboards/tender_data.json` |
| Commercial model map | `ops/ISZE_Commercial_Model_Map.html` | Reference |
| Tools legal map · AI tools overview | `ops/ISZE_Tools_Legal_Map.html` · `ops/ISZE_AI_Tools_Overview.html` | Reference |

### Pricing — **Mode B / internal QA until list-to-pocket is signed** (hub §1 item 2)

| Dashboard | File | State |
|---|---|---|
| Pricing full analysis pack | `pricing/ISZE_Pricing_Full_Analysis_Pack.html` | Internal — audit PASS_WITH_CAVEATS, integrity weak |
| Pricing history findings | `pricing/ISZE_Pricing_History_Findings_Dashboard.html` | **Provisional** — do not quote leakage € |
| IAM quality positioning (overview + ITUK / ISD / IMOTORS) | `pricing/ISZE_IAM_Quality_Positioning_*.html` | Active internal |
| Pricing action map · BI · readiness · proposal v1 · scraped intelligence · live pricing | `pricing/ISZE_Pricing_*.html` | Internal working set |

### Static PRISM twins and packs

| Pack | File |
|---|---|
| BI twins (4 self-contained snapshots) | `bi/Warranty_Intelligence.html` · `Price_Realization.html` · `Parc_Cohorts.html` · `Dealer_Sellout.html` — built by `bi/_build_bi_twins.py` |
| IDS 2026 country packs | `ids/` (24 files, v1.4 — Baumann MIDI averages rule locked) |
| GPS kickback stretch FY27 · MD capture pack · UMI SPA | `gps/` · `md_pack/` · `spa_internal/` |

Non-ISZE: `side/PROPERTIQ.html`.

---

## Open queue

| Item | State | Blocked on |
|---|---|---|
| **V4 — Supabase live Master KPIs** | Not started | Schema + credentials (hub §1 item 11) |
| **Filename renames to canonical `vN`-free names** | Blocked by design | Build scripts hardcode `vN` — plan in [`CANONICAL.md`](../CANONICAL.md) |
| **Competitor vintage labels (Mode A)** | Meta already flags vintages; the UI label is not built | Jerome (B10) — PartsPool 2026-03-29 ≠ Eucon UK 2023 |
| Hygiene | Archive stale UIO v11; monthly sales update protocol | nothing |

**V3 is done:** Golden Window overlay, Competitiveness Class C, Master ↔ PRISM links, single-home navigation rewrite.

Full programme queue: [`ISZE_ROADMAP.md`](../ISZE_ROADMAP.md). GPS specifics: [`gps.md`](gps.md).
