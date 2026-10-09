# Measurement report — mail, order channel, time

**Date:** 2026-10-07 · **Prepared for:** Jerome · **Internal only**

This answers four questions that came out of the milestone-catalogue session: how
much mail we receive now versus the same month last year, where the SPA upside
is, who could move to EDI, and how much time each tool saves. Two of the four
could be measured today. Two could not, for a reason worth stating plainly
rather than guessing around.

---

## 1. Mail volume — measured, with one hard limit

**Result:** a clean, 13-month, zero-error count of every message in the mailbox.

Tool: `04_tools/interactions/measure_mail_volume.py` (read-only; counts dates
only, never a subject or a body). Output:
`01_data/17_interactions/mail_volume_monthly.csv` and `.json`.

| Month | Received | Sent | Total |
|---|---:|---:|---:|
| 2025-10 | 1,746 | 130 | 1,876 |
| 2025-11 | 1,907 | 308 | 2,215 |
| 2025-12 | 1,471 | 247 | 1,718 |
| 2026-01 | 1,869 | 295 | 2,164 |
| 2026-02 | 1,999 | 223 | 2,222 |
| 2026-03 | 2,154 | 436 | 2,590 |
| 2026-04 | 2,824 | 406 | 3,230 |
| 2026-05 | 1,740 | 226 | 1,966 |
| 2026-06 | 1,653 | 271 | 1,924 |
| 2026-07 | 2,046 | 499 | 2,545 |
| 2026-08 | 1,541 | 234 | 1,775 |
| 2026-09 | 1,709 | 296 | 2,005 |
| 2026-10 | 448 | 127 | 575 (to 7 Oct) |

**The limit you have to know about.** The mailbox as this PC sees it holds
**exactly 12 months**. The oldest message is dated 2025-10-07, and the count is
23,107 in the Inbox and 26,805 across Inbox and Sent. Anything older than twelve
months is not on this machine to count.

**What that means for your question.** "Less mail than the same month last year"
**cannot be answered from history**, because last year's same month is not on the
machine. The one apparent year-on-year pair — October 2026 against October 2025
at −69% — is an artefact: October 2026 is seven days old, not a month. It must
not be quoted.

**What we can do about it.** We now have a dated, monthly baseline from October
2025. If the snapshot is kept and re-run each month, the true year-on-year builds
itself from here — but only going forward. Miss a month and that comparison is
gone with the mailbox.

**What it does not cover.** Own mailbox only. The shared Sales and Parts mailboxes
are a separate decision (governance gate G0b) and are not in these numbers.

---

## 2. Order channel — the EDI proxy failed its own test

**Result: negative. The method does not work on the current data.**

The billing extract has no order-type field, so there is no column that says "this
line came in by EDI". The plan was to use the customer purchase-order reference as
a proxy: a manual order carries a PO, an EDI order normally does not.

Tool: `04_tools/interactions/measure_order_channel.py`. Output:
`01_data/00_derived/order_channel_by_distributor.csv`.

What it found:

| Year | Lines | Lines with no PO | No-PO share |
|---|---:|---:|---:|
| 2023 | 123,610 | 50 | 0.0% |
| 2024 | 141,823 | 34 | 0.0% |
| 2025 | 136,501 | 39 | 0.0% |
| 2026 | 94,940 | 23 | 0.0% |

The purchase-order field is populated on essentially every line — 99.97%. That
includes Petros Petropoulos, a distributor on EDI, whose no-PO share is also
0.0%. So the proxy does not separate EDI from manual ordering at all, and it must
not be used to rank distributors. The script says so itself in its validation
output.

**What this means.** You cannot tell, from anything on this machine, which
customer orders by EDI today. To answer it we need one of:

1. An order-type or order-source field on the SAP extract (the clean route), or
2. A list from IT of which customers are on EDI, joined to billing by customer.

Until then, the EDI question is unanswerable, and any number offered for it would
be invented.

---

## 3. SPA — no register exists to answer "what I could secure"

**Result: cannot be answered as asked, and the reason is structural.**

There is no SPA status file anywhere in the workspace. What exists is the history
of individual cases as spreadsheets (`ISZE_SPA_Optimizer_V4.xlsx` with its "MD
Approval Request" sheet, `SPA_2026_UTI_12M`, the PMS SPA study) and one run-rate
page for UTI only (`02_dashboards/sales/ISZE_SPA_RunRate_UTI.html`).

Nothing records, per case, whether it was proposed, approved, active, expired or
declined. So "all the SPAs I could manage to secure" has no source: you cannot
total what was secured without a case list, and you cannot project the upside
without it either.

**Two halves, two different needs:**

- **What was secured** needs a case register: one row per case (customer, part or
  basket, value, status, owner, dates). Cheap to build as a table; the work is
  keeping it filled, not coding it.
- **What could still be secured** is estimable — from the price-gap work, the
  classification and the capture data — but it needs the register underneath it
  first, so the estimate can be compared against what actually happened.

**Note on the shape.** A "what I could secure" list is a report, and on 2026-09-24
you cancelled reporting as the product (`TWO_PILLAR_DESIGNS_2026-09-24.md`). The
version that survives your own test is a workflow: a SPA case that is stuck at
approval and pushes a nudge to whoever holds it. The register is the same table
either way; the difference is whether it sits still or pushes.

---

## 4. Time saved — method set, nothing measured yet (on purpose)

**Result: a method and a log, no numbers.** This is deliberate, not an omission.

The ROI model in `00_docs/roadmaps/ai_sales_intelligence.md` §8.5 is a formula
with its inputs left to measure, and it says in plain words not to fill it with
illustrative figures in any shared document. The value ledger's hours column is
blank for the same reason.

New file: `00_docs/TIME_SAVED_MEASUREMENT.md` — three measurement methods
(before/after clock, volume × unit cost, or "not measured"), what a line must
carry to count, and a per-tool table of what is measurable and what the honest
limit is for each tool.

The per-tool table is the short version:

| Tool | Measurable? | How | The limit to state |
|---|---|---|---|
| Tender Monitor | Yes | Count notices per week × time per manual triage | Covers finding, not reading or bidding |
| Price scrapers | Yes | Parts priced per run | Covers collection, not the decision |
| PRISM | Yes | One question in the app vs by hand | One task, one person |
| Action Ledger | Yes | Items per run | Covers the list, not acting on it |
| Mail layer | Yes | Messages processed | Own mailbox only |
| SPA application | Yes | One basket by hand vs the tool | Covers building, not negotiating |
| Forecast / account health | Hard | Before/after account read | Value is a changed decision, not hours |
| Classification / AIM | Partial | Parts classified | Largely one-time, not recurring hours |
| Dealer ranking | Yes | Dealers scored per country | Covers the scoring, not the meeting |

To turn any row into a number, one real task has to be timed and written into the
log in that file. Until then it stays "not measured".

---

## What I would do next, in order

1. **Keep the mail snapshot.** One monthly re-run keeps the year-on-year building.
   Cheapest real win available, and it costs a scheduled task.
2. **Ask IT for the order-type field** (or the EDI customer list). One question,
   and it unlocks the whole EDI and supplier-list line.
3. **Build the SPA case register** as a plain table, then decide whether it stays a
   report or becomes a nudge-to-owner workflow.
4. **Time three tasks** — one tender week, one price-scraper run, one PRISM
   question — and fill the first three rows of the time log.

## Files from this session

- `04_tools/interactions/measure_mail_volume.py` — new (read-only mail counter)
- `04_tools/interactions/measure_order_channel.py` — new (EDI proxy, negative result)
- `00_docs/TIME_SAVED_MEASUREMENT.md` — new (method + log)
- `01_data/17_interactions/mail_volume_monthly.csv` / `.json` — new (the measurement)
- `01_data/00_derived/order_channel_by_distributor.csv` / `.meta.json` — new
