# After AIM scoring failed — what we do instead

**Last updated:** 2026-08-18  
**Hub:** [`ISZE_ROADMAP.md`](../ISZE_ROADMAP.md)  
**Prompts:** [`AIM_PRISM_REINVENTION_PROMPTS.md`](../AIM_PRISM_REINVENTION_PROMPTS.md)  
**Decisions:** `DECISIONS.md` 2026-08-18 (Prompt 1 null · Prompt 2 surface + hazard null · capture-trajectory fix)

**Status:** both research prompts are answered. This file is the working programme. Do not invent a new 0–100.

---

## In English

The old AIM “strategic score / high-risk map” looked like a pricing engine. It was a hand label that almost never fired, and it never predicted who would get worse. We tried fitted replacements (competitor gaps, BVP mix, commodity mix). They also failed a year-holdout against GPS and total capture. Last year already explains this year.

So we stop trying to rank distributors with a pricing-risk score.

**What still works, and is the job:**

1. **Name the part** — AIM classification (family L1/L2/L3). Keep it; do not rebuild it.
2. **Who needs a call this cycle** — GPS (€ per truck) × PMS **total** capture, plus Early Warning. That already separates the network.
3. **Prices vs aftermarket** — on the **part**, with the real date on the file. Not rolled into a distributor traffic light.
4. **Who has gone quiet** — account-health from mail timestamps and promises (P4 spec). Different question, already specified. Not a pricing model.
5. **Expected demand** — keep the flat service-frequency for now. A fitted oil-filter curve failed the same honesty test: it would hide under-capture by calling it “lower frequency.”

PRISM the product is Streamlit on port 8503. The other two apps freeze. Collapsing twenty pages into ten is filing, not a new brain — do it only if you say so.

---

## Closed — do not reopen without new data

| Closed | Why | Where |
|--------|-----|--------|
| AIM pricing-risk as a decision surface | 0.12 gate never fired; fitted replacements failed 2024→2025 holdout; persistence ρ = 0.92 GPS / 0.75 PMS | `DECISIONS.md` 2026-07-17 and 2026-08-18 Prompt 1 |
| `db_aftersales_risk` as the replacement | Same genus: hand-weighted 0–100 on a mislabeled 44-PN file and `year.max()` | `scripts/build_db_aftersales_risk.py` — park, do not promote |
| Fitted oil-filter hazard vs flat 0.5 / 1.0 | Holdout either recodes the gap as lower λ or overfits | `DECISIONS.md` 2026-08-18 Prompt 2 · `prism/docs/pilot_oil_filter_hazard.md` |
| Partial-year “declining capture” cliff | 33 fake alerts → 5 real; scorecards inherit the fix | `capture_trajectory.csv` |
| Gross / SPA / condition on billing | Closed 2026-08-11 — net-only forever | `ISZE_ROADMAP.md` |
| Auto365 as a PN price index | No OEM part-number join | `AUTO365_PN_JOIN.md` |
| Telematics / VIN usage as the next ask | Data we do not have; out of scope | Prompt 2 constraint |
| External “healthy capture %” (J.D. Power / NADA / DataMac) as an ISZE target | Three different metrics; none is ours | Prompt 2 constraint |
| Wallet-share commercial scorecard | Sketch only; needs your steer; mailbox file needs G0b | `DECISIONS.md` 2026-08-18 §5 |

`gps.md` § V3 (AIM strategic scoring, opportunity engine, AIM×GPS as a *scoring* product) is **superseded by this file**. The quadrant stays; the score does not come back.

---

## Live instead of the score

| Need | Use this | Do not use |
|------|----------|------------|
| Parts taxonomy | `aim_pn_classification.csv` + classifier (untouched) | Strategic Score / Must Review as a rank |
| Distributor map | `pages/16_AIM_GPS_Matrix.py` — GPS × PMS **total** capture | `aim_high_risk_pct` as an axis (context column only) |
| This-cycle call list | `pages/0_Early_Warning.py` | A new risk 0–100 |
| Aftermarket prices | Part-Groups / aftermarket HTML, vintage labelled | Rolling KS/Eucon into a DB-year flag |
| Expected demand | Current PMS factors | Shipping a “fitted” λ from the oil-filter pilot |

---

## Sequence

Rebuild / ship of HTML or live pages still needs the words **rebuild** or **ship** in the asking message. This roadmap is the plan, not permission.

### 1 — Do now (no new model)

| # | Work | Gate | Benefit |
|---|------|------|---------|
| 1.1 | ✅ **INTERNAL_MODE launcher** — hide leakage / attach / elasticity / scrape unless `PRISM_INTERNAL=true`. `run_prism_internal.ps1` shipped 2026-08-18. | Done | You can open PRISM with a distributor in the room |
| 1.2 | ✅ **Park `db_aftersales_risk`** — page caption + builder docstring: unvalidated rubric, not a KPI | Done | Stops agents treating it as the AIM replacement |
| 1.3 | ✅ **Vintage on competitor files (builders)** — `eucon_price_gap.csv` labelled PartsPool Autodoc DE/NO **2026-03-29**, not “Eucon 2023”. Country packs not rebuilt. | Builder labels done; HTML/pack rebuild only when you ask | Stops a 2026 DE/NO scrape posing as a 2023 UK survey |
| 1.4 | **Optional tab trim** — drop the documented duplicates (Strategic “Most exposed” / “Basket correlation”, Insights “BVP × Capture”, BVP extra PMS/GPS/AIM tabs). Cross-link. | Your OK | Less hunting. Not the 7-tab Network Intelligence rewrite |

### 2 — Next real build: who has gone quiet (P4)

This is the Prompt 1 redirect: “who needs attention” without a fake price-risk score.

| # | Work | Gate | Notes |
|---|------|------|--------|
| 2.1 | ✅ **Build `account_health.parquet`** from existing P2a (2026-08-18). Draft NONE/AMBER/RED — not a KPI. | Done (builder). **Your 1-day threshold pass still open.** | Who went quiet, without a fake price-risk score |
| 2.2 | CC-depth — **not required**; `n_cc` already on `interaction_fact` | Closed for P4 | Escalation uses max CC per thread |
| 2.3 | Surface: internal CSV / PRISM widget **after** 2.1 is calibrated — not a Mode A pack until you say ship | Your OK after 4.9 | Mode A: no pipeline jargon |

Detail and task list stay in `00_docs/roadmaps/ai_sales_intelligence.md` §9. This roadmap only says: **P4 is now first in the AIM-replacement queue**, not a side quest.

### 3 — Competitor prices as an operating tool (PN grain)

| # | Work | Gate | Notes |
|---|------|------|--------|
| 3.1 | 2023 UK IAM survey → Part-Groups / aftermarket view, labelled **2023 workshop**, not 2026 sell-out | Rebuild/ship when you ask | 152 survey PNs exist in raw; derived gap file today is 34 |
| 3.2 | KS International: keep as the PN-indexed scrape. Expand only on the written proposal (UMI/Germany oil-air-fuel holes) | Your OK before any live scrape | `PROPOSAL_EUCON_AND_SCRAPER_EXPAND.md` |
| 3.3 | Mekonomen: do not treat as a filter index (0 filter-role hits) | — | Closed finding |
| 3.4 | TMC / Tranzparts / Auto365: category or no-PN — never a PN join | — | Closed |
| 3.5 | Fitted ISZE→DB elasticity | Still **not quotable**. Resume only as **DB→DLR** when dealer sell-out coverage exists | `price_volume_elasticity.csv` |

A future DB-year price-risk model is allowed only if it beats last-year persistence on a stated holdout. Face-valid weights are disqualifying. Default: **do not try again** until we have either more complete years or a real PN-indexed competitor panel that predates the outcome year.

### 4 — PRISM product (Prompt 2 remainder)

| # | Work | Gate | Notes |
|---|------|------|--------|
| 4.1 | Canonical surface = **Streamlit :8503** | Already decided | Freeze Dash :8050 and Evidence.dev — no second KPI spine |
| 4.2 | IA phases 3–8 (Network Intelligence merge, Mix trim, ITUK hub, Tools) | **Separate sign-off** | Valid filing; not the default next work. Prefer 1.1 + 1.4 |
| 4.3 | PMS frequencies | Do not change from the oil-filter pilot | Air-filter 0.5 still provisional; ITUK brake 0.4 vs 0.8 pending their data; LCV 15k vs 20k blocked on SCR mix |
| 4.4 | Wallet-share scorecard | Your explicit steer | GPS + PMS **total** + IDS (UTI≠UMI) + latency after G0b. Commercial terms, not a dashboard tab |

Track B email/LLM (P2b / P3 / P6) stays behind **G0b**. Out of this programme.

---

## Classification (keep, small leftover)

Do **not** touch `modules/aim_pn_classifier.py`. Residual unclassified is 1.6% / 1.8% (CY2024 / CY2025). The open ~€1.12M is a **human class call** on readable PNs (`aim_classification_gap_report.md`). Apply only via `aim_gap_suggestions_*.csv` with confidence ≥ 3, then rebuild classification — not a new engine.

---

## Kill rules (always on)

- No new weighted rubric presented as validated.
- No “this predicts X” without train/holdout and a baseline (flag nobody / last year / Δ = 0).
- No FACTS.md or live page without `run_pipeline_and_verify.ps1` green.
- No rebuild/ship without those words in the current message.
- No blending UTI into UMI / IDS Israel.
- PMS primary = **total** capture, not genuine-only.

---

## Reproduce

| Artefact | Path |
|----------|------|
| AIM scoring backtest | `03_analytics/Isuzu/prism/docs/AIM_PRICING_RISK_BACKTEST_2026-08-18.md` |
| Oil-filter hazard pilot | `03_analytics/Isuzu/prism/docs/pilot_oil_filter_hazard.md` |
| IA + surface | `03_analytics/Isuzu/prism/docs/DASHBOARD_IA.md` §7–§8 |
| P4 spec | `00_docs/P4_DETERMINISTIC_SIGNALS.md` |
