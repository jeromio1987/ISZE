# Legitimate-interest assessment (LIA) — distributor correspondence analysis

**Art. 6(1)(f) GDPR · Legitimate Interests Assessment**
**Status:** OUTLINE — unscreened, unsigned. A structure to be completed and approved, not an approval.
**Owner:** `[[LEGAL_OWNER]]` · **Prepared by:** `[[PREPARER_NAME]]` · **Date:** `[[DATE]]`
**Roadmap ref:** `../roadmaps/ai_sales_intelligence.md` §5 task 0.3, §14 item 2
**Related:** [`01_DPIA_OUTLINE_mail.md`](01_DPIA_OUTLINE_mail.md) · [`03_ART13_14_NOTICE_mail.md`](03_ART13_14_NOTICE_mail.md)

**Handling rule:** complete without attaching any message. Do not quote a distributor's wording to demonstrate a business interest.

---

## 0. Scope of this LIA

This LIA covers **local, deterministic processing of the controller's own business correspondence** for operational measurement.

It **excludes**:
- any transfer to a third-party service or language model — that needs a separate assessment plus a vendor DPA, SCCs, zero-retention and EU residency in writing
- the shared `Sales` / `Parts` mailboxes — colleagues' correspondence, which requires the works-council step

Read with: [`00_README_GOVERNANCE_PACK.md`](00_README_GOVERNANCE_PACK.md).

---

## 1. The three-part test

Art. 6(1)(f) requires all three. Write each answer, then state the conclusion. Do not skip to the conclusion.

### 1.1 Purpose test — is there a legitimate interest?

| Candidate interest | Legitimate? | Whose? |
|---|---|---|
| Measuring and improving the controller's own response time to distributor enquiries | Yes | Controller |
| Understanding how long elapses between a distributor's stated need and an order | Yes | Controller |
| Knowing whether commitments made in correspondence are kept | Yes | Controller **and** distributor |
| Admin efficiency in handling routine distributor correspondence | Yes | Controller |

**Character of the interest:** operational and administrative. It is not marketing, not profiling for persuasion, and not surveillance of individuals. The controller is analysing **its own service performance**, measured from correspondence in which it is a party.

`[[LEGAL_OWNER]]` to state the primary interest in one sentence and confirm it is the interest actually served by the processing.

### 1.2 Necessity test — is the processing necessary?

| Question | Answer |
|---|---|
| Is there a less intrusive way to measure response latency? | No. No CRM, no ticket system, no call transcripts, no lead log exist (roadmap §1.2). Manual sampling cannot produce a p50/p90 |
| Can the purpose be met with less data? | The current design stores metadata and counts only. §4 of the DPIA is the answer to this question |
| Could aggregate distributor-level data suffice without any person-level data? | **Partly — but not fully.** Latency and commitment-keeping are measured at the level of *who replied*, which is a role, not a person. `[[LEGAL_OWNER]]` to test the boundary: what is the least person-linked design that still measures the thing? |
| Is the volume proportionate? | 30% of examined mail in the last run matched a distributor domain. The rest is discarded before any field is read |

**Round-trip test (a fairness argument in the controller's favour, state it):** the distributor benefits from faster replies and from the controller keeping its own promises. This is not a one-way extraction. Task 6.3 of the roadmap goes further — showing a distributor the profile built about them and asking if it is right. `[[LEGAL_OWNER]]` to decide whether that should be a condition of this LIA rather than a later design choice.

### 1.3 Balancing test — do the subject's interests override?

| Factor | Assessment |
|---|---|
| **Nature of the data** | Business correspondence metadata. **No special category data** — hard-blocked at extraction |
| **Reasonable expectations** | A distributor's parts manager writing to a supplier's sales lead expects the supplier to read, act on and follow up the message. They do not necessarily expect structured measurement of it. **This is the weakest point of the assessment and should be written as such** |
| **Impact on the subject** | No decision is taken about any individual. Nothing is published about them by name. The realistic worst case is discomfort on learning that response times are measured — not a loss of rights, employment or service |
| **Relationship** | B2B counterparties, not consumers. Not employees, unless shared mailboxes later enter scope — at which point this LIA is void and the works-council step applies |
| **Vulnerability** | Adults in a professional capacity, acting for an organisation |
| **Safeguards** | Roles never names · 10-signal display floor · small-n suppression · no bodies stored · no egress · DSAR path proven · purpose limitation recorded |

**Balance:** the interest is real, the data is minimal, the impact is low, and the safeguards are structural rather than procedural. **Subject to §2.**

---

## 2. Conditions

State these as binding on the processing. If a condition is not met, the LIA does not hold.

1. **Local only.** No transfer of text, subjects, senders or addresses to any external service. Any egress voids this LIA and requires the full G0b package plus a vendor assessment.
2. **Own mailbox only.** Shared mailboxes remain out of scope until the works-council step is complete.
3. **No named individuals in output.** Roles only, always.
4. **Purpose limitation.** The derived data is used for operational measurement. It is **not** an input to individual performance assessment, and not a lever in commercial negotiation.
5. **No special category data**, and no retained competitor pricing intent.
6. **Transparency.** The Art. 13/14 notice is issued — see [`03_ART13_14_NOTICE_mail.md`](03_ART13_14_NOTICE_mail.md). **A LIA without the notice is not a defensible LIA.**
7. **Retention actually enforced.** The purge job is scheduled and its audit reviewed. **Currently open — the script exists but is not scheduled.** An unenforced retention promise undermines the balancing test.

---

## 3. Conclusion

| Field | Value |
|---|---|
| Outcome | `[[OUTCOME — legitimate interest substantiated / substantiated with conditions / not substantiated]]` |
| Conditions adopted | `[[CONDITIONS_ADOPTED]]` |
| Legal owner | `[[LEGAL_OWNER]]` |
| Signed date | `[[SIGN_DATE]]` |
| Review date | `[[REVIEW_DATE]]` |

---

## 4. Open items for legal

1. State the primary interest in one sentence (§1.1).
2. Test the least person-linked design that still measures latency (§1.2) — this is the item most likely to change the engineering.
3. Decide whether *showing the profile to the distributor* (roadmap task 6.3) is a **condition** of this LIA or a downstream design choice. Making it a condition is the stronger position and costs little.
4. Confirm that annual review is the right cadence, or set a shorter one.
5. Confirm the reasonable-expectations weakness in §1.3 is disclosed to the DPO rather than smoothed over.
6. Name the owner of the retention job — condition 7 is currently a promise without an operator.
