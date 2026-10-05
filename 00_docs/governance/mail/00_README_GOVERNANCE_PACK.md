# Mail governance pack — index

**Created:** 2026-09-22 · **Owner:** Jerome (VP Sales ISZE) · **Status:** drafts, nothing filed
**Gate this pack exists to close:** **G0b** — *anything leaving the device, or touching shared mailboxes*
**Roadmap:** [`../roadmaps/ai_sales_intelligence.md`](../roadmaps/ai_sales_intelligence.md) §2 (gates), §3 (P0), §14 (compliance checklist)
**Predecessor (signed):** [`../G0A_LOCAL_MAIL_SCOPE.md`](../G0A_LOCAL_MAIL_SCOPE.md) — local-only, own mailbox, authorized 2026-08-12

This folder turns "we should do a DPIA" into five documents that can be submitted. Each one is short on purpose. Every field that needs a person, a date or a legal judgement is written as an explicit `[[PLACEHOLDER]]` — a placeholder is a request, not a filled answer. **Nothing in this folder is signed, and nothing in this folder permits egress.**

---

## Why this pack exists now

Jerome said "go ahead please" (2026-09-22). That authorises work. It does **not** name an approved LLM route, and it does not satisfy G0b. The roadmap §4 defines G0b as closing when *all* of the following exist:

| G0b condition (roadmap §4) | Document in this pack | State |
|---|---|---|
| DPIA approved | [`01_DPIA_OUTLINE_mail.md`](01_DPIA_OUTLINE_mail.md) | Draft, unscreened |
| LIA written | [`02_LIA_OUTLINE_mail.md`](02_LIA_OUTLINE_mail.md) | Draft, unscreened |
| Art. 13/14 notice | [`03_ART13_14_NOTICE_mail.md`](03_ART13_14_NOTICE_mail.md) | Draft wording |
| Works-council step done | [`04_WORKS_COUNCIL_ASK_mail.md`](04_WORKS_COUNCIL_ASK_mail.md) | Ask drafted, not sent |
| Retention policy | [`05_RETENTION_SCHEDULE_mail.md`](05_RETENTION_SCHEDULE_mail.md) | Draft, consistent with what P2a already does |
| LLM DPA + zero-retention + EU residency in writing | **Not started** — needs a named vendor | Open |
| **Approved LLM route named** | **Not started** — needs Jerome | **Open — the single blocking name** |

**Read this consequence carefully:** five of the seven can be advanced by paperwork. Two cannot be advanced by anyone in this workspace, because they name a third party (the vendor) and a decision (the route). That is why "go ahead" produces a governance pack rather than a running language model.

---

## The one rule that governs this whole folder

**Bodies, subjects, senders and addresses never leave this machine.** Not in an email to the DPO. Not in a chat. Not pasted into an external tool. Not as an example. Not redacted "just one".

Every document in this folder is written so it can be submitted **without** attaching a single message. If a reviewer needs to see a sample, they come to the machine under G0a, or they get the derived-field schema (which is what [`01_DPIA_OUTLINE_mail.md`](01_DPIA_OUTLINE_mail.md) §4 describes).

---

## What "go ahead" already unlocked (no signature needed, no egress)

These were already possible before 2026-09-22 and remain possible now. Nothing here waits on G0b.

- Refresh the local deterministic tables from the own mailbox (in the agent browser / classic Outlook, when Jerome is present)
- Rebuild `account_health.parquet` — the deterministic P4 signal layer
- Recompute response latency, commitment keep-rate, signal→order latency, topic entropy, escalation cadence
- Refresh the retention dry-run audit
- Answer the P4 calibration task (4.9) sitting with Jerome
- The P1 / P5 workstreams (catalogue coverage, forecast) — untouched by mail governance

See `01_data/90_INBOX/MAIL_NEXT_STEP_2026-09-22.md` for the operational version of this list.

---

## What is blocked until G0b closes

| Blocked | Why |
|---|---|
| Any language model touching mail text (P2b: intent, sentiment, implicit commitments) | G0b + named route (B1b) |
| Shared **Sales** and **Parts** mailboxes | G0b **+ works-council** — colleagues' correspondence, not Jerome's |
| Draft generation into Outlook, digests, any outbound automation (P3) | G0b |
| Engagement profiling (P6) | G0b + P2b |
| Any artefact derived from the interaction layer that leaves this machine | G0a §6 / §7 |

---

## Boundary record (what this session did and did not do)

| Check | Result |
|---|---|
| Mail body, subject, sender or address transmitted off this machine | **None.** No network call of any kind was made |
| Graph / OAuth / tenant consent / new mailbox connection created | **None** |
| Bulk mail pull executed | **None.** Source tables were read, not refreshed |
| Outlook opened by an agent | **No** |
| Shared Sales / Parts mailbox read | **No** |
| Mail sent | **No** — and `Mail.Send` is not requested anywhere in this stack |
| New `alwaysApply` rule added | **No** |
| Files written | `00_docs/governance/mail/` (6 docs) + `01_data/90_INBOX/MAIL_NEXT_STEP_2026-09-22.md` |

Everything above is derived from files already on local disk under G0a.
