# Session manifest — everything created (2026-08-12)

Single index of every file, table, and script produced this session. Working English throughout, per instruction.

---

## 1. Governance

| File | What | Status |
|---|---|---|
| [`G0A_LOCAL_MAIL_SCOPE.md`](G0A_LOCAL_MAIL_SCOPE.md) | Scope memo: own mailbox only, 24-month retention, no bodies stored | **Signed 2026-08-12** |

G0b (LLM / shared mailbox gate) was raised and discussed but **not pursued** — no DPO process exists to sign it. Treat P2b/P3/P6 as indefinitely blocked, not "pending."

---

## 2. Code — `04_tools/interactions/`

| File | Size | What it does |
|---|---|---|
| [`collect_mapi.py`](../04_tools/interactions/collect_mapi.py) | 39.8 KB | MAPI collector. Reads own Outlook mailbox (Inbox + subfolders + Sent) via COM, read-only. Windows scans in 30-day chunks with per-window checkpointing so an RPC drop doesn't lose progress. Extracts derived fields only — never stores message bodies or subjects |
| [`build_db_domains.py`](../04_tools/interactions/build_db_domains.py) | 3.2 KB | Reads the distributor master contact list, generates the domain allow-list |
| [`build_stakeholder_dim.py`](../04_tools/interactions/build_stakeholder_dim.py) | 8.7 KB | Aggregates interaction_fact into pseudonymous stakeholder profiles: role, decision authority, churn flag, response latency |
| [`build_commitment_status.py`](../04_tools/interactions/build_commitment_status.py) | 4.7 KB | State machine: classifies each extracted commitment as met / missed / open / unknown, based on thread continuation past due_date |
| [`suggest_db_domains.py`](../04_tools/interactions/suggest_db_domains.py) | 5.2 KB | Ranks unmatched mail domains by volume, proposes candidate matches for distributors with no contact on file. Proposes only — nothing auto-added |
| [`purge_expired.py`](../04_tools/interactions/purge_expired.py) | 9.9 KB | Retention hard-delete skeleton. Dry-run by default; `--apply` to execute; `--stakeholder-id` for DSAR lookup/erasure. **No scheduled job wired up** |
| [`db_domains.yaml`](../04_tools/interactions/db_domains.yaml) | 1.7 KB | The allow-list itself: 24 unambiguous distributor domains + UMI/UTI (added this session) |

---

## 3. Data output — `01_data/17_interactions/`

Regenerable by rerunning the scripts above. Gitignored (local only).

| File | Rows | What |
|---|---|---|
| `interaction_fact.parquet` | 9,001 | One row per message. Timestamp, direction, db_code, stakeholder_id, topics, part numbers, commitment flag. No body, no subject |
| `commitment_fact.parquet` | 926 | Extracted promises: type, due_date, owner_side (db/isze), status (met/missed/open) |
| `stakeholder_dim.parquet` | 203 | Pseudonymous contacts: role_inferred, decision_authority, churn_flag, activity window. 93 rows above the 10-interaction evidence bar, rest suppressed |
| `db_response_latency.parquet` | 16 | Response time p50/p90 per distributor. 8 rows above evidence bar |
| `interaction_fact.meta.json` | — | Run stats: 31,532 examined, 9,490 kept, 21,667 unmatched, 375 non-mail, 0 errors |
| `commitment_fact.meta.json` | — | Status counts + keep-rate by owner_side |
| `purge_expired.meta.json` | — | Last dry-run audit: 0 expired |
| `_collect_run_20260812.log` | — | Full run log, 24-month collection |
| [`README.md`](../01_data/17_interactions/README.md) | — | Table descriptions, rebuild commands, rules |

**Collection scope:** 2024-08-01 → 2026-07-22 (24 months). Own mailbox: Inbox root + 3 subfolders (IE30, Inbox_2, Outlook_Customer_Manager) + Sent.

---

## 4. Specs / plans — `00_docs/`

| File | What | Status |
|---|---|---|
| [`P4_DETERMINISTIC_SIGNALS.md`](P4_DETERMINISTIC_SIGNALS.md) | 8 account-health signals computable from P2a tables with zero LLM. Schema + draft alert thresholds. | **Builder live 2026-08-18** (`build_account_health.py`). Thresholds still draft — not a KPI. |
| [`P5_FORECAST_BUILD_PLAN.md`](P5_FORECAST_BUILD_PLAN.md) | Deterministic demand forecast: ETS/ARIMA per DB × category, parc as exogenous regressor, MinT reconciliation, override audit trail, rolling-origin backtest. 6-phase, ~18-day build plan | **Spec only — not built** |

---

## 5. Roadmap — `00_docs/roadmaps/ai_sales_intelligence.md`

Updated this session:
- §0 dual-track status: P2a marked complete
- §7.4 (P2a task table): all 8 tasks (2a.0–2a.8) marked with final counts
- §9 (new): P4 deterministic signals section added, links to spec
- §10 (renumbered from §9): P4 predictive scoring — unchanged, still blocked
- Section numbers §10–12 shifted by one to accommodate new §9

---

## 6. Ad-hoc analysis (not saved as a table)

Ran a one-off script (`analyze_mails.py`, scratchpad — not committed) against the four P2a tables. Output was printed to chat, not persisted. Findings:

- Response latency: fastest ICELAND (0.1h), slowest GREECE (18.3h)
- Commitment keep-rate: 62.5% overall. Weakest: GERMANY 11%, MALTA 19%, IRELAND 29%, ROMANIA 30%, SWEDEN 34% (small samples on some)
- Stakeholders: 203 found, 93 with evidence. Roles: 81 parts_manager, 11 workshop
- Churn: only 5 flagged contacts total — not currently a signal worth acting on

**This was console output only.** If you want it as a recurring table, that's what P4_DETERMINISTIC_SIGNALS.md specs out (not yet built).

---

## 7. What is NOT built

- P4 deterministic (spec exists, code does not)
- P5 forecast (plan exists, code does not)
- P2b (LLM enrichment) — blocked, no governance path
- P3 (action routing) — blocked, depends on P2b
- P4 predictive (revenue-at-risk model) — blocked, depends on P2b
- Scheduled retention job (2a.6 skeleton only)
- CC-depth extraction (needed for P4's escalation-cadence signal)

---

## 8. Git commits this session

```
7f0a1cd Add P4 deterministic signals spec (operational layer before predictive model).
3affbfa Mark P2a complete in roadmap: all 3 tables live, 24-month run done, G2 awaits LLM clearance.
8bc9c4b Complete P2a (local email interaction layer): collector, builders, scope memo.
```

P5_FORECAST_BUILD_PLAN.md and this manifest are **not yet committed**.
