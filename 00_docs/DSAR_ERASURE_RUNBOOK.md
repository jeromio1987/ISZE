# DSAR / erasure runbook — interaction layer (internal · internal)

**Gate:** G0a · [`G0A_LOCAL_MAIL_SCOPE.md`](G0A_LOCAL_MAIL_SCOPE.md)  
**Roadmap:** [`roadmaps/ai_sales_intelligence.md`](roadmaps/ai_sales_intelligence.md) §7.4 task **2a.6** · compliance checklist §14 items 8–9  
**Owner (ops):** account holder / eng · **Owner (legal clock):** DPO — erase within **30 days** of a valid erasure request  
**Status:** Runnable 2026-08-12 — derived parquet only; Outlook never touched

This is internal. Do not paste into shared decks or distributor mail.

---

## 1. What we store (and what we do not)

| Stored (derived) | Never stored |
|---|---|
| `interaction_fact` — timestamps, direction, DB, topics, PNs, hashes, `stakeholder_id`, `retention_expires` | Message bodies, subjects, attachment bytes/names |
| `commitment_fact` — type, due date, `sentence_sha256`, status | Commitment sentence text |
| `stakeholder_dim` — pseudonymous activity / functional role | Plain email, display name |
| `db_response_latency` — p50/p90 hours per DB | Person-level latency |

`stakeholder_id` = salted SHA-256 of the counterparty address (salt at `%LOCALAPPDATA%\ISZE\interactions_salt.txt`, **outside the repo**). Plain email is not in the parquet.

---

## 2. SLA

| Clock | Rule |
|---|---|
| Retention | 24 months from `occurred_at` → `retention_expires` |
| Monthly job | Dry-run first; `--apply` only when counts look expected |
| DSAR erasure | Locate + delete by `stakeholder_id` within **30 days** of a valid request |
| Scope | Local derived tables only. Does **not** delete the original Outlook message (controller already holds it as ordinary business mail; this layer is the analytics extract) |

---

## 3. Tables touched

| Table | Path | Retention purge | DSAR erase |
|---|---|---|---|
| `interaction_fact` | `01_data/17_interactions/interaction_fact.parquet` | Drop `retention_expires` < as-of | Drop rows with matching `stakeholder_id` |
| `commitment_fact` | `…/commitment_fact.parquet` | Cascade on deleted `interaction_id` | Same cascade |
| `stakeholder_dim` | `…/stakeholder_dim.parquet` | Drop orphan ids | Drop that `stakeholder_id` row |
| `db_response_latency` | `…/db_response_latency.parquet` | **Not** rewritten in-place | **Not** rewritten in-place — refresh via `build_stakeholder_dim.py` after `--apply` |

Audit log of every purge/lookup: `01_data/17_interactions/purge_expired.meta.json`.

---

## 4. Tooling

Script: [`04_tools/interactions/purge_expired.py`](../04_tools/interactions/purge_expired.py)

| Flag | Effect |
|---|---|
| *(none)* | Retention dry-run (default) |
| `--apply` | Write deletes |
| `--as-of YYYY-MM-DD` | Retention cut-off (default: today UTC) |
| `--stakeholder-id <hash>` | DSAR erase mode (dry-run unless `--apply`) |
| `--lookup` | With `--stakeholder-id`: counts only, never writes |

**Hard rules:** never opens Outlook · never sends · never touches Sales/Parts mailboxes · never ships shared output from this folder.

---

## 5. Retention purge (monthly)

```powershell
$env:ISZE_ROOT = "C:\Users\jerom\Desktop\claude\ISZE"

# 1) Dry-run — expect dropped ≈ 0 until first cohort ages past 24 months
python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py

# 2) Inspect meta
Get-Content $env:ISZE_ROOT\01_data\17_interactions\purge_expired.meta.json

# 3) Only if dry-run counts are expected (Jerome / DPO OK to delete):
# python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py --apply
# python $env:ISZE_ROOT\04_tools\interactions\build_stakeholder_dim.py
```

First real delete cycle falls due ~24 months after the oldest retained `occurred_at`.

---

## 6. DSAR — locate then erase (≤ 30 days)

### 6.1 Resolve email → `stakeholder_id`

Only the account holder with the local salt can recompute the hash. From a trusted shell (do not commit the salt or the email):

```powershell
python -c @"
import hashlib, os
email = input('email: ').strip()
salt_path = os.path.join(os.environ['LOCALAPPDATA'], 'ISZE', 'interactions_salt.txt')
salt = open(salt_path, encoding='utf-8').read().strip()
# Must match collect_mapi._h: sha256(salt + value.lower())[:32]
print(hashlib.sha256((salt + email.lower()).encode('utf-8')).hexdigest()[:32])
"@
```

If the collector ever changes hash length/format, update this snippet in the same PR.

### 6.2 Lookup (no deletes)

```powershell
python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py --lookup --stakeholder-id <HASH>
```

Record: interaction rows · commitment rows · dim present · `db_codes` · first/last seen. File the JSON output (or the meta file) with the DSAR ticket.

### 6.3 Erase dry-run → apply

```powershell
# Dry-run first — must match lookup counts
python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py --stakeholder-id <HASH>

# Apply only after dry-run matches and DPO/Jerome authorize delete
# python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py --stakeholder-id <HASH> --apply
# python $env:ISZE_ROOT\04_tools\interactions\build_stakeholder_dim.py

# Prove gone
python $env:ISZE_ROOT\04_tools\interactions\purge_expired.py --lookup --stakeholder-id <HASH>
```

Expected after apply + rebuild: `interaction_fact_rows = 0`, `commitment_fact_rows = 0`, `stakeholder_dim_row = false`. Latency file is DB-level — rebuild refreshes aggregates; it never held a person key.

### 6.4 What this does **not** cover

- Original messages still in Outlook (ordinary mailbox retention / legal hold — separate policy)
- Shared Sales/Parts mailboxes (out of G0a; blocked until G0b)
- Any shared artefact that never received this data (should be none by design)
- Re-ingest: a later `collect_mapi.py` run can recreate derived rows if the mail is still in the mailbox and still matches the allow-list. For a lasting erasure, also remove or exclude the source message under normal mail governance, or pause re-collect for that address until policy says otherwise.

---

## 7. Proof log (2026-08-12 close-out)

| Check | Result |
|---|---|
| Dry-run retention (`purge_expired.py`) | **0** expired interactions / commitments / stakeholders (cut-off 2026-08-12). `retention_expires` still in 2027-08…2028-08 band |
| Stakeholder cascade | Hardened: retention only drops ids that lose their **last** row to *this* expiry — does **not** re-sync dim to a partial `interaction_fact` |
| `--apply` | **Not run** (Jerome authorized proceed on runbook + harden; not an explicit delete) |
| Outlook | Untouched |
| Live fact note | Folder may hold a **partial** re-collect (`interaction_fact.meta.json` `partial: true`) while `stakeholder_dim` was built from an earlier fuller pass — re-collect + `build_stakeholder_dim.py` is a separate ops task, not a purge |
| G2 | Still **not** claimable — gold set / extraction precision is **P2b** (task 2b.1); **2a.6 ops path is claimable** |

---

## 8. Related files

| File | Role |
|---|---|
| `04_tools/interactions/purge_expired.py` | Retention + DSAR erase |
| `04_tools/interactions/build_stakeholder_dim.py` | Rebuild dim + latency after apply |
| `04_tools/interactions/collect_mapi.py` | Writes `retention_expires` + `stakeholder_id` |
| `01_data/17_interactions/README.md` | Operator index |
| `01_data/17_interactions/purge_expired.meta.json` | Last run audit (gitignored with folder) |
