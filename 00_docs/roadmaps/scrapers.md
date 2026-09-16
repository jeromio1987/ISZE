# Scrapers & tenders — roadmap

**Last updated:** 2026-08-26
**Hub:** [`ISZE_ROADMAP.md`](../ISZE_ROADMAP.md) · **Location:** `04_tools/`
**Owner:** Claude scheduled tasks (health report runs automatically)
**Live register:** [`AUTOMATION_REGISTER.md`](../AUTOMATION_REGISTER.md)
**Tender working backlog (authoritative, evidence-gated):** `04_tools/ISZE_Tender_Monitor_Install/_OPEN_BACKLOG_ARRANGED.md`

---

## Current state

| Scraper | Status | Output | Schedule |
|---|---|---|---|
| Tender Scraper | ✅ Live task `ISZE Tender Monitor` | `01_data/14_dashboards/tender_data.json` | Weekly Mon 07:30 |
| Competitive pricing (KS, Tranzparts, TMC, Mekonomen, Auto365) | ✅ Live task `ISZE_PMS_IAM_Refresh` — **do not** also import `ISZE_ScraperRefresh_WeeklyTask.xml` (double-run) | `04_tools/autodoc_scraper/*_results.csv` | Weekly Mon 07:00 |
| Autodoc / Oscaro | **Retired** — Cloudflare Turnstile blocks 100% of requests | `autodoc_results.csv` (frozen) | None |
| Discount Scraper | Optional / personal promos — not ISZE core | `04_tools/discount-scanner/deals_dashboard.html` | Weekly Thu 07:00 |

**Canonical versions**

- Tender: `04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py` · task `ISZE Tender Monitor`
- Competitive pricing: `04_tools/autodoc_scraper/refresh_and_check_drift.py` · task `ISZE_PMS_IAM_Refresh`
- Discount: `04_tools/discount-scanner/discount_scraper.py` · XML `ISZE_DiscountScanner_WeeklyTask.xml`

**KS/IAM index:** catalog tree expanded 2026-08-25 (`01_data/01_Pricing/_raw/ks_catalog_tree_expand_20260825.csv`, 69 rows) — KS matches now **302** (126 unique PNs) in `revision_exception_queue.csv`.

---

## Open queue

Ordered. Jerome's standing priority: **portal coverage before cosmetic UI**.

| Prio | Item | State | Next |
|------|------|-------|------|
| **P0** | **ES PLACSP egress** | Spain is the last high-lift portal not returning rows. The fetcher exists (`fetch_spain_placsp`, Atom + ZIP paths) and is `CODE_READY` — blocked by a **WAF deny on Jerome's runner**, not by missing code. Est. +15–40 gated notices / 30d once egress works | Find a session/IP path that PLACSP accepts. Probed again 2026-08-27 from a remote container: inconclusive, that runner's own gateway denies the host (policy 403 on CONNECT), so it is not a test of PLACSP |
| **P0** | National portal coverage (rest) | **16/29** countries LIVE, 2 CODE_READY (ES, LT), rest DARK/BLOCKED national. IT PNCP, DE oeffentlichevergabe, AT, CZ, RO, PT, DK, BG were wired 2026-08-25 | Remaining lift is P2/P3 per country — GR credentials, LT key, SK/HU registration. Evidence: `_source_health.json`, `_COUNTRY_TENDER_PORTALS_MAP.md` |
| **P1** | TED detail enrichment | Partial — capability code on; detail GET needs TED auth | Obtain TED auth, then enrich |
| **P2** | Tender relevance scoring | Not started | Score 1–5 on title, country, value; filter ≥ 3 |
| **P2** | `scrape_error` column (KS + successors) | Not started | Distinguish genuine price gap from scrape failure |
| **P3** | RSS / feed failures | Israel entity parse error, Belgium non-XML response, UK Find a Tender 429s | `04_tools/manual_review_required.md` items 2–4 |
| **P3** | Lidl hardcoded category id `a10051271` | Unverified | Check after next discount run |
| **P4** | Health-report thresholds + stale-scraper push (ntfy.sh) | Not started | `04_tools/scraper_health_report.md` |

**`ISZE_PMS_IAM_Refresh` note:** the Monday 07:00 run is occasionally interrupted by sleep/stop (`0xC000013A`). Prefer an overnight manual `refresh_and_check_drift.py` if Monday morning fails.

---

## Closed — do not reopen

| Closed | Date | Why |
|---|---|---|
| **Nordics tender API keys** (Doffin / HILMA) | 2026-08-25 | **DONE.** `nordics_api_keys.env` filled, `verify_nordics_keys.py` ALL OK, source health OK (Doffin 37 / HILMA 54 matches, NO 11 + FI 1 merged). Never put "paste Nordics keys" on a waiting-on-Jerome list, audit, or overnight brief again. Escalate only on a **new** evidenced failure such as a 401 after a previously OK run. `DECISIONS.md` 2026-08-25 · `_NORDICS_BLOCKED.md` |
| Autodoc / Oscaro scraping | 2026-07-14 | Cloudflare Turnstile blocks every request; retired from the health check |
| Auto365 as a **PN price index** | — | No OEM part-number join — `04_tools/autodoc_scraper/AUTO365_PN_JOIN.md`. The scraper still runs; its output is not a price index |
| GPS maps FR/PL/IT/ES | 2026-08-25 | Done (null) — no SPU rows exist for those countries in `gps_spu_by_distributor.csv`; labelled `has_spu=false`. Never invent an SPU |
| Spare `ISZE_ScraperRefresh_WeeklyTask.xml` import | 2026-07-16 | Would double-run the live `ISZE_PMS_IAM_Refresh` task |

---

## Dashboard integration (standing)

- Tender JSON is auto-injected via `01_data/14_dashboards/tender_data.json` (alias `01_data/dashboards/`) — **the only live feed path**.
- Competitive Pricing tab: top 50 PNs, IAM vs ISZE SP, Class C risk flags. Mode A needs the competitor **vintage labels** decision (hub §2, B10) before shipping.
