# Market coverage vs dark map — Isuzu-relevant tender capacity

**Date:** 2026-08-25  
**Tool:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Snapshot:** `isze_dashboard_v4_data.json` generated `2026-08-25T15:55:27Z` · `_source_health.json` as of same day  
**Rule:** Ranges, not fake precision. Null ≠ 0. No invented revenue. Full capacity = all leads that matter for Isuzu — not every EU tender on earth.

---

## Verdict (one line)

We are probably seeing about **35–55%** of the Isuzu-relevant addressable public-procurement notice stream in the ISZE footprint (confidence **Medium**): strong on TED above-threshold, weak or dark on DE national, Nordics without keys, and most Med/CEE below-threshold portals.

---

## 1. What “100%” means (the denominator)

### Addressable universe

**100% = public procurement notices that could plausibly become an Isuzu commercial lead**, after the live product-fit / selection gate:

| Include | Exclude (current gate) |
|---|---|
| Goods vehicles / LCV / pickup / chassis-cab / tipper / rigid truck purchase | Passenger cars, SEND / client transport, taxi, buses/coaches |
| Truck / LCV fleet R&M and parts-adjacent contracts | Pure tyre supply/repair; towing; fire/refuse/ambulance specials |
| Markets in the ISZE scrape footprint (TED country filter + national UK/NL/BE/IL + NO/FI when keyed) | Every TED notice on earth; non-footprint countries; passenger transport CPV `600…` |
| Above **and** below TED thresholds (national portals matter below threshold) | Invented “shadow” private fleet deals with no public notice |

**Product-fit segments** (`_PRODUCT_FIT_GATE.md`): `pickup` and `truck` can carry GPS € when fleet + distributor SPU exist; `lcv_van`, `rm_only`, and `weak` stay as **leads** but GPS € is null (no invented N-Series wallet). Seeing the lead ≠ sizing GPS €.

### Geography (footprint)

TED filter (`TED_TARGET_COUNTRIES`, 29 codes):  
GBR, IRL, POL, PRT, GRC, ISR, DEU, FRA, ESP, ITA, NLD, BEL, DNK, SWE, NOR, FIN, ROU, HUN, CZE, SVK, BGR, HRV, AUT, LVA, LTU, EST, SVN, **CYP**, **MLT**.

Named gaps still outside a working national feed: **Iceland**, **Kazakhstan** (GPS sales row may exist; KAZ has **no** SPU → linkage stays null). Switzerland not in TED EU filter.

### Time window

- **Operational scrape lookback:** `LOOKBACK_DAYS = 30` in `tender_scraper_v3.py` (rolling ~1 month).
- **Planning / probe windows** in phase1 docs sometimes used ~70 days — useful for discovery, not what the weekly bat currently fetches.
- For “full capacity” planning, treat the denominator as a **rolling 30–90 day** notice stream; extending lookback is backlog (effort low, noise risk medium).

### Explicitly not chasing

- Passenger / SEND / route transport (CPV `600…`, noise titles).
- Pure tyres, towing, cemetery kit, fire/refuse/ambulance bodies.
- Every municipal stationery/IT tender that happens to say “vehicle” in Hebrew/Dutch without an LCV keep-signal.
- Private OEM deals and dealer stock with no public notice.
- **GPS € on van/LCV-only** buys (lead yes; wallet no — product-fit gate).

---

## 2. What we see today (the numerator)

### Live pipeline (post Isuzu gate + product-fit)

| Metric | Value | Notes |
|---:|---:|---|
| Notices | **211** | Gated workbook / v4 rebuild |
| Opportunities | **186** | Families after dedupe |
| Selective / Watch / Ignore | 9 / 35 / 142 | Actionable shortlist ≈ **44** |
| Product segments | truck 70 · pickup 40 · lcv_van 41 · weak 30 · rm_only 5 | From v4 JSON |
| With fleet count in notice | **13 / 186 (7.0%)** | List feeds rarely publish counts |
| GPS-sized (€/yr) | **3** · sum **€1,488.22** | Post product-fit (vans stripped); null ≠ 0 |
| Published contract value | essentially empty on list feed | `TED_FETCH_DETAIL = False` |

Owner clusters (opportunity counts): CEE 72 · DACH 35 · Benelux 26 · Med+FR ~49 · Nordics 8 · UK/IE 6 · Israel 5.

Source mix on opportunities: TED/EU-dominated (~192 EU-tagged notices in meta); BE national 9; Israel 9; UK CF residual 1 after gate (intentional passenger cut).

### Source health (live `_source_health.json`)

| Source | Status in JSON | Operator read |
|---|---|---|
| TED Europa | **OK** · last_count 605 | Spine for above-threshold EU/EEA |
| UK Find a Tender | **OK** · 22 | Above-threshold UK |
| UK Contracts Finder | **OK** · 121 raw | Most fail Isuzu gate (passenger/route) — intentional |
| Netherlands TenderNed | **OK** · 25 | National NL below/alongside TED |
| Belgium publicprocurement.be (SEA) | **OK** · 14 | Live national BE (9 after gate) |
| Israel mr.gov.il | **OK** · 18 | Live national IL (9 after Hebrew LCV gate) |
| Norway Doffin | **BROKEN*** · 0 · “API key not set” | *Code path intends **AWAITING_KEY** after health fix; keys file **missing** |
| Finland HILMA | **BROKEN*** · 0 · “API key not set” | Same — **AWAITING_KEY**; `nordics_api_keys.env` **not present** |
| Germany DTVP/NRW | **BROKEN** · 0 · HTTP 404 | No free anonymous feed; paid Professional Edition for alerts |
| Belgium RSS | **BROKEN** / retired | SPA shell — superseded by SEA; treat as **RETIRED** |
| Israel RSS | **BROKEN** / retired | SPA shell — superseded by mr.gov.il |
| Israel data.gov.il CKAN | **SUSPECT** | Frozen ~Feb 2021 — secondary only |

\*Parallel source-health work is teaching the scraper to write `AWAITING_KEY` / `RETIRED` instead of red BROKEN for intentional skips. Do not treat JSON “BROKEN” on Nordics as a dead API — it is **missing Jerome registration**.

### TED coverage

- **29** ISO markets in filter (CYP/MLT added Phase 1).
- Above-threshold commercial vehicle / R&M CPV query + keywords.
- Detail enrichment **off** (`TED_FETCH_DETAIL = False`) — thin deadlines, almost no values, rare fleet counts.

### Known blind spots (evidence-backed)

1. **DE national (DTVP / Vergabe.NRW)** — 404; TED-only for Germany above-threshold; below-threshold municipal/utility fleets largely dark.
2. **NO / FI national** — free APIs exist; blocked only by missing keys (`NORDICS_API_KEYS.md`). TED still shows a few NO/FI rows (3 + 2 opps) — above-threshold only.
3. **SE / DK** — TED only; no dedicated national scraper (volume on TED is thin in this snapshot: SE 3, DK 0).
4. **FR / IT / ES / PL / most CEE** — TED only; below-threshold darkness is structural.
5. **Fleet extract ~7%** — source limitation, not a dashboard bug (`_WHY_UNSIZED_GPS.md`).
6. **GPS map nulls** — FR, PL, IT, ES, NL, CZ, AT, … have no distributor/SPU row even when fleet is known.
7. **IL Hebrew** — gate now keeps LCV/truck Hebrew; autocomplete/search is keyword-swept, not a full exhaust of mr.gov.il.
8. **ISL / KAZ** — no working national feed identified; KAZ GPS linkage stays null (no SPU).

---

## 3. Dark market estimate (coverage bands)

Bands = share of **Isuzu-relevant public notices** in that cluster we are **likely already ingesting** into the gated pipeline (TED ± national), not share of GPS-sized rows and not share of network revenue.

| Cluster | Opps in snapshot | Plausible coverage band | Confidence | Why |
|---|---:|---|---|---|
| **UK / IE** | 6 | **55–75%** of gate-passing public LCV/truck notices | Med | FaT + CF + TED alive; CF volume collapses under gate (mostly noise). Below-threshold UK LCV that never hits CF keywords still dark. |
| **Benelux** | 26 | **60–80%** | Med–High | BE SEA + TED + NL TenderNed OK. BE RSS retired. Lux thin/TED-only. |
| **Israel** | 5 | **50–70%** of Hebrew LCV/truck-shaped public notices | Med | mr.gov.il live + Hebrew gate; keyword/autocomplete not exhaustive; CKAN historical only. |
| **Nordics** | 8 | **20–40%** now → **55–75%** after NO/FI keys | Med | TED above-threshold only for NO/FI until keys; SE/DK national still missing. |
| **DACH** | 35 | **25–45%** | Med | DE volume is TED-heavy in our feed, but DE below-threshold (DTVP) is a large dark mass; AT TED-only; CH out of filter. |
| **CEE** | 72 | **30–50%** | Low–Med | TED covers above-threshold; national below-threshold portals largely absent. High opp *count* ≠ high *coverage*. |
| **Med + France** | ~49 | **25–45%** | Low–Med | TED-only for FR/IT/ES/PT/GR; CYP/MLT in filter but thin; below-threshold municipal fleets mostly dark. |
| **ISL / KAZ** | 0 | **0–10%** | High (that it is dark) | No live national feed; TED ISR is Israel, not ISL; KAZ not in TED EU set. |

### Overall footprint blend

Weighting by where Isuzu cares (network markets) and by how much public LCV work sits **below** TED thresholds:

| Overall | Band | Confidence |
|---|---|---|
| **Share of addressable Isuzu-relevant notices we likely see** | **~35–55%** | **Medium** |
| Share of those leads we can **GPS-size** | **~1–3%** of opps (3/186) | **High** (measured) — sizing ≠ coverage |
| Share with any fleet count | **~7%** | **High** (measured) |

Do **not** convert these bands into a single “we see 47%” KPI. Use the range.

---

## 4. Path to full lead capacity (prioritized backlog)

Separate **coverage** (see the lead) from **sizing** (fleet / GPS €). Full lead capacity does **not** require every row GPS-sized.

| # | Action | Impact on coverage | Effort | Dependency | Noise risk |
|---:|---|---|---|---|---|
| **1** | **Register Nordics keys** — Doffin + HILMA → `nordics_api_keys.env` (`NORDICS_API_KEYS.md`); run `verify_nordics_keys.py` | High for NO/FI (band jumps ~20–40% → ~55–75% in Nordics) | Low (~10 min Jerome) | Free API subscription | Low if CPV/keyword gate stays |
| **2** | **DE honesty + free path check** — keep DTVP **WONTFIX/RETIRED** unless paid Professional Edition is approved; optionally probe state portals / open-data dumps; document TED-only DE in operator banner | Honesty High; true coverage lift only if paid/scrape alternative found | Med–High | Paid DTVP **or** brittle HTML scrape | Med–High if scrape without gate |
| **3** | **Below-threshold national portals** still missing — prioritize by network weight: **FR, PL, IT, ES**, then SE/DK, then thin CEE | High for Med/CEE lead volume | High (per portal) | API key / auth / scrape; legal ToS | Med — gate must stay tight |
| **4** | **TED detail enrichment** — enable authenticated detail fetch for shortlisted notices (fleet, deadline, value) | Low on *new* leads; **High on sizing quality** of leads we already see | Med | TED API auth; rate limits | Low if limited to gated IDs |
| **5** | **CPV / country gaps from Phase 1** — `50114000` already added; optional later: bus R&M `50113000` with hard filters; leasing CPV only with vehicle co-keywords; keep passenger CPVs out | Low–Med incremental | Low | Code change + re-scrape | Med–High if passenger/leasing reopened |
| **6** | **Product-fit: more real leads vs more noise** — keep Hebrew/Latin keep-signals; do **not** reopen SEND/`600…`/bare Dutch `van`/tyres; optional: raise Selective threshold visibility, not widen fetch | Improves *useful* capacity, not raw count | Low | Scoring/UI only | Low |
| **7** | **GPS map rows** for FR/PL/IT/ES/NL/CZ when commercial SPU exists | Zero new leads; unlocks sizing on existing fleets | Low–Med | Real SPU data only — never invent | None (null stays null if no SPU) |
| **8** | **Extend lookback 30 → 70–90 days** | Med (more in-window backlog) | Low | Runtime / TED volume | Med duplicate/noise |
| **9** | **IL exhaustiveness** — paginated HTML search beyond autocomplete | Low–Med for IL | Med | Scrape fragility | Low with Hebrew gate |
| **10** | **ISL / KAZ** — only if a free structured feed appears | Niche | Unknown | Feed discovery | — |

### Coverage vs sizing — keep them apart

```
Full lead capacity  =  see every gate-passing notice in footprint
                     ≠  GPS € on every row
                     ≠  published contract value on every row
```

Honest sizing levers: TED detail, human PDF read into outcomes, real SPU map rows.  
Forbidden: invent fleet, invent SPU, treat null as €0, call GPS “expected revenue.”

---

## 5. Optional dashboard chip

**Not patched into `build_dashboard_v4.py` this turn** — a parallel source-health agent is actively editing scraper/health/dashboard (RETIRED / AWAITING_KEY banner logic). Avoid merge fights.

| Artefact | Path |
|---|---|
| Chip HTML/CSS snippet (ready to paste) | `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_coverage_chip_snippet.html` |
| This paper | `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_MARKET_COVERAGE_DARK_MAP.md` |

After source-health lands, paste the snippet into the KPI strip (navy/terracotta, CSS hover tooltip, no CDN) and rebuild v4.

---

## 6. Operator checklist — next concrete moves

1. Jerome: create `nordics_api_keys.env` from example; subscribe Doffin Public + HILMA AVP-Read; `python verify_nordics_keys.py`.
2. Next bat run: confirm NO/FI leave AWAITING_KEY → OK with non-zero counts.
3. Accept DE as TED-only until paid DTVP or a free alternative is approved — do not silently pretend national DE is covered.
4. Queue TED detail auth for sizing — do not confuse with “more markets.”
5. Re-open this paper after one post-keys scrape and refresh the Nordics band.

---

## Evidence index

| Doc / file | Role |
|---|---|
| `_source_health.json` | Live source statuses |
| `isze_dashboard_v4_data.json` | Counts, segments, countries |
| `_PRODUCT_FIT_GATE.md` | GPS eligibility vs lead visibility |
| `_WHY_UNSIZED_GPS.md` | Fleet ~7%; sizing ≠ coverage |
| `_phase1_coverage_cpv_assessment.md` | CPV widen + DE/BE/IL/CYP/MLT |
| `_phase1_endpoint_discovery.md` | BE SEA / IL mr.gov.il / TED CYP-MLT |
| `_phase1_il_be_merge.md` | BEL 9 + ISR 9 after Hebrew gate |
| `NORDICS_API_KEYS.md` | Key registration |
| `_ISUZU_RELEVANCE_AUDIT.md` | Gate tighten 773→~193 notices |
| `_GODTIER_CHECKLIST.md` | Quality bar |
| `CURSOR_TASK_fix_dark_markets.md` | Earlier dark-market task (IL/BE now largely fixed) |
