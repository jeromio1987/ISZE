# Retention schedule — mail interaction layer

**Status:** DRAFT — but the rules below already match what the running code does today. This document governs; the code implements.
**Owner:** `[[DPO_NAME]]` · **Operator:** `[[RETENTION_OWNER]]` · **Date:** `[[DATE]]`
**Roadmap ref:** `../roadmaps/ai_sales_intelligence.md` §5 task 0.8, §14 item 8
**Related:** [`../DSAR_ERASURE_RUNBOOK.md`](../DSAR_ERASURE_RUNBOOK.md) · [`01_DPIA_OUTLINE_mail.md`](01_DPIA_OUTLINE_mail.md) §5 R6

---

## 1. Schedule

| # | Data | Location | Retention | Basis | Deletion mechanism |
|---|---|---|---|---|---|
| 1 | `interaction_fact` — one row per message, derived fields only | `01_data/17_interactions/interaction_fact.parquet` | **24 months** from `occurred_at` | Operational need spans two annual cycles | `retention_expires` written at row creation; `purge_expired.py` |
| 2 | `commitment_fact` — promise type, due date, status | `…/commitment_fact.parquet` | **24 months**, cascaded from `interaction_id` | Orphan rows are meaningless | Cascade delete with the parent interaction |
| 3 | `stakeholder_dim` — pseudonymous roles and activity | `…/stakeholder_dim.parquet` | **24 months**; row dropped when it loses its last interaction | Dim is derived, not source | Cascade from `interaction_fact` |
| 4 | `db_response_latency` — p50/p90 per distributor | `…/db_response_latency.parquet` | Not row-dated; **rebuilt** after any purge | Holds no person key by design | Re-run `build_stakeholder_dim.py` |
| 5 | `account_health` — DB × month aggregates | `…/account_health.parquet` | Not row-dated; git-ignored, regenerable | No person key | Regenerated from 1–3 |
| 6 | `body_sha256` | Inside `interaction_fact` | **24 months**, with its row | Provenance only | Same as row 1 |
| 7 | `sentence_sha256` | Inside `commitment_fact` | **24 months** | Provenance only | Same as row 2 |
| 8 | **Message bodies, subjects, attachments, names, addresses** | **Nowhere** | **Never stored** | Data minimisation, DPIA §4.2 | Not applicable — no copy exists |
| 9 | Purge audit log | `…/purge_expired.meta.json` | `[[AUDIT_RETENTION]]` — recommend 36 months | Proof of compliance outlives the data | Manual |
| 10 | Pseudonymisation salt | `%LOCALAPPDATA%\ISZE\interactions_salt.txt` | Life of the processing | Reversal key — must not be in the repo | Manual, on processing end |
| 11 | Original Outlook messages | Mailbox on the managed workstation | **Out of scope here** | Ordinary business mail under normal mailbox policy | Mailbox retention policy — a separate decision |

**Row 11 matters.** This layer is an analytics extract, not the record of the correspondence. Deleting from this layer does not delete the message. The DSAR runbook says so explicitly and it should stay that way.

---

## 2. Why 24 months

Two annual cycles covers year-over-year comparison without holding a decade of metadata. It is long enough for the latency and commitment KPIs to have a comparison period and short enough to argue at a balancing test. `[[DPO_NAME]]` to confirm or set a different figure — **one figure must be chosen and stated in both this schedule and the Art. 13/14 notice**, because the notice commits to 24 months.

---

## 3. Enforcing it — the honest status

| Component | State |
|---|---|
| `retention_expires` written at row creation | **Implemented.** Every row carries its own expiry |
| Purge script | **Implemented** — `04_tools/interactions/purge_expired.py`, dry-run by default, `--apply` to write |
| Last audit | 2026-08-12 — **0 expired** rows. First real deletion falls due 2027-08 onward |
| Scheduled job | **NOT IMPLEMENTED.** No cron, no scheduled task, no monitored cadence |
| Audit review | Not assigned to a named person |

**This is the weakest control in the pack.** Every other document in `00_docs/governance/mail/` describes a control that either exists or is honestly absent. Here a control exists and nothing operates it. A retention promise that depends on someone remembering is not a retention control, and an assessor will say so.

**To close it:**
1. Name the operator — `[[RETENTION_OWNER]]`
2. Schedule a monthly run (dry-run by default; `--apply` only on review)
3. Point a monitor at `purge_expired.meta.json` freshness — if the file is older than ~35 days, something is wrong
4. Register it — `../AUTOMATION_REGISTER.md` already has the slot `isze-mailbox-intake` under "Stub"

The monthly runbook already exists at [`../DSAR_ERASURE_RUNBOOK.md`](../DSAR_ERASURE_RUNBOOK.md) §5. The gap is scheduling and ownership, not procedure.

---

## 4. DSAR / erasure

| Clock | Rule |
|---|---|
| Valid erasure request → rows deleted | **Within 30 days** |
| Lookup | By `stakeholder_id`, salted hash recomputed locally (only the salt holder can do this) |
| Scope of erasure | This layer only. Outlook messages are not touched — they are ordinary business mail under mailbox policy |
| Proof | `purge_expired.py --lookup` after apply must return zero rows |
| Re-ingest risk | A later collection run **can recreate** the rows if the message is still in the mailbox and still matches the allow-list. For lasting erasure, exclude the address or remove the source message under normal mail governance. **This limitation is disclosed in the Art. 13/14 notice and is not a defect — but it must be handled, not forgotten** |

Full procedure: [`../DSAR_ERASURE_RUNBOOK.md`](../DSAR_ERASURE_RUNBOOK.md) §6.

---

## 5. Review

| Trigger | Action |
|---|---|
| Any scope change (shared mailboxes, LLM route, output leaving the machine) | Re-assess retention before the change, not after |
| New Outlook replaces classic Outlook | Collector is rewritten — confirm the new writer still sets `retention_expires` |
| Annual | Confirm 24 months still correct and still matches the published notice |
| Retention job misses two consecutive months | Treat as an incident, not a backlog item |

---

## 6. Open items

1. Name `[[RETENTION_OWNER]]` and put the monthly run on a schedule (§3).
2. Confirm 24 months, or choose a different figure and update the Art. 13/14 notice to match.
3. Set `[[AUDIT_RETENTION]]` for the purge log.
4. Confirm the re-ingest limitation is acceptable and disclosed — it is already stated in the notice, so the notice and this schedule must not drift apart.
5. Decide what happens to the salt on processing end, and record it.
