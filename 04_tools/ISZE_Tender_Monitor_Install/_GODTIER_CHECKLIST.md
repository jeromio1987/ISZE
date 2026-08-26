# God-tier checklist — ISZE Tender Engine

**Updated:** 2026-08-25 · **Tool:** `04_tools/ISZE_Tender_Monitor_Install/`  
**Rule:** PASS only with live evidence. WONTFIX needs a reason.

---

## PAPER

| # | Item | Status | Evidence |
|---|---|---|---|
| P1 | Single coherent operator story (what / how / limited / numbers) | **PASS (re-scored)** | `00_EXEC_ONE_PAGER.html` + `OPERATOR_INDEX.md` + `01_OPERATOR_RUNBOOK.md` (deep audit: `_PAPER_DEEP_REVIEW.md`) |
| P2 | SETUP matches code (no “paste key into .py”) | PASS | SETUP points to `nordics_api_keys.env` / `NORDICS_API_KEYS.md`; scraper uses `nordics_keys.py` |
| P3 | Relevance / release notes match *live* headline figures | **PARTIAL** | Live = **211/186** · GPS **€1,488** / 3 sized; older notes still cite 193/172 · €30,410 as if current — treat those as historical |
| P4 | `CURSOR_PROMPTS_v4_engine.md` status not stuck on PROPOSAL if shipped | PASS | Status **SHIPPED** |

## ENGINE

| # | Item | Status | Evidence |
|---|---|---|---|
| E1 | GPS addressable = fleet × (max_spend/uio); capture = fleet × actual SPU; product-fit gate | PASS | Live GPS sum **€1,488.22** on **3** truck-sized rows |
| E2 | Headline shows GPS floor + known contract value; nulls honest | PASS | `renderHeadline()`; missing values as — |
| E3 | Selection net Isuzu-fit (cut SEND/passenger, CPV 60…, demote generic car R&M) | PASS | Live **211/186**; CPV60=0; BEL/ISR national OK |
| E4 | Source health loud; AWAITING_KEY / RETIRED not fake BROKEN | PASS | Banner + `_source_health.json` (Nordics AWAITING_KEY; DTVP/RSS RETIRED) |
| E5 | Outcome dropdown REMOVED from v4 UI | PASS | No `STATUS_OPTS` / `setOutcomeStatus` in built HTML |
| E6 | Dashboard opens offline, light-only, contrast OK | PASS | Embedded DATA; light navy/paper |
| E7 | v2 dashboard still works (backwards-compatible fields) | PASS | `build_dashboard_v2.py` still builds |
| E8 | No capture > 100%; no keys in git | PASS | capture>1 count 0; keys only via env/example |
| E9 | No “expected revenue” / forecast wording for GPS | PASS | Addressable-if-won copy |

## Counts (live vs historical)

| Metric | Pre-gate | After Isuzu gate | **Live (product-fit + BEL/ISR)** |
|---|---:|---:|---:|
| Notices | 773 | 193 | **211** |
| Opportunities | 679 | 172 | **186** |
| GPS-sized | 11 | 6 | **3** |
| CPV `60000000` | 54 | 0 | 0 |
| Addressable GPS € / yr (sized) | ~5,915 (actual-SPU bug) | 30,410 (max wallet, vans included) | **€1,488** (pickup/truck only) |

Snapshot: `isze_dashboard_v4_data.json` · 2026-08-25.

## WONTFIX

| Item | Reason |
|---|---|
| Fit/Win/Econ weight retune (UK Attack=0) | Explicitly out of scope; prefer filter gate |
| Invent GPS for FR/PL/ES without SPU rows | Hard rule: null not 0 |
| Full re-scrape this session | Gate applied on live xlsx; next `run_tender_monitor.bat` writes gated sheets |

## Loop status

- Pass 1 inventory: **done**
- Pass 2 engine: **done** (product-fit + health honesty landed after first checklist)
- Pass 3 paper: **re-opened 2026-08-25** — `_PAPER_DEEP_REVIEW.md`; exec one-pager shipped; phase pile still at root (archive move deferred)
- Pass 4 re-measure: **partial** — live GPS/health aligned in hub + one-pager; release-notes endpoint table still historical

## Deliver paths

- Checklist: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_GODTIER_CHECKLIST.md`
- Open v4: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\OPEN_isze_dashboard_v4_opportunity.cmd`
- Nordics env example: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\nordics_api_keys.env.example`
