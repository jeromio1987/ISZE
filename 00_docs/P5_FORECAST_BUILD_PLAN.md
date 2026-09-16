# P5 — Deterministic Forecast (no LLM, no gates)

**What you get:** monthly reconciled demand forecast by DB × category, with override audit trail. Deterministic only (ETS/auto-ARIMA). No model judgment.

**What you don't get:** revenue-at-risk scoring (that needs LLM + shared mailbox = blocked). Sentiment analysis (blocked). Intent classification (blocked).

**Timeline:** 3 weeks.

**Blockers:** zero. Builds from P1 (PN coverage ✅ 98.2%) + existing sales_fact + UIO parc data.

---

## 1. Inputs

| Source | What | Status | Path |
|---|---|---|---|
| sales_fact | billing history by DB × PN × month | ✅ Live | `01_data/04_sales/` + PRISM loader |
| parts_catalog_dimension | active part numbers | ✅ Live | derived |
| UIO v19 | parc by fleet/model | ✅ Live | `06_uio/_CURRENT/` |
| P1 coverage | part → category mapping | ✅ Done | `01_data/01_Pricing/pn_coverage_classification.csv` |
| P2a commitment_fact | promised delivery dates (weak signal) | ✅ Live | `01_data/17_interactions/commitment_fact.parquet` |

---

## 2. Build phases

### Phase 5.1 — Series construction (1 week)

**Input:** sales_fact aggregated to (db_code, category, month)

**Output:** `demand_series.parquet` — one row per DB × category × month, with:
- `units_sold` (count of line items)
- `revenue` (billed)
- `first_seen` / `last_seen` (activity window per series)
- `sparse_flag` (< 3 non-zero months = sparse, needs special handling)

**Method:** deterministic aggregation + sparsity detection. No model yet.

**Intermittency handling:** Croston's method for sparse series (where demand is bursty). Split into demand size vs. demand frequency, forecast both, recombine.

---

### Phase 5.2 — Baseline models (1 week)

**For each series:**

1. **Trend + seasonality** (ETS — exponential smoothing)
   - Auto-detect seasonal period (12-month, 6-month, none)
   - Fit additive or multiplicative per series
   - Output: point forecast + 80%/95% PI (prediction intervals)

2. **ARIMA** (if ETS doesn't fit well; auto-ARIMA with AIC selection)
   - Differencing order auto-detected
   - Output: point + PI

3. **Naive** (last-seen value) — fallback for series with < 6 months history

4. **Parc-as-exogenous regressor**
   - If UIO parc grows/shrinks, demand should track
   - Fit linear model: `demand ~ parc + trend`
   - Boost forecast if parc trend is positive, dampen if negative

**Output:** `forecast_candidates.parquet` — each series has 4 candidate forecasts (ETS, ARIMA, naive, parc-boosted).

---

### Phase 5.3 — Reconciliation (3 days)

**Problem:** individual DB forecasts won't sum to ISZE total because of rounding, model disagreement, etc.

**Method:** MinT (minimum trace reconciliation) — Wickramasuriya et al. 2019

- Forecast individual series
- Adjust all forecasts so they sum to aggregate correctly
- Prioritize leaf-level accuracy (DB × category) over top-level

**Output:** `forecast_reconciled.parquet` — single agreed forecast per series, guaranteed to sum correctly.

---

### Phase 5.4 — Override mechanism (3 days)

**The human judgment layer:**

Create `forecast_overrides.parquet`:
- `db_code`, `category`, `month`, `delta_units`, `delta_revenue`, `reason`, `owner`, `timestamp`
- All changes are logged deltas, never edit-in-place
- Monthly report: `sum(delta_units) / sum(base_forecast)` = override magnitude

**Example:**
```
db_code=ITUK, category=SUSPENSION, month=2026-10, 
delta_units=+50 (reason="new model launch confirmed by sales team"),
owner=jerome, timestamp=2026-08-15
```

**Output:** `forecast_final.parquet` = reconciled forecast + approved deltas.

---

### Phase 5.5 — Backtest (3 days)

**Validate before shipping:**

**Rolling-origin backtest:**
- Train on months 1–12
- Forecast month 13
- Shift window, repeat
- Measure WAPE (weighted absolute percentage error) + bias per DB × category

**Output:** `backtest_report.parquet`
- WAPE by DB (identify which DBs need manual tuning)
- Seasonal bias (does the model overforecast Q3, underforecast Q4?)
- Sparse-series performance (do the Croston forecasts work or fail?)

**Acceptance criterion:** WAPE < 30% for series with ≥12 months history. (Adjust per your historical baseline if you have one.)

---

### Phase 5.6 — Dashboard / export (2 days)

**Outputs:**

1. **CSV export** (monthly refresh)
   - `forecast_final_2026_09.csv`: DB, category, month, units_forecast, revenue_forecast, 80%_lower, 80%_upper, override_delta, override_reason

2. **PRISM page** (read-only)
   - Portfolio view: DB, YTD actual vs forecast, next-3-month outlook, largest variances
   - Detail drill: DB × category, forecast vs actual history, override audit trail
   - Backtest scorecard: WAPE by DB, trend

3. **Monthly refresh hook**
   - Runs first business day of month
   - Pulls fresh sales_fact, re-runs models
   - Flags series where actual >> forecast or << forecast (variance alert)
   - Emails Jerome: "Forecast update ready, variances flagged"

---

## 3. What this does NOT do

| Capability | Why not | Blocker |
|---|---|---|
| Revenue-at-risk scoring (which DBs will lose $?) | Needs sentiment + intent from email | No LLM access (B1b blocked) |
| Shared mailbox data (sales objections, lost deals) | Needs G0b approval | No governance buy-in |
| Win/loss root-cause analysis | Requires email intent classification | No LLM |
| Forecast lift from email signals | Needs commitment → order correlation | Would be nice, data exists, low priority |

---

## 4. Data lineage & audit

| Output | Producer | Frequency | Retention | Audit trail |
|---|---|---|---|---|
| demand_series.parquet | 5.1 | monthly | 36 mo | sales_fact version + filter rules logged |
| forecast_candidates.parquet | 5.2 | monthly | 24 mo | model versions + hyperparams |
| forecast_reconciled.parquet | 5.3 | monthly | 24 mo | MinT matrix + adjustment deltas |
| forecast_overrides.parquet | 5.4 | append-only | 24 mo | all columns signed (who, when, reason) |
| forecast_final.parquet | reconciled + overrides merge | monthly | 24 mo | lineage to both sources |
| backtest_report.parquet | 5.5 | monthly | 12 mo | train window, test window, metrics |

**All** include `extractor_version` + `produced_at`. Re-extraction appends, never mutates.

---

## 5. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Sales_fact has blind spots (P1 residual: €1.38M non-catalogue) | Classify blind spots by DB. Forecast only on catalogue parts. Non-catalogue demand gets manual override or flat-line |
| Sparse series (intermittent demand) will have high WAPE | Croston method addresses; document WAPE separately for sparse vs dense. Alert on sparse forecasts so you know uncertainty is high |
| Parc data lags (UIO not real-time) | Okay — parc is annual/quarterly anyway. Use last-seen value if lagged. Document lag in forecast schema |
| Override magnitude creep (people override too much, rendering the model useless) | Monthly report: `override_magnitude = sum(abs(delta)) / sum(forecast)`. Alert if > 15%. |
| DB launches new product mid-month, forecast breaks | Override mechanism captures this. New product = manual forecast (no history yet) |

---

## 6. Success criteria

✅ **Ship:** 
- Forecast generated monthly, reconciled, override-auditable
- Backtest WAPE < 30% on dense series
- Override magnitude < 15% on average
- Dashboard queryable by DB + category + month

✅ **Not required:**
- Outbeat a commercial baseline (you may not have one; baseline is the first measurement)
- Predict revenue-at-risk (that's P4 predictive, blocked)
- Explain causation (that's P6 engagement playbooks, blocked)

---

## 7. Timeline & ownership

| Phase | Effort | Start | End | Owner |
|---|---|---|---|---|
| 5.1 Series construction | 5 d | Week 1 | Week 1 | Claude |
| 5.2 Models | 5 d | Week 1–2 | Week 2 | Claude |
| 5.3 Reconciliation | 2 d | Week 2 | Week 2 | Claude |
| 5.4 Override mechanism | 2 d | Week 2–3 | Week 3 | Claude |
| 5.5 Backtest | 2 d | Week 3 | Week 3 | Claude |
| 5.6 Dashboard + export | 2 d | Week 3 | Week 3 | Claude |
| **Total** | **~18 d** | — | **Week 3 end** | — |

---

## 8. After P5: what's blocked

**P4 predictive** (revenue-at-risk model) needs:
- Email intent classification (which category did they object to?)
- Shared mailbox access (where the lost deals are documented)
- Both require B1b + LLM.

**P5 alone is not enough to predict which DBs will fail.** It only says "demand will be X next month." It does NOT say "ITUK is at risk of leaving us."

That's why you need the email layer: to see objections, dropped commitments, escalations. **Without shared mailbox + LLM, you're forecasting blind.**

---

## Recommendation

**Build P5 now.** It's 3 weeks, no dependencies, no governance, zero blockers.

**You'll have:** monthly demand forecast + override audit trail by September.

**You'll know:** which categories are trending, which DBs are flat/growing, which series are sparse (risky).

**You won't know:** why a DB is at risk or how to save a deal in progress. That's email + LLM.

**Decision point:** by end of September, decide — do you want revenue-at-risk scoring (P4 predictive) or is the forecast enough?
