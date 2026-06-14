# Scrapers — roadmap

**Last updated:** 2026-06-13  
**Hub:** [`ISZE_ROADMAP.md`](../../ISZE_ROADMAP.md) · **Location:** `04_tools/`  
**Owner:** Claude scheduled tasks (health report runs automatically)

---

## Current state

| Scraper | Status (2026-05-10) | Output | Schedule |
|---|---|---|---|
| Tender Scraper | Healthy | `01_data/dashboards/tender_data.json` (via v3 publish) | Weekly |
| Autodoc Scraper | Healthy | `04_tools/autodoc_scraper/autodoc_results.csv` — 300 PNs | Monthly |
| KS Scraper | Healthy | `04_tools/autodoc_scraper/ks_results.csv` — 300 PNs | Weekly |
| Discount Scraper | Stale | `04_tools/discount-scanner/deals_dashboard.html` — last run 2026-04-28 | Weekly |

**Canonical versions:**

- Tender: `04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py`
- Autodoc: `04_tools/autodoc_scraper/autodoc_scraper.py`
- KS: `04_tools/autodoc_scraper/ks_scraper.py`
- Discount: `04_tools/discount-scanner/discount_scraper.py`

**Known issues (open):**

1. Doffin (Norway) API requires subscription key — no key registered yet
2. Discount Scraper stale — needs manual run: `python discount_scraper.py`
3. Lidl URL hardcodes category ID `a10051271` — verify after next discount run

---

## Immediate actions

1. **Run discount scraper manually** — promotions stale
2. **Verify Lidl output count** — update URL if 0 results
3. **Doffin key** — low priority unless tender coverage gap persists 2+ weeks

---

## V2 — Quality and coverage

### 2.1 Tender source coverage (Medium, 2–3 h)

TED EU, Doffin, HILMA return near-zero. Add Belgium/NL portals (e-Procurement.be, TenderNed).

**Done when:** At least 3 sources contributing regularly.

### 2.2 Tender relevance scoring (Medium, 3–4 h)

Score 1–5 on title, country, value. Filter score ≥ 3.

### 2.3 Autodoc + KS result quality (Low–Medium, 2 h)

Add `scrape_error` column; distinguish genuine gap vs scrape failure.

---

## V3 — Dashboard integration

- Auto-inject tender JSON into dashboard HTML (already via `01_data/dashboards/tender_data.json`)
- Competitive Pricing tab: top 50 PNs, Autodoc vs ISZE SP, Class C risk flags

---

## V4 — Monitoring

- Extend health report thresholds (`04_tools/scraper_health_report.md`)
- Push notification (ntfy.sh) on stale scrapers
- Version consolidation — one canonical path per scraper (v3 tender only)

---

*V3 dashboard integration is highest business value after hygiene items.*
