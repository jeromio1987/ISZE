# P4 — Account-health KPIs

**Status 2026-08-18:** builder live — `04_tools/interactions/build_account_health.py` writes gitignored `01_data/17_interactions/account_health.parquet` (`p4-v1`). Draft thresholds. **Not a KPI.** No shared / PRISM widget until task 4.9 (your calibration) then 2.3/4.10.

**CC-depth:** uses existing `n_cc` (P2a.9 collector change not required).

**Mail-to-order:** NULL on months after `sales_fact` ends (currently 2026-03-31).

**Objective:** convert signal→order latency + commitment tracking into actionable account signals for sales ops.

**Input:** P2a tables (interaction_fact, commitment_fact, stakeholder_dim, db_response_latency).

**Output:** account_health.parquet (one row per DB + month), queryable for alert / dashboard.

---

## 1. Signals

| Signal | Formula | Unit | Why |
|---|---|---|---|
| **Response latency SLA** | p50 of (outbound ts - inbound ts), rolling 30d | hours | Proxy for account engagement. Slow → account going cold |
| **Commitment met-rate** | met / (met + missed), rolling 90d | % | Fulfilment quality. Dropping → supply or credibility issue |
| **Signal→order latency** | ts(order_in_sales_fact) - ts(first_mention_in_mail), rolling 90d | days | Sales cycle speed. Rising → friction in decision chain |
| **Stakeholder churn** | count(churn_flagged=True) / total_active, rolling 90d | % | Personnel risk. Spike → relationship key-person dependency |
| **Escalation cadence** | count(CC-depth ≥ 3) / total_threads, rolling 30d | % | Pads & Shoes signal. Rising → unresolved objections |
| **Topic concentration** | 1 - entropy([topic_counts]), rolling 90d | [0,1] | Narrow focus (=0.9) → one-product account; broad (=0.3) → healthy cross-sell |
| **Email activity volume** | count(interactions), rolling 30d | /day | Engagement baseline. Drop > 30% → alarm |
| **Open commitments** | count(status='open' AND due_date < today), rolling 30d | count | Overdue actions. > 3 in rolling window → escalate to account mgr |

---

## 2. Alert thresholds (draft)

| Signal | Amber | Red | Action |
|---|---|---|---|
| Response latency p50 | >7 days | >14 days | Account mgr review |
| Commitment met-rate | <60% | <40% | Supply/quality escalation |
| Signal→order latency | +50% vs 6mo avg | +100% | Deal friction diagnostic |
| Stakeholder churn | >25% | >50% | Key-person at risk; retain interview |
| Escalation cadence | >20% | >40% | Objection root-cause |
| Topic concentration entropy | <0.4 | <0.3 | Upsell opportunity |
| Activity volume drop | >30% | >50% | Account pause (churn risk) |
| Overdue commitments | 2–3 | >3 | Task escalation |

---

## 3. Schema

```sql
CREATE TABLE account_health (
  db_code               STRING,
  year_month            STRING,  -- "2026-08"
  response_latency_p50  FLOAT,   -- hours
  response_latency_p90  FLOAT,   -- hours
  commitment_met_rate   FLOAT,   -- [0,1]
  signal_to_order_days  FLOAT,   -- days, NULL if no order in window
  stakeholder_churn_pct FLOAT,   -- [0,1]
  escalation_cadence    FLOAT,   -- [0,1]
  topic_entropy         FLOAT,   -- [0,1]
  activity_volume_per_day FLOAT, -- count/day
  overdue_commitments   INT,     -- count
  alert_level           STRING,  -- NONE | AMBER | RED
  alert_reasons         ARRAY<STRING>,
  produced_at           TIMESTAMP,
  extractor_version     STRING,
  PRIMARY KEY (db_code, year_month)
);
```

---

## 4. Data lineage

| Input table | Field(s) used | Notes |
|---|---|---|
| interaction_fact | occurred_at, direction, db_code, topics, n_amounts | Direction filters inbound vs outbound for latency |
| commitment_fact | db_code, due_date, status, made_at, owner_side | Filters to db→isze promises for met-rate. |
| stakeholder_dim | db_code, churn_flag, decision_authority, consensus_width | Flags per stakeholder; aggregated to DB level |
| sales_fact | db_code, order_date, line_PN | Join to find first mail mention → order ts |

---

## 5. Build steps (draft task list)

| # | Task | Effort | Notes |
|---|---|---|---|
| 4.1 | Implement latency calculators (p50/p90 rolling 30d) | 1 d | Reuse `db_response_latency.parquet` schema; add rolling windows |
| 4.2 | Implement commitment met-rate (rolling 90d) | 0.5 d | Filter commitment_fact to db→isze promises only |
| 4.3 | Implement signal→order latency (PN regex on mails vs sales_fact order_date) | 1 d | Cross-table join; NULL if no orders in window |
| 4.4 | Implement stakeholder churn aggregator (rolling 90d) | 0.5 d | Aggregate churn_flag per DB from stakeholder_dim |
| 4.5 | Implement escalation cadence (CC-depth spike detector) | 0.5 d | Count threads with CC-depth ≥ 3 / total threads |
| 4.6 | Implement topic entropy (Shannon) | 0.5 d | Frequency distribution of topic[] over rolling 90d |
| 4.7 | Implement alert router (thresholds → alert_level + reasons) | 0.5 d | Deterministic rule engine, versioned |
| 4.8 | Build parquet writer + metadata | 0.5 d | Rolling monthly, append-only |
| 4.9 | Manual calibration (run on 6mo backfill, review thresholds) | 1 d | Hand-verify 3–5 accounts; tune amber/red boundaries |
| 4.10 | Integration with dashboard / ops runbook | 1 d | Either HTML widget (shared compatible) or direct CSV export |

**Estimated:** 6–7 d (developer) + 1 d (you: calibration) = 1.5 week.

---

## 6. Risk & assumptions

| Risk | Mitigation |
|---|---|
| CC-depth not in interaction_fact (not yet extracted) | Add to P2a.9 (minor collector update) |
| Signal→order latency requires PN regex on mail (already done P2a.3) but join to sales_fact could have gaps | Evidence bar: only use if ≥10 interactions with PN mentions. Else mark as NULL |
| Entropy measure sensitive to topic lexicon coverage | Baseline now; tune after 2–3 months of ops |
| Alert thresholds guessed (not calibrated) | Backfill 6 months; hand-review 3–5 accounts; iterate |

---

## 7. Not in scope for P4

- Psychometric profiling of individuals
- Predictive churn model (P6)
- Forecast reconciliation (P5)
- Intent classification (P2b)

---

## Next

Once B1b (Cowork clearance) lands and P2b ships implicit-commitment detection, P4 can add:
- Objection themes (from intent classification)
- Sentiment slope (improving vs declining engagement)
- Win-rate lift by account-health signal

For now, P4 is **deterministic only** — timestamps, counts, regex, state machines. No model.
