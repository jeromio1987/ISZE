# DLOD — a costed design for running it across the ISZE network

**Written:** 23 September 2026
**Status:** internal draft for the business owner. Not for distribution.
**Companion to:** `ISUZU_UNIVERSE_3_0_2026-09-23.md` (pillar four), and the megaprompt of the same date.
**File:** `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy\DLOD_NETWORK_ROLLOUT_2026-09-23.md`

---

## How to read this

This is an internal note. It asks the question the business owner asked — how to run DLOD across all
ISZE dealers without it costing too much — and it answers with arithmetic rather than a slogan.

**DLOD in this document is Don't Lose the Deal**, the ITUK programme that supports a dealer defending a
job when the customer has a competitor's offer in front of them. It is not "Deal of the Day", which is a
different idea that shares two initials and appears in earlier editions. Where this document says DLOD it
means only the competitive-quote defence programme.

### The evidence labels

Every substantive claim carries one of four labels, as the programme's own evidence law requires:

- ***Measured*** — counted in a named source file, and reproduced on 23 September 2026.
- ***Inferred*** — a conclusion drawn from measured data, with the reasoning shown.
- ***Proposed*** — a design or a decision not yet taken.
- ***Unknown*** — recorded as unknown. It is not filled with an assumption.

**An unlabelled number in this document is an error.** Where a cost is unknown it says unknown; an empty
cost is not zero.

One distinction is used throughout and matters:

- **The billing layer** is what ISZE billed to a distributor. This is the layer the finance department
  sees, the layer that carries the money, and the layer that carries almost no information about *why*
  the money moved.
- **The order layer** is one step upstream: the commercial document behind a billing line, which carries
  the free-text reference that a person typed. This is where a programme name survives, if it survives
  anywhere.

---

## 1. The situation in one paragraph

The business owner has decided the intent: DLOD should reach the whole network. The question is how to do
that without spending more than it is worth. Two facts govern the answer, and both are measured. First,
**the recorded ITUK spend is small: two documents of €30,000 each over two years.** Second, **the
programme has never recorded a single case** — not one part, dealer, competitor quote or outcome — so
nobody can currently say whether those two payments bought anything. That second fact is what makes a
naive network rollout dangerous. Scaling a programme you cannot evaluate multiplies the spend without
multiplying the knowledge. The design below is therefore built around a single principle: **buy the
ability to judge a case before buying the volume of cases.**

---

## 2. The baseline, measured

### 2.1 What exists, in counts

I searched the layers in order, from the billing layer up to the order layer.

**The billing layer — the derived working file.** `01_data\00_derived\sales_fact.parquet` holds 538,346
invoice lines over 3 January 2023 to 31 August 2026. **A case-insensitive search for the text `DLOD`
across all twelve of its columns returns zero hits.** *Measured.* This is the search that earlier
documents reported, and it reproduces.

**The billing layer — the rebate lines.** The same file carries **48 lines** with the material and
description `REBATE`. These are real: they run from 27 March 2023 to 31 March 2026, across **12
distributor entities**, and total **€1,403,122.32**. *Measured.* They carry no list price, no part
number, and no figure key — that is what makes them rebates rather than parts. Eight of the 48 belong to
ITUK (SAP 2575 and 2194) and total **€324,096.61**. *Measured.*

**The order layer — where the label actually lives.** The source extract `01_data\00_derived\
order_headers_from_Order_Detail.csv` holds 11,809 order and credit documents over 1 January 2025 to 31
August 2026, and it carries a free-text field for the reference a person typed. Searching *that* field
finds the programme name:

| Line | Date | Entity | Value |
|---|---|---|---|
| reference `DLAD Q1 2023` | 6 June 2023 | ITUK | €14,421.73 |
| reference `DLAD Q2 2023` | 15 September 2023 | ITUK | €10,273.90 |
| reference `DLOD 2023 Q3+Q4` | 3 January 2024 | ITUK | €5,304.37 |
| reference `dlod` | 30 March 2026 | ITUK | €30,000.00 |

*Measured*, from the raw billing extract `01_data\00_derived\cy2023_2024.csv` and `...\cy2026_q1.csv`,
whose `Purchase order no.` column preserves the typed reference. The same extract also shows a second
document of exactly **€30,000 dated 14 February 2025**, in a slice of the raw extract whose typed
reference column is blank for that line. *Measured* (amount and date); *Measured* (absence of a typed
reference); *Inferred* that it is the same programme, on the grounds that it is the same entity, the
same value, the same rebate material and the same credit-document type as the two lines that are
labelled.

### 2.2 The corrections this baseline forces

Four things in the wider record have to be corrected, because the brief requires it and because each one
changes the design.

**A. The claim that the ledger "carries rebate lines labelled with it" is true only in the loose sense.**
The ledger does not carry the programme name. The label sits in the order layer's typed reference, and
the billing layer's own derived working file drops that field entirely. **The chain from programme name to
billing line is broken in the middle.** *Measured.* This matters because it is exactly the chain an
evaluation would need: today you can find the money, or you can find the name, but not both from one
place.

**B. The brief's statement that a search "returns nothing usable at case level" understates what is
there, and the megaprompt's statement that it "returns nothing" overstates what is missing.** The truth
is in between: **four labelled lines exist, they are all ITUK, and none of them carries a part, a dealer,
a competitor or an outcome.** They are one line each. So the search does return something — it returns
four payments — and it still returns no case. *Measured.*

**C. The megaprompt's search was run over the wrong file for this purpose.** It searched all 538,346
billing rows and found nothing, because the field that holds the label is not among the twelve columns
the billing file carries. A reader who concluded "the label does not exist" would be wrong. The label
exists, in two raw slices, in a column the derived file left behind. *Measured.*

**D. A second acronym appears in the same field, and I cannot resolve it.** Two labelled lines in 2023
read **`DLAD`** and total **€24,695.63**. Across 2023 the two acronyms together total **€60,000.00**,
which is exactly 2 × €30,000. *Measured* (the lines and the totals). *Unknown* (what DLAD stands for).
It may be an earlier name for the same programme, a sister programme, or something else. **It must not be
silently folded into DLOD, and it must not be silently dropped.** It is flagged here as the first thing
to confirm with ITUK.

### 2.3 What can genuinely be counted

| Question | Answer | Label |
|---|---|---|
| DLOD-labelled lines in the billing file | **0** | *Measured* |
| DLOD-labelled lines in the order layer / raw billing slices | **4** (2 clearly DLOD, 2 DLAD, both tested above) | *Measured* |
| Value of the 2 clearly-DLOD lines | **€35,304.37** | *Measured* |
| Value of the 4 lines together | **€60,000.00** | *Measured* |
| Value of the 2 documents of exactly €30,000 | **€60,000.00** | *Measured* |
| Rebate lines of any kind, whole ledger | **48** lines, **€1,403,122.32** | *Measured* |
| Rebate lines, ITUK | **8** lines, **€324,096.61** | *Measured* |
| Period spanned | 27 Mar 2023 → 31 Mar 2026 | *Measured* |
| Distributors with rebate lines | **12** | *Measured* |
| **Cases** (part, dealer, competitor quote, outcome) | **0** | *Measured* |
| Cost per case | **unknown** | *Unknown* |
| Whether any job was kept | **unknown** | *Unknown* |

**The one number the brief asks me to use as the anchor is confirmed: €30,000, twice.** It is not one
memorandum — it is two documents of the same value a year apart, plus an earlier 2023 line of €5,304.37
covering two quarters. Wherever this document uses "€30,000 per market per year" it is treating the
anchor as a rate, not as a quotation for a network programme. That treatment is ***Inferred*** and the
assumption is named every time it is used.

### 2.4 What the files do not contain

- **No case record of any kind.** *Measured.*
- **No memorandum on disk.** A filename sweep for `MOU`, `memorandum` and `incentive` across the
  workspace returns distributor IDS files, UTI GPS incentive models and legacy programme documents, and
  **no DLOD memorandum**. *Measured.* The memorandum's existence rests on the earlier Outlook search
  recorded in the strategy critique, not on a file I can open. **I am reporting it as remembered, not
  verified.**
- **No competitor quote, no price gap, no won-or-lost flag, anywhere.** *Measured.*
- **A defect that must be flagged: two rebate lines of €15,568.00 each, same distributor, same date,
  same value, to the same entity, appear once in the order layer and twice in the billing layer.**
  *Measured.* The other thirteen rebate lines in the same March-2026 batch and the same window match
  one-to-one. This is the class of defect the dispute record already carries for the workshop data
  (identical rows held as potential duplicates, reported both ways, never silently removed). **It is
  reported here rather than resolved, and it is why no total in this document should be treated as exact
  to the euro.**

---

## 3. The scale of "all ISZE dealers"

### 3.1 The dealer estate, verified

I counted the dealer file myself rather than accepting the brief's numbers. **The file is
`01_data\00_derived\ids_dealer_network.csv`.**

| Network | Dealer rows |
|---|---|
| France | 84 |
| Spain | 45 |
| UK CV | 44 |
| UK LCV | 43 |
| Italy | 41 |
| Norway | 38 |
| Belgium | 34 |
| Greece | 34 |
| Israel LCV | 29 |
| Poland | 23 |
| Switzerland | 22 |
| Denmark | 20 |
| Hungary | 19 |
| Portugal | 16 |
| Romania | 15 |
| Netherlands | 9 |
| Cyprus | 1 |
| Luxembourg | 1 |
| Malta | 1 |
| **Total** | **519 rows across 19 networks** |

*Measured.* The brief's counts reproduce **exactly**, network for network, with one wording correction:
"plus single entries" is three single-entry networks — Cyprus, Luxembourg and Malta — not one. There are
**514 distinct dealer names** against 519 rows, so five networks carry a repeated name. *Measured.*

### 3.2 The count that matters more than the total

**Roughly two fifths of the 519 rows sit in markets that this workspace's own rules place outside the
business owner's book.** France 84, Spain 45, Italy 41, Switzerland 22 and Poland 23 come to **215 rows,
which is 41.4% of the estate.** *Measured* (the rows); *Inferred* (the exclusion, from the workspace's
own rule that those markets belong to a different distributor network).

**The dealer estate of 519 is the estate that was self-assessed. It is not the same thing as the estate
that would be eligible for a DLOD programme.** The difference between those two is a decision the
business owner has to take, not a fact I can measure. *Unknown* until he takes it.

### 3.3 The scaling factor

The ITUK programme's own dealer population, and the network estate, on each available basis:

| Basis | ITUK | Network | Factor |
|---|---|---|---|
| IDS dealer rows, UK CV | 44 | 519 | **×11.8** |
| IDS dealer rows, UK CV, distinct names | 44 | 514 | ×11.7 |
| Dealers in the ITUK sales-to-dealer file, CY2025 | 64 | 519 | ×8.1 |
| UK dealer rows, both UK lanes (truck and light commercial) | 87 | 519 | ×6.0 |

*Measured*, each from its own file. **The scaling factor is between ×6 and ×12 depending on which
ITUK population you call the starting point**, and that spread is itself the honest answer: ITUK's
dealer count is 44 in one file and 64 in another, because the IDS assessment and the sales-to-dealer
listing are two different populations that have never been reconciled into one approved name list. The
dispute record already carries this as an open item — the account-to-workshop match resolves to 32 clean
pairs and "a name match is not an approved identity". **Use ×11.8 as the headline factor, and carry the
×6.1-to-×11.8 band wherever the number travels.** *Measured* for the counts; *Inferred* for which one to
use as the headline.

### 3.4 Two things about the dealer file that affect any rollout

**The score scale is not uniform, and any tiering lever built on it will be wrong.** 334 of the 519 rows
carry a score between 0 and 100, averaging 77.5. **The other 185 rows — every dealer in France, Spain,
Italy and one network's worth in Switzerland — carry values in the thousands, up to 7,761.** *Measured.*
The file's own description calls the column "a 0–100 score", which is true of 16 of the 19 networks and
false of four. **The 334 and 77.5 figures that already travel in the wider record reproduce exactly —
they are correct about the subset they describe, and that subset is not the estate.** Any design that
tiers dealers by score, or that offers support to "the weaker dealers", must first fix this column or it
will select the wrong dealers in five markets.

**The file carries no date and nothing but a city for location.** `address` is empty on all 519 rows, and
the date cell in the source workbook is blank. *Measured.* So a rollout cannot be sequenced by geography
from this file, and the one assessment it describes has no vintage.

---

## 4. The affordability problem, quantified

### 4.1 The anchor and its limit

The only recorded value is **€30,000**, and it is **two documents in one market**. That is the whole
evidence base for the cost of a network programme. ***Inferred*, and the assumption is explicit: the
fixture below treats €30,000 as the cost of one market for one year. It is one market's incentive, it may
not be representative, and a market four times ITUK's size might need four times as much or might need no
more at all, because the anchor records what was paid rather than what was required.**

Reliable cost per market: **Unknown.** Reliable cost per dealer: **Unknown.** What follows is arithmetic
on a stated assumption, which is what the brief asks for.

### 4.2 Total exposure at €30,000 per market per year

| Basis | Markets | Total per year | Per dealer row |
|---|---|---|---|
| ITUK alone | 1 | €30,000 | €682 (÷44) / €469 (÷64) |
| Six largest markets | 6 | €180,000 | €610 |
| Markets with 9 or more dealers | 16 | €480,000 | €930 |
| All 19 networks | 19 | €570,000 | €1,098 **← misleading, see below** |

*Proposed* arithmetic on a *Measured* anchor.

**The €1,098 per dealer row in the last line is a bad number and should not be used.** It divides 19
markets' incentives by 519 dealer rows, and 215 of those rows are in markets outside the book. The honest
per-dealer figure on the 16-market basis is **€930**, and on the six-largest-market basis it is **€610**.

### 4.3 The same totals against what the network bills

The network billed **€33,168,696 of parts in FY2026** (1 April 2025 to 31 March 2026, 29 billing entities
on 22 distributor codes). *Measured.* Over the whole horizon, from 3 January 2023 to 31 August 2026, the
same basis totals **€118,074,369 across 30 billing entities**, of which **€116,238,676 sits on the 25
entities the workspace classes as network distributors**. *Measured.*

**One caveat, because it is the kind of thing that gets quoted wrong.** The record carries a safe wording
of "€117.6m of parts billed across 22 distributors" for this horizon. **I could not reproduce €117.6m or
the 22-distributor count exactly from the billing file on the day I built this** — I get €118.07m across
30 entities, or €116.24m across the 25 network entities, and 22 is the count of distinct distributor
codes rather than of billing entities. The programme's own rule is that a safe figure which cannot be
reproduced on the build day is not printed. **So the figure used here is the one I measured, €118.07m,
and the €117.6m wording is reported as reproduced-not.** *Measured.*

| Route | Cost per year | Share of one year's billed parts |
|---|---|---|
| ITUK alone | €30,000 | 0.09% |
| Six largest markets | €180,000 | 0.54% |
| Sixteen markets | €480,000 | 1.45% |
| Nineteen markets | €570,000 | 1.72% |

*Proposed* arithmetic on *Measured* inputs.

**This is the single most useful number in the document, and it cuts both ways.** Even the full 19-market
version costs **1.7% of one year's billed parts** — which is not, on its face, an alarming sum. **But the
cheapness is exactly the danger, not the reassurance.** A cost small enough to approve without argument is
also small enough to approve without evaluation, and a programme that runs for three years at 1.7% and
cannot say what it bought has spent 5% of a year's parts on an unmeasured bet. **The affordability
problem is real, but it is second. The first problem is that the spend is currently unevaluable.**

### 4.4 The exposure that is not the money

The brief asks specifically whether the approval path becomes the binding constraint, and it does.

The record describes the programme as running on a memorandum with **Japan-side sign-off**. *Measured*,
from the earlier Outlook search recorded in the strategy critique; **not verified by me, because no
memorandum is on disk.** If every case needs that route:

| Scale | @ €250/case | @ €1,000/case | @ €5,000/case |
|---|---|---|---|
| ITUK alone (€30,000) | 120 cases/yr | 30 | 6 |
| Sixteen markets (€480,000) | 1,920 cases/yr | 480 | 96 |

*Proposed*, because case size is not measured anywhere.

**At any realistic case size, a network-wide programme generates tens to hundreds of approval events a
month.** A route designed for a handful of annual memoranda does not become a network approval path by
being used harder. *Inferred.* **So the binding constraint on a network rollout is very likely the
sign-off path rather than the cash** — and a design that ignores this will buy a support programme it
cannot operate. This is the strongest single argument for delegation, and it is lever 6 below.

### 4.5 Administrative cost per credit note

**Unknown, and honestly unknown.** No file on disk records the cost of raising a credit note. *Measured*
(absence). The only grounded statement available is that the administration is already being performed —
48 rebate lines exist, so the organisation knows how to raise one — and therefore the **marginal**
administrative cost of recording a case against a credit note that is being raised anyway is close to
zero, while the marginal cost of a **new** claim-and-approve workflow per case is not. *Inferred.* That
distinction is what lever 8 turns on.

---

## 5. Design levers to keep the cost down

Ranked by how much cash or administrative burden each one saves. Effect, risk and assumption on each.

### Lever 1 — Buy the evidence first, not the volume

**Effect: largest single saving, and it is a saving of waste rather than of cash.** The first money spent
should buy case records, not cases. Until a case record exists, every euro of support is unrecoverable
knowledge.

**Risk:** slower visible progress. A pilot that produces a ledger rather than a subsidy looks like
nothing is happening.
**Assumes:** that a case record can be defined and collected cheaply — see §6, where it can.

### Lever 2 — A minimum eligible deal value

**Effect: removes the small claims that cost more to administer than they defend.** The workspace's own
campaign analysis makes the argument that a programme paying per campaign **without a size floor spends
most of its money in the smallest markets** — the highest deep-discount shares sit in the smallest
markets. *Measured*, from the earlier campaign study. **The floor is the cheapest single control
available, because it costs nothing to operate.**

**Risk:** a floor set too high means the programme never fires in small markets at all, and the
distributors who most need support get none.
**Assumes:** that the deal value is known at the moment support is requested. It is not, today.

### Lever 3 — A cap per case

**Effect: converts an open-ended concession into a bounded one.** Without it, a single large fleet job
can absorb a market's whole allowance.
**Risk:** the cap gets set at the level of the largest case anyone can remember, which defeats it.
**Assumes:** a case value can be estimated before the price is agreed. This is the same unknown as
lever 2.

### Lever 4 — A cap per dealer per year

**Effect: stops the support concentrating on one or two dealers and calls that a programme.** Needed
because the current evidence cannot show which dealers use it — no case names a dealer. *Measured.*
**Risk:** it caps the dealers who genuinely face the most competition, in a market where two or three
dealers carry the whole contested book.
**Assumes:** a dealer identity can be attached to a case. It cannot today.

### Lever 5 — A cap per market per year, and the tiering that sits with it

**Effect: this is what makes the total exposure knowable in advance.** A network programme's cost is
unknowable without it. Sizing by market, on parts billed in the last twelve months:

| Tier | What it covers | Cost at €30,000/market |
|---|---|---|
| Three largest markets | ITUK, IUK and the third | €90,000 |
| Largest six | through UMI — 70.0% of network parts | €180,000 |
| Largest eleven | through CIS-KTK — **90.3% of network parts** | €330,000 |
| All nineteen | the whole assessed estate | €570,000 |

*Measured* (the shares, computed from the billing file); *Proposed* (the tiers).

**Eleven markets reach 90.3% of the network's parts billed for 58% of the full-estate cost.** *Inferred.*
That is the most important trade in the whole design: **the last eight markets cost €240,000 a year and
reach 9.7% of the business.**
**Risk:** the small markets are exactly where a competitor can take a job cheaply, so leaving them out
may lose more than it saves. The campaign study's own finding points this way.
**Assumes:** that parts billed is the right way to size a market's competitive exposure. It is a proxy,
not a measure of exposure.

### Lever 6 — Delegate the approval, and keep only the envelope with Japan

**Effect: removes the binding constraint identified in §4.4.** The envelope is agreed once, annually, by
the existing route. Cases inside it are approved locally against a written rule. **This saves no cash at
all and it is probably the highest-value lever in the list**, because the alternative is a programme that
generates hundreds of approval events through a route built for a handful.
**Risk:** delegation without a case record is how an envelope becomes a slush fund. **This lever is only
safe in combination with §6.**
**Assumes:** the business owner is willing to delegate inside a capped envelope, and that the Japan-side
route is content to approve an envelope rather than approve cases. *Unknown* until asked.

### Lever 7 — Additional-only support, not a flat concession

**Effect: the workspace's own arithmetic puts a flat concession at about five times the cost of an
additional-only concession on the same volume** — on stated hypothetical inputs, a 100-unit baseline at
€100 net with €70 parts cost: a 5% concession on all 120 units leaves €3,000 of parts gross profit,
against €3,500 if the concession applies only to the 20 additional units. *Measured* as arithmetic on the
paper's stated inputs; the inputs themselves are hypothetical and the paper says so.

**Risk:** it requires a documented baseline, which means recording what the dealer would have bought
anyway — the hardest thing to agree and the easiest to argue about.
**Assumes:** a baseline exists and both sides accept it. It does not exist today.
**Note on margins.** The paper expresses this in gross profit and margin, which is the right way to talk
about it. A 5% concession on a line carrying €30 of gross profit is a decision about margin, not about a
price multiplier.

### Lever 8 — Self-service claiming against the existing credit-note step

**Effect: this is the lever that decides whether the administration is affordable.** The organisation
already raises rebate credit notes — 48 of them in the record. *Measured.* **Recording a case against a
credit note that is being raised anyway has a marginal cost near zero. Building a separate claim, review
and approval workflow per case does not**, and at the case volumes in §4.4 a separate workflow would
become the programme's real cost. *Inferred.*

**Risk:** self-service on the honour system, with no evidence required, produces exactly the asserted
competitor quote that lever 9 exists to prevent.
**Assumes:** whatever holds the case record can be reached by the distributor without a new login and
without a new licence.

### Lever 9 — Require the competing offer to be evidenced, not asserted

**Effect: the strongest filter available, because it makes the support auditable at the moment it is
given rather than months later.** The programme's whole purpose is defending against a competitor's
offer; if the quote is not recorded, the programme cannot distinguish a defence from a discount.
**Risk:** friction at the moment of the sale. A dealer who must photograph a competitor's quote while the
customer waits may simply not ask for support. **That risk is real and it is the main reason to keep the
evidence requirement to the cheapest possible form — the quoted price and the part, nothing more.**
**Assumes:** distributor willingness to disclose a competitor's quote. This is the same disclosure
question the wider programme is already asking for, and it should be asked once, not twice.

### Lever 10 — Credit rather than cash

**Effect: none on the money — a €30,000 credit note and a €30,000 payment cost the same.** Its effect is
on administration and on control: a credit is settled inside the existing ledger, an unrelated party
invoice is not. **Do not expect this lever to save cash; expect it to save process.**
**Risk:** a credit only helps a distributor who is buying. A dealer in genuine difficulty cannot use a
credit.
**Assumes:** the distributor continues to purchase.

**On non-cash commercial material** — training, technical support, an engineer visiting a fleet. This is
the one form of support that may build capability instead of discounting, and it is the only lever here
that might be *better* than cheaper. **But it is unmeasurable in the current evidence and it cannot be
given a cost from the files. *Unknown.***

---

## 6. What would have to be recorded for this to be testable

### 6.1 The minimum case record

For a later evaluation to be possible, one case must record the following. Nothing here is speculative;
each field is the minimum needed to answer one question.

| Field | The question it answers |
|---|---|
| Date | When |
| Distributor and dealer | Who asked |
| Part or component in words | What was at stake |
| The competing offer: price and part | Was there really a competitor |
| Our price before support | What the gap was |
| Support requested and granted | What it cost |
| Outcome: won, lost, or unknown | Did it work |
| If won, the subsequent order reference | Can the win be verified in the ledger |

*Proposed.* **Eight fields. Seven are typed once; the eighth is filled in later or left as unknown.**

### 6.2 The before-and-after view, and why it is the part that actually costs

A case record alone proves a case happened. It does not prove anything improved. For that, the design
needs the affected dealer and the affected family seen **before and after** the case.

**That is the part with a real limit, and the limit is measured. The available ITUK sales-to-dealer file
covers one year, and 2023, 2024 and 2026 exist only as national totals.** *Measured.* So a dealer-level
before-and-after has no counterpart year in the current data. The dispute record already states this
plainly: within-year monthly patterns are permissible where coverage supports them, and **a year-on-year
reading is not merely discouraged — the data cannot support it.**

**The consequence for this design is direct.** A cases-only record gives a count of cases and a count of
euros. It does not give the before-and-after view, and **without the before-and-after view the programme
still cannot be called successful from its own volume** — which is exactly the caution the programme's own
pillar already carries. *Measured* (the data limit); *Inferred* (the consequence).

**What closes the gap: six to nine more months of the existing sales-to-dealer file, one dealer-level
year bought forward.** That is not a new system. It is the file the organisation already receives,
requested again a year later. *Proposed.*

### 6.3 What it costs

Two components. Both are stated as ranges because the inputs are ranges.

| Component | Cost | Basis |
|---|---|---|
| One-off: define the record and build the before-and-after view inside the existing review | Internal build time, **no new cash** | *Proposed* |
| Running: filling eight fields on a credit note that is being raised anyway | **≈5 minutes per case** | *Proposed* |
| At 360–960 cases a year network-wide (§4.4, at 30–80 cases/month) | **30–80 hours a year, ≈0.02–0.05 of a person** | *Proposed* arithmetic |
| At the record's own indicative fully-loaded rate of €90,000–130,000 per person per year | **≈€1,800–€6,500 a year** | *Proposed*, using the rate already published in the programme's own review |

**Is that small relative to the support it makes evaluable? Yes, on these assumptions — and the "on these
assumptions" is doing real work.** €1,800–€6,500 against €480,000 of support at the sixteen-market route
is **0.4% to 1.4%**. *Inferred.*

**Three conditions have to hold for that conclusion, and each one is testable:**

1. **The record rides the credit note.** If it becomes a separate system with its own login, the cost
   stops being five minutes per case and becomes a licence, a support contract and a training
   obligation — and the 0.4%-to-1.4% answer no longer holds. *Unknown* until the delivery route is
   chosen.
2. **The case record is not mistaken for the evaluation.** The record makes a case *judgeable*. The
   before-and-after view is what makes the programme *evaluable*, and it needs the second year of data
   from §6.2. **A programme with case records and no second year can describe its spend and still not
   defend it.** *Inferred.*
3. **The outcome field is filled honestly or left alone.** An outcome field that is filled in by the
   person who benefits from the support answers nothing. The cheapest honest form is a reference to an
   order that either exists in the ledger or does not. *Proposed.*

---

## 7. Three routes, costed

### Route A — Evidence pilot: three markets, twelve months

| | |
|---|---|
| **Cost** | **€90,000** support (3 × €30,000), plus **€1,800–€6,500** recording. *Proposed* (support), on the *Measured* anchor. |
| **Reaches** | Three markets. At the three largest — ITUK, IUK and the third — **47.2% of the network's parts billed**. *Measured.* |
| **Proves** | Whether cases can be captured at all; whether a competitor's quote can be obtained at the point of sale; whether the approval path survives contact with volume. |
| **Assumes** | That three distributors will run a case record for a year without a visible subsidy increase. |
| **Trade-off** | It does not prove the programme *works* — one year gives no before-and-after. It proves the programme is *measurable*, which is the necessary first thing. |

### Route B — Capped rollout: eleven markets, capped per dealer and per case

| | |
|---|---|
| **Cost** | **€330,000** support (11 × €30,000), reaching **90.3%** of billed parts, plus the recording cost. *Proposed* on the *Measured* exposure table. |
| **Reaches** | 90.3% of the network's parts billed, for 58% of the full-estate cost. |
| **Proves** | Whether the design survives at scale with a per-case cap, a per-dealer cap and delegated approval inside a Japan-approved envelope. |
| **Assumes** | Delegation happens (lever 6) — otherwise the approval path strangles it. It also assumes a case value can be estimated before the price is agreed, which is *Unknown* today. |
| **Trade-off** | **The eight markets left out cost €240,000 and reach 9.7% of the business.** That is the deliberate saving, and it is also the exposure: those are the markets where a competitor can take a job cheaply. |

### Route C — Full network: nineteen markets, unrestricted cases

| | |
|---|---|
| **Cost** | **€570,000** support, **€1,098 per dealer row** — and per §4.2 that ratio divides 19 markets by an estate that includes 215 rows outside the book, so the defensible per-dealer figure is **€930** on the 16-market basis. *Proposed.* |
| **Reaches** | The whole assessed estate of 519 rows across 19 networks, 215 of which are outside the book. |
| **Proves** | Nothing that Routes A and B do not already prove. |
| **Assumes** | That 519 dealer rows are the right eligible population, and that a network-wide approval path exists. Neither is established. |
| **Trade-off** | **It scales a programme that has never recorded a single case.** This is the route the brief warns against, and the arithmetic is why: 1.7% of one year's billed parts is small enough to approve without argument and large enough that three years of it without evaluation is 5% of a year's parts spent on an unmeasured bet. |

### What I recommend

**Route A, then Route B, and Route C only after Route B has produced a before-and-after that holds.**

Route A is not a timid choice. It is the only route that answers the question that actually blocks
everything else — **can a case be recorded at all?** — and it does so for **€90,000 plus change, which is
0.27% of one year's billed parts.** *Proposed* on *Measured* inputs. Route A is also the only route whose
value does not depend on the answer being favourable: if cases cannot be captured, that is worth knowing
before €480,000 is committed, and €90,000 is a cheap way to find out.

**What has to be true for the recommendation to hold:**

1. **The eleven-market tier is a real tier** — that the 90.3%-of-parts figure reflects where competitive
   pressure actually sits, not just where volume sits. *Unknown.* Parts billed is a proxy for exposure,
   not a measure of it, and the campaign study's own finding — that the deepest discounts sit in the
   *smallest* markets — argues against it. **This is the assumption I would attack first.**
2. **The approval path can be delegated inside an envelope** (lever 6). If it cannot, no route above
   Route A is operable, and the recommendation becomes Route A repeated rather than extended.
3. **The case record rides the credit note** (§6.3). If it needs its own system, the recording cost stops
   being small relative to the support, and each route's economics change.
4. **`DLAD` is either the same programme or a different one** — and until that is settled, the 2023
   baseline is two acronyms rather than one.
5. **The business owner settles the eligible estate.** 519 rows or 304. A 41% difference in the
   denominator changes every per-dealer figure in this document.

---

## 8. The honest limit

The design cannot currently establish the following, and each gap has a named closure.

**1. Whether DLOD works.** The programme has never recorded a case, so no before-and-after exists. **What
closes it:** the eight-field record in §6.1, plus the second year of the existing sales-to-dealer file in
§6.2. Neither is new technology; both are new discipline.

**2. What a case costs.** Every per-case figure in this document is arithmetic on an assumed case size,
not a measurement. **What closes it:** the first year of case records. After one year the case size is
measured, and every number in §4.4 becomes real.

**3. What a market's support should be.** The €30,000 anchor is two documents in one market. **What closes
it:** the memoranda themselves. They are not on disk. The earlier work cites them from an Outlook search;
**I am reporting that, not verifying it**, and I have said so wherever the anchor is used.

**4. Whether the money is defensible at all.** A credit note proves support was paid. It does not prove
the customer was kept or that our share of the parts on that job grew. **This is the central limit of the
whole design**, and it is not closed by anything in this document — it is only made closable by the
record and the second year.

**5. What the compliant admin cost is.** Unknown, with no source on disk. **What closes it:** a single
answer from finance on the cost of raising one credit note. It is one question.

**6. What `DLAD` is.** Unknown. **What closes it:** one question to ITUK.

**7. Whether the €15,568 duplicate is a duplicate.** Reported, not resolved, per the programme's own
standing rule on identical rows.

---

## 9. What the files contradicted in the brief

| The brief said | The files say | Label |
|---|---|---|
| A search for DLOD "across all 538,346 billing rows returns nothing usable at case level" | The search returns **nothing at all** in the derived billing file, and **four labelled lines** in the raw billing slices, because the derived file drops the column that holds the label. The conclusion is right; the reason given is wrong, and the wrong reason is dangerous — it invites the reader to conclude the label does not exist. | *Measured* |
| "The billing ledger carries rebate lines labelled with it" | The ledger carries rebate lines; **the programme name is not on them.** It sits in the order layer's typed reference. The chain from label to money is broken in the middle. | *Measured* |
| "One prior-year memorandum states a €30,000 incentive" | **Two documents of €30,000 exist**, one dated 14 February 2025 and one dated 30 March 2026. Plus a 2023 line of €5,304.37. | *Measured* |
| Dealer counts: France 84, Spain 45, UK CV 44, UK LCV 43, Italy 41, Norway 38, Belgium 34, Greece 34, Israel LCV 29, Poland 23, Switzerland 22, Denmark 20, Hungary 19, Portugal 16, Romania 15, Netherlands 9, "plus single entries" | **All reproduce exactly.** "Plus single entries" is **three** networks — Cyprus, Luxembourg, Malta. 519 rows, 514 distinct names. | *Measured* |
| Nothing in the brief | **A second acronym, `DLAD`, appears in the same field** and accounts for €24,695.63 of the 2023 lines. Unresolved. | *Measured* / *Unknown* |
| Nothing in the brief | **The dealer score column is on two different scales** — 185 of 519 rows exceed 100, up to 7,761, across four networks. | *Measured* |
| Nothing in the brief | **Two rebate lines of €15,568.00 appear twice in the billing layer and once in the order layer.** | *Measured* |

**Two things I could not verify:** the memorandum (not on disk), and the Japan-side sign-off (remembered
from an earlier search, not re-pulled by me). **One figure I could not reproduce:** the safe wording
"€117.6m of parts billed across 22 distributors" — I measured €118.07m across 30 billing entities, and
the document uses my measured figure. **Two things I did not attempt:** any email, Outlook or network
step, per instruction, and any test of the ITUK billing horizon, which I left as the wider record has it.

---

## 10. Files used

| File | What it is | What it does and does not contain |
|---|---|---|
| `01_data\00_derived\sales_fact.parquet` | ISZE billing, one invoice line per row | 538,346 lines, 3 Jan 2023 – 31 Aug 2026. **No DLOD. No typed reference column.** 48 `REBATE` lines, €1,403,122.32. |
| `01_data\00_derived\order_headers_from_Order_Detail.csv` | Order and credit documents with the typed reference | 11,809 documents, 1 Jan 2025 – 31 Aug 2026. **Carries the commercial label.** Contains `DLOD`, `kickback`, `sales support`, `scrap`. |
| `01_data\00_derived\cy2023_2024.csv` | Raw billing extract | 287,452 lines, 3 Jan 2023 – 30 Dec 2024. **Carries the typed reference** — this is where `DLOD 2023 Q3+Q4` and both `DLAD` lines live. |
| `01_data\00_derived\cy2025_raw.csv` | Raw billing extract | 147,409 lines, 2 Jan 2025 – 30 Dec 2025. Typed reference largely blank — **the €30,000 of 14 Feb 2025 is here without a label.** |
| `01_data\00_derived\cy2026_q1.csv` | Raw billing extract | 41,278 lines, 5 Jan 2026 – 31 Mar 2026. Carries `dlod` (30 Mar 2026). |
| `01_data\00_derived\ids_dealer_network.csv` | Dealer self-assessment, one row per dealer per network | 519 rows, 19 networks, 514 distinct names. **No date, address empty on all rows, score column on two scales.** |
| `01_data\00_derived\distributor_dimension.csv` | Entity reference | Keys the 34 SAP codes to distributor names and roles. Used to identify which entity each rebate line belongs to. |
| `Isuzu Universe\01_Strategy\UNIVERSE_WHITE_PAPER_KILLER_MEGAPROMPT_2026-09-23.md` | The brief | §5.4 the programme description; §7 the evidence law. |
| `Isuzu Universe\_MERGED_MASTER_2026-09-21\00_THE_MAP.md` | Where the evidence sits | The folder map, the closed decisions, the standing limits. |
| `Isuzu Universe\_MERGED_MASTER_2026-09-21\02_DISPUTED_CLAIMS_AND_RESOLUTIONS.md` | The dispute record | 40 headline conflicts, the adjudicated position, and the standing rule on identical rows that this document follows for the €15,568 pair. |
| `Isuzu Universe\_MERGED_MASTER_2026-09-21\04_SOURCE_MANIFEST_AND_HORIZONS.md` | Sources and their clocks | Every source's identity, period and horizon. **This is the file that carries the "no DLOD case register" finding, and it states it from a filename and column search — which is why the label in the order layer was missed.** |
| `...\CONSOLIDATED_ITUK_2026-09-21_01\evidence\MERGED_CLAIM_TABLE.csv` | The claim register | **No DLOD or rebate row exists in it.** *Measured.* The register the brief names as "the authority for disputed figures" has never carried this programme, which is why the disagreement over whether the label exists was never caught. |
| `ISUZU_UNIVERSE_WHITE_PAPER_REVIEW_2026-09-21.md` § the €300,000 comparison | The only other place a DLOD value is discussed | Confirms the €30k reading and states the caution that a rebate records that money moved rather than what it bought. |
| `UNIVERSE_STRATEGY_REVIEW_CRITIQUE_2026-09-21.md` §3d | The ITUK DLOD chapter | The MOU, rebate and sign-off description, cited from an Outlook search. **Not verified by me.** |

**No part numbers, no line-level billing and no supplier purchase costs appear in this document.**

---

## Revision record

| Date | Change |
|---|---|
| 2026-09-23 | First version. Written as the companion to the Universe 3.0 DLOD pillar. |
