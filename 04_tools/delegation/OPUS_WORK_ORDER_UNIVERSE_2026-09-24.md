# Opus work order — Isuzu Universe judgement tasks (24 September 2026)

Eight tasks. Each block is self-contained: paste one block per Opus chat.
Ordered hardest-hitting first. Blocks 1 and 2 are the two that block money you are
already spending — if only two run, run those.

**These are judgement tasks, not build tasks.** Seven of the eight end in a written
recommendation. None of them changes a shared dashboard, sends mail, or creates a
scheduled job.

---

## Rules that apply to every block

- Work in `C:\Users\jerom\Desktop\claude\ISZE`. Before starting, read `CLAUDE.md`,
  `INDEX.md`, and the last 10 rows of `00_docs\agent\DELEGATOR_BOARD.md`.
- **Never load `01_data\raw\sales\*.XLSX` or any line-level billing.** Use the
  derived CSVs and parquet.
- **Numbers:** green `01_data\00_derived\_verification_report.json` →
  `metrics_snapshot.json` → `FACTS.md`. These win over decks, memory and any GPT file.
- **Never invent a number.** If data is missing, write that it is missing.
- Write files as UTF-8 **without BOM** (Python `open(..., "w", encoding="utf-8")`;
  never PowerShell `Set-Content`).
- Plain business English. No internal shorthand in anything a person outside the
  agent team might read: say **sales to dealer**, **parts billed**, **the price list**,
  **reference dealer price**. Say **shared/external** vs **internal/private**, never
  Mode A / Mode B.
- Money first, pieces only with a part name and a fleet denominator. Never add unlike
  euros. Warranty is its own line.
- **UTI ≠ UMI** (two different Israel distributors, never blended).
  **IUK ≠ ITUK** (pickup vs truck).
- **No emails. No publishing. No new scheduled tasks, and no change to an existing one.**
- When finished: append ONE row to `00_docs\agent\DELEGATOR_BOARD.md` in its existing
  table format, and report back in **under 150 words** — what you concluded, what you
  read, and anything you could not establish.

---

## 1 · Attack the pillar board (small, do first)

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in
04_tools\delegation\OPUS_WORK_ORDER_UNIVERSE_2026-09-24.md.

Context: 02_dashboards\hub\ISZE_UNIVERSE_BOARD.html scores six pillars against five
named conditions each, giving an overall 53%. AIM 60%, IDS 60%, Pricing & Margin Lab
60%, PRISM 60%, Range & Campaign Planner 40%, Coordinated tenders 40%. The scores are
an agent's checklist, stated openly so they can be argued with. Nobody has argued with
them yet.

Read: the board HTML, 01_data\00_derived\universe_board_state.json (the scores and the
condition texts), and 02_dashboards\_build\build_universe_board.py (how each condition
is actually tested).

Do:
1. For each of the 30 conditions, say whether it is a real condition or a generous one.
   Name any condition that is satisfied by something a distributor could not open or use.
2. Re-score all six pillars on your own reading, and show where you differ and why.
3. Name the single most misleading number on the page — the one most likely to give
   Jerome a false sense of progress — and say what it should read instead.
4. Say which pillar is flattered most and which is understated, if any.

Do not edit the board, its builder, or the state file. Your output is a memo.

Write 02_dashboards\hub\_review\PILLAR_BOARD_ATTACK_2026-09-24.md: the attack, the
counter-scores, and the one number to change.
```

---

## 2 · The coverage decision (the money decision)

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in
04_tools\delegation\OPUS_WORK_ORDER_UNIVERSE_2026-09-24.md.

The question: carry on building our own competitor cross-reference, buy a paid
cross-reference licence, or stop. One page. With the money attached.

What is true today, all measured:
- The cross-reference reaches 131 of our 16,511 part numbers, carrying EUR 5,639,298
  of billing. 69 of those parts have two or more sources; only 22 competitor numbers
  are confirmed by more than one independent source.
- Of the 486 biggest parts (Tier A), 342 — 63.5%, worth EUR 13,543,552 — have no
  competitor number and no peer number at all. They are not unsearched; there is
  nothing to search with.
- A model that predicts a competitor price from our list price is typically 46% off.
  One flat ratio for every part is 48% off. The model adds almost nothing.
- Only two competitor sources are still fetched every week, one by part number and one
  by maintenance category only. Three were retired for giving false matches; two block us.

Read: 00_docs\agent\AFTERMARKET_INTELLIGENCE_STATE_20260924.md, then
04_tools\aftermarket_intelligence\state\CROSSREF_GRAPH_REPORT.md,
RATIO_MODEL_REPORT.md and MATCH_INDEX_REPORT.md, then the spot-check result
01_data\90_INBOX\_aftermarket_spotcheck_20260924\SPOTCHECK_RESULT_AI_2026-09-24.md
and the independent-witness file beside it.

Do:
1. State what each of the three routes reaches, in part numbers and billed euro.
2. State what each costs: our own time per source, and the licence route's cost if a
   figure can be sourced at all (if it cannot, say so and say who quotes it).
3. Name what each route cannot do. In particular: no amount of scraping by our own
   number reaches the 342 Tier A parts, because there is nothing to search with.
4. Give ONE recommendation, with the single number that decides it.
5. Name the condition that would change your answer.

Write 00_docs\COVERAGE_DECISION_2026-09-24.md. This is internal. Do not buy anything,
do not contact any vendor, do not subscribe to anything.
```

---

## 3 · Design the two weak pillars

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in
04_tools\delegation\OPUS_WORK_ORDER_UNIVERSE_2026-09-24.md.

Two of the five tools in the strategy are the weakest: Range & Campaign Planner (no
file exists at all) and Coordinated tenders (collection works, the rest does not).
Design what a distributor would actually open and use.

Read: Isuzu Universe\01_Strategy\ISUZU_UNIVERSE_3_0_2026-09-23.md (chapter 2 for the
five tools, chapter 7 for how each is meant to work), the Action Centre at
Isuzu Universe\ISUZU_UNIVERSE_Action_Centre_local_2026-09-24.html, and the existing
Atlas and dealer-standard pages at 02_dashboards\ids\ and
Isuzu Universe\02_Atlas\AIM_Parts_Atlas_v2.0.html.

Do, for each of the two:
1. The first screen, and the one question it answers.
2. What the user types or picks, and what comes back.
3. Which files on disk already hold the inputs, by name.
4. What the output looks like on one page — describe it concretely enough to build from.
5. Why a distributor would spend time on it. If the honest answer is "it would not",
   say that instead, and say what would have to be true for it to be worth building.

Constraint: no internal terms on anything that could reach a distributor, and a
national vehicle total cannot be allocated to dealers by sales or geography.

Write 00_docs\TWO_PILLAR_DESIGNS_2026-09-24.md. Design only — build nothing.
```

---

## 4 · Close the tender outcome loop

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in
04_tools\delegation\OPUS_WORK_ORDER_UNIVERSE_2026-09-24.md.

The live feed holds 619 public-tender opportunities. 279 are repair-and-maintenance
contracts, 236 of those are R&M with no vehicle purchase, and 29 open R&M tenders have
a deadline on or after today. Outcomes recorded so far: 0. The win-rate calculation in
the file needs a minimum sample of 20 before it will report anything.

The question: what is the smallest thing that records pursue / pass / won / lost and
actually gets filled in.

Read: 04_tools\ISZE_Tender_Monitor_Install\tender_outcomes.py (how outcomes are stored
today, meta.outcomes_store), 01_data\14_dashboards\tender_data.json (the outcome
fields and the min-sample setting), and the per-distributor digest plus its CSV at
04_tools\ISZE_Tender_Monitor_Install\rm_digest\ if that folder exists.

Do:
1. Say who fills this in, at what moment, and from where — name the role, not a job title.
2. Say what the five options mean precisely, and what counts as won vs lost.
3. Say how the entry gets back into the feed, and what stops it being filled in.
4. Say what the list looks like once 20 outcomes exist, and what it can say that it
   cannot say today.
5. Name the smallest version that would actually survive contact with a distributor.

Write 00_docs\TENDER_OUTCOME_DESIGN_2026-09-24.md. Design only — no code, no schema
migration, and do not write into the outcome store.
```

---

## 5 · Settle what `OE RRP` is

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in
04_tools\delegation\OPUS_WORK_ORDER_UNIVERSE_2026-09-24.md.

One column in the July 2025 Eucon file is unestablished and it is holding up a
decision. The column called `OE RRP` holds 4,652 rows — 92% of the file — with a price
attached to OUR part number. It is not our list price: on the eight part numbers where
both exist it runs 2.46x to 3.14x our list. It is also not an aftermarket competitor's
price. Nobody has established what it is, and it must not be loaded anywhere until
someone does.

Read: 00_docs\agent\AFTERMARKET_INTELLIGENCE_STATE_20260924.md section 3 (the trap and
the two candidate explanations), then the July file itself
(01_data\...\Eucon_Online28072025.xlsx, sheet Fresh list_Export_28072025_0932), and the
March 2024 file's RRP sheet for comparison.

Do:
1. Test the two candidates: a vendor's own recommended retail for the part, or a
   converted price in an undeclared currency.
2. Look for internal evidence — a declared currency on one side and not the other, a
   relationship to the real competitor price column, a relationship to any known rate.
3. Reach a definite answer if the evidence supports one. If it does not, state the
   single question that must go to Eucon, worded so a yes/no or a one-line answer closes it.
4. Say what each answer would mean: if it is a vendor retail price, is the column an
   asset or a liability for pricing work?

Write 01_data\90_INBOX\OE_RRP_2026-09-24.md. Read-only. Do NOT open NOTE_Eucon.txt,
do NOT contact Eucon, and do NOT load the column into any file.
```

---

## 6 · The purpose question

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in
04_tools\delegation\OPUS_WORK_ORDER_UNIVERSE_2026-09-24.md.

An open question has been sitting since 18 August and it decides what every ranked
list in this work sorts by. Three candidate purposes were written down:
(a) defend the UK truck book, (b) the next price revision, (c) a maintenance-parts
campaign. Nobody has chosen.

Read: 00_docs\agent\AFTERMARKET_INTELLIGENCE_STATE_20260924.md section 7 item 3,
DECISIONS.md (the open entries), and 00_docs\roadmaps\pricing.md.

Do:
1. Recommend ONE purpose, in the first sentence. Not a menu.
2. Say what evidence in the workspace supports that choice over the other two.
3. Say what changes as a result: which list sorts by what, which parts rise, which
   dashboard becomes the working view, and what stops being shown.
4. Say what you would drop to make it happen, because the answer almost certainly
   means not doing one of the other two now.

Write 00_docs\PURPOSE_DECISION_2026-09-24.md. Internal. This is a recommendation for
Jerome, not a decision you take.
```

---

## 7 · Ireland and Portugal, 2013/14

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in
04_tools\delegation\OPUS_WORK_ORDER_UNIVERSE_2026-09-24.md.

Two of the five markets with registration-grade data have a break nobody has resolved.
In the fleet workbook, Ireland row 26 goes 2,390 to 12 and Portugal row 51 goes 16,605
to 23 between 2013 and 2014 — drops of 99.5% and 99.9% in one year. Those are two
different populations with no join between them.

The consequence: every scrap rate, trend or per-truck rate computed across that break
for those two markets is meaningless, and both markets sit inside published figures.
Ireland's GPS fleet (3,056) and wallet fleet (2,161) already disagree by 41.4%, and the
break is the reason.

Read: 00_docs\agent\STATE_PACKET.md (the UIO sections and the source audits),
01_data\90_INBOX\UIO_DATA_INVENTORY_2026-09-22.csv,
01_data\90_INBOX\UIO_HISTORY_AUDIT_2026-09-22.md, and the workbook
06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx sheet 1.UIO Overview.

Do:
1. Decide: is this fixable from a source on disk, or is it a clean exclusion? Pick one.
2. If fixable, name the source and the method. If not, define the exclusion precisely —
   which years, which rows, and what publishes a caveat instead of a number.
3. List every current number that is unsafe until this is settled, and every number
   that remains safe. Be specific; "any rate across the break" is not specific enough.
4. Note what this does to the two published fleets that already disagree for Ireland.

Two further defects are recorded for the same workbook and can go in the same memo:
the MIDI tag column understates MIDI by about a third, and the two summary tables at the
foot are pinned to 2024 while the main row runs to 2030.

Write 00_docs\IE_PT_BREAK_2026-09-24.md. Do not edit the workbook or any UIO file.
Do not rebuild the ceiling — that is explicitly held.
```

---

## 8 · Prepare the Eucon licence question

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in
04_tools\delegation\OPUS_WORK_ORDER_UNIVERSE_2026-09-24.md.

Three generations of Eucon cross-reference files are the main asset behind our
competitor matching, and nobody has established whether they may be used. There are
calendar entries titled "Eucon annuleren" in January, February and March 2026, a budget
approval for a Eucon invoice in August 2025, and the 2021 report itself in the mail
attachments. Two files arriving on a Thursday afternoon a week before quarter end is
consistent with a final extract, and with a renewal. We do not know which, and the
difference decides whether those ~4,600 match rows may leave the EU.

Read: 00_docs\agent\AFTERMARKET_INTELLIGENCE_STATE_20260924.md section 7 items 1 and 2.
Do NOT open NOTE_Eucon.txt and do not read the password it holds.

Do:
1. Write the precise questions, in the order they must be answered: is the contract
   live or ended; what do the terms permit for price monitoring; what do they permit
   for processing outside the EU; what happens to the data if the contract has ended.
2. For each question, say who can answer it — role, not a name.
3. Say what each answer opens or closes: which of the coverage routes from the
   coverage decision become available, and which become impossible.
4. Flag anything that should stop before a lawyer is involved, and anything that is
   safe to do regardless of the answer.

Write 00_docs\EUCON_LICENCE_BRIEF_2026-09-24.md. One page. Do not contact anyone, do
not send anything, and do not delete or move any Eucon file.
```

---

## What this work order deliberately does not do

- No shared dashboard, HTML pack or deck is rebuilt by any block.
- No emails, no publishing, no scheduled tasks touched.
- No price is changed and no price list is edited.
- Block 2 is a recommendation. The purchase, if any, is Jerome's to make.
- Blocks 5 and 8 must not open `NOTE_Eucon.txt`.

## Already in flight elsewhere (do not duplicate)

Three Cursor workers are running from
`04_tools\delegation\CURSOR_WORK_ORDER_UNIVERSE_2026-09-24.md`:
- Block A — point PRISM's tender page at the live tender feed.
- Block B — build the weekly per-distributor R&M tender digest.
- Block C — independent witnesses for 11 spot-check rows.
- Block D — register the classification release; **waits for Jerome's signal.**
