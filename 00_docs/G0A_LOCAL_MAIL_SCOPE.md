# G0a — local mail processing scope memo

**Date:** 2026-08-12 · **Owner:** VP Sales ISZE · **Roadmap:** [`roadmaps/ai_sales_intelligence.md`](roadmaps/ai_sales_intelligence.md) §5, §7.4
**Status:** **AUTHORIZED 2026-08-12** (Jerome “go”) — P2a collector may run on own mailbox. Still does **not** cover P2b / P3 / P6 / shared mailboxes (**G0b**).
**G0b pack (2026-09-22):** drafts to close the wider gate — DPIA, LIA, Art. 13/14 notice, retention schedule, works-council ask — are in [`governance/mail/`](governance/mail/00_README_GOVERNANCE_PACK.md). None is signed; this memo remains the only authority for local own-mailbox processing.

This is the one-page record that makes the local collector a controlled activity rather than an ad-hoc script. It is deliberately narrow: everything that would widen it is listed in §7 as explicitly out of scope.

---

## 1. Purpose

Measure how commercial signals travel between ISZE and its distributors, so that response latency, signal→order latency and commitment reliability become measurable. These three metrics do not exist today in any system (roadmap §1.1).

## 2. Legal basis

Legitimate interest (GDPR Art. 6(1)(f)) — operational analysis of the controller's own business correspondence, by the account holder, on data the account holder already lawfully accesses. No new access right is created or exercised.

A full LIA is **not** required at this scope because processing is local, produces no content store, and generates no output about any identified person. It **is** required before G0b. Do not read this memo as covering G0b.

## 3. Scope — what is processed

| | |
|---|---|
| **Mailbox** | `jerome.van.der.pluym@isuzu-e.com` only — the account holder's own |
| **Folders** | Inbox + **Inbox subfolders**, Sent Items + **Sent subfolders** (own store only; recurse via COM `Folders`) |
| **Filter** | Only messages where a distributor domain from `04_tools/interactions/db_domains.yaml` appears as sender or recipient. Everything else is discarded before any field is read |
| **Access** | Local MAPI/COM against the installed Outlook profile — read-only, no OAuth, no app registration, no new permission |
| **Egress** | None remote. Collector blocks remote `create_connection`; local COM/RPC to Outlook remains (required) |

## 4. Data minimisation — what is stored

**Stored:** timestamps, direction, thread id, DB code, `folder` path (e.g. `inbox/Archive`), pseudonymous stakeholder id (salted SHA-256), counterparty domain, recipient counts, topic tags, validated part numbers, counts of amounts/dates, an explicit-commitment boolean, attachment count, subject **length**, body **length**, body SHA-256, commitment type / due date / `sentence_sha256` (never the sentence text).

**Never stored:** message bodies · subjects · attachments · attachment names · sender or recipient names · plain e-mail addresses.

The body hash exists to prove provenance without retaining the text. The salt lives at `%LOCALAPPDATA%\ISZE\interactions_salt.txt`, outside the repository, and is never committed.

## 5. Retention

24 months from message date, written into each row as `retention_expires`. Hard-delete job: `04_tools/interactions/purge_expired.py` (roadmap task 2a.6 — dry-run default; `--apply` writes). First delete cycle falls due 24 months after the oldest retained row. DSAR locate/erase (by `stakeholder_id`, ≤30 days): [`DSAR_ERASURE_RUNBOOK.md`](DSAR_ERASURE_RUNBOOK.md).

## 6. Output and access

`01_data/17_interactions/` — git-ignored, local disk only. Visible to the account holder. Nothing derived from it goes into a deck, a dashboard or a distributor-facing document without a separate decision.

**Small-n rule:** no DB × topic cell with fewer than 10 messages is displayed or quoted.

## 7. Explicitly out of scope under G0a

| Out of scope | Gate that would allow it |
|---|---|
| Shared **Sales** and **Parts** mailboxes (colleagues' correspondence) | G0b + works-council step |
| Sending any content to an LLM or any external service | G0b + named approved route (B1b) |
| Intent classification, sentiment, engagement profiling | G0b (P2b / P6) |
| Draft generation, digests, any outbound automation | G0b (P3) |
| Any output naming an individual | never — roles only |
| Storing another OEM's pricing intent found in correspondence | never — dropped at extraction |

## 8. Review

Revisit when: (a) shared mailboxes are proposed for inclusion, (b) any LLM step is added, (c) output leaves this machine, (d) classic Outlook is replaced by New Outlook and the collector is rewritten. Any of those four voids this memo and requires G0b.
