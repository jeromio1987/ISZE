# `01_data/17_interactions/` — local interaction layer (G0a)

**Gate:** [`00_docs/G0A_LOCAL_MAIL_SCOPE.md`](../../00_docs/G0A_LOCAL_MAIL_SCOPE.md)  
**G0b drafts (not signed):** [`00_docs/governance/mail/`](../../00_docs/governance/mail/00_README_GOVERNANCE_PACK.md)  
**DSAR / erasure (2a.6):** [`00_docs/DSAR_ERASURE_RUNBOOK.md`](../../00_docs/DSAR_ERASURE_RUNBOOK.md)  
**Collector:** [`04_tools/interactions/collect_mapi.py`](../../04_tools/interactions/collect_mapi.py)  
**Allow-list:** [`04_tools/interactions/db_domains.yaml`](../../04_tools/interactions/db_domains.yaml)

> **Staleness (checked 2026-09-22):** the three P2a tables are **41 days old** (last written 2026-08-12, newest message 2026-08-12), while `01_data/00_derived/sales_fact.parquet` was rebuilt 2026-09-21 and bills through 2026-08-31. Refresh commands + a known `sales_fact` window defect: [`01_data/90_INBOX/MAIL_NEXT_STEP_2026-09-22.md`](../90_INBOX/MAIL_NEXT_STEP_2026-09-22.md) PART 3.

## What lives here

| File | Role | Producer |
|---|---|---|
| `interaction_fact.parquet` | One row per message. Derived fields only (no body, no subject) | `collect_mapi.py` |
| `interaction_fact.meta.json` | Run stats, version, scope | `collect_mapi.py` |
| `commitment_fact.parquet` | Explicit dated promises + `status` (open/met/missed/unknown) | `collect_mapi.py` → `build_commitment_status.py` |
| `commitment_fact.meta.json` | Status counts + keep-rate by owner_side | `build_commitment_status.py` |
| `stakeholder_dim.parquet` | Pseudonymous contacts: role, activity, consensus width, churn flag | `build_stakeholder_dim.py` |
| `db_response_latency.parquet` | Hours from inbound to our reply, p50 / p90 per DB | `build_stakeholder_dim.py` |
| `account_health.parquet` | One row per DB × month. Eight deterministic signals + NONE/AMBER/RED from draft thresholds. **Not a KPI until Jerome calibrates.** | `build_account_health.py` |
| `account_health.meta.json` | Builder version, threshold copy, coverage notes | `build_account_health.py` |

## Rules

- Own mailbox only until G0b
- Salt for `stakeholder_id` is outside the repo (`%LOCALAPPDATA%\ISZE\interactions_salt.txt`)
- Folder is gitignored — regenerate locally
- Do not put shared decks / shared HTML on top of this without a separate decision
- **Evidence bar:** rows below 10 interactions carry `sufficient_evidence = False`. They are written, never displayed — and `role_inferred` is blanked on them rather than published weak.
- `role_inferred` is a **functional** label from topic mix (`parts_manager` / `finance` / `workshop` / `md`). Not personality.
- Commitment `met` = later same-thread activity at/after `due_date` (deterministic proxy). Not LLM-judged.

## Rebuild

```powershell
# Collect (checkpoints every 250 kept). One process only; bounce Outlook if COM dies.
# --folders inbox,sent recurses into Inbox\subfolders and Sent\subfolders (own store).
$env:PYTHONUNBUFFERED = "1"
python -u $env:ISZE_ROOT\04_tools\interactions\collect_mapi.py --since 2024-08-01 --folders inbox,sent --dry-run
python -u $env:ISZE_ROOT\04_tools\interactions\collect_mapi.py --since 2024-08-01 --folders inbox,sent

python $env:ISZE_ROOT\04_tools\interactions\build_commitment_status.py
python $env:ISZE_ROOT\04_tools\interactions\build_stakeholder_dim.py
python $env:ISZE_ROOT\04_tools\interactions\build_account_health.py

# Retention hard-delete (2a.6) — dry-run first; never touches Outlook
python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py
# python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py --apply
# python $env:ISZE_ROOT\04_tools\interactions\build_stakeholder_dim.py   # after --apply

# DSAR locate / erase by stakeholder_id (see DSAR_ERASURE_RUNBOOK.md)
# python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py --lookup --stakeholder-id <HASH>
# python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py --stakeholder-id <HASH>
# python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py --stakeholder-id <HASH> --apply
```

Last purge/lookup audit: `purge_expired.meta.json` (written next to these parquet files).

Extractor `det-v2`: broader EN/NL/DE commitment cues, nearby-sentence dates, typed commitments (`delivery` / `stock_confirm` / `price_quote` / `meeting` / `data_delivery` / `order_volume`). Still no body/subject stored.

## Missing distributors

ARMENIA / KAZAKHSTAN / PALESTINE still have no contact on file. **UMI** (`umi.co.il`) and **UTI** (`uti.co.il`) were added 2026-08-12 — keep them separate, never blend.
