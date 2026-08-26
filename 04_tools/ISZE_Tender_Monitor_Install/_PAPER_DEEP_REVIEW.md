# Paper deep review — ISZE Tender Engine

**Date:** 2026-08-25  
**Scope:** Documentation / narrative pack only (not an engine refactor).  
**Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Live snapshot used for truth:** `isze_dashboard_v4_data.json` generated `2026-08-25T16:15:49Z` · `_source_health.json` same day.

**Question answered:** Is the paper pack god-tier, and what must change so a manager can follow one story in five minutes?

**IDS dealer module (Jerome item 1):** **DONE — engine + paper.**  
`ids_dealer_linkage.py` wired into `gps_pms_linkage` / v4 rebuild. Facts: `_IDS_DEALER_MODULE.md` · hub link in `OPERATOR_INDEX.md` · real-field note on `00_EXEC_ONE_PAGER.html`. Live: 519 IDS dealers · 113/186 opps with dealer · DE dealer-unmapped (no DE tab). GPS floor unchanged **€1,488** / 3 sized / 211 / 186 · Nordics **AWAITING_KEY**.

---

## A. Inventory

| File | Purpose | Audience | Freshness vs live engine |
|---|---|---|---|
| `OPERATOR_INDEX.md` | Front door: what / how / broken / numbers | Jerome | **STALE** on source statuses (still says BE RSS / DTVP / Nordics **BROKEN**) |
| `SETUP.txt` | Install + run + key rules | Jerome / eng | **PARTLY STALE** — Nordics still “BROKEN / key not set”; BE SPA listed as if primary national is dead (SEA is OK) |
| `NORDICS_API_KEYS.md` | Register Doffin/HILMA | Jerome | **ALIGNED** |
| `_NORDICS_BLOCKED.md` | One Jerome action for keys | Jerome | **ALIGNED** (AWAITING_KEY, empty env) |
| `_OPEN_BACKLOG_ARRANGED.md` | P0–P4 status board | Jerome / eng | **ALIGNED** (P0 BLOCKED; P1–P2 DONE; snapshot €1,488) |
| `_GODTIER_CHECKLIST.md` | PASS/FAIL quality bar | Eng / SteerCo | **STALE figures** — still 193/172 notices/opps and €30,410 GPS; paper P1 claims PASS prematurely |
| `_V4_RELEASE_NOTES.md` | What shipped in v4 | Eng / SteerCo | **STALE endpoint** — stops at pre–product-fit €30,410; no van-gate chapter |
| `_ISUZU_RELEVANCE_AUDIT.md` | Selection-net diagnosis | Eng | **STALE counts** (193/172); still “Belgium national BROKEN” |
| `_PRODUCT_FIT_GATE.md` | Van/LCV ≠ GPS € | Jerome / eng | **ALIGNED** (€1,488 · 3 sized · segments) |
| `_WHY_UNSIZED_GPS.md` | Why GPS cells empty | Jerome / SteerCo | **PARTLY STALE** — still “6 GPS-sized”; live is **3** after product-fit |
| `_WHY_MARKET_TABLE_EMPTY.md` | Why By-market looked empty | Jerome | **ALIGNED** (honest null reasons + chips) |
| `_MARKET_COVERAGE_DARK_MAP.md` | 35–55% coverage story | Jerome / SteerCo | **MOSTLY ALIGNED** counts; **STALE** Nordics row still says BROKEN / keys file missing; chip section says “not patched” but chip **is** in v4 HTML |
| `_SOURCE_HEALTH_FIX.md` | RETIRED / AWAITING_KEY honesty | Eng | **ALIGNED** |
| `CURSOR_PROMPTS_v4_engine.md` | Design pack (phases 0–6) | Eng | Status **SHIPPED** OK; **§2 body still cites 778→680** as “current” |
| `CURSOR_WORKFILE_tender_monitor.md` | Early phase workfile | Eng | **ARCHIVE** — acceptance still “IL/BE BROKEN” |
| `CURSOR_TASK_fix_dark_markets.md` | Dark-market task brief | Eng | **ARCHIVE** — IL/BE largely fixed; revenue table is briefing context, not live notice counts |
| `_AUDIT_v3_baseline.md` | Phase 0 baseline | Eng | **ARCHIVE** (correct for 24 Aug baseline) |
| `_phase1_endpoint_discovery.md` | Portal discovery | Eng | **ARCHIVE** |
| `_phase1_coverage_cpv_assessment.md` | CPV widen recommendations | Eng | **ARCHIVE** (50114000 noted as added) |
| `_phase1_il_be_implementation.md` | BE SEA + IL mr.gov.il wire-up | Eng | **ARCHIVE** — health labels pre-RETIRED rename |
| `_phase1_il_be_merge.md` | BEL/ISR merge counts | Eng | **ARCHIVE as current** — GPS floor frozen at **€30,410** (pre product-fit) |
| `_phase2_extraction_report.md` | Fleet/deadline/value fill rates | Eng | **ARCHIVE** (pre-gate 773-notice base) |
| `_coverage_chip_snippet.html` | KPI chip paste source | Eng | Living reference; **already integrated** in v4 |
| `_PAPER_DEEP_REVIEW.md` | This review | Jerome | Living |
| `_IDS_DEALER_MODULE.md` | Dealer/MAP story | Jerome / eng | **ALIGNED** — 519 dealers; RO/DE examples; match methods |

**Not paper (ignore for narrative):** probe scripts, `.xlsx`, `.json` dumps, `.bak`, bat/ps1, scraper/core Python.

---

## B. Truth audit vs live engine

### Live figures (authoritative)

| Metric | Live |
|---|---:|
| Notices / opportunities | **211 / 186** |
| Selective / Watch / Ignore | **9 / 35* / 142** (*meta decision_counts may show Watch 36 — family vs notice edge; use opp list) |
| With fleet count | **13** |
| GPS-sized (pickup/truck + map) | **3** · sum **€1,488.22** / yr |
| Segments | truck 70 · pickup 40 · lcv_van 41 · weak 30 · rm_only 5 |
| BEL / ISR in source_counts | BE **9** · Israel **9** (national) |
| Nordics | Doffin + HILMA **`AWAITING_KEY`** (env empty) |
| DE DTVP / BE RSS / IL RSS | **`RETIRED`** |
| DE service.bund | **OK** (12) |
| Coverage band (paper estimate) | **~35–55%** Medium — not a measured KPI |
| Outcome dropdown in v4 HTML | **Absent** (`STATUS_OPTS` / `setOutcomeStatus` not in HTML) |

GPS sized rows today: DE Solingen €742.93 · DE Passau €495.29 · RO Bacau €250.00 — all `truck`.

### Contradictions (docs vs live)

| Claim still in paper | Where | Live truth | Severity |
|---|---|---|---|
| Addressable GPS **€30,410** / 6 sized as *current* | `_GODTIER_CHECKLIST`, `_V4_RELEASE_NOTES`, `_phase1_il_be_merge`, relevance audit GPS section | **€1,488.22** / **3** sized after product-fit | **HIGH** — commercial misread |
| Notices/opps **193 / 172** as current | Checklist, release notes, relevance audit | **211 / 186** (post BEL/ISR Hebrew keep) | **HIGH** |
| Nordics / DTVP / BE RSS = **BROKEN** | `OPERATOR_INDEX`, `SETUP.txt`, parts of dark map | **AWAITING_KEY** / **RETIRED** | **HIGH** — wrong ops signal |
| Belgium national “still BROKEN”; SPA as if only BE path | SETUP, OPERATOR_INDEX, relevance audit | **Belgium publicprocurement.be OK (14)**; RSS RETIRED | **HIGH** |
| “6 GPS-sized” / unsized narrative as if max-wallet vans still count | `_WHY_UNSIZED_GPS.md` opener | Product-fit strips van GPS; sized = **3** | **MED** |
| Dark map: keys file **missing**; chip “not patched” | `_MARKET_COVERAGE_DARK_MAP.md` §§2 & 5 | Env **exists** (empty); chip **in** v4 HTML | **MED** |
| Checklist paper P1 **PASS** (“single coherent story”) | `_GODTIER_CHECKLIST` | Pile of phase notes + stale headlines | **MED** (grade inflation) |
| CURSOR_PROMPTS §2 “Current run: 778→680” | Design pack body | Superseded thrice | **LOW** if readers only see SHIPPED header |
| €5,915 as bug / paste key into `.py` / outcome dropdowns | Historical in release notes / checklist *as fixed* | Correctly fixed — **do not revive** | OK if labeled historical |
| Unsized “175” as live KPI | Not found as current operator claim | Live no-fleet **173** of 186 | N/A — no active contradiction |

### What is *not* a contradiction

- €30,410 and €5,915 as **historical** before/after maths (actual SPU bug → max wallet → van product-fit) — fine in a dated changelog, wrong as today’s headline.
- Coverage **35–55%** as a Medium-confidence band — consistent across dark map + KPI tip; not inventing a single %.
- “No expected revenue” / null ≠ 0 — consistent across SETUP, product-fit, unsized, dark map.

---

## C. Narrative quality

**Is there ONE coherent story a manager can follow in 5 minutes?**  
**No.** There is a strong *set* of method notes written the same day, but the front door (`OPERATOR_INDEX` + checklist + release notes) still sells yesterday’s headline (€30k GPS, BROKEN Nordics/BE) while the best truth lives in later files (`_PRODUCT_FIT_GATE`, `_WHY_MARKET_TABLE_EMPTY`, `_OPEN_BACKLOG_ARRANGED`, dark map).

| Dimension | Grade | Note |
|---|---|---|
| **Structure** | **D+** | Chronological phase dump + parallel agent notes; no numbered SteerCo path until this review’s proposed tree |
| **Clarity** | **B−** | Individual explainers (unsized, product-fit, market empty) are plain and good; front door contradicts them |
| **Commercial usefulness** | **C+** | Operator can run the bat and open v4; manager cannot trust the € headline without reading three more docs |
| **SteerCo-readiness** | **C+** (improving) | Exec one-pager + hub live; IDS dealer facts linked; remaining gap = glossary polish / archive move |

Best single “method” pages today: `_PRODUCT_FIT_GATE.md`, `_WHY_UNSIZED_GPS.md`, `_MARKET_COVERAGE_DARK_MAP.md`, `_WHY_MARKET_TABLE_EMPTY.md`.  
Worst as *current truth*: `_GODTIER_CHECKLIST.md` counts block, `_V4_RELEASE_NOTES.md` endpoint table, `OPERATOR_INDEX` “broken” list.

---

## D. Gaps for “god-tier paper”

| Missing artefact | Why it matters |
|---|---|
| **Executive one-pager** (HTML or MD) | Five-minute path: what it is, live counts, GPS floor €1,488, coverage band, one ask (Nordics keys) |
| **Glossary** | Notice vs opportunity · GPS floor vs contract value · sized vs unsized · product segment · AWAITING_KEY vs BROKEN vs RETIRED · lead vs GPS € |
| **One before→after table** spanning v3 → gate → product-fit (not three partial tables in three files) |
| **Definition of “real Isuzu market €”** vs lead count | Explicit: GPS € = pickup/truck wallet floor on sized rows only; lead count = gate-passing opps; neither is network revenue |
| **Asks block** | Nordics keys (P0); accept DE TED-only; optional TED detail / FR-PL portals (backlog) |
| **IDS dealer story** | **DONE** — `_IDS_DEALER_MODULE.md` + v4 Dealer/IDS column (real rankings only) |
| **Freshness banner** | Every living doc needs “snapshot date + figures” or “historical” label |

---

## E. Recommended paper architecture

```
ISZE_Tender_Monitor_Install/
  OPERATOR_INDEX.md              ← hub (link only; keep short)
  00_EXEC_ONE_PAGER.html         ← SteerCo / Jerome 5-min
  OPEN_00_EXEC_ONE_PAGER.cmd
  01_OPERATOR_RUNBOOK.md         ← run / keys / open dashboard
  02_METHOD_GPS_PRODUCT_FIT.md   ← pointers + frozen definitions
  03_COVERAGE_DARK_MAP.md        ← pointer to living dark map + backlog
  _PAPER_DEEP_REVIEW.md          ← this audit
  _OPEN_BACKLOG_ARRANGED.md      ← living eng status
  _NORDICS_BLOCKED.md            ← single ask until P0 clears
  NORDICS_API_KEYS.md
  SETUP.txt                      ← keep as install detail; runbook summarizes
  _PRODUCT_FIT_GATE.md           ← living method (canonical)
  _WHY_UNSIZED_GPS.md            ← living method
  _WHY_MARKET_TABLE_EMPTY.md     ← living UX honesty
  _MARKET_COVERAGE_DARK_MAP.md   ← living coverage
  _SOURCE_HEALTH_FIX.md          ← living health model
  _V4_RELEASE_NOTES.md           ← update endpoint OR move old table to archive note
  _GODTIER_CHECKLIST.md          ← re-measure against live before claiming PASS
  _paper_archive/                ← phase notes, workfiles, baseline audit
```

| Action | Files |
|---|---|
| **Keep (living)** | OPERATOR_INDEX, SETUP, NORDICS_*, product-fit, unsized, market-empty, dark map, source-health fix, backlog, Nordics blocked |
| **Merge into runbook/hub** | Duplicate “how to run” between SETUP and OPERATOR_INDEX — runbook owns ops; SETUP stays install |
| **Archive** | `_AUDIT_v3_baseline`, all `_phase1_*`, `_phase2_*`, `CURSOR_WORKFILE_*`, `CURSOR_TASK_fix_dark_markets` |
| **Keep but label SHIPPED/history** | `CURSOR_PROMPTS_v4_engine.md` (do not delete — design authority) |
| **Rewrite counts** | Checklist, release-notes endpoint, OPERATOR_INDEX broken list, WHY_UNSIZED opener, dark-map Nordics/chip notes |
| **Do not invent** | Dealers outside IDS rankings / DE tab; GPS € for vans; Nordics counts while AWAITING_KEY |

**Implement this turn:** `00_EXEC_ONE_PAGER.html` + numbered front docs (`01`–`03`) + hub refresh (`OPERATOR_INDEX`, `SETUP`, checklist counts, unsized opener). **Archive move deferred** (auto-review blocked relocating historical `_phase*` / workfiles) — treat those files as historical by convention; do not use them as current headlines.

---

## F. Straight verdict for Jerome

### Is the paper god-tier?
**No.**

Method depth is strong (product-fit, unsized honesty, coverage band, market null reasons). SteerCo packaging is not: front-door figures and source labels lag the live engine by one product-fit generation, and there is no single five-minute story.

### Top 5 paper fixes (ranked)

1. **Freeze one live headline table** (211 / 186 · GPS €1,488 / 3 · AWAITING_KEY Nordics) on exec one-pager + OPERATOR_INDEX — kill €30,410 as “current.”
2. **Rename health language** everywhere operators look: RETIRED / AWAITING_KEY ≠ BROKEN; BE SEA / IL mr.gov.il = OK.
3. **One before→after** table: v3 noise → Isuzu gate → product-fit GPS strip → coverage band.
4. **Archive phase pile** so managers never open `_phase1_il_be_merge` as today’s truth.
5. **IDS dealer facts linked** (hub + one-pager + `_IDS_DEALER_MODULE.md`) — re-score checklist paper P1 after glossary if still open.

### Engine vs paper

| Side | What |
|---|---|
| **Engine-side (live code)** | IDS dealer ↔ MAP (**shipped**); Nordics scrape once keys pasted; TED detail / FR–PL backlog code; market reason chips (shipped); product-fit GPS gate (shipped); source-health RETIRED/AWAITING_KEY (shipped) |
| **Paper-side (this review)** | Narrative coherence, stale figure purge, exec one-pager, archive, glossary, SteerCo path — **not** another scraper refactor |

---

## Evidence paths

- Review: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_PAPER_DEEP_REVIEW.md`
- Live JSON: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isze_dashboard_v4_data.json`
- Health: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_source_health.json`
- Open v4: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\OPEN_isze_dashboard_v4_opportunity.cmd`
