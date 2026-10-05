# Isuzu aftersales - context for a research assistant

**Prepared:** 2026-09-19 for Jerome van der Pluym, VP Vehicle Parts Sales, Isuzu Motors Europe (ISZE), branch IE40.
**Purpose:** give a general-purpose research model enough grounding to reason about Isuzu aftersales without
inventing facts, so that any research question about the aftermarket business can be answered against real
structure and real numbers.

This is a **separate, self-contained set of six files**. It replaces nothing and it overwrites nothing.
Everything in the older `08_gpt/2_KNOWLEDGE_FILES/` folder was last reconciled in April/July 2026 and some of
it is now actively wrong (it still quotes a superseded oil-filter capture rate that must not be used). If a
model has both sets loaded, it will contradict itself. Load this set.

---

## What is in this set

| File | What it gives you |
|---|---|
| `00_READ_ME_FIRST.md` | This file: how to use the set, and the rules you must follow |
| `01_ISUZU_AND_ISZE_BUSINESS.md` | The business: who sells to whom, the market entities and the mapping from the distributor names in the plan and the monthly report to the country and the data code, the vehicle ranges, the fiscal year, the price chain, who does what |
| `02_NUMBERS_AND_HOW_THEY_ARE_BUILT.md` | The live numbers with their as-of dates and source files, how each is calculated, and where each can and cannot be quoted |
| `03_OPERATIONS_OPEN_WORK_AND_CAVEATS.md` | What runs every month, what is under way, what is blocked, and every known data problem stated honestly. It also carries the FY2027 plan by market and by month, where the plan came from, and the monthly reporting cycle |
| `04_GLOSSARY_AND_HOW_TO_WRITE.md` | Every acronym and internal code decoded, plus the writing rules (plain English, margins not factors, units need context) |
| `05_COMPETITOR_PRICING_AND_ACTIONS.md` | Competitor and independent-aftermarket pricing, what evidence exists and its limits, and the commercial action layer: the open action register, the FY2027 action plan and the dealer-level performance file |

Sizes are small (a few tens of kilobytes in total). There are no spreadsheets in this set on purpose, so that
there is one source of truth for every figure. If someone needs to *compute* rather than *read*, see
"Adding data" below.

---

## Rules you must follow

**1. Never invent a number.** Every figure in these files carries an as-of date and the file it came from.
If a question cannot be answered from these files, say so and say what is missing. A wrong number is worse
than no number.

**2. When numbers disagree, say which one you are using and why.** Several measures exist in two versions on
purpose - for example ITUK's service-demand figure exists on an external standard and on an internal one.
That is explained in file 02. Do not average them, and do not silently pick one.

**3. A unit count is never an answer on its own.** Pieces, units and quantities mean nothing without three
things beside them: the euro value, which part family it is, and the vehicle fleet it sits on. "258,824 units"
is not a finding. "258,824 oil filters, EUR 5.8M, on 47,783 light commercial vehicles" is. Lead with euro or
with a rate per vehicle, never with a bare count.

**4. Talk in margins, not in factors.** Internally, prices are built with a divisor (a class factor) and a
source discount factor. Translate both into margins before discussing them. If the factor has to appear for
traceability, give the margin first and the factor second. Jerome quotes and negotiates in margin.

**5. Plain business English.** No invented shorthand, no agent vocabulary, no metaphors that need a glossary.
Short complete sentences. Lead with the conclusion, then the reasoning, then the caveats. Write as a colleague
would speak across a desk.

**6. Two audiences, two registers.** This file set is internal. Anything that leaves ISZE - a distributor
mail, an IML Japan paper, a meeting pack, a shared dashboard - must be written so that a distributor can read
it without ISZE's private shorthand. File 04 has the vocabulary table.

**7. Ask which market before answering about "the business".** The network is 18 markets with a fleet count
plus four billing entities without one, and two of the countries (United Kingdom, Israel) each contain two
separate distributors that must never be blended. A network average hides most of what matters.

**8. Some material is background only and must never appear in an output.** Two things are named here
precisely. First, the parent company's revenue target and the commentary around it, in file 01 section 9:
that paragraph is there so that a reasoning answer is calibrated, and it must not be quoted, reproduced or
paraphrased, and the target figure must not appear in any answer. Second, any euro figure that a file in this
set marks internal-only, specifically the euro column in the open action register (file 05 section B.1) and
the network service-demand euro total in file 02 section 3. Both are working figures, not published ones. If
an answer would need one of them, say the figure is internal and reason without printing it.

---

## What "operations" means here

The aftersales operation is not one system. It is a set of decisions, each fed by different data:

- How big is the fleet, where is it, is it growing? (fleet / trucks in service)
- How much does each truck spend on parts a year? (spend per truck in service)
- Of the service demand the maintenance schedule implies, how much did we actually sell? (service-demand cover)
- When a customer buys a value part instead of an original one, how much of that is happening? (mix)
- What is the total spend available in a market, and how much of it is ours? (target spend per truck, the
  ceiling, and the gap)
- How healthy is each distributor's account - who has stopped ordering, who is at risk? (account health)
- What price is the market asking, versus our own reference price? (price index)
- Where are public tenders that need a parts offer? (tender pipeline)
- What does warranty cost us, in which market and on which component? (warranty)
- What is on the action list this month? (action ledger)

File 02 defines each of these and gives the current figure.

---

## Adding data (expected)

Attach these four small files from the ISZE workspace as well. They are the derived outputs behind every
number in file 02, and the set is expected to travel with them rather than without them: a model that has
only the six documents can read a number, but it cannot compute across the figures, compare two markets on
one basis, or answer a question the documents do not already contain the answer to. Do not copy them into
this folder - attach them where they are, so there is one version:

| File | What one row is |
|---|---|
| `01_data/00_derived/wallet_waterfall.csv` | one market x one year: fleet, target-spend ceiling, what we captured, the gap |
| `01_data/00_derived/gps_spu_by_distributor.csv` | one market x one year: parts billed, fleet, spend per truck |
| `01_data/00_derived/pms_capture_by_db_year.csv` | one market x one year x one service category: expected units, actual units, cover, gap |
| `01_data/00_derived/mix_genuine_bvp_pms.csv` | one market x one year x one part family: original vs value parts, units and euro |

**Do not attach** anything under `01_data/raw/` (line-level billing) or any full price list. Those are
restricted and cannot leave the internal workspace.

---

## One sentence summary of the business

ISZE is the European parts hub for Isuzu: it buys parts from Japan (IML) and Thailand (IMIT), sets the
European selling price list, and sells to national distributors, who sell to dealers, who sell to fleets -
and the commercial question that matters is how much of the service spend that the Isuzu fleets in those
markets generate actually reaches Isuzu rather than an independent aftermarket competitor.
