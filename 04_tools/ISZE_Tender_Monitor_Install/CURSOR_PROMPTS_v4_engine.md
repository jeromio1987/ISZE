# Cursor prompt pack — Tender Engine v4

**Status: SHIPPED — phases 0–6 delivered 2026-08-25; god-tier tighten loop same day.**  
Original proposal text kept below for history. Live operator entry: `OPERATOR_INDEX.md` + `SETUP.txt`.

Written 2026-08-25. Do not treat §0 as blocking — D1–D5 were agreed and built.

Goal: maximum tender coverage across every ISZE market, and a new dashboard that expresses each
opportunity in **GPS and PMS terms** rather than as a procurement notice.

---

## §0 — Design decisions to confirm before anything is transferred

| # | Decision | Proposed | Why it matters |
|---|---|---|---|
| D1 | Never state expected revenue | **Agreed — "addressable opportunity" only** | We do not track tender outcomes, so we have no win rate. Any figure implying expected revenue is unsupportable. |
| D2 | Spend-per-unit basis | **Per-country from `gps_spu_by_distributor.csv`**, not one blanket figure | Real SPU ranges from ~€377 (Israel) to ~€665 (Ireland). A single number would be wrong in most markets. |
| D3 | Start recording outcomes | **Yes — build the field now, even though it is empty** | Twelve months of outcomes is the only way to ever answer "what do we win?" |
| D4 | Scope of v4 | Engine + dashboard. **Not** scoring-model re-tuning | The UK zero is a separate diagnostic question. |
| D5 | Tool shareable with MIDI / IMG | **Build market-agnostic, no hard-coded ISZE-only assumptions** | Per Jerome: whatever we build could be used by them. |

---

## §1 — How to run this

Six phases. **Run them in order, one Cursor session each.** After each phase, send me the diff and the
run log and I will review before you start the next. Do not batch phases — later phases depend on data
shapes created earlier.

Paste the **Global context block** (§2) at the top of every phase prompt.

---

## §2 — Global context block (prepend to every phase)

```
PROJECT CONTEXT — ISZE Tender Engine v4

Repo:  C:\Users\jerom\Desktop\claude\ISZE
Tool:  04_tools\ISZE_Tender_Monitor_Install\
  tender_scraper_v3.py   — source fetchers (one function per portal)
  isze_core_v3.py        — scoring engine, extraction helpers
  build_dashboard_v2.py  — HTML dashboard builder
  run_tender_monitor.bat — orchestrator
Live output: 01_data\14_dashboards\tender_data.json  (also mirrored into the tool folder)

WHAT THIS SYSTEM DOES
Scrapes European public procurement portals weekly, classifies each notice against Isuzu's
target categories, scores it (Fit / Win / Econ), and produces a distributor-ready lead brief.
Current run: 778 raw notices -> 680 scored opportunities across 26 markets.

HARD RULES
1. Never invent or estimate a number. If a field is unknown, emit null — never 0, never a guess.
2. Never present a figure as expected or forecast revenue. This system has NO outcome data and
   therefore no win rate. Everything is "addressable opportunity if won".
3. Never present a capture rate above 100%. If the maths produces one, the denominator is wrong —
   stop and report it rather than displaying it.
4. Do not commit API keys. Read them from environment variables.
5. Do not re-tune the Fit/Win/Econ scoring weights in this work. Out of scope.
6. Preserve backwards compatibility of tender_data.json: add fields, never rename or remove
   existing ones, because downstream dashboards read them.
7. Python 3.14 on Windows. Console is cp1252 — never print raw non-ASCII to stdout without
   encoding guards, it will crash the run.

STYLE
Small, reviewable commits. One concern per commit. Log what you changed and why.
```

---

## §3 — PHASE 0 · Audit and baseline (no functional changes)

```
PHASE 0 — AUDIT AND BASELINE. Make no functional changes in this phase.

Produce a written audit at 04_tools\ISZE_Tender_Monitor_Install\_AUDIT_v3_baseline.md covering:

1. SOURCE INVENTORY
   For every fetch_* function in tender_scraper_v3.py: the portal, the exact URL(s) called,
   the countries it is supposed to cover, and whether it returned anything in the last run
   (see tender_monitor_log.txt).

2. LIVE PROBE
   Write a throwaway script that GETs every source URL and records: HTTP status, Content-Type,
   byte length, whether the body contains <item> or <entry>, and the first 200 bytes.
   Record the results in the audit. IMPORTANT: two sources are known to return HTTP 200 with an
   HTML page instead of a feed — identify every source where this is true, do not assume it is
   only those two.

3. FIELD COMPLETENESS
   Load 01_data\14_dashboards\tender_data.json. For every field in the notices array, report the
   percentage populated. Rank by emptiness. This tells us where extraction is failing.

4. COVERAGE MAP
   For each of the 26 markets returning notices: notice count, action-tier count, and which source
   supplied them. Then list every ISZE market that returns ZERO notices.

5. DEAD CODE AND RISK
   Any fetcher that cannot possibly work (dead URL, missing key, unimplemented), any bare
   except: clause that would swallow a real failure, any place where a failure is logged as "0
   results" rather than as an error.

Do not fix anything yet. The audit is the deliverable.
```

**Acceptance:** an audit file that tells us, per source, whether it is alive — with evidence.

---

## §4 — PHASE 1 · Source layer, maximum coverage

```
PHASE 1 — SOURCE LAYER. Goal: the largest possible number of relevant tenders, and never a
silent failure again.

TASK A — SOURCE HEALTH (do this first, everything else depends on it)
Every dead source currently returns HTTP 200 with a valid-looking body, so the run reports
"0 results" instead of an error. Build:
  - validate_feed(name, response) -> error string or None. Flags: body under a minimum size,
    HTML served where a feed is expected, no <item>/<entry> elements.
  - A rolling state file _source_health.json tracking consecutive zero-result runs per source.
  - Status per source: OK / SUSPECT (3+ consecutive empty runs) / BROKEN (validation failed).
  - A loud SOURCE HEALTH block printed at the END of the run listing anything not OK.
Wire it into every fetcher.

TASK B — REVIVE THE DEAD SOURCES
  * Israel (mr.gov.il): the RSS URL now returns a 662KB HTML page, HTTP 200, zero <item>
    elements. The endpoint is retired — a lenient XML parser will NOT help. Find the current
    machine-readable source: check for an API or OpenData tenders dataset on mr.gov.il or
    data.gov.il first; then a current RSS/Atom path; only as a last resort scrape the HTML
    search-results page still served at the old URL. Also populate a real Deadline — the old
    implementation hard-coded it empty.
  * Belgium (publicprocurement.be): returns a 1,196-byte JavaScript app shell. Open the site's
    search in a browser, watch the Network tab, identify the JSON/XHR API it calls, and use that.
    Check for a published open-data endpoint first.

TASK C — SWITCH ON WHAT IS ALREADY BUILT
  Norway (Doffin) and Finland (HILMA) fetchers are written but early-return on a blank API key.
  Read keys from ISZE_DOFFIN_API_KEY and ISZE_HILMA_API_KEY environment variables, falling back
  to the module constant. Never commit a key.

TASK D — CLOSE THE COVERAGE GAPS
  * Cyprus and Malta are EU members, so above-threshold notices SHOULD already arrive via TED.
    They currently return zero. Investigate whether the TED country filter or CPV gate is
    excluding them BEFORE building anything new.
  * Germany below-threshold (DTVP) is unimplemented. Assess feasibility and implement if viable.
  * Iceland (EEA) and Kazakhstan (outside TED): assess whether a usable national source exists.
    Report findings; implement only if straightforward.

TASK E — WIDEN THE NET WITHIN EXISTING SOURCES
  Review the CPV target list and keyword filters. We are looking for light commercial vehicles,
  pickups, and — most importantly — vehicle repair, maintenance, fleet management and
  fleet-leasing-with-servicing contracts. Check for relevant CPV codes currently NOT in the
  target list. Report what you would add and the expected volume impact BEFORE adding it.

Report per source: notices before, notices after.
```

**Acceptance:** every source either returns data or is explicitly reported BROKEN. Total notice count up.

---

## §5 — PHASE 2 · Extraction completeness

```
PHASE 2 — EXTRACTION. Goal: fill the fields that are currently empty, because empty fields are
why most of the pipeline cannot be triaged.

Current state: 76% of notices have no deadline, 90% no contract value, 97% no fleet size.

TASK A — MULTILINGUAL FLEET SIZE
extract_fleet_size() in isze_core_v3.py is English-only and title-only, so it fires on 1 notice
in 778. A tested multilingual replacement is provided at:
  04_tools\ISZE_Tender_Monitor_Install\_reference_fleet_extractor.py
It reaches ~22 of 778 at roughly 95% precision. Port it, and:
  - pass BOTH title and description at every call site (several currently pass title only)
  - keep the guards: reject 1900-2100 (years), reject when "/" abuts the number, cap at 3000,
    take the MAXIMUM plausible match not the first
  - add a fleet_size_confidence field: "extracted" or null. Never guess.

TASK B — DEADLINE RECOVERY
76% of notices have no deadline. Determine whether the source data contains it and the parser is
missing it, or whether it genuinely is not published. Report the split before fixing. For TED,
check whether the detail endpoint carries a deadline that the list endpoint does not — if so,
fetch detail for notices that pass the CPV gate.

TASK C — VALUE RECOVERY
Same approach for contract value (currently 10% populated).

TASK D — R&M AND SERVICE SIGNAL
The rm_contract flag is the single most commercially important field we have. Audit how it is
currently set and how reliable it is. Multi-language service terminology should be recognised:
manutenzione, entretien, Wartung, onderhoud, mantenimiento, manutenção, konserwacja, údržba,
mentenanță, karbantartás, vedlikehold, underhåll. Report precision on a manual sample of 20.

Report field completeness before and after, as a table.
```

**Acceptance:** measurable lift in deadline, value, fleet-size and R&M-flag completeness, with the
before/after table. No field ever populated by estimation.

---

## §6 — PHASE 3 · GPS and PMS opportunity linkage ★ the new capability

```
PHASE 3 — GPS AND PMS LINKAGE. This is the core new capability of v4.

Today a tender is a procurement notice. It should be expressed in the terms this business actually
manages: GPS (genuine parts share) and PMS (periodic maintenance) opportunity.

DATA AVAILABLE — use these, do not invent equivalents:
  01_data\00_derived\gps_spu_by_distributor.csv
     year, distributor_code, country, region, uio_units, spend_per_unit_eur,
     max_spend_eur, gps_capture_vs_max, traffic_light
  01_data\00_derived\pms_capture_by_db_year.csv
     year, distributor_code, pms_category, category_label, line_type, uio_units,
     expected_qty, actual_qty, actual_rev_eur, capture_rate, avg_sp_eur, revenue_gap_eur
  01_data\00_derived\capture_recovery_model.csv
     distributor_code, pms_category, capture_rate_actual, gap_units, gap_type,
     gap_revenue_at_genuine

TASK A — COUNTRY TO DISTRIBUTOR MAPPING
Build an explicit, reviewable mapping from tender country to distributor_code. Put it in a
separate config file, not buried in code — it will need maintenance. Where a country has no
distributor mapping, emit null and report it. Do not guess.

TASK B — GPS OPPORTUNITY PER TENDER
For each opportunity with a known fleet_size AND a mapped country:
    gps_addressable_per_year_eur = fleet_size * spend_per_unit_eur (that country, latest year)
Use the country-specific SPU. Do NOT apply one blanket figure — real SPU ranges from roughly
EUR 377 to EUR 665 depending on market, so a single number would be materially wrong in most.
Emit null where fleet_size or the mapping is unknown. Record which year's SPU was used.

TASK C — PMS OPPORTUNITY PER TENDER
For the same opportunities, express the PMS-category demand the fleet would generate, using the
per-category expected quantities and average selling prices for that distributor. Show it as a
category breakdown (oil filter, air filter, brake, etc.), not a single number.

TASK D — THE CAPTURE FRAMING (read this carefully)
For the mapped country we know the CURRENT capture rate. So each tender can be expressed as:
   - addressable parts demand the fleet generates
   - what we would capture at TODAY's capture rate for that market
   - what we would capture if the fleet sat under an R&M contract through the authorised channel
The DIFFERENCE between those last two is the actual argument for pursuing R&M tenders.

CRITICAL CONSTRAINTS ON THIS PHASE:
  - Label every output "addressable opportunity", never "expected revenue" or "forecast".
    We do not track tender outcomes and therefore have NO win rate. Any wording implying we
    know what we will win is unsupportable and must not appear in field names, labels or tooltips.
  - Never display a capture rate above 100%. If the maths yields one, the denominator is wrong —
    stop, log it, and surface it as a data-quality error.
  - Where fleet size is unknown (most notices), these fields are null. Do not substitute an
    average. A null is honest; an average is a fabrication.

Add to each opportunity: gps_addressable_per_year_eur, pms_demand_by_category,
capture_at_current_rate_eur, capture_under_rm_eur, opportunity_basis (a human-readable string
stating exactly what was multiplied by what).
```

**Acceptance:** every sized opportunity carries a GPS figure derived from its own market's SPU, with
a stated basis, and nulls everywhere the inputs are missing.

---

## §7 — PHASE 4 · The new dashboard

```
PHASE 4 — NEW DASHBOARD: GPS AND PMS OPPORTUNITY VIEW.

Build a NEW dashboard alongside the existing one. Do not replace isze_dashboard_v2.html —
the existing view stays working.

AUDIENCE: senior management and commercial colleagues. Not analysts. Someone should understand
the page in thirty seconds without training.

REQUIRED VIEWS
1. HEADLINE — total addressable GPS opportunity currently visible in the pipeline, with an
   explicit count of how many opportunities are sized versus unsized. The unsized count must be
   as prominent as the value, because it is the honest caveat: what we can see is a floor.
2. BY MARKET — for each market: notices, action-tier count, addressable GPS opportunity, current
   capture rate, and the R&M-linked share. Sortable.
3. OPPORTUNITY TABLE — one row per opportunity: buyer, country, deadline, decision, fleet size,
   GPS addressable per year, R&M flag. Default sort: GPS addressable descending, NOT notice date.
4. PMS BREAKDOWN — for a selected opportunity, the parts-category demand its fleet would generate.
5. SOURCE HEALTH BANNER — driven by _source_health.json from Phase 1. If a source is dead, that
   must be visible on the page, not buried in a log.
6. COVERAGE VS REVENUE — the diagnostic view: each market's share of network revenue against its
   share of the actionable pipeline. This is what exposes markets we under-watch.

RULES
- Self-contained HTML. No CDN, no external fonts, no external scripts — it must open offline.
- Set an explicit light background and text colour on html, body and every panel, and set
  color-scheme: only light. Without this the page is unreadable for anyone using a dark-mode
  browser.
- Readability is a hard requirement, not a preference: body text no smaller than 13px, generous
  line-height, strong contrast, clear hierarchy. Assume it will be read on a laptop in a meeting.
- Any figure with a null input renders as an em dash, never as 0.
- Every derived number needs a hover or footnote stating its basis.
- Never label anything "expected revenue" or "forecast". "Addressable opportunity" throughout.
```

**Acceptance:** opens offline, readable in dark-mode browsers, sorts by opportunity value, and shows
its own data gaps honestly.

---

## §8 — PHASE 5 · Outcome tracking (the missing feedback loop)

```
PHASE 5 — OUTCOME TRACKING. Small phase, disproportionate long-term value.

We currently cannot answer "how many tenders do we win?" because we do not record outcomes. That
is the single biggest gap in the whole system — it is why every figure elsewhere must be labelled
"addressable" rather than "expected".

Build the capture mechanism now, even though it starts empty:

1. A simple editable outcome store (JSON or CSV) keyed by opportunity_id, with fields:
   status (not pursued / bid / won / lost / no-bid), decision_date, loss_reason
   (price / spec / network coverage / financial capacity / other), competitor_if_known,
   actual_parts_revenue_12m, notes.
2. Dashboard editing so an owner can set status inline; persist to the store.
3. The store must survive a weekly rebuild — never overwritten by a fresh scrape.
4. A summary panel: outcomes recorded, win rate ONCE there is a meaningful sample.
   Below a minimum sample size, display "insufficient data" rather than a misleading percentage.

Do NOT compute or display a win rate from a handful of records.
```

**Acceptance:** an owner can mark an outcome, it survives the next weekly run, and no win rate is
shown until the sample justifies it.

---

## §9 — PHASE 6 · Validation and regression

```
PHASE 6 — VALIDATION.

1. Full run of run_tender_monitor.bat end to end. Capture the log.
2. Regression: confirm every field the old dashboard reads still exists with the same name.
3. Data-quality report comparing v3 baseline to v4:
   notices by source, field completeness, markets covered, sized opportunities,
   total addressable GPS opportunity.
4. Spot-check 15 opportunities by hand against their source notice URL. Report any mismatch.
5. Confirm: no capture rate above 100% anywhere; no key in any committed file; page opens offline;
   page is readable in a dark-mode browser.
6. Write _V4_RELEASE_NOTES.md — what changed, what improved with numbers, what is still broken,
   and what was deliberately left out of scope.
```

---

## §10 — What I will review after each phase

Send me the diff and the run log. I will check:

- **Fabricated numbers** — any field populated by estimate, average or fallback where the real value
  was unavailable. This is the failure mode I will look hardest for.
- **Silent failures** — bare excepts, HTTP 200 treated as success, empty results logged as normal.
- **Wording drift** — "expected", "forecast" or "projected" creeping into labels where the honest
  word is "addressable".
- **Capture-rate integrity** — anything above 100%, and whether the denominator is defensible.
- **Backwards compatibility** — fields the existing dashboard reads that may have been renamed.
- **Precision claims** — where Cursor reports a lift, I will re-run the measurement independently.
