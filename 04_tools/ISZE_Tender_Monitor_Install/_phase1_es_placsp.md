# Phase 1 — Spain PLACSP (+ Italy PNCP fall-through)

**Date:** 2026-08-25  
**Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Constraint:** Same Isuzu gate + product-fit. Null ≠ 0. No invented notices. Criticality labels preserved (stated fleet ≠ market potential). Nordics keys untouched.

---

## Verdict

| Portal | Result |
|---|---|
| **#1 Spain PLACSP** Atom / open-data ZIP | **WAF_BLOCKED** from this runner → health **CODE_READY** (not BROKEN) |
| **#2 Italy PNCP** pubblicitalegale JSON | **LIVE** — wired, gated, merged |

Official ES Atom URLs still documented (Hacienda / OpenPLACSP). Probe + Selenium Chrome + Referer from Hacienda all return WAF HTML deny on `contrataciondelestado.es` / `contrataciondelsectorpublico.gob.es` (Atom **and** monthly ZIP **and** `datosabiertos/*`).

---

## Pipeline

1. Focused scrape: `python tender_scraper_v3.py --only es,it` → `isuzu_tenders_v3_es_it.xlsx`
2. Merge: `merge_es_it_into_main.py` — re-gate + dedupe vs other main sheets
3. Publish: `publish_live_tender_json.ps1`
4. Rebuild: `build_dashboard_v4.py` (criticality hero / three layers / portal-map caveat / six tabs / CV / Aftersales / IDS unchanged)

---

## Counts (measured 2026-08-25)

### Spain PLACSP

| Metric | Count |
|---|---:|
| Pre-gate Atom fetch | **0** (WAF) |
| Post-`normalize_batch` / Isuzu gate | **0** |
| Merged into main | **0** |

### Italy PNCP (fall-through)

| Metric | Count |
|---|---:|
| Pre-gate vehicle-keyword matches (scanned ≈2000 of ~4164 /30d) | **32** |
| Post-`normalize_batch` gate (side xlsx) | **2** |
| Merge re-gate drop | **0** |
| Merged into main | **2** |

### Main feed (after merge)

| Metric | Before | After |
|---|---:|---:|
| Notices | 254 | **256** (+2 IT) |
| Opportunities (v4) | 228 | **230** (+2) |
| Stated fleet pickup/truck | 18 | **18** (unchanged — IT rows no extractable fleet) |
| Stated fleet all segments | 156 | **156** |
| GPS-sized €/yr | 1,488.22 | **1,488.22** |
| Aftersales tagged | — | **40** of 230 |
| IDS dealer linkage | preserved | preserved |

**Honest read:** IT notice lift is real but small after the Isuzu gate (32→2). ES remains dark nationally until WAF/session egress works. Stated-fleet hero stays **18** — coverage gap, not market size.

---

## Wiring

| Piece | Path / flag |
|---|---|
| Fetcher | `fetch_spain_placsp` · `fetch_italy_pncp` in `tender_scraper_v3.py` |
| Focused | `--only es` · `--only it` · `--only es,it` |
| Weekly bat | `run_tender_monitor.bat` full scrape includes ES+IT |
| Merge | `merge_es_it_into_main.py` |
| Health | `_source_health.json` — Spain **CODE_READY** · Italy **OK** 32 |
| Side xlsx | `isuzu_tenders_v3_es_it.xlsx` |

---

## ES endpoints tried (all WAF)

- `…/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom`
- `…/sindicacion_1044/PlataformasAgregadasSinMenores.atom`
- Matching monthly `*_YYYYMM.zip` and `datosabiertos/*`

**Unblock path:** different egress IP / Hacienda session cookie / local OpenPLACSP ZIP drop — then the same fetcher parses Atom via existing `_parse_procurement_rss` + `KEYWORDS_ES`.

## IT endpoint used

- `https://pubblicitalegale.anticorruzione.it/api/v0/avvisi` (public JSON; detail `…/avvisi/{id}`)
- Client-side Italian vehicle stems + Isuzu gate downstream
- `dati.anticorruzione.it` CKAN remains rejected — not used

---

## Criticality preserved on v4 rebuild

- Hero: **Stated fleet in captured notices (pickup/truck)** — not market potential
- Three layers: ~20k LCV / ~78k CV ≠ CV tenders ≠ 18 stated units
- Portal map + ~21% LIVE caveat
- Six tabs · CV filter · Aftersales · IDS

---

## Deliverables

- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_phase1_es_placsp.md` (this file)
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_phase1_es_it_merge_stats.json`
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3_es_it.xlsx`
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isze_dashboard_v4_opportunity.html`
- Open: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\OPEN_isze_dashboard_v4_opportunity.cmd`
