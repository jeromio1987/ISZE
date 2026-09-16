# Phase 1 — FR + PL merge into main tender feed

**Date:** 2026-08-25  
**Workspace:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Constraint:** Same Isuzu gate + product-fit + Hebrew noise patterns. Null ≠ 0. No invented SPU. IDS dealer MAP preserved.

---

## Pipeline

1. Focused scrape (already done): `python tender_scraper_v3.py --only fr,pl` → `isuzu_tenders_v3_fr_pl.xlsx`  
   Pre-gate fetch: **FR 52** · **PL 38**. Side xlsx post-`normalize_batch` gate: **FR 20** · **PL 23**.
2. Merge: `merge_fr_pl_into_main.py` — re-gate + dedupe by URL / Source Notice ID vs other main sheets; create `France BOAMP` / `Poland BZP` sheets on main.
3. Publish: `publish_live_tender_json.ps1` → live `tender_data.json`
4. Rebuild: `build_dashboard_v4.py --json-input …\tender_data.json` (IDS + product-fit + market chips intact)

---

## Counts (measured 2026-08-25)

| Metric | Before merge | After FR/PL merge |
|---|---:|---:|
| Side FR (post-gate rows) | 20 | — |
| Side PL (post-gate rows) | 23 | — |
| Merge gate drop (re-check) | — | **0** FR · **0** PL |
| Cross-sheet / internal dupes | — | **0** / FR dup 0 · PL 0 |
| Main notices | 211 | **254** (+43) |
| Main opportunities (v4) | 186 | **228** (+42; 1 family collapsed at v4 gate) |
| GPS-sized opportunities | 3 | **3** (unchanged) |
| GPS addressable floor (€/yr) | **1,488.22** | **1,488.22** (honest — FR/PL still no SPU) |
| With fleet count | 13 | **15** |
| Addressable vehicles (pickup/truck fleet sum) | (sibling KPI) | **18** (8 rows) |
| Stated fleet all segments | (sibling KPI) | **156** (15 rows) |
| IDS dealers in rankings | 519 | **519** |
| Opps with IDS dealer name | 113 | **155** |

FR/PL national GPS € = **null** (yaml / pack still no France or Poland SPU). Product-fit still blocks van GPS. Hebrew-irrelevant noise patterns unchanged (Latin FR/PL).

---

## Weekly bat

`run_tender_monitor.bat` runs full `tender_scraper_v3.py` (no `--only`).  
Scraper now includes **FR BOAMP + PL BZP on `run_all`** (same public fetchers as `--only fr,pl`). Bat comment updated. Nordics keys still empty / AWAITING_KEY — untouched.

---

## Deliverables

- Main xlsx: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3.xlsx`
- Side scrape: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3_fr_pl.xlsx`
- Merge helper: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\merge_fr_pl_into_main.py`
- Merge stats: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_phase1_fr_pl_merge_stats.json`
- Live JSON: `C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json`
- v4 HTML: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isze_dashboard_v4_opportunity.html`
- Open: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\OPEN_isze_dashboard_v4_opportunity.cmd`
