# P4 account-health — calibration runbook (Mode B)

**Owner:** Jerome (task 4.9) · **Builder:** `build_account_health.py` · **Export:** `export_account_health_calibration.py`

Draft thresholds live in `00_docs/P4_DETERMINISTIC_SIGNALS.md` §2. **Not a KPI** until you sign off.

---

## Files

| File | Role |
|------|------|
| `01_data/17_interactions/account_health.parquet` | One row per DB × month (gitignored) |
| `account_health.meta.json` | Row counts, latest alert mix, threshold JSON |
| `account_health_calibration.csv` | Full history — all 8 signals + draft alert |
| `account_health_latest_flagged.csv` | Latest month only — AMBER/RED for review |

---

## Refresh

```powershell
cd $env:ISZE_ROOT
python 04_tools/interactions/build_account_health.py
python 04_tools/interactions/export_account_health_calibration.py
```

---

## Your 1-day pass (4.9)

1. Open **`account_health_latest_flagged.csv`** — scan AMBER/RED rows. False positives?
2. For each signal, spot-check 2–3 DBs against raw mail (own mailbox, G0a).
3. Adjust thresholds in `build_account_health.py` → `THRESHOLDS` dict only after evidence.
4. Re-run builder + export; note changes in `DECISIONS.md` when locked.
5. **UTI ≠ UMI** — never merge rows when judging Israel.

Known quirk (documented in meta): latency spec is in **days** but p50 is stored in **hours** — latency rarely trips until unit fix or 4.9.

Mail-to-order is **NULL** when the 90d window sits after `sales_fact` ends (currently 2026-03-31).

---

## After calibration

- Task 4.10: internal PRISM widget or CSV-only ops view — **only when you say ship**.
- Early Warning remains the primary sales call list until then.
