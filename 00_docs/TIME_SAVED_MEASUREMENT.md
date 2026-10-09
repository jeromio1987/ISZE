# Time saved by a tool — how to measure it, and the log

**Purpose:** a per-tool time figure, measured on real tasks, not estimated. This
file is the method and the running record. It exists because the ROI model in
`00_docs/roadmaps/ai_sales_intelligence.md` §8.5 says, in plain words, not to
populate a time figure with illustrative numbers, and because the value ledger's
hours column is blank for the same reason.

**Rule for anything that leaves this machine:** a time cell stays blank until a
timed observation sits behind it. No figure is ever derived from "this is
probably about an hour".

---

## The method — three ways to get a number, cheapest first

You do not need a stopwatch on everything. Use the cheapest method that the tool
allows, and say which method produced the number.

| Method | How | Good for | Honesty level |
|---|---|---|---|
| **A. Before/after clock** | Time the same task by hand once, then time it with the tool. One or two runs each. | A repeatable task: building a weekly view, pulling a price gap, drafting a mail | Strongest. Use wherever possible |
| **B. Volume x unit cost** | Count the items the tool processed in a period, multiply by a stated time per item | Scrapers, collectors, batch joins (e.g. N notices x M minutes) | Medium. The count is measured; the unit cost is a stated assumption that must be written down |
| **C. Not measured** | — | Anything not yet timed | Say "not measured" and move on |

## What a measured line needs

Every line in the log below carries all five, or it is not a measurement:

1. **Tool or task** — named plainly.
2. **Method** — A, B, or C.
3. **The measured part** — the clock time, or the item count.
4. **The stated assumption** — the per-item time or the by-hand baseline, written out.
5. **What it does not cover** — the honest limit.

## How to record one

Copy the block and fill it in. Keep it short.

```
### YYYY-MM-DD — <tool> — <task>
- Method: A / B / C
- Measured: <clock time, or item count in the period>
- Assumption: <per-item minutes, or the by-hand baseline, and where it came from>
- Result: <hours per period or per run>
- Does not cover: <what this number is NOT>
- Who timed it: <name>
```

---

## The log

### Worked example (NOT a measurement — a template)

```
### 2026-10-07 — Tender Monitor — weekly tender review
- Method: B
- Measured: <N> open notices in the week (from tender_data.json)
- Assumption: <M> minutes to find and triage one notice by hand (state how you got M)
- Result: N x M minutes per week
- Does not cover: reading or bidding the tenders; only the searching step
- Who timed it: <name>
```

The example above is deliberately left with blanks. Filling it with round numbers
is exactly the failure this file exists to prevent.

### Recorded measurements

| Date | Tool | Method | Measured | Assumption | Result | Timed by |
|---|---|---|---|---|---|---|
| — | — | — | — | — | not measured yet | — |

---

## Per tool — what can be measured, and how

This is the honest status of each tool: whether a number is possible, and what it
would take. It is not a results table.

| Tool | Measurable? | Method | What it would take | The limit to state |
|---|---|---|---|---|
| Tender Monitor | Yes | B | Count open notices in a week; time one manual search+triage | Does not cover reading or bidding; only the finding |
| Competitive price scrapers | Yes | B | Count parts priced per run | Does not cover the price decision, only the collection |
| PRISM (analytical app) | Yes | A | Time one question answered in the app vs by hand | One person, one task; not a whole day's work |
| Action Ledger | Yes | B | Count open items; time building one by hand | Does not cover acting on the items |
| Forecast / account health | Hard | A | Time a manual account read before vs after | The signal may change a decision, which is value, not hours |
| Mail / interaction layer | Yes | B | Count messages processed; time manual triage | Own mailbox only; not the shared mailboxes |
| SPA application | Yes | A | Time one basket built by hand vs by the tool | Does not cover the negotiation |
| Classification / AIM | Partial | B | Count parts classified | Mostly a one-time job, not a recurring hourly saving |
| Dealer ranking (IDS) | Yes | B | Count dealers scored per country | Does not cover the dealer meeting |

## Where these numbers may and may not be used

- **May:** internal planning, deciding which tool to invest in next, your own
  review of where the time went.
- **May not:** any shared deck or distributor pack, until the measurement is real
  and dated. A time figure that has not been timed is the fastest way to lose the
  argument the number was meant to support.

## Related

- `00_docs/roadmaps/ai_sales_intelligence.md` §8.5 — the ROI formula, inputs to
  be filled, and the instruction not to invent them.
- `00_docs/VALUE_LEDGER_2026Q3.md` — the same rule at the euro level.
