# Works-council ask — mail interaction layer

**Status:** DRAFT ASK — not sent, not reviewed.
**Owner:** `[[HR_OWNER]]` · **Sponsor:** Jerome, VP Sales ISZE · **Date:** `[[DATE]]`
**Roadmap ref:** `../roadmaps/ai_sales_intelligence.md` §5 task 0.5, §14 item 10, blocker **B1c**
**Related:** [`01_DPIA_OUTLINE_mail.md`](01_DPIA_OUTLINE_mail.md) · [`03_ART13_14_NOTICE_mail.md`](03_ART13_14_NOTICE_mail.md) · [`05_RETENTION_SCHEDULE_mail.md`](05_RETENTION_SCHEDULE_mail.md)

**Scope of this ask:** the **shared `Sales` and `Parts` mailboxes**, and only those. The own-mailbox processing is already authorized separately under [`../G0A_LOCAL_MAIL_SCOPE.md`](../G0A_LOCAL_MAIL_SCOPE.md) and is **not** part of this consultation.

---

## 1. What we are asking

We request the council's view before we extend a local, deterministic email-measurement process from the account holder's own mailbox to two **shared** mailboxes — `Sales` and `Parts`.

We are consulting **before** doing it. No processing of shared-mailbox content has taken place, and none will until this step concludes.

`[[HR_OWNER]]` to confirm the correct body (`[[WORKS_COUNCIL_BODY_NAME]]`) and the correct procedure under the applicable Dutch or local consultation framework. **`[[LEGAL_OWNER]]` must confirm whether this is an advice right, a consent right, or an information duty in this specific case before the ask is sent** — the answer changes the wording of §5.

---

## 2. Why the shared mailboxes matter, and why they are the delicate part

The own mailbox contains the account holder's correspondence with distributors. The shared `Sales` and `Parts` mailboxes contain **colleagues' correspondence** — including internal exchanges that were never addressed to the account holder and were never intended for analysis.

That is a different processing situation, and we are treating it as one:

- The data subjects change. They become our own staff, not only distributor staff.
- The reasonable-expectations question is harder. A colleague writing to a shared sales mailbox does not expect measurement of their response time.
- Whether the employer may do this at all is a consultation question, not a technical one.

**We are not asking the council to approve the own-mailbox processing, which is outside this scope.** We are asking whether the shared mailboxes may be brought in, and on what conditions.

---

## 3. What the processing actually is — stated plainly

Answer these as questions the council will ask, in the order they will ask them.

| Question the council will ask | Answer |
|---|---|
| **Does a person read the emails?** | No. Software extracts metadata and counts. No human reads correspondence for this purpose |
| **Does an AI or external service see the content?** | **No.** No content leaves the machine. No language model, no cloud service, no vendor. This is the current design and it is a hard boundary |
| **What is written down about a person?** | A pseudonym, a functional role (for example parts manager), and activity counts — number of messages, first and last contact, response times. **No name, no e-mail address, no text** |
| **Are individual performance assessments produced?** | **No.** Output is aggregate per distributor: median reply time, share of dated promises kept, message volume, topic mix. Not per person. The role label exists so we can tell a workshop contact from a finance contact, not to evaluate anyone |
| **Could it be used for performance management?** | Not under this design, and purpose limitation is written into the assessment. If the council wants that prohibition recorded as a condition, we will record it |
| **How long is it kept?** | 24 months from the message date, then deleted. Full schedule: [`05_RETENTION_SCHEDULE_mail.md`](05_RETENTION_SCHEDULE_mail.md) |
| **Can someone have their data deleted?** | Yes, within 30 days of a request, by pseudonym. Procedure exists: [`../DSAR_ERASURE_RUNBOOK.md`](../DSAR_ERASURE_RUNBOOK.md) |
| **Can someone opt out?** | `[[OPT_OUT_POSITION]]` — **this is a policy decision for HR/legal, not an engineering one. State it explicitly rather than leaving it implicit.** An honest answer here is worth more than an evasive one |
| **What has already been done?** | Own-mailbox processing only, since 2026-08-12, under a written scope memo, local only. Nothing from a shared mailbox, ever |
| **What happens if the council says no?** | The shared mailboxes stay out of scope. The programme still runs on the own mailbox, the structured sales data and the forecast. **The shared-mailbox corpus is an enhancement, not a foundation** |

**Be careful with the last row.** Say it because it is true — the programme does not die without the shared mailboxes. It is a real, honest fallback, and it makes the consultation genuine rather than a formality.

---

## 4. What we are not asking

- We are not asking about the account holder's own mailbox. That is authorized separately.
- We are not asking to send any automated message to anyone, ever. `Mail.Send` is not requested anywhere in this system.
- We are not asking to profile anyone's personality, temperament or attitude. That was explicitly designed out — the roadmap's original "personality-driven playbooks" was renamed to account-level engagement behaviour precisely to avoid this.
- We are not asking to monitor attendance, working hours, productivity or private communication. Non-distributor mail is discarded before any field is read.

---

## 5. Questions for the council

1. Does the council consider the shared `Sales` / `Parts` mailboxes to be within scope of our consultation right? `[[LEGAL_OWNER]]` to confirm the procedural framing first.
2. What conditions would the council require?
3. Does the council want the role-only restriction and the no-performance-management purpose recorded as binding conditions?
4. Does the council want sight of the DPIA and the retention schedule before deciding?
5. Does the council want a periodic report — for example annually — confirming what is processed and that retention was enforced?
6. Does the council want the own-mailbox processing to be reported to it as well, even though it is out of scope for approval?

---

## 6. What this ask does not replace

| Required anyway | Why |
|---|---|
| DPIA | [`01_DPIA_OUTLINE_mail.md`](01_DPIA_OUTLINE_mail.md) — required independently |
| LIA | [`02_LIA_OUTLINE_mail.md`](02_LIA_OUTLINE_mail.md) — required independently |
| Art. 13/14 notice to staff | [`03_ART13_14_NOTICE_mail.md`](03_ART13_14_NOTICE_mail.md) — staff are data subjects too |
| Retention enforcement actually running | [`05_RETENTION_SCHEDULE_mail.md`](05_RETENTION_SCHEDULE_mail.md) §3 — **currently not scheduled** |

A works-council consultation does not substitute for any of these. All four must close before shared mailboxes enter scope.

---

## 7. Ask log

| # | Step | Owner | Status |
|---|---|---|---|
| 1 | Confirm the correct body and the procedural framing | `[[LEGAL_OWNER]]` | `[[STATUS]]` |
| 2 | Decide the `OPT_OUT_POSITION` in §3 | `[[HR_OWNER]]` + `[[LEGAL_OWNER]]` | `[[STATUS]]` |
| 3 | Send the ask | `[[HR_OWNER]]` | `[[STATUS]]` |
| 4 | Council response | `[[WORKS_COUNCIL_BODY_NAME]]` | `[[STATUS]]` |
| 5 | Conditions recorded and implemented | `[[HR_OWNER]]` | `[[STATUS]]` |
| 6 | Only then: extend scope, update the G0a memo, re-run the collector | Eng | Blocked |

**Until step 6 completes, the shared mailboxes are out of scope and the collector's own-store guard stays in place.**
