# Tender Engine v3 — baseline audit (Phase 0)

**Written:** 2026-08-25 · **No functional changes**  
**Live data:** `01_data\14_dashboards\tender_data.json` (generated `2026-08-24T05:33:31Z`)  
**Last monitor run log:** `tender_monitor_log.txt` — run started `ma 24/08/2026 7:30:00`  
**Probe evidence:** `_probe_sources_v3_results.json` (live GETs this session)  
**Analysis dump:** `_audit_analyze_v3_results.json`

Baseline snapshot from that JSON: **778 raw notices → 680 opportunities** across **26 named markets** (plus placeholder junk rows — see §5).

---

## 1. Source inventory

Every `fetch_*` in `tender_scraper_v3.py`, with the URL(s) it calls, intended coverage, and what the **24 Aug 2026** weekly run actually returned.

| Fetcher | Portal | URL(s) called | Countries intended | Last run result (24 Aug) |
|---|---|---|---|---|
| `fetch_uk` | UK Find a Tender (OCDS) | `https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages` | United Kingdom | **22** matches (100 releases fetched; stages filter empty → retry without stages) |
| `fetch_contracts_finder` | UK Contracts Finder (OCDS) | `https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search` | United Kingdom (lower-value) | **121** unique matches (429 rate-limits observed, recovered) |
| `fetch_ted` | TED Europa API v3 | POST `https://api.ted.europa.eu/v3/notices/search` | 27 ISO codes in `TED_TARGET_COUNTRIES` (see list below) | **605** after CPV/keyword filter (761 raw fetched) |
| `fetch_ted_detail` | TED notice detail | GET `https://api.ted.europa.eu/v3/notices/{id}` | same | **Not called** — `TED_FETCH_DETAIL = False` |
| `fetch_germany` | DTVP RSS + Vergabe.NRW | `https://www.dtvp.de/Center/company/public/procurement/rss` · `https://www.vergabe.nrw.de/VMPSatellite/satellite.vm` | Germany below-threshold | **0** — DTVP HTTP 404, NRW HTTP 404 |
| `fetch_belgium` | publicprocurement.be RSS candidates | `https://www.publicprocurement.be/supplier/feed/rss` · `https://www.publicprocurement.be/en/rss` | Belgium below-threshold | **0** — parse error / empty |
| `fetch_netherlands` | TenderNed Atom | `https://www.tenderned.nl/papi/tenderned-rs-tns/rss/laatste-publicatie.rss` | Netherlands | **25** keyword matches |
| `fetch_doffin` | Doffin (Norway) | `https://betaapi.doffin.no/public/v2/notices` | Norway | **0** — early-return: `No API key set — skipping.` |
| `fetch_hilma` | HILMA (Finland) | `https://hns-hilma-prod-apim.azure-api.net/avp/hilmatenders/` | Finland | **0** — early-return: `No API key set — skipping.` |
| `fetch_israel` | mr.gov.il RSS | `https://mr.gov.il/ilgstorefront/he/rss/Tenders.xml` | Israel | **0** — `mismatched tag: line 53, column 2` (HTML body) |

**TED country filter (`TED_TARGET_COUNTRIES`, 27 codes):**  
GBR, IRL, POL, PRT, GRC, ISR, DEU, FRA, ESP, ITA, NLD, BEL, DNK, SWE, NOR, FIN, ROU, HUN, CZE, SVK, BGR, HRV, AUT, LVA, LTU, EST, SVN.

**Not in TED filter (but named as ISZE / coverage-gap markets in the v4 pack):** CYP, MLT, ISL, KAZ.

**Last-run totals (log):** UK FaT 22 · UK-CF 121 · TED 605 · DE national 0 · BE 0 · NL 25 · NO 0 · FI 0 · IL 0.

---

## 2. Live probe (2026-08-25)

Throwaway script: `_probe_sources_v3.py`. Every listed URL was GETed/POSTed this session.

| Source | HTTP | Content-Type | Bytes | `<item>` | `<entry>` / feed | HTML? | Verdict |
|---|---:|---|---:|:---:|:---:|:---:|---|
| UK Find a Tender | 200 | application/json | 5,126 | — | JSON OK | no | **ALIVE** |
| TED search | 200 | application/json | 6,429 | — | JSON OK | no | **ALIVE** |
| TED detail sample (`…/123456-2026`) | 400 | (empty) | 43 | — | — | no | Endpoint exists; sample id invalid (expected). Detail fetch still disabled in code. |
| Contracts Finder OCDS | 200 | application/json | 7,241 | — | JSON OK | no | **ALIVE** |
| TenderNed RSS | 200 | application/atom+xml | 24,676 | no | **`<atom:entry>` ×25** (namespaced — literal `<entry` not present) | no | **ALIVE** |
| Israel RSS | 200 | text/html;charset=UTF-8 | **661,445** | **no** | no | **yes** | **DEAD — HTML where feed expected** |
| Belgium RSS `/supplier/feed/rss` | 200 | text/html | **1,089** | no | no | **yes** | **DEAD — HTML SPA shell** |
| Belgium RSS `/en/rss` | 200 | text/html | **1,196** | no | no | **yes** | **DEAD — HTML SPA shell** |
| DTVP RSS | **404** | text/html | 12,508 | no | no | yes | **DEAD — 404 HTML** |
| Vergabe.NRW | **404** | text/html | 43,598 | no | no | yes | **DEAD — 404 HTML** |
| Doffin (no key) | **404** | application/json | 54 | — | — | no | Unreachable without key (404 body); code never calls it when key blank |
| HILMA (no key) | **404** | application/json | 54 | — | — | no | Same as Doffin |

### HTTP 200 + HTML (not a feed) — complete list from this probe

1. **Israel** — `mr.gov.il/.../rss/Tenders.xml` → 661 KB HTML search page, zero `<item>`.
2. **Belgium** — both RSS candidate URLs → ~1.1–1.2 KB JS app shell, zero feed elements.

These are exactly the silent-failure class described in the v4 pack: status 200, body present, parser fails or finds nothing, log shows `0` / a parse error, run continues as if the market simply had no tenders.

**Probe caveat for Phase 1 `validate_feed`:** TenderNed is a healthy Atom feed that uses **`<atom:entry>`**, not bare `<entry>`. A validator that only looks for `<item` / `<entry` will false-positive BROKEN on NL. Check for `b"<item"`, `b"<entry"`, **and** `b":entry"` / Atom Content-Type.

First ~200 bytes of each body are stored in `_probe_sources_v3_results.json`.

---

## 3. Field completeness (`notices` array, n=778)

Ranked by emptiness. Fleet size treats `0` as empty (extractor default). Value treats `0`/blank as empty.

| Field | Populated | Empty % |
|---|---:|---:|
| FleetSize / fleet_size | 1 | **99.9%** |
| brand_hits | 1 | 99.9% |
| Est. Value / value_amount | 70 | **91.0%** |
| framework_hits | 114 | 85.3% |
| CPV Desc | 134 | 82.8% |
| Procedure Type | 134 | 82.8% |
| Buyer Type | 138 | 82.3% |
| Notice Type | 143 | 81.6% |
| Currency | 160 | 79.4% |
| Description | 168 | 78.4% |
| Deadline / Deadline Date / days_to_deadline | 189 | **75.7%** |
| rm_hits | 287 | 63.1% |
| service_hits | 391 | 49.7% |
| vehicle_hits | 614 | 21.1% |
| score_drivers | 631 | 18.9% |
| data_gaps | 719 | 7.6% |
| CPV Code | 739 | 5.0% |
| Buyer | 748 | 3.9% |
| Published Date | 748 | 3.9% |
| Country / Country Code / Published / Source Notice ID / Title / URL | 773 | 0.6% |
| Lifecycle, Score, Source, decision, fit/win/econ scores, rm_contract, urgency, tier, … | 778 | 0.0% |

**Cross-check with `meta.stats`:** `missing_deadline` 589 (75.7%), `missing_value` 706 (90.7%) — matches.

**Headline extraction failures (confirm v4 Phase 2 premise):**

- Deadline empty on **~76%** of notices.
- Contract value empty on **~91%**.
- Fleet size present on **1 / 778** (~0.1%).
- `rm_contract` is always set (boolean) — 360 `True` / 418 `False` in this file; that is a classification flag, not a “populated field” in the same sense as deadline/value.

The ~0.6% empty on Title/URL/Country is not real notices — it is the five Excel placeholder rows from empty sheets leaking into the JSON (see §5).

---

## 4. Coverage map

### Markets with notices (opportunity counts from live JSON)

Action-tier = decision `Attack` or `Selective`.

| Code | Market | Notices | Opportunities | Action-tier | Supplying source(s) |
|---|---|---:|---:|---:|---|
| GBR | United Kingdom | 143 | 125 | **0** | UK FaT (22), UK-CF (103 opps) |
| ROU | Romania | 90 | 71 | 51 | TED |
| DEU | Germany | 72 | 66 | 6 | TED only (national DE = 0) |
| FRA | France | 53 | 51 | 26 | TED |
| POL | Poland | 58 | 51 | 16 | TED |
| NLD | Netherlands | 46 | 46 | 8 | TED (21) + TenderNed (25) |
| ESP | Spain | 47 | 45 | 13 | TED |
| CZE | Czechia | 38 | 37 | 13 | TED |
| ITA | Italy | 31 | 25 | 11 | TED |
| HUN | Hungary | 18 | 17 | 9 | TED |
| PRT | Portugal | 18 | 17 | 13 | TED |
| SWE | Sweden | 16 | 16 | 1 | TED |
| BGR | Bulgaria | 32 | 15 | 13 | TED |
| BEL | Belgium | 15 | 14 | 2 | TED only (national BE RSS = 0) |
| NOR | Norway | 15 | 14 | 2 | TED only (Doffin skipped) |
| GRC | Greece | 16 | 13 | 5 | TED |
| SVK | Slovakia | 17 | 13 | 2 | TED |
| IRL | Ireland | 9 | 9 | 2 | TED |
| HRV | Croatia | 10 | 8 | 5 | TED |
| LTU | Lithuania | 8 | 8 | 3 | TED |
| SVN | Slovenia | 5 | 5 | 2 | TED |
| EST | Estonia | 5 | 4 | 0 | TED |
| LVA | Latvia | 6 | 4 | 1 | TED |
| AUT | Austria | 2 | 2 | 0 | TED |
| FIN | Finland | 2 | 2 | 0 | TED only (HILMA skipped) |
| DNK | Denmark | 1 | 1 | 0 | TED |

**26 markets with real opportunities.** Decision mix: Attack 2 · Selective 202 · Watch 152 · Ignore 324.

### ISZE / named markets with ZERO notices

| Code | Market | In TED filter? | Why zero (evidence) |
|---|---|---|---|
| **ISR** | Israel | **Yes** | National RSS dead (HTML). TED filter includes ISR but **zero ISR notices** in this snapshot — either no matching CPV/keyword hits in-window, or TED ISR coverage is thin; national source would be the below-threshold path. |
| **CYP** | Cyprus | **No** | Explicitly absent from `TED_TARGET_COUNTRIES` — not a CPV-gate mystery until the country is added to the query. |
| **MLT** | Malta | **No** | Same as Cyprus. |
| **ISL** | Iceland | **No** | Comment in scraper: Iceland deliberately removed from TED filter. |
| **KAZ** | Kazakhstan | **No** | Outside TED; no national fetcher. |

**UK diagnostic (out of Phase 0 / v4 D4 scope, recorded only):** 125 opportunities, **0** action-tier. Volume without triage — separate scoring question.

---

## 5. Dead code and risk

### Cannot work as written (or always empty)

| Item | Evidence | How failure is reported today |
|---|---|---|
| Israel RSS | HTTP 200 HTML, 0 `<item>`; log `mismatched tag` | Printed as error, then **0 results** — not a hard SOURCE BROKEN state |
| Belgium RSS ×2 | HTTP 200 HTML shells; log `RSS parse error: syntax error` | Printed as 0 matches + soft “TED covers above-threshold” |
| DTVP RSS | HTTP 404 every recent run; comments already admit no free anonymous feed | Logged as HTTP 404, total DE national 0 |
| Vergabe.NRW | HTTP 404; HTML scrape never produces structured rows even on 200 | Logged skip; no notices |
| Doffin / HILMA | `DOFFIN_API_KEY = ""` / `HILMA_API_KEY = ""` module constants; early return | Logged as skip — honest, but keys are not read from env (`ISZE_DOFFIN_API_KEY` / `ISZE_HILMA_API_KEY` not wired) |
| TED detail enrichment | `TED_FETCH_DETAIL = False` | Dead path for deadline/value recovery from detail API |

### Silent / soft failure patterns

1. **`get_with_retry` / `post_with_retry`** — broad `except Exception`, sleep, retry, then **`return None`**. Callers often treat None as “no data” rather than “transport failed”.
2. **HTTP 200 + wrong content type** (IL, BE) — no feed validation; failure looks like empty market.
3. **Empty Excel sheets become fake notices.** `save_to_excel` writes a one-cell placeholder message when a sheet has zero rows. The dashboard builder then ingests those strings as `Source` values. Live JSON still contains:
   - `No DE national results — DTVP portal may require browser access…`
   - `No results — add DOFFIN_API_KEY…`
   - `No results — add HILMA_API_KEY…`
   - `No Israel results found`
   - `No Belgium RSS results — TED covers above-threshold BE`  
   These inflate `raw_notices` and create a junk “UNK” opportunity family. **Empty should mean empty sheet, not a notice row.**
4. **No bare `except:`** (bare except with no type) in `tender_scraper_v3.py`, `isze_core_v3.py`, or `build_dashboard_v2.py`. Risk is `except Exception` that swallows and continues — present in retry helpers and most fetchers.

### Comment vs reality

- Inline comments (2026-08-11) correctly flag BE/DTVP as non-feeds. Live probe **reconfirms** both; Israel comment still frames it as entity/parse issues in places — the real disease is **retired RSS → HTML**.
- Header comment claims TED detail fetch “fixes” missing deadline/value — the flag is off, so that claim is aspirational, not live behaviour.

---

## 6. Acceptance checklist (Phase 0)

| Requirement | Status |
|---|---|
| Source inventory for every `fetch_*` | Done (§1) |
| Live probe of every source URL with status / ctype / bytes / item|entry / preview | Done (§2 + `_probe_sources_v3_results.json`) |
| Identify every HTTP-200-HTML-not-feed source | **Israel + both Belgium URLs** (§2) |
| Field completeness ranked by emptiness | Done (§3) |
| Coverage map + zero-notice ISZE markets | Done (§4) |
| Dead code / silent failure / “0 results” masking | Done (§5) |
| Functional code changes | **None** (audit only) |

---

## 7. What Phase 1 should treat as already proven

Do not re-diagnose these; fix them:

1. Israel endpoint is **retired** (HTML). Need a new machine-readable source — parser leniency will not help.
2. Belgium RSS candidates are **SPA shells**. Need XHR/open-data API — not a better XML parse.
3. DTVP anonymous RSS **404**; structural gap, not a typo.
4. CYP + MLT are **absent from `TED_TARGET_COUNTRIES`** — check that before building new fetchers.
5. `validate_feed` must accept **namespaced Atom** (`atom:entry`) or TenderNed will be marked BROKEN incorrectly.
6. Stop writing Excel placeholder strings that reappear as notices in `tender_data.json`.

---

*End of Phase 0 audit. Diff = this file + throwaway probe/analysis scripts only. Ready for Jerome review before Phase 1.*
