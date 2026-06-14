# ISZE — Consolidated roadmap

**Last updated:** 2026-06-13  
**Domain detail:** [`roadmaps/`](roadmaps/) · **Registry:** [`MAP_REGISTRY.yaml`](MAP_REGISTRY.yaml)

> **Numbers:** `../FACTS.md` wins over any deck, memory, or GPT file. Pipeline: green `01_data/derived/_verification_report.json` → `metrics_snapshot.json`.

---

## Live now (PRISM + derived pipeline)

| Capability | Location |
|------------|----------|
| GPS spend per unit | PRISM `pages/2_GPS.py` · `gps_spu_by_distributor.csv` |
| PMS capture (registry + BVP catalogue) | `pages/3_PMS.py` · `pms_capture_by_db_year.csv` |
| Fig-key / PR00 catalogue | `parts_catalog_dimension.csv` · `gps_v2_fig_key.md` |
| AIM × GPS quadrant | `pages/16_AIM_GPS_Matrix.py` · `aim_gps_matrix.csv` |
| Decision models | `pages/18_Decision_Models.py` · `wallet_waterfall.csv`, etc. |
| Pipeline verify | `scripts/run_pipeline_and_verify.ps1` |
| PMS assumptions (editable) | `prism/data/pms_capture_assumptions.yaml` |
| Static HTML refresh | `build_isze_dashboard_json.py` + `inject_dashboard_overlays.py` |
| Data integrity audit | `pages/10_Data_Integrity.py` · `mislabelled_sku_audit.csv` |

Run PRISM: `03_analytics/Isuzu/prism/run_prism.ps1` (port **8503**)

---

## Build now

| Item | Blocker | Domain |
|------|---------|--------|
| Interval-aware air vs oil capture | Maintenance schedule ratio from IML | PRISM |
| SAP fig key on `sales_fact` | CY export column | Pipeline |
| 2025 UIO in capture | V17 / DVLA 2025 file | UIO |
| CY2026 AIM dashboard | AIM workbook | HTML |
| Supabase live Master KPIs | Schema + credentials | HTML V4 |
| Discount scraper refresh | Manual run overdue | [scrapers](roadmaps/scrapers.md) |
| Dashboard filename renames | Build scripts hardcode vN | [html](roadmaps/html.md) · [`CANONICAL.md`](CANONICAL.md) |

---

## Domain roadmaps

| Domain | File | Status |
|--------|------|--------|
| HTML dashboards | [`roadmaps/html.md`](roadmaps/html.md) | V3 overlay + V4 Supabase |
| Scrapers | [`roadmaps/scrapers.md`](roadmaps/scrapers.md) | Discount stale; tender V2 scoring |
| GPS / fig-key / AIM | [`roadmaps/gps.md`](roadmaps/gps.md) | V2 enrichment in PRISM |
| Jarvis / tools | [`roadmaps/tools.md`](roadmaps/tools.md) | V2 data-out-of-code |

---

## Data integrity (do not quote externally until closed)

See `03_analytics/Isuzu/prism/docs/DATA_INTEGRITY_FLAGS_2026-05-28.md` — priority: interval-aware PMS (C), returns confirmation (H).

---

## Workspace cleanup

Open decisions (UI primary for external share, ISZE_Dashboard merge): [`ISZE_Cleanup_Plan.md`](ISZE_Cleanup_Plan.md)
