# Scrapers — roadmap

**Last updated:** 2026-07-26  
**Hub:** [`ISZE_ROADMAP.md`](../../ISZE_ROADMAP.md) · **Location:** `04_tools/`  
**Owner:** Claude scheduled tasks (health report runs automatically)  
**Live register:** [`AUTOMATION_REGISTER.md`](../AUTOMATION_REGISTER.md)

---

## Current state

| Scraper | Status (2026-07-26) | Output | Schedule |
|---|---|---|---|
| Tender Scraper | ✅ Live task `ISZE Tender Monitor` — last OK 2026-07-20 (result 0); next Mon 07:30 | `01_data/14_dashboards/tender_data.json` | Weekly Mon 07:30 |
| Competitive pricing (KS, Tranzparts, TMC, Mekonomen, Auto365) | ✅ Live task `ISZE_PMS_IAM_Refresh` — **do not** also import `ISZE_ScraperRefresh_WeeklyTask.xml` (double-run). Last scheduled 2026-07-20 exited interrupt (`0xC000013A`); manual `refresh_and_check_drift.py` re-run started 2026-07-26 ~21:28 | `04_tools/autodoc_scraper/*_results.csv` | Weekly Mon 07:00 |
| Autodoc / Oscaro | **Retired** — Cloudflare Turnstile blocks 100% of requests | `autodoc_results.csv` (frozen) | None |
| Discount Scraper | Optional / personal promos — task may be registered; not ISZE core | `04_tools/discount-scanner/deals_dashboard.html` | Weekly Thu 07:00 |

**Canonical versions:**

- Tender: `04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py` · live task name `ISZE Tender Monitor`
- Competitive pricing: `04_tools/autodoc_scraper/refresh_and_check_drift.py` · live task name `ISZE_PMS_IAM_Refresh`
- Discount: `04_tools/discount-scanner/discount_scraper.py` · Task XML: `ISZE_DiscountScanner_WeeklyTask.xml`

**Known issues (open):**

1. Doffin (Norway) API requires subscription key — no key registered yet
2. Discount Scraper optional — personal supermarket promos, not ISZE work
3. Lidl URL hardcodes category ID `a10051271` — verify after next discount run
4. Israel RSS entity parse error, Belgium RSS non-XML response, UK Find a Tender 429s — see `04_tools/manual_review_required.md` Items 2–4
5. `ISZE_PMS_IAM_Refresh` Mon 07:00 sometimes interrupted (sleep / stop) — prefer overnight manual if Monday AM fails

---

## Immediate actions

1. ~~Re-import Tender Monitor~~ — **done** (live, verified)
2. ~~Import competitive pricing refresh~~ — **done** as `ISZE_PMS_IAM_Refresh` (spare XML is redundant)
3. ~~Manual competitiveness refresh~~ — **in progress** 2026-07-26 (KS leg of `refresh_and_check_drift.py`)

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
