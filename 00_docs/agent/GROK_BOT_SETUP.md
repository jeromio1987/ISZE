# Grok Bot — setup

**Status:** internal · written 2026-10-07 · companion to
[`EXTERNAL_AI_SERVICES.md`](EXTERNAL_AI_SERVICES.md)

This is how to stand up the first Bot. It is written so that the job, the boundary and the
acceptance bar are decided before the Bot is created, not after.

---

## 1. Where it fits

Claude, Cursor and PRISM all stop when this laptop closes. The Windows tasks in
[`../AUTOMATION_REGISTER.md`](../AUTOMATION_REGISTER.md) only fire on this machine. Grok Bot is
different: it runs on a computer in Cursor's cloud, on a schedule, whether or not the laptop is on.

That makes it the right home for the **unattended public-internet work**:

- the long polite crawls (a full scrape pass is hours of waiting, at a fixed request spacing);
- watching public portals for new notices;
- monitoring public competitor or market pages and reporting only what changed.

It is the **wrong** home for anything that needs our own numbers, our price list or our mail. That
material never leaves this machine — see the boundaries in
[`EXTERNAL_AI_SERVICES.md`](EXTERNAL_AI_SERVICES.md).

The split in one line: **Claude decides and checks, Cursor builds on this machine, GPT does look and
research, Grok Bot grinds the public web around the clock and hands back a document.**

---

## 2. Access — no second purchase

The Bot signs in with the **Cursor account**, not a separate login. Access is included with the paid
individual Cursor plans. Open the Cursor usage screen and confirm a Grok Bot grant is shown before
spending time on setup. If it is not shown, that is the first thing to settle.

---

## 3. Create one Bot, with one job

One Bot, one focus. The first job is an **external intelligence watch** — the daily version of the
paused weekly brief (`isze-weekly-intelligence-brief` in the automation register, last real output
`05_memory/briefs/weekly_W17_2026_intel.txt`).

Why this first: it is public sources only, it produces something readable rather than a table, and
it is easy to grade — either the stories are real and sourced, or they are not.

Give the Bot:

- **a short name** — e.g. `ISZE Intel Watch`
- **one primary job** — "Watch public sources for changes that matter to Isuzu parts, and report
  them with sources."
- **how it should work** — public web only, never send anything, report a source that failed as
  failed.

---

## 4. Connect the minimum

Start with the Bot's own browser and nothing else. That is enough for the watch.

**Do not connect the company mailbox.** Mail is internal under the boundary, and a cloud service
reading it is a separate decision with its own governance step, not a default. Same for Drive and
Slack: connect only when a specific job genuinely needs it and the boundary still holds.

If a step needs a login you own, the Bot will hand you the screen to type the password yourself.

---

## 5. The first skill — paste-ready

A skill is the instruction set the Bot reuses. Paste the block below into the skill (or hand it to
the Bot and ask it to save it as a skill named `isze-intel-watch`). Edit the source list to taste;
keep the boundaries as they are.

```
isze-intel-watch

When to use it
  A recurring public-source watch for anything that changes the parts picture for Isuzu in Europe:
  part prices in public shops, aftersales and service news from other truck makers, public tender
  notices, regulatory changes (emissions, EV targets), and Isuzu product news.

Inputs
  Public web pages only. No internal data, no files from a private repository, no mailbox, no
  documents unless handed over explicitly for this run.

Sequence
  1. Fetch each source in the source list below, politely: at most one request every two seconds
     per site, and stop if a site asks crawlers to stay away.
  2. From each source, keep only items that would change a decision: a price move, a new part or
     programme, a regulatory change, a tender notice, a product launch.
  3. For every item kept, record the exact page and the date it was published or observed.
  4. Write the output document (format below).
  5. Do not send, post, reply, message or publish anything. Return the document only.

Source list (edit freely)
  - public part shops your contact names: the current set is in the scraper programme notes
  - EU and national public procurement portals
  - trade press for commercial vehicles and the aftermarket
  - regulator and government pages for emissions and vehicle targets
  - the manufacturer's public news pages

Output format
  # ISZE Intel Watch - <date>
  ## Top items (at most five, most consequential first)
  - <what changed> - <why it matters> - <source page and date>
  ## Everything else worth noting
  - one line each, same source-and-date form
  ## Sources that did not load
  - <source> - <what happened> - <what was tried>
  Never fill a gap from assumption. A source that failed is reported as failed.

Boundaries
  - Public sources only. If a page needs a login you own, stop and ask; do not work around it.
  - Never quote or compute an internal figure - no margin, no capture rate, no billed total.
  - Never send, post, publish or reply. Draft only, and hand the draft back.
  - If a source's format changed so the extract is unreliable, say so and fall back to reporting
    the link rather than guessing the value.
  - No prices for our own parts. Public competitor prices only, with the page and date.

Validation before returning
  - Every quoted number appears on the page it is attributed to.
  - Every item has a date.
  - The "did not load" section is honest, including when it is empty.

If this is run as a scheduled routine
  - Approve before anything leaves the building; the routine's only job is to produce the document.
  - If more than half the sources fail, stop and report that rather than writing a thin document.
```

---

## 6. Turn it into a routine

Make the skill a routine by asking the Bot in chat, in this shape (the Bot records these fields):

- **owning Bot** — the one just created
- **schedule and time** — daily is a reasonable start; weekly is also fine
- **input source** — the public source list in the skill
- **expected result** — the intel document, named and dated
- **approval boundary** — nothing is sent, posted or published; the run only produces the document
- **when a source is missing** — report it as missing; do not substitute

Confirm the routine shows a **next run**. It runs with the laptop closed.

---

## 7. The checkpoint — how the output is accepted

The Bot's output is treated exactly like a DeepSeek batch or a GPT reply:

1. The document is filed into `01_data/90_INBOX/` (the inbox is the only landing place for
   unsorted material).
2. Claude reads it and checks every figure and source against the page it names.
3. Nothing enters a dashboard, a deck or a workbook until that check passes.
4. The same acceptance bar as the machine-produced rows in the scraper programme: if a number
   cannot be traced to the source, it is not used.

A run with an honest "these sources did not load" section is worth more than a full-looking
document with a guessed number in it.

---

## 8. Keep the roster small

Add a second Bot only after the first has run clean for a week. Good second jobs, when they come:

- **public portal reach** — find the reachable public route for the tender portals still dark, in
  the same way the reach recon did for the scraper sites;
- **the long crawls** — the polite multi-hour fetches, so they stop tying up this machine.

Several Bots that each own one job beat one Bot doing everything.

---

## 9. What this deliberately does not do

- It does not connect the mailbox, send anything, or push to main.
- It does not receive a clone of this repository, and it is not planned to.
- It does not read the price list, the billed numbers or any distributor-tied figure.
