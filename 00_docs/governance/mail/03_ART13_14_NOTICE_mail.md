# Art. 13/14 transparency notice — distributor correspondence measurement

**GDPR Art. 13/14 · information to data subjects**
**Status:** DRAFT WORDING — not issued, not legal-reviewed.
**Owner:** `[[LEGAL_OWNER]]` · **Date:** `[[DATE]]` · **Version:** `[[VERSION]]`
**Roadmap ref:** `../roadmaps/ai_sales_intelligence.md` §5 task 0.4, §14 item 3
**Related:** [`02_LIA_OUTLINE_mail.md`](02_LIA_OUTLINE_mail.md) · [`01_DPIA_OUTLINE_mail.md`](01_DPIA_OUTLINE_mail.md)

**Why Art. 14 and not Art. 13.** The personal data is not collected from the data subject; it comes from correspondence the controller already holds. Art. 14 therefore applies. Where the same notice is given to the controller's own staff, Art. 13 applies and the same wording works with `[[EMPLOYER]]` substituted.

**Two channels, same wording:**
1. A **contract annex** for distributor organisations — `[[ANNEX_REFERENCE]]`, issued to `[[DISTRIBUTOR_CONTACT]]`, effective `[[EFFECTIVE_DATE]]`
2. A **public/internal privacy page** at `[[PRIVACY_PAGE_URL]]`

---

## DRAFT WORDING BEGINS

### How we measure our service to you

**Who we are.** `[[CONTROLLER_LEGAL_ENTITY]]` ("we"). Contact for this notice and for your rights: `[[PRIVACY_CONTACT]]`, `[[PRIVACY_CONTACT_ADDRESS]]`.

**What this is about.** We measure how well we serve our distributors. Three things we could not previously measure: how quickly we reply to you, how long it takes between you telling us you need something and an order being placed, and whether we keep the delivery and pricing promises we make in writing. We do this by analysing our own e-mail correspondence with you.

**Why we do it.** It is our legitimate business interest to run our distributor service well (Art. 6(1)(f) GDPR). We have assessed this and concluded that it does not override your interests, because of how little data we keep and because nothing is decided about you as an individual. You can ask us for a summary of that assessment.

**What we actually read and keep.** We analyse the correspondence we exchange with your organisation. From it we record:

- when a message was sent and whether it came in or went out
- which distributor organisation it concerns
- the topic area, taken from a fixed short list (for example pricing, availability, warranty, logistics)
- part numbers, checked against our parts catalogue
- **how many** amounts and dates appear — **not** the amounts or the dates themselves
- whether the message contains a dated promise, and when that promise was due
- whether someone is answering in a known role (for example parts manager), recorded under a **pseudonym**, not a name

**What we never keep.** We do not store, in any form:

- the text of any message or its subject line
- any attachment or attachment name
- your name, or anyone's name
- any e-mail address in readable form

We keep a cryptographic fingerprint of the message text. That lets us prove which message a figure came from without holding the text itself.

**What we do not do.** We do not use this to assess any individual's performance. We do not sell it or share it. We do not use it to train any external artificial-intelligence service. We do not send you automated messages, and no automated system replies to you on our behalf. Nothing here makes a decision about you, and no message content is transferred outside `[[SITE]]`.

**How long we keep it.** 24 months from the date of the message, then deleted. The technical measurements are deleted by an automated job; the original messages in our mailbox follow our normal mailbox retention policy, which is separate.

**Your rights.** You may ask to see what we hold, ask us to correct it, ask us to delete it, object to the processing, or ask us to restrict it. Contact `[[PRIVACY_CONTACT]]`. `[[COMPLAINT_AUTHORITY — e.g. the Dutch DPA (Autoriteit Persoonsgegevens)]]` handles complaints. If you ask us to delete your data, we will locate and delete the measurements relating to you within 30 days.

**How to reach us.** `[[PRIVACY_CONTACT]]` · `[[PRIVACY_CONTACT_ADDRESS]]` · `[[PRIVACY_CONTACT_EMAIL]]`

**Last updated.** `[[EFFECTIVE_DATE]]` · **Previous version.** `[[PREVIOUS_VERSION]]`

## DRAFT WORDING ENDS

---

## How to issue this

| # | Step | Owner | Status |
|---|---|---|---|
| 1 | Legal review and approval of the wording above | `[[LEGAL_OWNER]]` | `[[STATUS]]` |
| 2 | Translate for Dutch-speaking distributor contacts if the contract language requires it | `[[LEGAL_OWNER]]` | `[[STATUS]]` |
| 3 | Decide whether it goes out as a contract annex, a standalone notice, or both | `[[LEGAL_OWNER]]` + Jerome | `[[STATUS]]` |
| 4 | Name the notice in the LIA (`LAWFUL` condition 6) — **the LIA does not hold without it** | `[[LEGAL_OWNER]]` | `[[STATUS]]` |
| 5 | Set the review cadence — recommend annually, and on any scope change | `[[LEGAL_OWNER]]` | `[[STATUS]]` |

---

## Things this notice must not become

- **Not a consent request.** The basis is legitimate interest. Wording that reads like a consent form turns an Art. 6(1)(f) assessment into a consent collection exercise and weakens the position.
- **Not a marketing message.** No distributor-facing sales content in the same communication.
- **Not a place for internal terms.** No codenames, no phase numbers, no programme names. A distributor reads this; the register reference belongs in the cover note, not in the notice.

---

## Open items for legal

1. Confirm Art. 14 and confirm the "disproportionate effort" question — if data subjects are very numerous, Art. 14(5)(b) allows a public notice instead of individual notice. `[[LEGAL_OWNER]]` to decide and record.
2. Name the complaint authority and the privacy contact.
3. Confirm the 30-day deletion commitment is achievable (the DSAR runbook supports it — [`../DSAR_ERASURE_RUNBOOK.md`](../DSAR_ERASURE_RUNBOOK.md)).
4. Confirm the sentence about not training external AI services will remain true. **It is true today** — no external service is used. If an LLM route is later named, this sentence must be revisited before it becomes inaccurate.
5. Decide whether the contract annex needs distributor-side signature to be effective, and if so who collects it.
