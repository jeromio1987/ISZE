# DPIA outline — distributor correspondence analysis (mail interaction layer)

**Art. 35 GDPR · Data Protection Impact Assessment**
**Status:** OUTLINE — unscreened, unsigned. This is a structure to be completed and approved, not an approval.
**Owner:** `[[DPO_NAME]]` · **Prepared by:** `[[PREPARER_NAME]]` · **Date prepared:** `[[DATE]]`
**Controller:** `[[CONTROLLER_LEGAL_ENTITY]]` · **Roadmap ref:** `../roadmaps/ai_sales_intelligence.md` §5 task 0.2, §14 item 1
**Related:** [`02_LIA_OUTLINE_mail.md`](02_LIA_OUTLINE_mail.md) · [`05_RETENTION_SCHEDULE_mail.md`](05_RETENTION_SCHEDULE_mail.md) · [`00_README_GOVERNANCE_PACK.md`](00_README_GOVERNANCE_PACK.md)

**Handling rule:** complete this DPIA **without** attaching any message. Everything needed is described in §4 as field names. If a sample is judged necessary, it is viewed on the controller's own machine under the local-processing control, not transmitted.

---

## 1. Why a DPIA is required

| Trigger (Art. 35(3) / WP248 criteria) | Applies? |
|---|---|
| Systematic and extensive evaluation of personal aspects, automated, used to take decisions | **Partially.** Counts and latency aggregates per distributor; no Art. 22 decision. See §6 |
| Large-scale processing of special category data (Art. 9) | **No** — hard-blocked at extraction (see §4.3) |
| Systematic monitoring of a publicly accessible area | No |
| Processing at scale of business correspondence involving identifiable individuals | **Yes** |
| Novel use of technology | **Yes** — automated extraction from correspondence |

Two criteria met → treat as requiring a DPIA. **`[[DPO_NAME]]` to confirm or downgrade, and record the reasoning either way.**

---

## 2. Description of the processing

| | |
|---|---|
| **Nature** | Automated extraction of derived metadata from business e-mail between the controller and its distributors |
| **Scope — mailbox** | `jerome.van.der.pluym@isuzu-e.com` (own) — **G0a scope only** |
| **Scope — shared mailboxes** | `[[DECIDE: in scope or explicitly deferred]]` — shared `Sales` / `Parts` contain colleagues' correspondence and require the works-council step before inclusion |
| **Scope — period** | 24 months rolling |
| **Scope — filter** | Only messages where a distributor domain from `04_tools/interactions/db_domains.yaml` appears as sender or recipient. Last full run: 9,490 kept of 31,532 examined (30%); 21,667 discarded unmatched, 375 non-mail |
| **Geography** | Local processing on one controlled workstation inside `[[SITE]]`. **No transfer. No processor. No cloud.** |
| **Storage** | `01_data/17_interactions/` — git-ignored, local disk only |
| **Retention** | 24 months from message date; bodies never stored at all — see [`05_RETENTION_SCHEDULE_mail.md`](05_RETENTION_SCHEDULE_mail.md) |
| **Data subjects** | Distributor staff (counterparties) and, where shared mailboxes ever enter scope, controller staff |
| **Estimated subject volume** | `[[SUBJECT_COUNT]]` pseudonymous `stakeholder_id` values in the last run; `[[DB_COUNT]]` distributors |

---

## 3. Purpose and necessity

**Purpose.** Measure three quantities that do not exist in any current system: (a) how long the controller takes to reply to a distributor's action-requiring message, (b) how long elapses between a distributor raising a need and an order being placed, (c) whether promises made in correspondence are kept.

**Necessity.** Each of these is a commercial-process defect with no other instrument. The controller has no CRM, no call transcript capture and no lead log (roadmap §1.2). The alternative measurements were considered and rejected: manual sampling cannot produce a latency distribution; a survey measures what distributors believe, not what the correspondence shows.

**Proportionality.** The processing reads **metadata and counts**, not narratives. It produces no record of what any individual said. Section 4 is the operative part of this assessment.

---

## 4. Data minimisation — the design that carries this DPIA

### 4.1 Fields derived and stored

Message timestamps · direction (inbound/outbound) · thread identifier · distributor code · folder path · pseudonymous `stakeholder_id` (salted SHA-256) · counterparty domain · recipient and cc counts · topic tags from a fixed 9-token lexicon · validated part numbers · **counts** of amounts and dates (never the values) · explicit-commitment flag · attachment count · subject length · body length · body SHA-256 · commitment type, due date and `sentence_sha256`.

### 4.2 Never stored, at any point, in any form

Message bodies · subjects · attachments · attachment names · sender or recipient display names · plain e-mail addresses.

**Body hash.** `body_sha256` exists so provenence can be asserted without retaining text. A hash is not recoverable text. `[[DPO_NAME]]` to confirm acceptance of the hash as non-personal / pseudonymous.

### 4.3 Hard blocks at extraction

| Block | Mechanism |
|---|---|
| Special category data (health, union, political, religious) | Not extracted; no field exists to receive it |
| Another OEM's pricing intent | Dropped at extraction by rule, never stored — roadmap §14 item 14, competition-law exposure |
| Non-distributor mail | Discarded **before any field is read** |
| Named individuals in output | No output carries a name — roles only |

### 4.4 Pseudonymisation

`salt` stored at `%LOCALAPPDATA%\ISZE\interactions_salt.txt`, **outside the repository**, never committed. Without the salt the `stakeholder_id` cannot be reversed to an address. Re-identification is possible for the controller (who holds the salt) — this is pseudonymisation, not anonymisation, and the DPIA should say so plainly rather than overclaim.

**Residual risk:** a reader who knows the correspondence could infer who a `stakeholder_id` is from role + timing. `[[DPO_NAME]]` to assess whether this residual is acceptable at the current aggregation level.

---

## 5. Risks to data subjects and mitigations

| # | Risk | Likelihood | Severity | Mitigation | Residual |
|---|---|---|---|---|---|
| R1 | A distributor learns the controller keeps derived analytics on their correspondence | Medium | Severe | Roles only, never names; profile-shown-to-DB design (task 6.3); no shared artefacts | `[[RESIDUAL_ASSESSMENT]]` |
| R2 | Re-identification from role + timing | Low | Medium | Aggregation; 10-interaction display floor; small-n suppression (no cell under 10 signals) | `[[RESIDUAL_ASSESSMENT]]` |
| R3 | Function creep — latency data used in commercial negotiation or against an individual | Medium | Severe | Purpose limitation clause in this DPIA; no score ships without evidence refs; access log | `[[RESIDUAL_ASSESSMENT]]` |
| R4 | Egress by accident — text reaches a model or a cloud tool | Low | Severe | No network calls in the deterministic layer; G0b gate before any LLM; separate assessment for the named route | `[[RESIDUAL_ASSESSMENT]]` |
| R5 | Subject exercises rights and the controller cannot find their rows | Low | Medium | DSAR runbook exists and is runnable — [`../DSAR_ERASURE_RUNBOOK.md`](../DSAR_ERASURE_RUNBOOK.md) | Low — erasure path proven by dry-run |
| R6 | Retention job never runs, data outlives policy | Medium | Medium | `retention_expires` set at write; purge script exists | **Open — the job is not scheduled.** See [`05_RETENTION_SCHEDULE_mail.md`](05_RETENTION_SCHEDULE_mail.md) §5 |
| R7 | Works-council obligation missed if shared mailboxes are added later | Medium | Severe | Shared mailboxes are out of scope under G0a; excluded from this DPIA until step 0.5 and 0.8 complete | Controlled by scope |
| R8 | Another OEM's pricing intent retained | Low | Severe | Dropped at extraction | `[[RESIDUAL_ASSESSMENT]]` |

---

## 6. Art. 22 — automated decision-making

**Position: no Art. 22 decision is taken.** The system produces aggregate distributor-level measurements. It does not decide credit, terms, supply or any individual's treatment, and it produces no legal or similarly significant effect for any data subject.

**Design constraint that keeps this true:** the deliverable is a **ranking aid**, and a human decides. Every displayed figure must carry its supporting interactions. Band thresholds are set by human capacity ("how many accounts can be worked this month"), never by a model probability cut-off. See roadmap §10 and §14 item 7.

`[[DPO_NAME]]` to confirm this position or qualify it.

---

## 7. Consultation

| Party | Needed? | Status |
|---|---|---|
| Data Protection Officer | **Yes** | `[[DPO_NAME]]` — `[[STATUS]]` |
| Works council / employee representatives | **Only if** shared mailboxes or controller-staff monitoring enter scope | Ask drafted: [`04_WORKS_COUNCIL_ASK_mail.md`](04_WORKS_COUNCIL_ASK_mail.md) |
| Distributors (data subjects) | **Transparency notice** — not consent | Wording: [`03_ART13_14_NOTICE_mail.md`](03_ART13_14_NOTICE_mail.md) |
| IT security | Yes — for any future LLM route | `[[IT_CONTACT]]` |
| Procurement / vendor review | Yes — only if an LLM route is named | `[[PROCUREMENT_CONTACT]]` |

---

## 8. Sign-off

| Field | Value |
|---|---|
| DPIA reference | `[[DPIA_REF]]` |
| DPO name | `[[DPO_NAME]]` |
| DPO opinion | `[[DPO_OPINION — accept / accept with conditions / reject]]` |
| Conditions imposed | `[[CONDITIONS]]` |
| Signed date | `[[SIGN_DATE]]` |
| Review date | `[[REVIEW_DATE]]` — recommended 12 months, or on any scope change |
| Supersedes | Nothing. First DPIA for this processing |

**Scope change triggers a re-assessment:** shared mailboxes · any LLM or external service · output leaving the machine · a change in what is stored.

---

## 9. Open items for the DPO

1. Confirm the DPIA trigger assessment in §1, or record a reasoned downgrade.
2. Confirm the body hash is acceptable as pseudonymous rather than personal data.
3. Confirm the residual re-identification risk (R2) is acceptable at the current aggregation level.
4. Confirm the Art. 22 position in §6.
5. Name the retention-job owner — R6 is the one risk where the control exists but is not operated.
6. Decide whether the shared `Sales` / `Parts` mailboxes are in scope. If yes, the works-council step is a precondition, not a parallel task.
