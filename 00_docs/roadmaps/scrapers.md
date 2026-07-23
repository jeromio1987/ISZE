# Scrapers — roadmap

**Last updated:** 2026-07-14  
**Hub:** [`ISZE_ROADMAP.md`](../../ISZE_ROADMAP.md) · **Location:** `04_tools/`  
**Owner:** Claude scheduled tasks (health report runs automatically)

---

## Current state

| Scraper | Status (2026-07-14) | Output | Schedule |
|---|---|---|---|
| Tender Scraper | 🔴 Dead since 2026-05-29 — **XML path fixed 2026-07-14; re-import Task Scheduler task** | `01_data/14_dashboards/tender_data.json` | Weekly Mon 07:30 |
| Competitive pricing (KS, Tranzparts, TMC, Mekonomen, Auto365) | 🟠 Stale — **scheduler XML created 2026-07-14; import task** | `04_tools/autodoc_scraper/*_results.csv` | Weekly Sun 21:00 (proposed) |
| Autodoc / Oscaro | **Retired** — Cloudflare Turnstile blocks 100% of requests | `autodoc_results.csv` (frozen) | None |
| Discount Scraper | Stale | `04_tools/discount-scanner/deals_dashboard.html` — last run 2026-04-28 | Weekly Thu 07:00 |

**Canonical versions:**

- Tender: `04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py` · Task XML: `ISZE_TenderMonitor_WeeklyTask.xml`
- Competitive pricing: `04_tools/autodoc_scraper/refresh_and_check_drift.py` · Task XML: `ISZE_ScraperRefresh_WeeklyTask.xml`
- Discount: `04_tools/discount-scanner/discount_scraper.py` · Task XML: `ISZE_DiscountScanner_WeeklyTask.xml`

**Known issues (open):**

1. Doffin (Norway) API requires subscription key — no key registered yet
2. Discount Scraper stale — needs manual run: `python discount_scraper.py`
3. Lidl URL hardcodes category ID `a10051271` — verify after next discount run
4. Israel RSS entity parse error, Belgium RSS non-XML response, UK Find a Tender 429s — see `04_tools/manual_review_required.md` Items 2–4

---

## Immediate actions

1. **Re-import Tender Monitor task** — `04_tools/ISZE_Tender_Monitor_Install/ISZE_TenderMonitor_WeeklyTask.xml` (path fixed 2026-07-14)
2. **Import competitive pricing refresh task** — `04_tools/autodoc_scraper/ISZE_ScraperRefresh_WeeklyTask.xml`
3. **Run discount scraper manually** — promotions stale since 2026-04-28

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
