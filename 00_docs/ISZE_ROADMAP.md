# ISZE — programme roadmap (hub)

**Last updated:** 2026-08-26 · **Domain detail:** [`roadmaps/`](roadmaps/) · **Registry:** [`MAP_REGISTRY.yaml`](MAP_REGISTRY.yaml)

> **Numbers rule:** green [`01_data/00_derived/_verification_report.json`](../01_data/00_derived/_verification_report.json) → `metrics_snapshot.json` → [`FACTS.md`](../FACTS.md). That order wins over any deck, memory file, or GPT answer.
> **Pipeline state 2026-08-25:** verify **116 pass / 0 warn / 0 fail** · `sales_fact` billed through **2026-06-30** · SaTy coverage min 92% (Q1 hole documented).

**How to read this file**

| Section | Use it for |
|---|---|
| [1. Open queue](#1-open-queue) | What is actually being built next — the only list that is work |
| [2. Waiting on Jerome](#2-waiting-on-jerome) | Decisions, not effort. Nothing here moves without an answer |
| [3. Live now](#3-live-now) | What already runs, and where it lives |
| [4. Shipped](#4-shipped) | Dated ledger of what closed — one line each, rationale lives in `DECISIONS.md` |
| [5. Closed — do not reopen](#5-closed--do-not-reopen) | Dead ends. Re-proposing one of these costs credibility |
| [6. Domain roadmaps](#6-domain-roadmaps) | Depth per domain |

Rationale, evidence and numbers for every closed item live in [`DECISIONS.md`](../DECISIONS.md) (append-only, newest first) and [`CHANGELOG.md`](../CHANGELOG.md). This hub stays short on purpose — it is a queue, not an archive.

---

## 1. Open queue

Ordered. `Blocked on` names the single thing that unblocks the item — if it says *nothing*, it is buildable today.

| # | Item | State | Blocked on | Detail |
|---|------|-------|------------|--------|
| 1 | **P4 account-health calibration** (task 4.9) | Builder live `p4-v1`; draft thresholds fire on 10 RED / 6 AMBER of 17 DBs — not yet a call list | **Jerome** — amber/red thresholds (B5) | [`P4_DETERMINISTIC_SIGNALS.md`](P4_DETERMINISTIC_SIGNALS.md) |
| 2 | **List-to-pocket sign-off** | Validation ran 2026-08-19 (`list_to_pocket_validation_2023_2025.csv`); leakage € stays **Mode B** until year-matched PR00/ZPR1→net joins are signed in writing | **Jerome** — written sign-off | `DECISIONS.md` 2026-08-25 |
| 3 | **P5 forecast go-live (G1)** | P5.2 + P5.6 built — 548 series, median WAPE 49.4%, `pages/19_Forecast.py` live as a surface | **Jerome** — sign G1 on 98.2% catalogue (B6/D6) + override policy (B7/D4) | [`P5_FORECAST_BUILD_PLAN.md`](P5_FORECAST_BUILD_PLAN.md) |
| 4 | **National tender portal coverage** | **ES PLACSP LIVE 2026-09-14** (Atom OK, 2 keyword / 0 gated this window). IT PNCP + DE OV already LIVE 2026-08-25. National LIVE **17/29**. | nothing — next DARK without a human key (HU/IE/SE/SK; EE RHR still HTTP 500) | [`roadmaps/scrapers.md`](roadmaps/scrapers.md) · `_ES_PLACSP_LIVE_20260914.md` |
| 5 | **Interval-aware air vs oil capture** (integrity flag C) | Shipped 2026-07-02 on a **provisional 0.5 air factor** | IML ratio confirmation | [`roadmaps/gps.md`](roadmaps/gps.md) · PRISM `pms_capture_assumptions.yaml` |
| 6 | **ITUK brake wear factor — 0.4 or 0.8** | 0.4 in force and now actually applied (fix 2026-07-21). Do not quote ITUK brake capture as locked | ITUK data (expected since 2026-08-11) | `DECISIONS.md` 2026-07-21 |
| 7 | **LCV generation-aware interval split** | Schedules on disk: RG21 RZ4F-TC **with SCR** = 15k km, without / older = 20k | chassis + registration-year cutoffs — PDFs alone do not map UIO years to SCR vs non-SCR | `01_data/03_PMS/service_schedules/` |
| 8 | **Fig-key V2 remainder** | `parts_catalog_dimension` live at 98.9% coverage | nothing — bulk PN→fig key from SAP IE40 PR00 column, EPC basket rows, Part Explorer wiring | [`roadmaps/gps.md`](roadmaps/gps.md) |
| 9 | **Residual PR00 gaps** | 24 PN / €67k ZPR1-path hardware + admin non-PN + parked UMI Shell. Supersession billed-on-old 925 PN / €2.48M (IE40 map, **not** EPC-validated) | nothing — EPC validation is the next slice | [`roadmaps/ai_sales_intelligence.md`](roadmaps/ai_sales_intelligence.md) §6 |
| 10 | **P2b / P3 / P6 (LLM on mail text)** | Specced, zero code. P2a runs local and deterministic | **B1b** approved LLM route named, then **G0b** (DPIA, LIA, works council) | [`roadmaps/ai_sales_intelligence.md`](roadmaps/ai_sales_intelligence.md) §4 |
| 11 | **Supabase live Master KPIs** (HTML V4) | Not started | schema + credentials | [`roadmaps/html.md`](roadmaps/html.md) |
| 12 | **Dashboard filename renames** | Blocked by design — build scripts hardcode `vN` | rename plan in [`CANONICAL.md`](CANONICAL.md) | [`roadmaps/html.md`](roadmaps/html.md) |
| 13 | **Scraper quality V2** | Tender relevance scoring, `scrape_error` column, RSS parse failures (Israel entity, Belgium non-XML, UK 429), Lidl category id | nothing — small items | [`roadmaps/scrapers.md`](roadmaps/scrapers.md) |
| 14 | **Workspace cleanup decisions** | UI primary for external share; ISZE_Dashboard merge | **Jerome** | [`ISZE_Cleanup_Plan.md`](ISZE_Cleanup_Plan.md) |

**Not on this list on purpose:** anything in §5. Also: no new 0–100 score on any surface, and no Dash / Evidence work — Streamlit :8503 is the product.

---

## 2. Waiting on Jerome

One answer each. Build effort is already sunk or trivial; these are the actual bottleneck. Source: [`AFTERMARKET_BI_BUILD_MENU_20260819.md`](AFTERMARKET_BI_BUILD_MENU_20260819.md) Tier B + the AI-sales gates.

**One sitting (2026-09-14):** recommended ticks are in [`DECISION_PACK_20260914.md`](DECISION_PACK_20260914.md). Until a row is ticked, do not apply it in code. Same-pass engineering (Monday seed, tenders, fig-key/EPC, scraper quality) does not wait.

| Ref | Decision | Consequence of no answer |
|-----|----------|--------------------------|
| B1 | Book B **alloc** ambition — +4% / +5% / launch-only | Revision book stays a review list, never a price move |
| B2 | **Seed €** for 9,591 no-L12M PNs — IML BOM vs UTI placeholders | Those PNs stay out of every € ranking |
| B3 | **Growth-factor sign-off** — keep 1.24 / 1.25 / ×1.25 UTI table? | Forecast and alloc inherit an unsigned assumption |
| B4 | **Guardrail policy** — auto-HOLD on IAM-undercut + proxy-adverse? | Every exception is manual |
| B5 | **P4 calibration** — amber/red thresholds | Queue item 1 blocked |
| B6 / D6 | **G1** — sign 98.2% catalogue coverage, or wait for P1.4 / P1.5? | Queue item 3 blocked |
| B7 / D4 | **P5 override policy** — who may delta a forecast, audit trail | Forecast cannot go live even after G1 |
| B8 | **Book A +3% alloc** | Explicit rebuild only — no default |
| B9 | **ITUK brake wear factor** 0.4 vs 0.8 | Queue item 6 blocked |
| B10 | **Competitor vintage labels (Mode A)** | Mode A keeps mixed-vintage files unlabelled in the UI |
| B1b | **Approved LLM route** for company text (Cowork or other) | P2b / P3 / P6 die; P1 + P2a + P4 + P5 still run |
| B1c | Shared `Sales` / `Parts` mailboxes — works-council step | Mail corpus stays halved |
| B4-gov | DPO for ISZE, or via IML legal | P0 governance is 2 weeks or 8 |

**Never put back on a waiting list:** Nordics tender API keys. They are **DONE** (verify ALL OK, Doffin + HILMA healthy) — `DECISIONS.md` 2026-08-25.

---

## 3. Live now

### PRISM — Streamlit, port 8503 (canonical analytical surface)

Run: `03_analytics/Isuzu/prism/run_prism.ps1` (Mode-A safe) · `run_prism_internal.ps1` (internal shelf: leakage, attach, elasticity, scrape).

| Page | Capability | Primary data |
|------|-----------|--------------|
| `0_Early_Warning.py` | This-cycle call list | `early_warning.csv`, `defection_alerts.csv` |
| `1_UIO.py` | Parc | UIO v19 (DVLA-based), `06_uio/_CURRENT/` |
| `2_GPS.py` | GPS spend per unit | `gps_spu_by_distributor.csv` |
| `3_PMS.py` | PMS capture (registry + BVP catalogue) | `pms_capture_by_db_year.csv` |
| `4_BVP.py` | BVP mix | `mix_genuine_bvp_pms.csv` |
| `9_Review_Pack.py` | Review pack export | derived |
| `10_Data_Integrity.py` | Integrity audit | `mislabelled_sku_audit.csv` |
| `14_Tender_Pipeline.py` | Tender pipeline | `01_data/14_dashboards/tender_data.json` |
| `18_Decision_Models.py` | Waterfall, runway, defection, attach | `wallet_waterfall.csv` et al. |
| `19_Forecast.py` | P5 forecast surface (**pre-G1**) | `forecast_final_2026_08.csv` + `forecast_final.parquet` (gitignored) |
| `20_Warranty.py` | Warranty expense per DB / FY | `distributor_warranty_expense_fiscal.csv` |
| `21_Realization.py` | List→pocket + ZPR1 gap (**Mode B**) | `pr00_realization_*_cy.csv`, `zpr1_vs_pr00_by_payer_year.csv` |
| `22_Parc_Cohort.py` | JP cohort (not UIO v19) | `07_UIO/vin/VIN_register.csv` |
| `23_Dealer_Sellout.py` | Multi-DB sell-out mix + SPU | `sellout_aim_network_mix_2025.csv` |
| `24_VPACC.py` | FY2027 VPACC action plan (121 items) | `vpacc_fy2027_action_plan_july.parquet` |
| `network_intelligence.py` · `ituk.py` · `internal_shelf.py` · `tools_marketing_calendar.py` | IA phases 3–8 result (2026-08-20) | see `prism/docs/DASHBOARD_IA.md` §8 |

The AIM × GPS quadrant is now a tab inside `network_intelligence.py` (merged 2026-08-20; source archived to `pages/_archive/16_AIM_GPS_Matrix.py`), on `aim_gps_matrix.csv` with **GPS × PMS total capture** axes. The pricing-risk axis is gone (§5). Everything under `pages/_archive/` is retired — do not link it as live.

### Derived spine + ledger

| Surface | Where |
|---|---|
| Quantitative spine | `01_data/00_derived/` (alias `01_data/derived/` is an NTFS junction — prefer numbered paths) |
| **P8 Action Ledger** | `action_ledger*.parquet/csv` + `02_dashboards/ops/ISZE_Action_Ledger.html` — 23,236 opportunities, €22.1M **mixed-basis source cells, not one wallet** |
| Pipeline verify | `03_analytics/Isuzu/prism/scripts/run_pipeline_and_verify.ps1` |
| PMS assumptions (editable) | `prism/data/pms_capture_assumptions.yaml` |

### HTML (Mode A unless flagged)

`02_dashboards/` is the single source of truth; `07_deploy/` is generated. Build → `_build/ship_gate_check.ps1` → `sync_to_deploys.ps1`.

| Pack | File |
|---|---|
| Master hub | `hub/MASTER_DASHBOARD.html` |
| Aftermarket BI Command Center | `sales/ISZE_Aftermarket_BI_Command_Center.html` |
| DB→DLR replenishment | `sales/ISZE_DB_DLR_Replenishment_CY2025.html` |
| Pricing full analysis pack | `pricing/ISZE_Pricing_Full_Analysis_Pack.html` (integrity weak — internal QA) |
| Pricing history findings | `pricing/ISZE_Pricing_History_Findings_Dashboard.html` (**provisional**) |
| Static PRISM twins | `bi/` (4 self-contained snapshots) |
| OS data map | `ops/ISZE_OS_Data_Map.html` |
| IDS 2026 packs | `ids/` (v1.4 — Baumann MIDI average rule locked) |

Full inventory: [`roadmaps/html.md`](roadmaps/html.md).

### Automation

Live scheduled tasks and their SSOT: [`AUTOMATION_REGISTER.md`](AUTOMATION_REGISTER.md). Tender Monitor (Mon 07:30) and `ISZE_PMS_IAM_Refresh` (Mon 07:00) are the two ISZE-core jobs — do **not** import the spare refresh XML (double-run).

---

## 4. Shipped

Newest first. One line each; the reasoning is in `DECISIONS.md` under the same date.

| Date | Shipped |
|------|---------|
| 2026-08-25 | **P8 Action Ledger** — nine adapters → `action_ledger*.parquet/csv` + ops HTML; `BILLING_HORIZON` now reads `max(sales_fact.billing_date)` |
| 2026-08-25 | Overnight process audit — verify green 116/0/0, junctions restored, Nordics keys closed as an ask |
| 2026-08-25 | `sales_fact` extended with `Q1FY2027.XLSX` (Apr–Jun 2026); dealer sell-out CSVs re-emitted for 5 DBs |
| 2026-08-20 | **PRISM IA phases 3–8** — Network Intelligence merged (7 tabs), Mix absorbed DB-mix-split, ITUK hub, Tools re-cut, sources archived. 71 tests green |
| 2026-08-19 | **Aftermarket BI Tier A** — 14 of 15 builds done: P5.2 + P5.6 forecast, replenishment dashboard, Book B review, GREECE as 5th DB, supersession delta, list-to-pocket validation, account-health ops pack, portfolio triage, PMS BVP regain, pricing history pack |
| 2026-08-18 | PRISM `INTERNAL_MODE` launcher split (MD-safe default) + duplicate tabs dropped by cross-link |
| 2026-08-18 | `capture_trajectory` partial-year guard — 33 declining alerts → 5, zero real declines hidden |
| 2026-08-18 | P4 account-health builder `p4-v1` (draft flags, gitignored parquet — **not** a KPI) |
| 2026-08-12 | P2a interaction layer complete — 3 tables, 24-month run (9,490 interactions, 926 commitments, 203 stakeholders), local + deterministic under G0a |
| 2026-08-11 | **Dated price-list history** PR00 + ZPR1 2023/2024/2025 + current 2026 under `01_data/01_Pricing/history/` |
| 2026-08-11 | CY2026 AIM dashboard on billing only — dual CY + FY windows in `aim_billing_windows.json` |
| 2026-08-11 | Spec C4 SAP pull closed 220 PN / €4.36M of the no-PR00 gap — catalogue PR00 coverage **98.2%** (was €4.96M / 15.1% at 2026-08-01) |
| 2026-08-11 | IDS 2026 v1.4 packs — Baumann MIDI average rule applied |
| 2026-07-26 | Tender Monitor + competitive-pricing refresh confirmed live as scheduled tasks |
| 2026-07-21 | `country_overrides.factors` fixed on the bucketed PMS path — ITUK brake capture 58.3% → 72.8% at the configured 0.4 |
| 2026-07-16 | Front/rear brake split dropped from `wear_factor` — network capture CY2025 23.8% → 32.0% (phantom tripled denominator removed) |
| 2026-07-03 | FY2025 completeness (Jan–Mar 2026 wired) · CR/RE credit-note exclusion (flag H) · 2025 UIO V19 in capture |
| 2026-07-02 | SAP fig key on `sales_fact` via `parts_catalog_dimension` join (98.9% coverage) |

---

## 5. Closed — do not reopen

No new data, no new proposal. Each of these was tested and failed, or was answered by Jerome.

| Closed | Date | Why |
|--------|------|-----|
| **Gross / SPA / condition columns on the billing extract** | 2026-08-11 | Not available. `sales_fact` is **net-only forever**. Discount vs SPA vs mix cannot be decomposed from billing — design around net + dated lists. **Do not re-ask.** |
| **AIM pricing-risk as a decision surface** | 2026-07-17 · 2026-08-18 | 0.12 gate never fired; fitted replacements failed the 2024→2025 holdout; persistence ρ = 0.92 GPS / 0.75 PMS. No new 0–100 on any surface |
| `db_aftersales_risk` as the replacement | 2026-08-18 | Same genus — hand-weighted 0–100 on a mislabelled 44-PN file. Parked, not promoted |
| Fitted oil-filter service frequency | 2026-08-18 | Null. All-DB OLS wins MAE only by absorbing under-capture into λ. Flat bucketed constants stay |
| `price_volume_elasticity.csv` (ISZE→DB) | 2026-08-11 | Deferred — DB→DLR only. Resume when dealer sell-out coverage grows |
| Brake front/rear split categories | 2026-07-16 | Front/rear is not a unit of commercial action; the only market with real data replaces both in one job |
| **Nordics tender API keys** | 2026-08-25 | DONE — verify ALL OK, Doffin + HILMA healthy, NO/FI merged. Never put on a waiting-on-Jerome list again |
| Autodoc / Oscaro scraping | 2026-07-14 | Cloudflare Turnstile blocks 100% of requests. Frozen CSV kept |
| Auto365 as a PN price index | — | No OEM part-number join |
| Telematics / VIN usage as the next ask | — | Data we do not have |
| External "healthy capture %" (J.D. Power / NADA / DataMac) as an ISZE target | — | Three different metrics; none of them is ours |

---

## 6. Domain roadmaps

| Domain | File | Status |
|--------|------|--------|
| AIM + PRISM after scoring failed | [`roadmaps/aim_prism_reinvention.md`](roadmaps/aim_prism_reinvention.md) | **Active** — the programme after the score kill: P4, PN prices, Streamlit surface |
| AI sales intelligence (mail → action, account health, forecast) | [`roadmaps/ai_sales_intelligence.md`](roadmaps/ai_sales_intelligence.md) | **Active** — Track A running; Track B stops at B1b/G0b |
| Aftermarket BI execution menu | [`AFTERMARKET_BI_BUILD_MENU_20260819.md`](AFTERMARKET_BI_BUILD_MENU_20260819.md) | **Active** — Tier A 14/15 done; Tier B is §2 above |
| GPS / fig-key | [`roadmaps/gps.md`](roadmaps/gps.md) | V2 enrichment in PRISM; V3 scoring **superseded** |
| HTML dashboards | [`roadmaps/html.md`](roadmaps/html.md) | V3 overlay shipped; V4 Supabase blocked on credentials |
| Scrapers / tenders | [`roadmaps/scrapers.md`](roadmaps/scrapers.md) | Both core tasks live; national portal coverage is the open P0 |
| Jarvis / isze-tools | [`roadmaps/tools.md`](roadmaps/tools.md) | V2 data-out-of-code done; V2.2 onward unstarted |
| Specs feeding the queue | [`P4_DETERMINISTIC_SIGNALS.md`](P4_DETERMINISTIC_SIGNALS.md) · [`P5_FORECAST_BUILD_PLAN.md`](P5_FORECAST_BUILD_PLAN.md) · [`PROMPT_ACTION_LEDGER_P8.md`](PROMPT_ACTION_LEDGER_P8.md) | Build specs, not status |

---

## 7. Integrity and hygiene

- **Do not quote externally until closed:** `03_analytics/Isuzu/prism/docs/DATA_INTEGRITY_FLAGS_2026-05-28.md` — live priorities are interval-aware PMS (flag C, queue item 5) and returns confirmation (flag H, judgment call not ERP-confirmed).
- **Mode B only:** leakage / list-to-pocket euros, pricing history findings, action-ledger stakes. Mode A needs the §2 sign-off.
- **Language:** Mode A never uses internal nicknames or personal names — see `AGENTS.md` § External IML / meeting language.
- **Workspace cleanup:** open items in [`ISZE_Cleanup_Plan.md`](ISZE_Cleanup_Plan.md).
