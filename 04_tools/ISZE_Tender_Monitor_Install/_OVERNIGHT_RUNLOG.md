# Overnight runlog — coverage track (12h deep capture)

**Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Started:** 2026-08-25 ~19:10 Europe/Berlin  
**Last update:** 2026-08-25 ~20:20  
**Presentation agent:** read this file for live counts; do not invent notices.

**Standing rules:** Null ≠ 0. No fake notices. Preserve criticality hero (“stated fleet in captured notices”). Preserve **not-for-us** hard-drop (`_NOT_FOR_US_GATE.md`). **Nordics DONE — do not open Doffin/HILMA browsers or re-ask keys.**

---

## Live snapshot (latest v4)

| Metric | Value |
|---|---:|
| Notices | **326** |
| Opportunities | **291** |
| Stated fleet pickup/truck | **174** (extract-subset — not market potential) |
| Stated fleet all segments | **196** |
| Aftersales tagged | **54** |
| `lcv_van` on desk | **3** (parts-only survivors) |
| CV opps (pickup+truck) | **215** |
| GPS €/yr sized | **~€37.2k** (10 rows) |
| Product segments | pickup=82 · truck=133 · weak=63 · rm_only=10 · lcv_van=3 |
| National LIVE footprint | **16/29 ≈ 55%** |
| CODE_READY | ES WAF · LT CVP apiKey |
| Workbook sheets | **20** |

Open: `OPEN_isze_dashboard_v4_opportunity.cmd`

---

## Source health (key rows)

| Source | Status | last_count | Gated merged |
|---|---|---:|---:|
| Norway Doffin | **OK LIVE** | 37 | **11** |
| Finland HILMA | **OK LIVE** | 54 | **1** |
| Denmark udbud.dk | **OK LIVE** | 6 | **4** |
| Portugal BASE | **OK LIVE** | 77 | **15** |
| Bulgaria CAIS EOP | **OK LIVE** | 159 | **5** |
| Czechia VVZ | **OK LIVE** | 80 | **7** |
| Germany oeffentlichevergabe | OK | 545 | 41 |
| Romania SEAP | OK | 147 | 13 |
| Austria USP | OK | 23 | 4 |
| Spain PLACSP | CODE_READY | 0 | 0 (WAF) |
| Lithuania CVP IS | CODE_READY | 0 | needs VPT apiKey |
| HU / IE / SE / SK / EE / GR / HR / SI / LV / CY / MT | BLOCKED | — | `_overnight_dark_block_paths.json` |

---

## Done this overnight track

1. DE OV · RO SEAP · AT USP — LIVE  
2. Nordics keys — **DONE** (do not re-touch)  
3. DK udbud — LIVE (`national_fetchers_dk.py` · 6→4)  
4. PT BASE dados.gov — LIVE (77→15)  
5. HU / IE / SE — BLOCKED with unblock paths  
6. **BG CAIS EOP OCDS** — LIVE (`national_fetchers_bg.py` · 159→5)  
7. **CZ VVZ** — LIVE (`national_fetchers_cz.py` · `createdAt[gte]` + client vehicle gate · 80→7)  
8. LT — CODE_READY; remaining CEE/Baltics/Med BLOCKED  
9. not-for-us + criticality + IDS preserved on v4 rebuild  

---

## Blocked / waiting

| Item | Status | Unblock |
|---|---|---|
| ES PLACSP | CODE_READY / WAF | Spanish egress or session cookies |
| LT CVP IS | CODE_READY | Free VPT `apiKey` header |
| HU EKR | BLOCKED | Operator registration / paid feed |
| IE eTenders | BLOCKED | Stable RSS/API from OGP |
| SE commercial DBs | BLOCKED | Budget for TendSign/Mercell/… |
| SK / EE / GR / HR / SI / LV / CY / MT | BLOCKED | See `_overnight_dark_block_paths.json` |
| TED detail enrich | PARTIAL | TED API Authorization key |

---

## Next (non-Nordics)

1. ES WAF workaround (egress) when available  
2. LT VPT key (operator, not browser spam) — optional CPV/export auth for CZ uplift  
3. Stop — remaining are honestly BLOCKED  

---

## Evidence

- `_FULL_ISZE_MARKET_STATUS.md`
- `_COUNTRY_TENDER_PORTALS_MAP.md`
- `_overnight_dark_block_paths.json`
- `_phase1_cz_merge_stats.json`
- `national_fetchers_cz.py`
- `scrape_cz_side.py` / `merge_cz_into_main.py`
