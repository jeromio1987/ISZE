# Full ISZE market status — national portal capture

**Date:** 2026-08-25 ~20:20 Europe/Berlin  
**Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Desk JSON:** `isze_dashboard_v4_data.json` (regenerated this wave)  
**Rule:** Null ≠ 0. Stated fleet ≠ market potential. Nordics keys DONE — do not re-open portals.

---

## Live desk (post not-for-us)

| Metric | Value |
|---|---:|
| Notices | **326** |
| Opportunities | **291** |
| CV opps (pickup+truck) | **215** |
| Stated fleet pickup/truck | **174** (17 rows — extract-subset) |
| Stated fleet all segments | **196** |
| Aftersales tagged | **54** |
| GPS €/yr sized | **~€37.2k** (10 rows) |
| National LIVE | **16 / 29 ≈ 55%** |
| CODE_READY | **2 / 29 ≈ 7%** (ES WAF · LT apiKey) |
| DARK / BLOCKED national | **11 / 29 ≈ 38%** |

Three layers: **(a)** ~20k LCV / ~78k CV · **(b)** 215 CV tenders captured · **(c)** 174 stated fleet. **174 ≠ 215 ≠ ~78k.**

---

## Per-country national status (TED filter footprint)

| Country | Status | Source / note | Next action |
|---|---|---|---|
| **UK** | **LIVE** | FaT + Contracts Finder | Maintain |
| **NL** | **LIVE** | TenderNed RSS | Maintain |
| **BE** | **LIVE** | SEA API | Maintain |
| **IL** | **LIVE** | mr.gov.il (+ IEC global partial) | IEC domestic GEO_BLOCKED |
| **FR** | **LIVE** | BOAMP ODS | Maintain |
| **PL** | **LIVE** | BZP API | Maintain |
| **IT** | **LIVE** | PNCP JSON (gate-tight) | Tighten CPV/search |
| **DE** | **LIVE** | oeffentlichevergabe Open Data + bund crumb · DTVP RETIRED | Maintain |
| **RO** | **LIVE** | SEAP NoticeCommon POST | Maintain |
| **AT** | **LIVE** | USP tenderlist CPV API | Maintain |
| **NO** | **LIVE** | Doffin Public API (keys DONE) | Maintain — **no re-subscribe** |
| **FI** | **LIVE** | HILMA eformnotices search (keys DONE) | Maintain — **no re-subscribe** |
| **DK** | **LIVE** | udbud.dk soegeresultat (`national_fetchers_dk.py`) 6→4 gated | Maintain |
| **PT** | **LIVE** | dados.gov BASE anúncios JSON 77→15 gated | Maintain |
| **BG** | **LIVE** | CAIS EOP daily OCDS on `storage.eop.bg` (`national_fetchers_bg.py`) 159→5 gated | Maintain |
| **CZ** | **LIVE** | VVZ `createdAt[gte]` + client vehicle post-filter (`national_fetchers_cz.py`) 80→7 gated | Maintain — fulltext/CPV still ignored server-side |
| **ES** | **CODE_READY** | PLACSP Atom/ZIP fetcher ready · **WAF_BLOCKED** this runner | Unblock: ES egress / residential session |
| **LT** | **CODE_READY** | CVP IS `cft-details-export` · HTTP 401 without apiKey | Free VPT API key (no browser spam) |
| **HU** | **BLOCKED** | EKR SPA/login; no free list API | EKR registration or paid aggregator |
| **IE** | **BLOCKED** | eTenders HTML; RSS 500; brittle | OGP structured feed |
| **SE** | **BLOCKED** | No single national gazette — commercial DBs | Paid TendSign/Mercell/… or UHM dump |
| **SK** | **BLOCKED** | ÚVO vestník HTML + reCAPTCHA | ÚVO open data / UVOstat paid |
| **EE** | **BLOCKED** | RHR `/opendata` HTTP 500 | Ministry fix or dump |
| **GR** | **BLOCKED** | KIMDIS “opendata” URL = login shell | Promitheus/GSIS credentials |
| **HR** | **BLOCKED** | EOJN HTML SPA | Structured API if published |
| **SI** | **BLOCKED** | eNaročanje HTML shell | Public JSON if published |
| **LV** | **BLOCKED** | IUB/EIS HTML | Open-data dump / API registration |
| **CY** | **BLOCKED** | eProcurement HTML (thin; TED covers above) | National feed if published |
| **MT** | **BLOCKED** | eTenders Malta HTML | Structured feed if OGP publishes |

**Outside filter:** ISL / KZ still DARK (P3). CH not in TED filter.

---

## What landed this wave (no Nordics spam)

| Item | Result |
|---|---|
| Nordics | **DONE** — untouched |
| CZ VVZ API | **LIVE** — `createdAt[gte]` date window works; client vehicle gate 80→7 · merged |
| BG CAIS EOP OCDS | **LIVE** — 159 raw → 5 gated · merged |
| LT CVP IS | **CODE_READY** — 401 without apiKey |
| EE / SK / GR / HR / SI / LV / CY / MT | **BLOCKED** with unblock paths (`_overnight_dark_block_paths.json`) |
| HU / IE / SE / ES | unchanged BLOCKED / CODE_READY |
| TED detail | Still needs TED API Authorization — not inventing fleet |

---

## Still not LIVE (national)

CODE_READY: **ES · LT**  
BLOCKED: **HU · IE · SE · SK · EE · GR · HR · SI · LV · CY · MT**

---

## Preserve

not-for-us · criticality three layers · IDS · six tabs · CV default filter · unsized honesty
