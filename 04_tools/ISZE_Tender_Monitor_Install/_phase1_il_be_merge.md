# Phase 1 — IL + BE merge into main tender feed

**Date:** 2026-08-25  
**Workspace:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Constraint:** No Fit/Win/Econ retune. Nordics keys untouched. EU Latin gate unchanged (no CPV 600… / SEND / towing / bare Dutch `van` / tyre-only reopen).

---

## Pipeline

1. Primary workbook (bat / builders): `isuzu_tenders_v3.xlsx`
2. Focused scrape: `python tender_scraper_v3.py --only bel,isr` → `isuzu_tenders_v3_bel_isr.xlsx`  
   (`normalize_batch` already applies `row_passes_isuzu_selection_gate` before write)
3. Merge: `merge_bel_isr_into_main.py` copies gated Belgium / Israel sheets into main (dedupe by URL / Source Notice ID vs other sheets)
4. Rebuild: `publish_live_tender_json.ps1` + `build_dashboard_v2.py` + `build_dashboard_v4.py`

---

## Counts (measured)

### Before Hebrew LCV signals (gate Latin-only)

| Metric | Value |
|---|---:|
| BEL raw | 14 |
| BEL after Isuzu gate | **9** |
| ISR raw (mr.gov.il) | 18 |
| ISR after Isuzu gate | **0** |
| Main notices | **202** |
| Main opportunities (v4) | **181** |
| GPS addressable floor (€/yr) | **30,410.44** |

### After Hebrew LCV + Hebrew noise (same day)

| Metric | Value |
|---|---:|
| BEL raw | 14 |
| BEL after Isuzu gate | **9** (unchanged) |
| ISR raw (mr.gov.il) | 18 |
| ISR after Isuzu gate | **9** |
| Main notices | **211** |
| Main opportunities (v4) | **186** |
| GPS-sized opportunities | 6 |
| GPS addressable floor (€/yr) | **30,410.44** (unchanged; max-wallet maths) |

Delta vs Latin-only merge: **+9 ISR notices**, opportunities **181 → 186**. GPS floor unchanged (no new GPS-sized fleets).

ISR kept: משאית R&M/purchase + רכבים מסחריים + מכליות/מרכבים. Dropped: רכב פרטי, כיבוי, צמיגים, גרירה, סטנדרטים false-positives.

Gate change: `ISUZU_LCV_SIGNAL_RE` / `ISUZU_NOISE_TITLE_RE` in `isze_core_v3.py` — Hebrew keep + passenger/taxi/bus/tow/tyre/fire noise. No bare `תחזוקה` (IT/facility). No bare Dutch `\bvan\b`.

---

## GPS check

- Formula remains `fleet × (max_spend_eur / uio_units)` via `gps_pms_linkage.py`
- Addressable GPS sum **€30,410.44** (not actual-SPU ~€5,915)
- 6/6 sized rows cite `max_spend` in `opportunity_basis`; near-€5,915 count = 0

---

## Deliverables

- Main xlsx: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3.xlsx`
- Side scrape: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3_bel_isr.xlsx`
- Live JSON: `C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json`
- v4 HTML: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isze_dashboard_v4_opportunity.html`
- Open: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\OPEN_isze_dashboard_v4_opportunity.cmd`
- Merge helper: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\merge_bel_isr_into_main.py`
