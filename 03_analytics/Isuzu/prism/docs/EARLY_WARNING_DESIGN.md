# Early Warning — one ops page, one priority list

**Status: BUILT and live, 2026-07-17.** `scripts/build_early_warning.py` → `pages/0_Early_Warning.py`, registered as its own top nav section above Fleet, chained into `run_pipeline_and_verify.ps1`. Companion to DASHBOARD_IA.md §4.2 — supersedes the planned Network Intelligence tab 1 "Most exposed".

## What the data forced us to change (found during build, all verified)

Three corrections that the paper design did not anticipate. Each one was killing or manufacturing alarms:

1. **`capture_trajectory.csv` / Strategic "Capture trend" is contaminated — 83% false alarms.** `modules/strategic_build.build_capture_trajectory()` regresses over every year in `pms_capture_by_db.csv` including the current **partial** year. Q1-only billing reads as a cliff (network median capture 2026 = 0.019 vs 0.094 in 2025). Measured: **35 declining alerts with 2026 in, 6 with it out; 29 of 35 are artifacts and 0 real declines are hidden.** Early Warning recomputes the slope itself with a partial-year guard. **The Strategic tab and the CSV still carry the contaminated flag — separate fix, not done here.**
2. **A declining category can still be over-capturing — the level gate.** 4.9% of DB×category×year rows have capture > 1.0 (max 3.03) with a flat `expected_qty`, i.e. the demand model under-predicts. ITUK brake_rotor runs 2.20 → 2.19 → 1.98: a −11pp/yr "decline" while still buying **198% of modelled demand**. Ungated it headlined this page at €313K. Alarms now require latest complete-year capture ≤ 100%; over-ceiling declines are suppressed and counted in the build log. Network exposure €605K → **€307K**.
3. **Silence ≠ defection when the category is dead.** 8 of 25 defection alerts are categories silent 13–33 months with €0 trailing revenue — never really bought, not walking away. Classed `dormant` and ranked below every live alarm.

Also: `trend_slope_pp_per_year` is a **misnomer** — the values are fractions/yr, not pp. `triple_threat` has no CSV (computed live in `strategic_charts.py`); `vor_airfreight.csv` is wired in `bvp_dashboard_data.py` but **missing on disk**. TURKEY is present in `db_aftersales_risk.csv` despite not being a distributor — excluded here.

## 0 · Problem

Risk signal is scattered across three destinations: Decision Models → Defection (silence alarms), Strategic (triple threat, VOR seasonality/profile, airfreight, geo risk — 15 tabs), and 15_Customer_Risk (weighted index, 5 tabs). Ops has to tab-hop and mentally join. Nothing answers "who do I act on, and why, this cycle?"

## 1 · The three signals that drive action (and why the others don't)

An action signal must (a) change between refreshes, (b) name a concrete move, (c) attach a €. Three qualify:

| # | Signal | Source (exists today) | Concrete move | Grain / freshness |
|---|---|---|---|---|
| 1 | **Silence** — order rhythm broken | `defection_alerts.csv` (`silent_months` vs `median_gap_months`, `trailing_12m_rev_eur`, `alert`) | Call the distributor/dealer about the silent category | entity × pms_category, monthly (vs `data_horizon`) |
| 2 | **Capture slope** — bleeding in motion | `capture_trajectory.csv` (`trend_slope_pp_per_year`, `trend_r2`, `alert_declining`) | Commercial intervention on the named category (pricing/PMS push) | DB × category, annual points but slope updates every refresh |
| 3 | **VOR stress** — availability burning trust now | `vor_seasonality.csv` (weekly `vor_pct`) + `vor_profile.csv` (`vs_network_pp`) | Supply-side fix; pre-position stock before the seasonal spike | DB × week — the only weekly-grain signal we have |

**Demoted to context (vanity as alarms):**
- **Concentration** (Gini/top-10) — structural, near-static; no "this week" move follows from a high Gini. Becomes a context column, not a row-generator.
- **Price exposure** (Eucon undercut %, AIM high-risk %) — changes only when the scraper refreshes; it's a *multiplier* on how bad silence/capture-drop is, not an alarm itself. The Customer Risk `risk_score` survives as the exposure weight.

Silence is the leading indicator, capture slope the confirming one, VOR the cause we can actually fix ourselves. Price exposure explains *why* they defect; it doesn't tell you *that* they are defecting — that's what the first two do.

## 2 · Page design

One page (or NI tab 1): **Early Warning**. No chart tabs. Three blocks:

### 2.1 Priority list (the page IS this table)
Rows = distributor; ITUK expands to dealer rows where `defection_alerts` carries dealer-level entities (check `level` column; `dealer_leakage_ituk.csv` stays out — relative-mix hint, not an alarm).

| Col | Content |
|---|---|
| Priority | rank by `alarm_severity × € exposure` (below) |
| Entity | DB code (▸ expand ITUK dealers) |
| **Why this cycle** | generated reason string from fired signals, e.g. *"brake silent 4 mo (median 1.3) · lubricants capture −5pp/yr (r² .81) · VOR 2.1× own baseline wk 24–27"* — rule-based concat of the firing rows, no free text |
| € at stake | `trailing_12m_rev_eur` of silent categories + declining-category revenue. Never the inferred-leakage € (internal-shelf rule holds) |
| Signals | ● silence ● capture ● VOR chips, ok/watch/act |
| Context | Customer-Risk score · top-10 rev share (small, grey — informs, never sorts) |

Scoring: each signal → 0 ok / 1 watch / 2 act. **As-built thresholds** (all in `build_early_warning.py`, calibrated on the real distribution rather than assumed):

| Signal | act | watch |
|---|---|---|
| Silence | `alert` ∧ trailing-12m rev > 0 | `alert` ∧ rev = 0 (→ `dormant` if also silent > 12 mo) |
| Capture | slope ≤ −0.05/yr ∧ r² ≥ 0.5 ∧ **latest capture ≤ 100%** | slope ≤ −0.02/yr ∧ r² ≥ 0.4 ∧ same gate |
| VOR | Δ ≥ +10pp **and** ≥ 1.25× own baseline | Δ ≥ +5pp and ≥ 1.15× |

VOR needs **both** a pp delta and a ratio: DBs near a 100% VOR ceiling (GREECE .70, ICELAND 1.00, ROMANIA .98 baseline) move large pp on trivial relative change, while UTI doubling .11 → .24 is a real regime shift worth only +13pp. Either test alone fires on the wrong half. Windows are order-count-weighted (median 95 orders/DB-week; only 3.7% under 10), so a thin week cannot swing the read; recent window needs ≥ 20 orders. At these gates **3 of 21 DBs act, 2 watch** on VOR.

Ranking: live before dormant, then severity, then **€ exposed, then corroboration**. Money outranks agreement deliberately — two signals agreeing on a €551 category is not a bigger ops problem than one hard signal on €80K. € is summed over *distinct categories* (max per category), so a category firing two signals cannot double-count.

### 2.2 Row drill-down (expander, not tabs)
Three sparkline strips per entity: order-rhythm heat by category (last-order month) · capture trend line · weekly VOR %. All from the same CSVs, no new math.

### 2.3 Export
`st.download_button` → `ISZE_Early_Warning_<horizon>.csv` = the list incl. reason strings. That is the whole "alerting stack" for v1.

Honesty banner (mandatory): "Signals measured against data horizon <YYYY-MM>, not today — 'this week' means 'this refresh cycle'. Silence horizon per defection_alerts. Wallet/capture ceilings are GPS max-spend, not forecasts."

## 3 · Strategic tabs — drop / demote (beyond DASHBOARD_IA kills)

| Strategic tab | Verdict | Rationale |
|---|---|---|
| Most exposed (triple threat) | **absorbed** | Its three axes are exactly signals 2/3 + exposure; the scatter becomes the drill-down, the list replaces the eyeballing |
| Stockout seasonality · Stockout profile · Airfreight cost | **demote to drill-down** | 3 tabs → 1 sparkline + € column; airfreight € shows in "€ at stake" tooltip |
| Capture trend | **absorbed** (signal 2) | |
| Network ranking (percentile radar) | **drop** | vanity ranking; no move follows |
| Geographic risk | **drop** | static map restating the DB list |
| Revenue concentration (Gini) | **demote to context column** | |
| Revenue bridge · Part lifecycle · Basket correlation (already killed in IA) | **drop from ops path** | annual-review material, not weekly ops; bridge stays reachable in Review Pack |
| PMS opportunity (€) · Capture recovery | stay in NI tab 2 (Opportunity €) | opportunity ≠ warning; different question |
| Price vs aftermarket · Substitution · Price premium | stay in NI tabs 5/6 | explanatory, feeds risk_score weight |

Net: Strategic's 15 tabs contribute 0 standalone tabs to the ops path. Customer Risk page deregisters (Ranking/Breakdown/Map → this page; Aftermarket scrape → internal shelf per IA). Decision Models loses the Defection tab → here; Waterfall/Runway stay MD-side.

## 4 · As built

| Piece | Status |
|---|---|
| `scripts/build_early_warning.py` | ✅ → `early_warning.csv` (19 entities) + `early_warning_signals.csv` (47 fired signals) |
| `pages/0_Early_Warning.py` | ✅ list + drill-down + 2 CSV exports |
| `app.py` nav | ✅ own "Early Warning" section above Fleet (20 modules) |
| `run_pipeline_and_verify.ps1` | ✅ chained after `build_defection_alerts`, before `build_metrics_snapshot` |
| Verification | ✅ AppTest 0 exceptions across all 10 entity drill-downs incl. dealer + dormant; real-browser render confirmed (nav, both Plotly charts, integer year ticks) |

**Current read (horizon 2026-03):** 11 act · 6 watch · 2 dormant · **€307K exposed**. Top: UTI (capture −5.3pp/yr to 33% on €80K **and** VOR 24% vs 11% own baseline — two independent signals agreeing), then UMI €48K, IRELAND €27K. DENMARK is the only 3-signal entity.

**Not done — deliberately left for a decision:** deregistering `15_Customer_Risk`, the Strategic tabs per §3, and Decision→Defection. Building the one page is additive; removing established destinations has blast radius (other pages/docs link them) and is the IA's later phase. The new page does not depend on their removal.

**Separate bug worth its own change:** the partial-year contamination in `build_capture_trajectory()` (finding 1 above) still affects `capture_trajectory.csv` and the Strategic "Capture trend" tab.

## 5 · Acceptance

Ops opens **one** page. Every alarm previously found via Strategic tab-hopping + Defection tab + Customer Risk page is a row here with a reason and a €. CSV export replaces any external alerting for v1.
