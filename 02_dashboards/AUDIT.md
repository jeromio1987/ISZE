# ISZE dashboards — consolidation audit

**As-of:** 2026-08-20 · **Authoritative inventory:** [`manifest.yaml`](manifest.yaml) (regenerated 2026-08-13, slightly stale) · **Roadmap:** [`00_docs/roadmaps/html.md`](../00_docs/roadmaps/html.md)

**Goal:** collapse ~90 deployed HTML files into a smaller, audience-aware set. PRISM (Streamlit :8503) stays the canonical live spine; HTML stays the static/deck layer.

**Decision taken (plan open item):** retire by **archive-and-keep** — stale files move into `_archive/` (deploy-skip), never hard-deleted. Reversible.

## Classification legend

- **KEEP** — canonical, active, keep in deploy.
- **MERGE** — content folded into a canonical twin; retire once superseded.
- **RETIRE** — stale / superseded / stub; moved to `_archive/`.

## The three packs (audience mapping)

| Pack | Audience | Language |
|------|----------|----------|
| **Internal** | ISZE ops + Jerome | Full pipeline detail, leakage/attach/elasticity only in PRISM internal mode |
| **Distributor (shared)** | DB-facing | Plain language, no pipeline jargon, no leakage |
| **Management** | MD pack / evaluaties / year-end | Deck-style summaries |

---

## Inventory & classification

### hub — entry points

| File | Class | Note |
|------|-------|------|
| `MASTER_DASHBOARD.html` | KEEP | Top-level KPI hub — becomes the single entry point |
| `AI_Operations_Explorer.html` | KEEP | AI ops reference |
| `index.html` | KEEP | Local index |
| `PROJECT_HUB.html` | MERGE | Fold into MASTER_DASHBOARD; retire after |

### fleet — parc & plan

| File | Class | Note |
|------|-------|------|
| `ISUZU_UIO_Dashboard_2026.html` | KEEP | Canonical (v19) |
| `ISUZU_UIO_Dashboard_2026_v18.html` | RETIRE | Superseded by v19 |
| `ISZE_FY2026_YearEnd_Review.html` | KEEP | Management pack |
| `ISZE_GPS_Dashboard.html` | KEEP | Canonical GPS |
| `ISZE_GPS_Dashboard_v9.html` | RETIRE | Redirect stub |
| `ISZE_Plan_Tracker_2030.html` | KEEP | |
| `ITUK_ZEV_Golden_Window_Dashboard.html` | KEEP | |

### gps — proposals

| File | Class | Note |
|------|-------|------|
| `ISZE_GPS_Kickback_Stretch_Proposal_FY27.html` | KEEP | |
| `ISZE_GPS_Network_SPU_Dashboard.html` | RETIRE | Stub (manifest) |
| `ISZE_GPS_TargetStudy_Reconciliation_Dashboard.html` | RETIRE | Stub (manifest) |

### ids — dealer evaluation

| File | Class | Note |
|------|-------|------|
| `IDS_2026_dealer_compare.html` + 20 country compares | KEEP | One pack, keep together |
| `IDS_2026_Explainer.html` | KEEP | |
| `IDS_2026_Country_Action_UX_proposal.html` | KEEP | |
| `IDS_2026_Kaizen_Belgium.html` | KEEP | |
| `IDS_2026_Portugal_dealer_map.html` | KEEP | |

### md_pack — management

| File | Class | Note |
|------|-------|------|
| `ISZE_MD_Pack_Capture_FY27_FY28.html` | KEEP | Management pack |

### ops — reference & tenders

| File | Class | Note |
|------|-------|------|
| `ISZE_AI_Tools_Overview.html` | KEEP | |
| `ISZE_Commercial_Model_Map.html` | KEEP | |
| `ISZE_OS_Data_Map.html` | KEEP | |
| `ISZE_Tender_Monitor_v2.html` | KEEP | |
| `ISZE_Tools_Legal_Map.html` | KEEP | |

### pricing — internal

| File | Class | Note |
|------|-------|------|
| `ISZE_Aftermarket_Live_Pricing_Dashboard.html` | KEEP | |
| `ISZE_Pricing_BI_Dashboard.html` | KEEP | |
| `ISZE_Pricing_Action_Map.html` | KEEP | |
| `ISZE_Pricing_Engine_Readiness_Dashboard.html` | KEEP | |
| `ISZE_Pricing_Full_Analysis_Pack.html` | KEEP | |
| `ISZE_Pricing_History_Findings_Dashboard.html` | KEEP | |
| `ISZE_Scraped_Price_Intelligence_Dashboard.html` | KEEP | |
| `ISZE_IAM_Quality_Positioning_Overview.html` | KEEP | |
| `ISZE_IAM_Quality_Positioning_Engine*.html` (4) | KEEP | Per-DB engine twins |
| `ISZE_Pricing_Proposal_v1.html` | MERGE | Superseded by Action Map / Full Analysis |

### sales — billing & capture

| File | Class | Note |
|------|-------|------|
| `AIM_Dashboard_CY2026.html` | KEEP | |
| `AIM_Dashboard_CY2025.html` | RETIRE | Superseded by CY2026 |
| `ISZE_Competitiveness_Dashboard.html` | KEEP | |
| `ISZE_Monthly_Sales_Tracker.html` | KEEP | |
| `ISZE_PartGroups_Sales_Explorer.html` | KEEP | |
| `ISZE_PartGroups_Sales_Explorer_OFFLINE.html` | RETIRE | Offline variant |
| `ISZE_Risk_Cockpit.html` | KEEP | |
| `ISZE_SPA_RunRate_UTI.html` | KEEP | |
| `ISZE_UTI_Replenishment_H2_2025.html` | KEEP | |
| `ISZE_DB_DLR_Replenishment_CY2025.html` | KEEP | |
| `ISZE_Aftermarket_BI_Command_Center.html` | KEEP | |
| `Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` | KEEP | Superseded live by PRISM `Dealer Sell-out` page; keep as HTML twin |
| `Dealer_Sellout_UTI_vs_ITUK.html` | MERGE | Folded into the AIM_GPS_ITUK_UTI twin |

### spa_internal / side / snapshots

| File | Class | Note |
|------|-------|------|
| `spa_internal/UMI_SPA_Proposed_Prices.html` | KEEP | Internal |
| `side/PROPERTIQ.html` | KEEP | Non-ISZE |
| `since_2026-06-01/` (4 files) | RETIRE | Snapshot folder duplicating live files |

### already archived

| File | Class | Note |
|------|-------|------|
| `_archive/*` (4 GPS files) | KEEP | Deploy-skip, retained by design |

---

## New BI surfaces (PRISM pages, this work)

| Page | Data | Audience |
|------|------|----------|
| `20_Warranty.py` | `distributor_warranty_expense_fiscal.csv` | Internal |
| `21_Realization.py` | `pr00_realization_*_cy.csv`, `zpr1_vs_pr00_by_payer_year.csv` | Internal |
| `22_Parc_Cohort.py` | `01_data/07_UIO/vin/VIN_register.csv` | Internal / Fleet |
| `23_Dealer_Sellout.py` | `sellout_aim_network_mix_2025.csv`, `sellout_aim_by_subgroup_2025.csv` | Internal / Distributor |

## Open follow-ups

- Regenerate `manifest.yaml` (it is disk-derived and now missing 08-19 files).
- Fold `PROJECT_HUB` into `MASTER_DASHBOARD` (single entry point) — needs a link audit first.
- Static HTML twins for the four new PRISM pages, once numbers are stable.
