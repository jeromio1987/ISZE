# Universe — Yellow Paper

**From parts data to a commercial decision**
AIM · IDS · PRISM

A connected specification for parts intelligence, dealer self-assessments and market context.

21 September 2026 · ISUZU EUROPE · Product and operating specification

---

## Document status

This paper is a **proposed product and operating specification**. It sets out what Universe is for, how it
is meant to work, what evidence it may use, what the distributor provides in return, what can be built
now, and what is still undecided.

Its own existence is not evidence that any part of it has been built. **Acceptance belongs to the release
evidence and the delivery gates, not to this paper.** Where a number appears, the source of that number,
the period it covers and the limits of what it can support are stated with it.

This supersedes the earlier proposal editions of the same paper. Where this paper states a position that
differs from an earlier one, this paper's position is the one to use, and the appendix of settled and open
decisions records what moved.

---

## How to read this paper, and the status words used in it

The paper has six parts and four appendices.

Part A says what Universe is for and what it is not. Part B sets out the operating model — how a
commercial question is followed from an observation to a recorded action, and what the organisation owes
in return. Part C is the evidence architecture: the flows, the layers, what a number may be read to mean,
and the rules that keep different kinds of evidence apart. Part D is the data and participation contract:
what the distributor provides, what it receives, and what is deliberately outside the ask. Part E is the
identity and parts substance, which is where the largest single gap sits. Part F is delivery: the pilots,
the workspace, the governance, the access position and the gates. Part G states the decisions the paper
leaves open, the honest position on money, and the next milestone.

Four appendices carry the definitions, the figures this paper is allowed to quote and in what words, the
decision trail, and where the evidence lives.

**Status words.** Every claim in this paper is one of the following, and only these.

| Word | What it means |
|---|---|
| **verified** | re-derived from the source and it reproduces |
| **corrected** | an earlier figure or label was wrong; this is the replacement, with the definition behind it |
| **contradicted** | the thing that was said is not true as written |
| **unsupported** | nothing held on our systems can answer it; the paper says whether the gap is a missing field, a missing file or a missing definition |
| **not tested** | it could be tested and deliberately was not, with the reason given |
| **no local copy available** | the document is named and we hold no copy of it |

There is no such status as "fully verified" and this paper does not use the phrase. A figure is verified
against a stated definition, for a stated population, over a stated period, counting or excluding stated
cases. A thing that has not been reviewed is not the same as a thing that is missing.

---

# Part A — Purpose and definition

## A1. The proposition

Universe is the distributor's connected aftersales review. It is the place where parts purchasing,
dealer-network information and market context sit beside a recorded action, so that a commercial question
can be followed through from what changed to what was agreed and what happened next.

It is not an attempt to put every available dataset on one screen. Its purpose is to make the
relationship between a claim, its evidence and the next decision explicit.

The working proposition is simple. Identify what changed. Locate the parts and the population involved.
Test the plausible explanations. Choose an intervention. Review the result. A useful conclusion names its
reporting period, which transaction flow it is drawn from, the affected parts, the limits of the evidence
and the person who owns the action. A chart without those elements is not a finished analysis.

Universe should make a decision easier to defend. It should not make incomplete evidence look complete.

**What Universe is not.** Universe is not a replacement for the enterprise systems that hold the trading
records. It is not an automated system that sets prices. It is not a tool for auditing distributors.
Three scope decisions are already settled and are not reopened by implication in this paper: the
portfolio overview stays as the entry point for understanding the range; the Genuine and value-tier
comparison stays as a central experience; and the previously built aggregate sales view stays **removed**,
not deferred for reintroduction. Product photography stays deferred at this stage.

## A2. The three pillars, and the possible fourth

**AIM — Aftermarket Intelligence Model.** AIM provides the parts classification foundation: it gives
purchasing data a usable product structure so that analysis can move from portfolio to family to part
number. Classification is not by itself proof that two parts are interchangeable, that either fits a
vehicle, or what a kit contains. Those relationships need their own evidence, and Part E says what counts
as that evidence.

**IDS — Isuzu Dealer Standards.** IDS records dealer self-assessments. It contributes what the dealer
reported about its own practices, the context of the assessment, and the follow-up that was agreed. ISZE
does not conduct distributor audits through IDS. Any presentation of IDS results must state the assessed
dealer population, the response coverage and the assessment dates.

**PRISM.** PRISM is the analytics codebase that produces the validated commercial calculations — parts
billed, modelled expected service demand, mix, and replenishment signals. Its functional boundary in this
paper is the vehicle and market-context pillar, and that boundary requires confirmation against the PRISM
specification before implementation. This is not a claim that every supporting dataset is already
integrated.

**AIM, IDS and PRISM remain working names.**

**Tender support.** Public procurement notices are a supporting module and a possible extension. They are
not an approved fourth pillar, and this paper does not treat them as one.

## A3. The four commercial outcomes

Universe exists to support four commercial outcomes. Each is stated as what the user should receive.

**Sales explanation.** A monthly change explained by the actual part numbers, families and purchasing
entities involved, with coverage changes separated from real changes in business.

**Pricing precision.** A support or price-review case tied to comparable offers, applicable parts and an
explicit gross-profit scenario — not a blanket discount recommendation.

**Market comparison.** Competitor evidence with a dated source, a stated matching basis and the relevant
commercial terms, placed beside the relevant product and market.

**Service-range opportunity.** An applicable part, kit or documented value-tier alternative worth
discussing, with a reason it may improve the offer. Absence of a purchase on its own is not an
opportunity. This last outcome is deliberately concrete: the aim is to complete or improve an applicable
offer, not to count the products that were not bought.

## A4. What success would look like, and what is not claimed

A distributor should be able to open a monthly review, understand a purchasing change, examine the actual
parts behind it, discuss a suitable response and record the outcome. ISZE should be able to support that
conversation from the same evidence, without rebuilding the explanation in a separate spreadsheet or
presentation.

That is the target. It is not the current state.

**What is not claimed.** Revenue uplift, time saved and improved capture are outcomes to test. They are
not established benefits of anything built so far. No return figure is evidenced anywhere on our systems,
and Part G states that position in full.

---

# Part B — The operating model

## B1. The shared operating loop

Every piece of work in Universe follows one loop.

**Observe.** Select one population, one reporting clock and one transaction flow. Identify the change and
the records behind it.

**Explain.** Examine product mix, returns, coverage changes, timing, the applicable vehicle context and
the available market evidence. Keep untested explanations as hypotheses, and label them as hypotheses.

**Act.** Create a commercial intervention or a data-quality follow-up. Give it an owner, a review date,
any approval it needs, and the observable outcome expected of it.

**Review.** Revisit the same scope on the same measurement basis. Distinguish a change you can see from an
effect you can attribute to the intervention.

The connection between the three pillars is therefore not simply navigation between three dashboards. It
is preservation of the same question and the same evidence as the user moves between them.

## B2. Four destinations, and two views that must not blur

The proposed navigation exposes four connected destinations: **portfolio**, **network**, **commercial
review** and **actions**. AIM, IDS and PRISM inform those destinations rather than requiring the user to
rebuild the same selection in three separate products.

The **distributor view** is a commercial workspace. It carries purchasing, covered sales-to-dealer
activity, product mix, market context and the actions agreed. Where it shows a self-assessment summary,
that summary is labelled as results from a defined dealer self-assessment population, and never as a
distributor audit score.

The **dealer view** shows only the commercial records legitimately assigned to that dealer or site. It
displays the source identity, the status of the relationship and the coverage behind the figures. Where
an account covers several sites, the view presents the account-level result rather than inventing an
allocation to one site.

A distributor workspace is a user-facing view. A database-backed deployment is a separate technical
choice, and the two should not share an ambiguous label.

## B3. The decision patterns Universe should support

These are five patterns of decision, not findings about a market or a dealer. Each must be populated with
accepted records before it becomes a commercial claim.

**A decline that can be explained.** Start with monthly purchasing for the defined part population and one
transaction flow. Show the part numbers contributing to the decline, the returns, the entities that were
active, and any break in coverage. Separate a change in quantity from a change in price or mix. Then test
the available supply, fitment, supersession, promotion and competitor evidence. The permitted action is a
targeted part-level investigation or offer — not a statement that the market is losing the business.

**A value-tier alternative that is actually applicable.** A genuine part has lost activity, or faces a
documented competitive offer. Retrieve a value-tier candidate only where fitment, function, contents and
commercial units can all be checked. A shared family label is not sufficient. Test whether the comparison
is one-for-one or a kit relationship. The permitted action is a discussion about an applicable
alternative, with technical approval where it is needed. **Where no match can be validated, no substitute
recommendation is made.**

**A gap between the two purchasing flows.** Activity from ISZE to the distributor slows while covered
activity from the distributor to its dealers is stable, or the reverse. Compare like periods and separate
returns, valuation differences and missing channels. Inventory and timing are possible explanations, not
measured facts, unless stock information exists. The permitted action is a replenishment or availability
discussion. It is not proof of overstock, of shortage, or of lost demand at the end customer.

**A dealer-support conversation informed by IDS.** A dealer reports a weakness in a defined IDS practice
while its purchasing pattern shows something worth discussing. First validate the dealer and site link,
the assessment date and the commercial period. Consider incomplete purchasing coverage and the other
explanations. The permitted action is an agreed support activity with a review of the later purchasing
pattern. The association does not prove that the self-assessed weakness caused the commercial result.

**A stronger support or tender case.** A distributor presents an identifiable competitive challenge for
defined parts, or a fleet requirement. Combine the actual historical purchasing, the applicable
alternatives, dated market evidence and explicit volume assumptions. Build a gross-profit comparison on
the correct cost and price basis. The permitted action is to approve, amend or reject a bounded support
proposal, with an owner, conditions and a review point. A lower gross-margin percentage can coexist with
higher gross profit, and the calculation has to show which one applies.

**Selection principle.** Prioritise an action when the signal is material, the evidence is sufficient and
somebody can realistically act on it. A data gap should create a specific data-quality task. It should not
be disguised as a sales opportunity in order to fill a list of five findings.

## B4. The standard for every finding

A finding is a small, reproducible evidence packet. It contains the following, and a packet missing any
of them is not finished.

| Element | Minimum content |
|---|---|
| Scope and coverage | The distributor or dealer population, the transaction flow, the reporting clock, the period, the included channels, the source version and the known gaps |
| Monthly evidence | A dated series in units or on a clearly named monetary basis, comparable periods, missing months visible, and an explanation of any break in coverage |
| Part-level contribution | Original and normalised part number, description, the family it sits in, the current and comparison measures, its contribution to the change, and returns where they exist |
| Product comparison | The documented genuine or value-tier relationship, applicability, pack contents, unit conversion and validation status |
| Interpretation | What is observed, which explanations are supported, which remain plausible, and what evidence would change the conclusion |
| Action and review | A named owner or accountable role, the proposed intervention, any required approval, the review date, the expected outcome and the later result |

**Chart rules.** Where a decline is claimed, show a monthly time series rather than two isolated totals.
Do not draw a continuous line through a month that was not reported, as though it had been measured. A
reported zero is a different thing from a missing observation, and the two are drawn differently. Separate
unit trends from price effects where the data supports it. Show which parts contribute to the change,
with an "other parts" remainder so that the contribution view reconciles to the selected total, and use
signed contributions for increases and decreases. State whether the comparison uses a fixed part
population or includes new and discontinued products. Do not add pieces, kits and sets together into a
supposedly comparable volume without a validated conversion. Where a common reference valuation is used,
disclose the price list date and which parts were priced. **A chart title must not call a reference
valuation sales revenue.**

## B5. Confidence as a decision status, not a score

Every finding carries one of four decision statuses, with the reason shown: **ready for review**,
**needs validation**, **context only**, or **withheld**.

There is no single confidence score, because a single score hides its ingredients. Coverage, identity
matching, applicability, price comparability and period alignment are separate checks and are reported
separately.

A report with no validated value-tier match says so. A report with no dealer-level feed stops at the level
its evidence supports. A data-quality action can still be useful, but its commercial benefit stays
unclaimed.

**Reproducibility test.** Another reviewer must be able to obtain the same total from the same accepted
data and the same version of the metric definition. The filters, the source references and the
calculation definition are exported alongside the presentation.

## B6. The response obligation

This chapter exists because the value of Universe is redeemed at one point only: when ISZE answers a
question from a distributor or a dealer and somebody acts differently as a result. Data collection
without an answer is not the product.

**The five response classes.** Universe uses five, and every incoming question falls into one of them:

1. routine information;
2. an application check;
3. a commercial decision;
4. a supply investigation;
5. a fuller service analysis.

**What counts as an answer.** An acknowledgement is not a substantive answer. A reply that says "awaiting
technical review" must name the next review arrangement and the information still needed. Where a
response date changes, the case retains the reason and the participant is told.

**The paper does not invent response-time targets.** They are agreed after the existing workload has been
measured: how information is assembled today, how many functions are involved, what is typed repeatedly,
and how long the participant waits. The deliverable of this stage is the measurement design, not an
unearned number. Once the measurement exists, response-time and adoption targets can be set against it.

**The capacity condition.** The receiving organisation must have both the capacity and the authority to
answer. That capacity is not funded today. This is not a detail: it is the failure mode the whole design
has to avoid.

**The position on case records.** There is no support-case register at case level anywhere on our systems.
Where an owner should be named, a role is named instead. Two checks make the point precisely. First, the
name of the existing competitive-quote programme returns **no hits across any column of all 538,346
billing rows** — a programme of that kind can leave a payment on the billing side, and a payment records
that money moved, not that a question was asked or answered. Second, a mileage question to the ITUK Parts
Director was drafted on 18 September 2026 and **is still unsent**.

**Why this fails by default, and therefore why it must be written down.** Software is cheap at the margin
and a person's time is not. The data collection is the half that can be specified, budgeted and built by
a project. The answer is the half that needs a named person with hours in the week, and it has no natural
home in a project budget because it is a recurring cost with no measured return attached. Left alone, the
cheap half gets built and the expensive half is deferred, and the product arrives looking complete while
the thing it was for never happens.

> A low marginal cost for software does not mean the response service is free.
>
> Software cannot substitute for an operating commitment. Otherwise, better data collection simply makes
> unanswered requests easier to count.

---

# Part C — Evidence architecture

## C1. The transaction flows, and the rule that they are never merged

Three flows exist, and they are different things.

**ISZE to distributor** records the distributor's purchasing from ISZE. **Distributor to dealer** records
the dealer's purchasing from that distributor. **Dealer to end customer** is a third, separate flow.

None is a substitute for another. Missing coverage in the second flow means that activity beyond it
is unknown, **not that it is zero**. The same physical part may appear in more than one flow, and those
values must not be added together as a single market-sales total. Timing differences between the flows may reflect order
cycles, returns, stock movements or other factors, and without the relevant evidence they do not prove
lost demand.

## C2. The four layers, and why the fourth is empty

| Layer | What it is | What it can be compared with |
|---|---|---|
| 1 | ISZE parts billed to the distributor | Layer 2 as a total, distributor to distributor |
| 2 | The distributor's sales to its dealers | Layer 1 as a total; layer 3 on shared part numbers |
| 3 | Parts recorded in workshop jobs | Layer 2 on shared part numbers |
| 4 | The dealer's sales to the end customer | **Nothing — there is no source for this layer** |

The layers differ in population, in currency and in identity. Layer 1 has no dealer column at all. Layer 3
names a workshop and a vehicle, but not a sale by a dealer. Layer 4 does not exist in any record we hold.
The four-layer comparison was deliberately not reconciled and remains **not tested**.

**An account map establishes identity only.** It does not create dealer-level billing, it does not
establish stock, and it is not proof of onward sale. Anyone who reads a dealer-to-account list as a way to
see a distributor's trade will be disappointed, and it is better to say so before the list arrives than
after.

## C3. What a number is allowed to mean

Every figure in Universe falls into one of five classes. The class determines what may be said about it.

| Evidence class | Permitted interpretation |
|---|---|
| Recorded quantity | Activity in the named source and covered population, on that source's declared unit basis |
| Recorded billing | Monetary activity in the named billing flow, with its currency, credits and accounting basis identified |
| Reference-price valuation | A quantity multiplied by a stated reference price. Useful for a common comparison basis. **Not actual selling revenue and not margin.** |
| Modelled demand or potential | An estimate built on explicit assumptions about the vehicles in service, the interval, applicability and valuation. **Not observed servicing.** |
| Hypothesis or candidate | A possible explanation, substitute or action that requires stated validation before any stronger claim is made |

A calculated total inherits the limitations of its inputs. **A precise euro value does not make a modelled
result measured.** Missing price coverage must be visible, and parts that could not be priced must not
silently become parts worth nothing.

## C4. Every comparison carries its scope

Every output persists its transaction flow, population, period, reporting clock, measure, currency,
valuation basis, source version and coverage state.

A partial current month is compared only with an equivalent cut-off, or it is labelled separately.
Calendar-year and fiscal-year views of the same activity are never added. Where supported, Universe uses
the latest complete month and trailing complete-month views, and preserves a different reporting clock
where the user has explicitly selected one. If a dealer or a channel enters the feed, its effect is shown
separately from like-for-like development.

**Coverage precedes ranking.** Establish which distributors, dealers, months, channels and part
populations each source covers before comparing performance. A declared population is not necessarily the
whole market. **Where a reliable denominator is unavailable, show what is covered rather than inventing a
completeness percentage.**

A result should become less certain when its evidence becomes weaker. It should not become more definite
simply because it has been placed on a dashboard.

## C5. Fleet, GPS, PMS and warranty — keep the business lenses apart

GPS concerns the broad genuine-parts opportunity. PMS concerns the defined interval and competitive-parts
scope. Their approved definitions, part populations and denominators are registered separately, and a
PMS-family result must not be relabelled as overall GPS performance.

**Purchasing intensity.** A useful lens is billing, or a common reference valuation, per relevant vehicle
in service. The numerator, the vehicle population, the period and the valuation basis must be compatible.
**This is not automatically market share.** A modelled potential is not a measured denominator of all
market transactions.

**Modelled service demand.** Expose the assumptions that drive the estimate: the relevant vehicles in
service, the age or usage profile where it is supported, the service interval, the quantity consumed per
event, applicability, the observation period and the value basis. Present a range or a sensitivity where
uncertainty materially affects the decision. **A single exact-looking estimate must not hide a weak fleet
or usage assumption.**

**Vehicle attribution.** The billing system holds no VIN, no chassis number and no model-level servicing
evidence. Vehicle attribution is permitted only through validated exclusive part applicability. Parts
that fit multiple weight bands or families remain pooled, and must not be allocated by fleet share merely
to complete the picture. Three views are maintained separately: recorded purchasing on parts that fit one
band only; modelled expected demand by band; and actual purchasing at market level. A market actual
repeated beside several bands is non-additive: it must not be summed across bands, and it must not be
divided by one band's expectation to claim measured service cover for that band. **A modelled allocation
of a market gap is not measured leakage, and it must not become a dealer ranking.**

Where the band file is used, the standing rule is: filter on the additive flag for the view that may be
summed; treat the exclusive-only column as the exclusive numerator; treat the also-fits column as
non-additive; and keep calendar and fiscal views separate. The corrected band rules supersede the earlier
set.

**Warranty is a different source.** Warranty records claims, defects and settlements. It does not provide
a complete record of scheduled maintenance. Low warranty value is not evidence of a healthy aftermarket,
and missing maintenance claims do not prove that dealers are failing to service vehicles. Warranty may
contextualise a product issue within its own coverage. It must not supply an invented service interval, a
maintenance-capture rate or a leakage conclusion. A claim pattern beside a parts trend creates a question
to investigate, not a commercial explanation.

## C6. Counted, not modelled — the distinction the reader needs

A figure is either **counted** in a named source with a stated population, or **modelled** on stated
assumptions. The second can never be dressed as the first.

Every modelled number names its assumptions and carries a range or a sensitivity. Every counted number
names its coverage limit and the direction of its bias. This is the rule that keeps the paper honest in
both directions:

- **Counts and observed monetary totals are floors.** A truck serviced elsewhere is not counted, and a
  dealer that did not report is not in the data.
- **Rates, per-vehicle figures and extrapolated expectations are not floors.** They carry the bias of
  whatever population and method produced them, and where a rate is printed the direction of its bias is
  printed with it or the rate is not printed.

A rate can therefore overstate even when the count under it understates, and a paper that says "every
figure here is a floor" is wrong. It is one of the phrases this edition removes.

---

# Part D — Data and participation

## D1. The minimum data contract

**What is asked for.** A monthly quantity feed with a declared population, submitted within an agreed
number of working days after month-end, with a closed month distinguished from a provisional one. The
proposed deadline is within ten working days, subject to agreement with the participating distributor.

**The preferred level of detail** is: distributor × dealer × calendar month × part number × unit of
measure × transaction type × channel. A more detailed feed may be accepted. Invoice prices and
end-customer information are not required, and Part D4 explains why that boundary matters.

**The required elements, each with its control.**

| Element | What it must carry, and the control on it |
|---|---|
| Distributor identifier | A stable identifier in an agreed namespace. Never resolved from a display name alone. |
| Dealer identifier | A stable source-system identifier, mapped explicitly to a legal entity or site, with aliases and effective dates maintained. |
| Reporting period | Calendar month and the source time basis; transaction dates preserved separately where they are supplied. |
| Original part number | A text value that preserves leading zeros and source formatting, with a normalised join key stored separately. |
| Signed quantity and unit | Whether a unit is a piece, a set, a kit or another measure. Positive sales and negative returns must remain distinguishable. |
| Transaction type and channel | Sale, return or adjustment; direct or wholesale. Preserve an explicit unknown rather than guessing. |
| Submission identifier | The distributor-period batch ID, revision, extraction timestamp and schema version. |
| Coverage declaration | Which dealers, channels and product scope are included; which records are excluded; which periods are missing; whether the month is provisional; and the known limitations. |

**The dealer population.** Provide a stable dealer roster, or an agreed controlled equivalent, including
dealers with no activity in the month. **Absence from a transaction file alone does not establish zero
activity, and it does not establish that a commercial relationship has ended.**

**Wholesale.** Declare whether wholesale is included, and to which known purchasing entity the sale is
attributed. **Do not assign a wholesaler's purchases to dealers further down the chain without a
supported relationship.**

**Correction and acceptance.** Revisions are full replacements for a distributor-month wherever possible.
A corrected batch **supersedes** the earlier accepted batch; it is not added to it. Reprocessing the same
submission must not duplicate quantities. Earlier versions and the reason for the revision are preserved.

Before acceptance, the feed is checked for identifiers, periods, quantities, units, duplicates, coverage
and control totals. The process records **accepted and quarantined quantities, not merely rejected row
counts**. An incomplete dealer mapping need not prevent a valid national total, but it **must** prevent
any dealer-level attribution that the mapping does not support.

In return, the distributor receives a receipt stating the accepted period, a coverage summary, the
exceptions raised and the route to correct them. Where a revision changes a dependent output, that output
is rebuilt and the reader is shown that the earlier published result has been restated.

## D2. Participation: start with the existing incentive, then earn the rest

**The honest starting position.** A portion of the distributor kickback is already tied to providing
sales-to-dealer information, and that condition is what starts the exchange. It is worth being precise
about what it buys.

The condition gets a file containing dealer, part number, period and quantity. **It does not get a file
that anyone cares about, and a file sent to satisfy a condition is the minimum that satisfies that
condition.** A compliant file can carry the required columns and still carry no prices, no vehicle
reference and no reason codes.

**The commercial terms of that kickback are not confirmed by any file in this workspace.** This paper
therefore states the mechanism and not the terms, and it names the confirmation as an open decision in
Part G. Where these papers describe a submission standard, that standard is a **proposal**, not a
statement of terms that already exist.

**Three reasons a distributor contributes.** Each is stronger or weaker than the others and the design
depends on knowing which.

| Reason | How it works | How strong it is |
|---|---|---|
| The requirement | The existing condition on the sales-to-dealer information. Buys frequency and coverage. | Strong enough to get a file. **Not strong enough to get a good one.** |
| Self-interest | The parts team already has to explain its own numbers every month. Where Universe assembles that explanation, contributing is the cheaper route to its own answer. | Strong, recurring, and the main engine of the exchange. |
| The defensive reason | A recorded reason code saying "the customer bought elsewhere at a lower price" protects the parts manager from being read as a weak seller. | Underrated. It is what keeps the file coming in month six. |

**The exchange test.** Every ask has to complete one sentence: **if the participant gives Universe X,
Universe returns Y, which helps them decide Z.** Any feature whose only justification is "better
visibility" is rejected, because it asks for something and returns nothing.

**The three-tier structure.** Core participation is the monthly file, which is the condition on the
existing incentive, and it earns the complete core review. Collaborative participation is voluntary: a
participant provides selected additional information for a specific agreed analysis and receives that
analysis. Strategic participation is where Universe becomes part of the distributor's normal process —
network reviews, follow-up on self-assessments, tender preparation, value-tier positioning, support
requests — and at that point the incentive has become almost irrelevant.

## D3. The levels of contribution

Contribution unlocks depth, and the rule that governs it is worth stating plainly: **a participant sees
the whole review experience at the level it can be computed, and the depth of the dealer and reason
picture unlocks as they contribute. Nothing is hidden out of spite — the deeper views cannot be computed
from less data.**

**Level 0 — ISZE data only.** Nothing new is asked for. The participant sees billing against target spend
per truck, family mix, the genuine against value-tier split, self-assessment results with the assessed
population and the round stated, position against comparable markets, and the tender panel. For ITUK, the
dealer-named picture already held for calendar 2025 is shown as a deliberate demonstration of what a
dealer-named file makes possible. This level must be genuinely useful on its own. It is not a teaser.

**Level 1 — sales to dealer. The mandatory core.** The ask is a dealer identifier, a part number, a
quantity and a reporting period. **No prices.** This unlocks the share of billing that moved onward, by
dealer and by family; the stocking position; part-number demand below the distributor; and the geographic
picture of where demand is thin. Prices are the field we least need and the field they most resist.

**Level 2 — dealer and network identity.** The ask is validated account and site relationships, and an
approved link to the dealer self-assessment round. **This link does not work today**, and Part E explains
exactly why. Until it does, no dealer in a distributor's network can be attributed to a billing entity
except by its market label.

**Level 3 — commercial context.** The ask is structured explanations rather than documents: a competitor
price quote, an availability or backorder situation, a tender involvement, a customer requirement, an
existing stock position, an application or fitment mismatch. This unlocks the reason behind a movement —
for example, that a family is down, and that roughly half of the movement is a price difference, a third
is supply, and the remainder is demand — and it builds a library of reasons that makes every later
review faster.

**Level 4 — optional operational information, assessed one item at a time.** Backorders are worth asking
for first: the highest-value operational ask, with a format that already exists. Stock is not asked for
yet: there is no stock measure anywhere in the business and no engine to use one. The dealer's own
service population is the highest-value long-term item and is **not** requested from the distributor — it
is built jointly with dealers. Workshop activity follows only after two completed reviews have produced a
repeated, decision-relevant question that genuinely needs service evidence. Warranty odometer readings
are not that evidence.

## D4. What is outside the mandatory feed, and why

The mandatory feed does not include: the distributor's selling price to its dealers; the dealer's selling
price to a customer; the distributor's margin; the dealer's margin; the distributor's stock; the dealer's
stock; customer names; fleet or customer account data; VIN; workshop repair orders; technician
information; customer invoices; customer personal data; or competitor invoices.

**This boundary is strategic, not administrative.** If Universe begins by requesting the distributor's
prices, margins, stock, customers, vehicles and workshop activity, it will read as ISZE trying to see
through the distributor rather than as ISZE helping the distributor run the authorised network. Once that
impression forms it is hard to undo, and the cost of undoing it is measured in the next three requests
that are refused.

Two further rules follow from it. **Optional sharing must never become a concealed condition for
receiving the basic return.** And for any optional module: **the moment an optional input becomes a
condition of access to the core review, the review stops being a product and becomes a form.**

## D5. What not to ask for yet, and what never to ask for

Not yet: prices on the sales-to-dealer file; dealer resale prices or anything implying a required resale
price; full stock and inventory valuation at entry; warranty odometer readings as a fleet or
service-population source; dealer-level vehicles-in-service derived by allocating a national fleet;
customer or VIN-level detail and workshop job cards, before a repeated question needs them; tender
feedback as a condition of anything; and any standards compliance scorecard or dealer league table.

Never as a measure of benefit: uploaded row counts, login counts, or the reference-price value of
workshop lines. These measure activity, not usefulness, and they are easy to present as results.

On dealer resale prices, the distinction matters and is worth writing down: monitoring and reporting is
one thing, and anything that reads as price coordination is a legal and relationship risk with no upside.
On the national fleet, the same: a dealer-level vehicles-in-service figure derived by dividing the market
fleet looks like a denominator and is not one.

## D6. The dealer proposition

**The dealer receives no kickback from ISZE.** The paper says so plainly because the dealer will ask.

What the dealer receives is help for its own business. Universe shows how its parts purchasing is
developing, which product families it uses, where genuine and value-tier alternatives are relevant, what
vehicle population may sit behind the demand it sees, and which follow-ups or commercial opportunities
deserve attention. The dealer can see the evidence behind a discussion, correct information that is
wrong, add local context, and take part in deciding what happens next.

What it is not: an ISZE dealer audit, and not a league table. The dealer leaves each review with something
it chose, and the previous one is visibly being tracked. That is the difference between a review and an
inspection, and it is also why the dealer proposition has to be different from the distributor's. **The
dealer must not become a coloured dot on a map controlled by ISZE.**

## D7. The dividend, and the test of the whole design

Three rules govern the return the participant receives.

**It lands in the same cycle in which it was earned.** A dividend delivered in the third quarter for a
contribution made in January is not a dividend; it is a promise.

**It attaches to a decision, not to a chart.** A new view is not a dividend. Something the participant
decided differently is.

**The contributor can audit it.** Each participant can see a list of what it gave, what was returned, and
which decisions the return touched. This is the rule that lets the exchange survive a change of
distributor staff, which is when most data programmes quietly stop.

**The test of the whole design, stated so that it can fail.** If the sales-to-dealer requirement
disappeared from the kickback tomorrow, distributors would continue supplying the data, because
withdrawing it would make their own Universe output materially worse.

That is measured through behaviour and not through survey scores: files corrected voluntarily rather
than to the minimum; optional information shared for a defined business case; Universe evidence used in
the distributor's own dealer reviews; dealers contributing explanations and agreeing actions; support
requests arriving with Universe evidence attached; tender opportunities moving into distributor action;
self-assessment follow-ups using commercial evidence; distributors asking for analyses that do not exist
yet; and data arriving reliably even when nobody reminds them about the kickback. **The strongest single
signal is voluntary enrichment — a distributor giving something that was explicitly not required,
because the previous exchange produced value.**

---

# Part E — Identity and parts

## E1. Four things that are not the same thing

Universe distinguishes four kinds of entity, and the distinction is the difference between a usable
per-dealer figure and an invented one.

| Entity | What identifies it today |
|---|---|
| A servicing workshop | A stable numeric identifier, 84 values, in one-to-one correspondence with the workshop name |
| A vehicle operator or lessee | A stable numeric identifier, 202 values, in one-to-one correspondence with the company name |
| A physical site | A depot name, 260 names, **with no identifier of any kind** |
| A purchasing dealer | **No identifier of any kind on our side** |

**The gap that governs everything else is the last row.** ISZE's billing system identifies a customer as a
sold-to account, and the account it holds is the distributor's. The distributor's sales-to-dealer file
identifies a dealer as a name. Those are two different namespaces held by two different organisations, and
nothing has ever bridged them — because from ISZE's side there was no commercial event that required a
dealer's identity.

The consequence is measurable and worth stating with its evidence. The purchasing file already contains
the two columns a join would need, and **both are blank on all 66,018 rows**. They are blank for a
concrete reason: there are only three purchasing accounts in scope on our side, and all three are the
distributor's own accounts, so there is nothing on the ISZE side to place beside a dealer site. The
coverage check states the position literally — purchasing accounts mapped to a dealer site: none of three.
Every dealer-level measure in this paper, and every comparison of what was billed against what was passed
on, sits behind that one missing list.

## E2. What a match is, and what it is not

A match on normalised company names — punctuation, legal suffixes and site brackets removed — is
**evidence to review, not an approval of identity.** Where a match is one-to-one it may be used to produce
a per-dealer view. Where the key is not one-to-one, **do not print a dealer page: print the collision
instead.**

Two rules travel with any match count. First, **the count printed is the count for the stated rule, and
the rule is named beside it.** A count without its rule is not a finding. Second, some entries in the
workshop list are not independent dealers at all — they include the head office, the national service
entities and the roadside recovery operations — and **any per-dealer page must exclude them.** A page
built without that exclusion would publish a page for the distributor's own recovery operation.

**And one thing a match can never do.** An account map connects identities. It does not create
dealer-level billing, it does not establish stock, and it is not proof of onward sale. A name match is
never evidence that goods moved.

## E3. Accounts and sites

One commercial account is not automatically one physical site. A multi-site account's quantities stay at
account level and must not be duplicated across site markers. Where an account covers several sites, the
view presents the account-level result instead of inventing an allocation to one of them.

A country, a submission cohort or a point on a map does not validate which distributor is responsible for
a site. Responsibility requires an explicit, dated relationship. **Unresolved sites are shown as
unresolved**, not silently assigned, and a map that shows a location close to a site has established
nothing about who serves it.

## E4. Parts: classification, supersession and equivalence

**Classification.** More than one classification release exists and **no single authority has been declared
between them.** This is an open decision, it belongs to the classification owner inside ISZE, and it is the
one blocking question ISZE can close without asking anybody else. Until a decision names one release, with
its version and its coverage, **no family label is printed outside ISZE.**

The figure in circulation about how far the classification has moved describes a **stale one-time copy
inside the main table**, not a live defect in the classification itself. The corrected rebuild restores
almost all of the affected part numbers to the right family. The paper therefore describes the position as
an unsettled release rather than as a data-quality problem, because that is what it is.

**The axis.** The classification carries two trees — a catalogue axis and a workbook axis — and they
disagree for many part numbers. **The axis must be named.** A sentence that says the classification places
these parts where competition applies is reading the catalogue label, and it must say so; the same parts
can sit under a service heading on the other axis, and both statements are true.

**Supersession.** One part number replaced by another. The table of replacements is safe to join: **no old
number maps to more than one current number**, so applying it cannot multiply a total. What it does is
**split a purchasing history across two codes**, which is why it is a step to run before a family total is
computed and not a footnote to add afterwards. Its authority, however, is unknown: it carries no date, no
source system and no reversal flag, and this paper names the confirmation of what it is as an open
decision. Wherever it is used, **the paper states which sheet of which file was applied.**

**Equivalence.** A pairing in any source is a **catalogue relationship, not a fitment approval.** Nothing
we hold is a fitment approval or a homologation. Two further distinctions matter:

- **"No pair exists" is not "no product exists."** A missing pairing is not evidence that a value-tier
  product fails to exist.
- **A supersession relationship is not application approval either.** The replacement table says one
  number replaces another. It does not say the replacement is approved for a vehicle. **Wherever a
  substitution is proposed, application must be validated separately before the alternative is
  recommended**, and until it is, the relationship is reported as a catalogue fact and nothing more.

No quality inference is drawn from tier or country of origin, in either direction. Those are recorded
attributes, not judgements.

**One population per calculation.** Every measure is computed on one named part population, and the
population prints beside the figure. Three exist for the worked family, and they are not interchangeable:

| Population | What it is | May it carry a replacement measure? |
|---|---|---|
| The named page part numbers | The short list chosen for the dealer page | Yes, for those numbers only; it does not describe the whole flow |
| The consumable elements inside the family | The replacement population — the parts that are themselves consumed in a service | **Yes. This is the one.** |
| The wider parts tree the book consumes | The family as a whole, including housings, caps, bolts, gaskets and assembly-level items | **No.** It is a family or purchasing view. It is never a replacement measure. |

## E5. IDS: what it is, and the limits on presenting it

IDS records a **dealer self-assessment**. That is what it is, and the paper says so every time it appears.

- The dealer records its own position against a checklist of five sections. No ISZE auditor visits.
- **There is one assessment round. No second round exists.**
- **There is no per-dealer assessment date.** The workbook contains a date field and it is empty on every
  sheet; there are no date-formatted cells in it anywhere. **Any statement of the form "as at this date,
  this dealer scored this" is not available.**
- A summary of dealer assessments identifies the assessed population and the assessment period.
- **A totals-only record must not generate section or question scores.** A blank is not a failure — it
  means that section was not scored — and a record with only a total cannot honestly produce a section
  view.
- **ISZE does not audit distributors.** A distributor-level presentation of IDS describes an assessed
  dealer population, its response coverage and its assessment dates. It never reads as a distributor
  audit score, and it never becomes a league table.
- A self-assessment score is therefore **context only. It is not a performance measure.**

The action register that sits beside the assessment is a **scaffold, not a working process**: it has rows,
it has no owners and no due dates, and every row reads open. **A blank register does not prove the network
is inactive.** It proves that no one has yet been asked to own anything, which is a different and more
useful conclusion.

## E6. Israel, and the other entities that are never blended

Two Israel distributors operate there, with separate systems and separate databases. The Israel country
pack belongs to one of them, and the other **did not take part in that assessment round.** They must
never be averaged, blended or presented as one figure, in any chart, correlation or register, because a
blended number would place one distributor's figures against a network that was never assessed.

The same rule applies everywhere it can: the two United Kingdom channels are different entities and are
never mixed. Country labels are spelled out in English in anything shared — not the internal code.

---

# Part F — Delivery

## F1. Two pilots, and why they are different

Two pilots are proposed, in two markets, and they are deliberately not the same shape.

**The national pilot.** Deliver a national commercial review — monthly, by family and part number, with a
clear statement of which transaction flow it comes from — together with a separately labelled view of the
defined dealer-assessment population, showing dates and response coverage. **Do not allocate national
purchasing to named dealers, and do not infer dealer performance from a national total.** The two panels
may sit adjacent, but the layout must not imply that a national purchasing pattern belongs to an assessed
dealer.

**The dealer-level pilot.** Demonstrate one path from a validated dealer to a monthly family pattern, the
parts contributing to it, and an evidence-backed action. Where a value-tier candidate exists, show its
relationship and its applicability evidence; where none exists, show the missing-match state rather than
leaving a gap. Join a self-assessment only where the site relationship and the relevant dates are
supported.

**Before any bridge between the flows is shown**, the relevant billing slice from ISZE to that distributor
is accepted and reconciled separately from the distributor's own sales-to-dealer feed. **The presence of
one source does not establish the availability or completeness of the other**, and a national total is
never divided among sites to create a dealer view.

## F2. Exit criteria for both

A pilot passes when one useful review can be reproduced, explained to its intended recipient, corrected
through the submission process, and followed into an action somebody owns. **It must also demonstrate its
unavailable-data state** — a pilot that cannot show what it does not know has not been tested.

A pilot does not pass because a map opens, or because every dealer has been given a score.

Two further rules. **No forced symmetry**: a credible national pilot and a credible dealer-level pilot are
preferable to two visually identical pilots built on incompatible evidence. And passing one pilot does not
certify the other: passing the national pilot does not certify the dealer-level mappings, and passing the
dealer-level pilot does not create the data the national pilot lacks.

## F3. The workspace experience

The four destinations, and the portfolio as the entry point for understanding the range, with the
genuine and value-tier comparison as a central experience.

Six operating rules follow from the evidence rules in Part C, and each is a requirement rather than a
preference.

**Context is preserved.** Opening a dealer, a family, a part or a follow-up preserves the selected period,
the reporting clock, the transaction flow and the population. Where the next view cannot support that
context, it explains the restriction before changing it.

**A change of basis is visible.** A switch from actual billing to a reference valuation is shown on the
face of the screen, not hidden in a tooltip.

**The context strip.** A compact strip sits near the headline result and carries six things: scope,
period, flow, measure basis, freshness and coverage. Source and metric details are one link away.

**Unknown and withheld are distinct states.** Neither renders as a zero.

**A review leads somewhere.** A commercial review opens the relevant parts and comparison evidence,
creates an action without retyping the scope, and exports a readable evidence packet. Actions return to
the analysis they came from. A correction is visible wherever the affected result appears.

**Complete paths before many incomplete pages.** The first release should favour a small number of
complete paths over a large number of pages that do not finish. A user should always know what the screen
measures, how to investigate it, and what can be done next.

**Maps do not establish responsibility.** The network atlas helps users navigate known sites. A country, a
submission cohort or a map location does not validate which distributor is responsible for a site, and
unresolved sites are shown as unresolved.

## F4. The logical data architecture

The architecture has four layers, and they are logical responsibilities rather than a choice of platform.
The choice of storage platform or application framework is a separate implementation decision.

1. Retained source submissions.
2. Accepted normalised records.
3. Versioned business definitions.
4. Published views and actions.

**Six record groups, with their responsibilities.**

| Record group | Required responsibility |
|---|---|
| Source batch and coverage | File identity, checksum, source owner, period, revision, schema, declared coverage, acceptance state and control totals |
| Commercial facts | Each transaction flow stored separately, with source keys, dates, part identifiers, quantities, units and the monetary basis where one exists |
| Product and applicability | Versioned classification assignments, descriptions, supersessions, kits, alternatives and applicability, each with its own evidence and status |
| Network and IDS | Organisations, purchasing accounts, physical sites, dated distributor relationships, assessments and assessment items kept separate from one another |
| Market and demand context | Vehicle fleet vintages, segment definitions, competitor observations, reference prices and versioned service-demand assumptions |
| Metrics, findings and actions | Definitions, input versions, scope, calculation lineage, evidence status, owner, approvals and outcome history |

**Joins must not manufacture volume.** State the expected relationship for every join and test for
duplication. A part that fits several weight bands, joined to several bands, must not multiply the
original purchasing total. An account linked to several sites must not produce several copies of its
result. Where a total changes after a join, the change is documented and reconciled.

Preserve original part identifiers alongside normalised keys. Keep unresolved mappings in an explicit
bucket and **do not discard their quantities from the reconciliation.** Test totals before and after
classification, relationship mapping and valuation.

**One definition for each named measure.** A shared register defines each measure — including the
business lenses, gross profit, recorded quantity, actual billing, reference valuation and modelled demand
— with an owner, a formula, an eligible scope, its exclusions, its reporting clock and its version.
**Different measures must not reuse the same label merely because they occupy the same place on a
screen.**

**Build in correction and reproducibility.** Accepted revisions are retained rather than overwritten. A
published result identifies which batch, which relationship versions and which metric version produced
it. A correction triggers recomputation of the results that depend on it and a visible restatement, while
the earlier published snapshot is preserved for review. A finding is stored as more than prose: its
scope, the query or calculation that produced it, its evidence links and its status. An automated
explanation may summarise these records; **it must not become the source of its own quantities, and it
must not silently redefine a measure.**

## F5. Governance and accountability

Five roles make the decisions, and each needs a person rather than a team name.

| Role | What it decides |
|---|---|
| Product owner | Scope and acceptance |
| Data owners | Source coverage and corrections |
| Metric owners | The business definitions |
| Commercial owners | Interventions and support terms |
| Technical owners | The application, permissions, testing and the release record |

**People are assigned to these roles before anything expands beyond the pilots.** A role with no name
attached is not an owner, and an unowned case does not count as delivered.

Two further assignments are specific. Interpretation of the self-assessments belongs with the accountable
standards owner. Product equivalence and fitment require a technical authority, and neither a
classification suggestion nor an automated match can substitute for that approval.

**Protecting the exchange.** Distributors receive their authorised information and approved comparative
context, and never unrestricted access to other distributors' records. Dealer views follow validated
relationships and access permissions. Aggregated comparisons account for the risk that a small population
reveals an individual participant. Optional information about prices, costs, stock and service needs an
explicit purpose, an access rule and a retention rule. Cross-distributor price sharing and competitively
sensitive benchmarking pass internal legal and competition review before release. Imported files and
narrative notes are treated as data and never as instructions, and automated assistants receive only the
access and the actions a review requires.

## F6. Access — the sentence that has to be in the paper

**A login or a hidden menu does not remove embedded wider-network data. Hiding another distributor behind
a filter is not access control.**

External sharing is a data-separation problem before it is a login problem. There is no host today: the
analysis application has no authentication, no static deployment is configured, and the folder that would
be published is not safe to publish as it stands, because it contains dealer-level material and
wider-network data that does not belong on a distributor-facing page.

## F7. A release is a retrievable deliverable

Every accepted release has one stable index that names its version, its date, its owner, its entry point,
its included modules, its data snapshot and its known limitations. It lists the actual deliverable
filenames with their integrity checks, and it identifies the portfolio, atlas and distributor-view entry
points explicitly.

**A temporary browser preview is not the release location.** A label such as "R1", or a statement that a
build is complete, is not evidence that a package exists, opens correctly and contains the agreed scope.
Earlier releases are retained, but the accepted release is unambiguous.

## F8. Test the failures that would damage trust

Before release, the following are tested rather than assumed: duplicate submissions; revised months;
missing periods; returns; unresolved dealers; multi-site accounts; multi-band applicability; and unpriced
parts. So are two behaviours that are easy to get wrong and expensive to get wrong: that actual billing
cannot silently switch to a reference valuation, and that repeated market actuals cannot be summed across
bands.

Regression tests preserve the corrected band behaviour, the removed aggregate sales view and the agreed
portfolio and genuine/value-tier scope. They also verify the national boundary of the national pilot, and
the distinction between a dealer's self-assessment and a distributor's commercial view.

The tested scenarios, their results, the outstanding issues and the approval are kept with the release.
**Saving a rule, or discussing a fix, is not proof that the running product has adopted it.**

## F9. Delivery gates

Four gates, each with a pass condition that can be checked.

**Foundation — establish the position.** Create the release index, the source-coverage register, the
metric register and the list of unresolved relationships. Identify which capabilities are accepted, which
are demonstrated only, which are proposed and which are blocked. Confirm the functional boundary of the
third pillar. Preserve the existing scope decisions before adding features.
*Pass condition:* a reviewer can identify the accepted product, the sources behind it and the
interpretation rules it applies, with no ambiguous "latest" file and no silent redefinition of any
measure.

**Pilot — complete two honest paths.** Deliver the national review and the dealer-level review at their
supported levels, each with a real monthly series, a part-level explanation, a validated comparison or an
explicit limitation, and an owned follow-up. Exercise a correction and show its effect.
*Pass condition:* each pilot can explain its figures, reproduce its result and demonstrate what is
unavailable.

**Participation — make the return repeatable.** Run the agreed monthly submission and return process.
Measure accepted coverage, exceptions, correction turnaround, and the work needed to produce a usable
review. Ask whether the distributor used the output in a commercial conversation, not merely whether
somebody logged in.
*Pass condition:* participants can maintain the feed, recognise its limitations and receive a useful
review without a bespoke rebuild every month. **Targets are agreed after the pilot measurement exists, not
before.**

**Expansion — add only demonstrated value.** Add markets or optional exchanges only after the relevant
controls work, and only when the benefit and the ownership of the maintenance are clear. Tender support,
richer availability analysis and photography are considered only on that basis. **Do not restore a
deferred feature merely to create the appearance of progress.**

## F10. What should be measured

Track three things separately, because they measure different things and combining them hides all three:
**data reliability**, **review usefulness**, and **commercial outcomes**.

Useful measures of reliability include valid mapped coverage and restated periods. Useful measures of
usefulness include the effort required to prepare a review and the number of actions reviewed or closed.
For commercial outcomes, realised gross profit on a bounded intervention, where it can be calculated on an
approved basis.

**Do not treat logins, modelled opportunity values, or the number of findings generated as realised
commercial value.**

---

# Part G — Open decisions, the money, and the next milestone

## G1. The decisions this paper leaves open

Each decision below has an owner, and each unblocks something specific. None of them is closed by writing
this paper.

| Decision | Owner | What it blocks | The smallest response that closes it |
|---|---|---|---|
| The dealer-name-to-account-number list for the pilot market | The distributor's parts function | The comparison of what was billed against what was passed on, at dealer level | One spreadsheet column pair, with an explicit code for a dealer that has no account |
| A named response owner, with hours, for each response class | ISZE commercial owner | The product's whole value, and any commitment of money behind it | Five names against five classes, and an agreed time to substantive answer |
| The classification release to treat as the authority | ISZE classification owner | Every family label printed outside ISZE | A decision naming one file, its version and its coverage |
| The recurring monthly file, its cadence and its owning role | The distributor, with the ISZE commercial owner | The second cycle. A single year proves a file was sent once, not that it will recur | Confirmation of format, cadence and owning role, with no new system |
| The currency of the workshop book | The distributor's parts function | Every monetary figure beside workshop work | One word |
| The approved replacement schedule, including the time leg and the quantity consumed per replacement | The manufacturer's parts and technical function, or the distributor's service documentation | The quantity-per-replacement choice that dominates the sensitivity of the demand comparison, at roughly ±100% | One table, plus a confirmation that it is the approved schedule for this market |
| What the part replacement table is, and whether it is current | The distributor or the manufacturer | Any part-number trend run through it | A written note naming its source system, its date and its scope |
| What the contract-type codes mean, and what the external service system name refers to | The distributor | Correct separation of scheduled work from warranty work, and the right to name the source at all | A written note, not a file |
| The dealer-to-site relationship rules | ISZE, with the distributor | Any dealer view, and any site-level statement | An approved rule for how a dealer, an account and a site are related |
| Access, audience and the host | ISZE workspace owner and the designated information owner | Anything that leaves ISZE | A named host and a written sharing rule |
| The two documents for which no local copy is available | The owner of the source conversation | The final status of the commercial chapter, which is provisional until they are supplied | The copies themselves. This is a request for a document, not for an approval |

**Five conditions are not data gaps and cannot be closed by analysis.** They are: an approved link
between a dealer and the standards round; a permitted-sharing decision covering what an internal
distributor note may contain and what ISZE may see; a host and an access design; a named owner at the
distributor for the monthly refresh; and a decision on the open business defaults recorded in the
appendix. These are conditions, and no amount of analysis removes them.

**The two-column ask, stated as it can be sent.** The first row of the table above is the smallest request
in this paper and it closes the largest gap, so it is worth writing out.

> Please send the dealer name and the account number you bill that dealer under, one row per dealer, for
> the 64 dealers in the calendar 2025 sales-to-dealer file. If a dealer has no account, mark it
> UNRESOLVED rather than leaving it blank. If one dealer trades under several names, or one account
> covers several names, add a third column saying so. Send it as a spreadsheet with the two columns as
> text, so the account numbers keep their leading digits.

**The test the sender runs before sending.** Each of the 64 names appears exactly once, and each account
number appears exactly once. If either count differs from the count of distinct values, the list is not
one-to-one and comes back as groups rather than being forced into pairs. The sender states how many of the
64 are covered. Where there is no account, the row reads UNRESOLVED — never blank, and never filled by
matching a similar name, because a plausible-looking guess is worse than an admitted gap and would carry
silently into every figure that uses it. And the distributor's own three purchasing accounts must not
appear mapped to a dealer site: if one of them turns up beside a dealer name, the mapping is pointing in
the wrong direction and the list comes back.

**What the ask must not contain, and why.** Not prices, not margins, not stock, not customer names, not
fleet or customer data, not VIN, not workshop repair orders, not competitor invoices, and not a full
price list. Bundling any of those into this request makes it read as ISZE trying to see through the
distributor rather than fill a gap in its own records, and once that impression forms it is hard to undo.
A request one person can answer in an hour teaches the opposite lesson.

**What it unlocks, stated honestly.** It fully unlocks one thing: the comparison of what was fitted
against what was bought for the one dealer, which is blocked today. Five other services receive partial
help, in the sense that a dealer name tied to an account makes a page possible without a collision. Two
receive no help at all: there is still no per-dealer fleet anywhere, so no per-dealer rate can be computed
from it, and there is still only one dealer-level year, so no trend is possible. And it resolves identity
rather than billing.

## G2. The money, stated honestly

**The commitment under discussion is a cap, not a return. No euro return is evidenced anywhere in the
material behind this paper.** This section states that position in full, because the alternative is a
number nobody can defend.

**Why a return cannot be calculated yet.** A return calculation needs two measurements on the same basis —
one before and one after. The benefit of Universe is redeemed when a question is answered and somebody
acts differently as a result. **Nobody has measured how many questions are asked today, how long they
take to answer, or how often the answer changes anything.** Until that starting measurement exists, a
return figure would be an invention, and the honest form for the commitment is a ceiling on deliverables
rather than a claim on a gain.

**Two comparables exist, and neither supports the number.** The first is a modest distributor support
incentive, one distributor, one year, paid as a rebate against a support programme. It shows that ISZE
does commit support money to a distributor. It does not show what a new product is worth, because a
rebate records that money moved rather than what the money bought. The second is the price revision for
the coming fiscal year, which produces a larger annual figure on a locked basis. **That is a decision about
the price list, taken on the same part numbers, and it must never be presented as a return from Universe.
It is money collected by charging more for the same parts, which is a different question from whether a
new service earns its keep.**

**What a contract can observe, and therefore what can be guaranteed.** Named deliverables existing by
named dates at stated locations. A named accountable individual for each service and each case — not a
team name, and one person who cannot hand ownership to another function. A substantive answer within an
agreed class and an agreed time. The monthly file with its four minimum fields and a coverage
declaration. A named pilot market with a named distributor owner. Data accuracy and coverage thresholds:
stable identifiers, reversible corrections and no silent overwrite. And the completion of defined
milestones, each evidenced rather than reported.

**What a contract cannot observe.** Incremental profit. That a quotation that was won would otherwise
have been lost. What a dealer sold onward. Freedom from displacement between dealers, because moving the
same business to a different month is not new annual business. Market growth. And a chain of cause
running from a documented decision to a measured result. Each of these has the same reason: every one of
them requires knowing what would have happened instead, and no measurement of an alternative that did not
occur exists anywhere. **The honest guarantee is the decision record, not the cause.**

**The recommended instrument.** A staged release against milestone checks, with the final stage held back
until the recurring exchange has actually repeated once and its corrections have been handled, and with
recovery or offset of any release that fails to evidence itself inside its cycle.

The reason for holding the last stage rather than the first is that the paper's own test of success is
repetition: repeated use for eligible work, and a participant that would continue if the reporting
incentive disappeared. Repetition only appears after the first cycle, so the release schedule has to leave
something behind to pay for it. A release linked to key performance numbers is the weakest option of all,
because it needs a starting measurement and a target, the starting measurement has not been taken, and
this paper refuses to set targets it cannot earn. Such a release would be negotiated against numbers
neither side could defend.

**The running cost, offered as an estimate and labelled as one.** Once two or three markets are live, a
fractional internal function covering two to four case types at a realistic monthly case volume implies a
small number of full-time equivalents, plus distributor-side owner time, plus product maintenance. At an
indicative fully loaded cost per person per year, that is a recurring annual cost of the same order as
the amount being asked for — and it recurs every year, while the cap does not. **The case volume is
inferred from the shape of the service rather than measured, so the range is a reasoning aid and not a
quotation, and it is not added to the cap.** Its purpose here is only to make one point clear: the cap
buys the first step, and the steps that follow have a running cost that is already the size of the
request.

## G3. The next milestone

Not the largest possible dashboard.

**The next milestone is a complete, trusted decision path**: one review that can be reproduced, explained
to the person it is for, corrected through the submission process, and followed into an action somebody
owns — together with an honest statement of everything it could not tell the reader.

---

# Appendix A — Definitions

**Organisations and entities**

- **ISZE** — the parts and aftersales organisation that sells to distributors.
- **IML** — Isuzu Motors Limited, the manufacturer. Holds the part-number catalogue and the service
  schedules.
- **ITUK** — Isuzu Truck (UK) Limited, the distributor of the larger vehicles in the United Kingdom, and
  the dealer-level pilot market. **Not the same organisation as IUK.**
- **IUK** — the distributor of the lighter vehicles in the United Kingdom. A separate entity with
  separate files, and never blended with ITUK.
- **UMI / UTI** — the two distributors in Israel, with separate systems and separate databases. The
  Israel dealer-standards pack belongs to one of them; the other did not take part in that round. They
  are never averaged or presented as one figure.
- **DB** — distributor, when describing the business view. An abbreviation, not a category.
- **ODS / DLR** — distributor / dealer, as used in identifiers and report names.

**Pillars, products and modules**

- **Universe** — the connected aftersales review this paper specifies.
- **AIM — Aftermarket Intelligence Model.** Holds the parts classification and the genuine against
  value-tier view. Answers: what was sold, in which family, at which tier?
- **IDS — Isuzu Dealer Standards.** The dealer self-assessment. Answers: what did the dealer record about
  itself, and what did we agree to do about it?
- **PRISM** — the analytics codebase that produces the validated commercial calculations. Answers: is the
  commercial evidence strong enough to act on?
- **SPA — Special Price Agreement.** Agreed price support on named parts for a distributor or a fleet.
- **BVP / value tier** — the lower-cost counter-priced version of a part, sold alongside the genuine one.
- **DLOD — "Don't Lose the Deal".** The pilot distributor's programme for competitive quotations.
- **Kaizen** — continuous improvement; the action-and-follow-through side of the standards work.

**Measures and business lenses**

- **GPS** — the broad genuine-parts opportunity, as a modelled commercial measure of parts billed per
  vehicle in service. A model output, not a measurement.
- **PMS** — the parts, maintenance and service view: what should have been consumed against what was.
  A model over observed sales.
- **UIO — units in operation.** Vehicles in service.
- **GP — gross profit**, in currency. **GM — gross margin**, as a percentage.
- **CY / FY — calendar year / fiscal year.** Two different reporting clocks, never mixed.
- **Recorded quantity** — what moved in the named source, on that source's own unit basis.
- **Actual billing** — the monetary records of the named billing flow, with its currency stated.
- **Reference valuation** — a quantity valued at a stated price list. Not actual billing, not revenue,
  not margin.
- **Modelled demand, or modelled target spend** — an estimate built on explicit assumptions about
  vehicles in service, interval, applicability and value. Not observed servicing.
- **Floor** — a lower bound. **A count or an observed monetary total with a coverage limit is a floor; a
  rate or an expectation is not.**

**Sales, purchasing and identity**

- **Sales to dealer** — what the distributor sold to its dealers. Wholesale. **Not** what a dealer sold to
  a customer.
- **Sell-through** — the share of what ISZE billed that moved onward to dealers. Not computable today,
  because the dealer-to-account link does not exist.
- **The four layers** — one, ISZE billed to the distributor; two, the distributor's sales to dealers;
  three, parts recorded in workshop jobs; four, the dealer's sales to the end customer, for which no
  source exists.
- **Sold-to account** — the billing account an invoice is addressed to. The distributor's account.
- **Payer code** — the account that pays, which can differ from the sold-to account.
- **Normalised name** — a company name with punctuation, legal suffixes and site brackets removed. A
  match on normalised names is evidence to review, not an approval of identity.
- **Crosswalk, or account map** — a list mapping one system's identifiers to another's. The missing one
  here maps a dealer name to the account number it is billed under.
- **Cardinality** — how many records on each side match. A parent-level name match is one-to-many, which
  is why it is not used for a per-dealer page.
- **Amplification** — a join multiplying rows. Every join is checked for it.
- **SaTy** — the order urgency classification on a billing line: stock order, vehicle off road, rush,
  production, credit, debit.

**Parts**

- **Part number** — the standard form is ten digits. Shorter alphanumeric codes are lubricants, batteries
  and accessories rather than service parts, although the reverse is not reliably true.
- **Family** — a group of part numbers doing the same job.
- **Population** — the explicit set of part numbers a given measure is computed on. **One population per
  calculation, printed beside the figure.**
- **Consumable element** — a part that is itself consumed in a service, as opposed to a housing, cap,
  bolt, gasket or assembly-level item.
- **Supersession** — one part number replaced by another.
- **Applicability** — whether a part actually fits, and is approved for, a given vehicle. **Separate from
  a catalogue pairing and separate from a supersession relationship.**
- **Fitment approval, or homologation** — official confirmation that a part is approved for a specific
  vehicle. **Nothing we hold is one.**
- **Classification release** — a dated, versioned file of part-to-family assignments. More than one
  exists and no authority is declared between them.
- **Axis** — which tree in the classification a label was read from. The catalogue axis and the workbook
  axis disagree for many parts, and the axis must be named.

**Vehicles and servicing**

- **VIN** — the seventeen-character vehicle identifier. The only safe vehicle key in this data.
- **Registration plate** — not a key. One plate in the workshop data maps to more than two thousand
  vehicles.
- **Odometer reading** — the distance reading taken at a workshop visit. Stored in kilometres, which is
  inferred rather than declared.
- **Annual distance** — kilometres per year derived from odometer readings over elapsed time. Never read
  from a column labelled as an annual mileage.
- **Replacement interval** — the distance between one completed replacement and the next, on one vehicle,
  for one part number. **A measurement of what happened, not a requirement.**
- **Documented interval** — what the manufacturer's service schedule requires. **The requirement, and the
  only input that can judge consumption without circularity.**
- **Distance and time, whichever comes first** — the requirement has two legs. A comparison against the
  distance leg alone understates it.
- **Jobsheet** — one visit to one vehicle.
- **Advice line** — work advised but not done. Not a job.
- **Survivor bias** — the sample consists of vehicles still appearing in the records, which skews towards
  hard-worked vehicles.
- **Odometer reset** — a reading that goes backwards.
- **Potential duplicate** — a row identical to another on its substantive fields. **Identical rows are
  potential duplicates only.** They are reported both ways with the difference visible, and a copy is
  never deleted.

**Geography**

- **Footprint** — where vehicles were seen being serviced. **An observation, not a territory.** It has no
  boundary and cannot give a dealer a fleet.
- **Catchment** — the area a dealer's observed vehicles came from, measured, and only for a subset.
- **Territory** — an assigned area of responsibility. **None exists in our records.**
- **Depot** — the operating site a vehicle was booked from. A real field, and not the same as a postcode.

**Governance and status**

- **Product owner / data owner / metric owner / commercial owner / technical owner** — the five
  accountability roles defined in Part F5. Each needs a person's name, not a team's.
- **Release index** — the one stable record naming an accepted release and everything in it.
- **The six status words** — verified; corrected; contradicted; unsupported; not tested; no local copy
  available. Defined in the front matter, and no other status exists.

---

# Appendix B — The figures this paper may quote, and the wording that travels with them

Only the figures below may appear as business numbers, and each carries its stated wording. A sentence
that needs a figure not on this list describes the position in words instead, or states that the number is
not available.

| Figure | Wording, and what must travel with it |
|---|---|
| Parts base | €117.6m of parts billed across 22 distributors, 2023-01-03 to 2026-08-31; the United Kingdom lane ends 2026-06-30. The earlier cut of about €112.1m is the same series at an earlier cut-off, not a different number. |
| Modelled target-spend ceiling | €55.3m, of which eight markets sit on a flat €250-per-truck placeholder holding 40.3%. State with it that this is a modelled ceiling and not a revenue forecast, and that a recovery percentage must not be applied to it to invent a revenue case. |
| Per-truck spend, pilot market | ITUK spent €248.54 per truck in 2025 against a reference ceiling of €11,835,911 on 22,389 trucks — 47.0% on the upper-reference basis. Name the denominator wherever the percentage appears. |
| Uncaptured service-demand value, pilot market | €2.11m in 2025, on a 50.85% capture rate measured against the vehicle-narrowed denominator. Say 50.85%, and say the denominator is a bucket sum rather than a count of vehicles. |
| Any capture rate above 100% | Not plottable at face value. A rate above 100% means the denominator is too low for that category, not that more than all demand was captured. Name the categories and the reason, or leave them off the chart. |
| Dealer names and units, pilot market | 64 named dealers took 223,897 units in calendar 2025, month rows only. The annual control row is a cross-check and is never added to the monthly rows. |
| Dealer self-assessment records | 519 dealer self-assessment records across 19 country lists, one round, no per-dealer date; 514 distinct names. |
| Vehicles in the workshop extract | State the extract's period with the count, and state that it is a floor: a vehicle serviced elsewhere, or not serviced at all, is not in it. |
| Vehicles with work in calendar 2025 | 2,402, of which 2,182 carry at least one part line. Never the superseded figure. |
| Multi-workshop servicing | 1,930 of 3,467 vehicles, 55.7%, were serviced at more than one workshop. Print it wherever a per-workshop count appears, because it is why such a count understates a fleet. |
| Worked dealer case, activity | 72 trucks, 70 of them on part lines, 269 jobs and 1,627 lines in the year. State the coverage limit with it: vehicles seen in the contract workshop book, so every count here is a floor. |
| Worked dealer case, parts value | 27,543.79, printed as **the workbook's own money unit, with no currency declared**. Never euro, never revenue, never cost, never margin. Sterling is a working assumption and not a finding. |
| Fitted units | 147 on the named part numbers; 148 on the consumable family. Print the population with the figure; neither is presented as the other. |
| Bought units | 719 on the named numbers; 836 on the consumable family; 852 across the family the book consumes. One population per figure, printed with it. |
| Fitted against bought | Blocked. No dealer-to-account key exists. Print it as separately labelled context and state that it must not be interpreted: different populations, different channels, and the difference between them is not a gap, a leak or a shortfall. |
| Measured replacement interval | Print a band with the number of observations beside it, never a single number. State that a measured interval is a record of what happened, not a requirement. |
| Annual distance, pilot market | 47,923 km/yr for one model group, derived from odometer readings over elapsed time, and a lower bound because most of those vehicles carry at least one odometer reset. The available annual-distance estimates are means over different populations and are never averaged. |
| Documented service interval | 40,000 km or 12 months for the larger model; 20,000 km or 12 months for the smaller one. State that the requirement is distance **or** time, whichever comes first, and that a comparison against the distance leg alone understates it. State that the market applicability of the manufacturer's schedule sheet is not established from the material held. |
| Expected units | Two separate scenarios, never averaged and never reduced to a single figure, each with the interval and its source named. On the narrowest population basis the defensible spread across estimators is 249 to 425, a 70% band, and the quantity consumed per replacement dominates the sensitivity at roughly ±100%. **Draw no servicing conclusion in either direction.** |
| Brakes | No expected demand. There is no published replacement interval for the pad. State that the expectation is not built and that the reason is the schedule, not the data. |
| Market reference | €248.54 of goods billed per truck in 2025, with the vehicle count and its basis printed beside it. A market reference, not a dealer fleet, and never allocated across dealers in any form. |

**Figures that may not be published anywhere in this paper.** The superseded capture percentage that
predates the split; any all-models mileage pair presented as a nested comparison; any capture rate above
100% plotted at face value; any sales-to-dealer coverage share that cannot be re-derived from a cited
source; the coverage denominator that matches no total in any file; the superseded fleet count; the
earlier mixed fitted-against-bought comparison; the superseded classification-movement figure in part
numbers and euro; the unsupported competitive-flag figure; any statement that a pipeline check is
currently failing; any figure whose definition or population is not stated in this paper itself; any
statement that the two sales files agree cleanly; any statement that an identity match is evidence that
goods moved; any claim that a name match proves two entities are the same legal person; any dealer-level
figure for a market or year without dealer names; any per-dealer rate or per-dealer fleet figure; any
market-share statement and any statement about what a dealer sold onward; any single number for expected
demand; any servicing conclusion in either direction; any euro label on a workshop line; any family label
printed outside ISZE while no classification release is pinned; any substitution recommendation where
application has not been validated; any statement that no value-tier brake pairing exists anywhere; any
figure from the superseded return; any statement that a named document does not exist; any promise of a
monetary return from the commitment under discussion; and any cost estimate presented as a quotation
rather than as a labelled estimate.

---

# Appendix C — The decision trail

**Decisions already settled, not reopened by this paper.**

| Decision | What it settles |
|---|---|
| The three pillars | AIM, IDS and PRISM, with tender support as a possible extension and not as an approved fourth pillar |
| The pilot markets | A national pilot and a separate dealer-level pilot, with the dealer-level path in the market that holds dealer-named data |
| The audience sequence | The distributor review first; dealer and workshop data as a triggered second phase |
| Odometer readings from warranty | Not used as a fleet or service-population source |
| Charging for data access | Explicitly out. The model earns through actions, not by charging for access to data |
| Dealer league tables and compliance scores | Not to be built |
| The currency of the workshop book | Not euro. No currency is declared in the file; sterling is a working assumption and not a finding |
| The two sales files | Not to be added, averaged, or reconciled by assumption |
| A national fleet divided across dealers | Forbidden in any form, including as a rate or a per-truck benchmark |
| The aggregate sales view | Removed, not deferred for reintroduction |
| Product photography | Deferred |
| The portfolio and genuine/value-tier comparison | Retained |

**Questions already answered, and not to be asked again.** Whether the two large oil filters are a
supersession pair — no, they are separate applications. Whether the two air filters are a pair — no.
Whether the two brake pads are a pair — no. Whether a per-dealer fleet or territory figure exists at the
pilot distributor — answered by absence, and asking again invites an allocation this design forbids.
Whether the general data-integrity check covers the claims in this paper — no, the claim register is the
authority for them. Whether a claim about a dealer's own retail sales is available — no source exists at
any level, and asking invites an invention.

**Questions that were listed as blocking and are not.** Territory mapping; a separate feed from the
maintenance system; recurring backorders; full tender coverage; and a complete brake comparison. None of
these is a prerequisite for the first historical review.

**Open decisions** are listed in Part G1, each with its owner, what it blocks and the smallest response
that would close it.

**One document known to exist and not held.** The revised commercial model and the feedback disposition
from the same discussion are named in the material behind this paper and **no local copy of either was
available**. The words "no local copy was available" are deliberate and are not the same statement as
"the document does not exist" — a search establishes the absence of a copy, not the absence of the
document. The commercial chapter of this paper is provisional until those copies are supplied.

---

# Appendix D — Where the evidence lives

For a reader who wants to check a figure.

**The consolidated evidence return**, which carries the adjudicated position on every disputed figure and
its machine-readable backing:

```
Isuzu Universe\_STRATEGY\_ORCHESTRATION\CONSOLIDATED_ITUK_2026-09-21_01\
  CURSOR_UNIVERSE_ITUK_CONSOLIDATED_RETURN.md
  evidence\  MERGED_CLAIM_TABLE.csv, METRIC_TABLE.csv, SOURCE_MANIFEST.csv, REHASH_PROOF.md
```

**The one-folder map of the whole subject**, twenty files, one topic each: the verified position, the
disputed claims, the corrections, the source manifest and horizons, the worked dealer case, the demand
and schedule work, the mileage and interval work, identity and the standards position, part numbers and
supersession, the sales-file reconciliation, the corrected dealer-page specification, the data-quality
traps, the commercial and participation model, the standards and atlas position, the strategy and
roadmap, the open questions by recipient, what may be implemented next, the independence and verification
log, and the glossary:

```
Isuzu Universe\_MERGED_MASTER_2026-09-21\
```

**The worked dealer case**, with its own re-derivation evidence beside it:

```
Isuzu Universe\_STRATEGY\_ORCHESTRATION\ITUK_CASE_2026-09-21_01\
```

**The commercial and guarantee papers:**

```
Isuzu Universe\01_Strategy\
```

**The data**, read-only and cited rather than copied: the workshop workbook, the sales-to-dealer files and
derived tables under the data folder, the part-classification files, the manufacturer's service-schedule
documents, the dealer-standards workbook and network file, and the tender feed.

**A note on the horizon.** The sources behind this paper end on different dates — the billing, the
workshop extract, the vehicle list, the sales-to-dealer files and the price observations all stop at
different points, and the self-assessment round carries no date at all. **There is no single reporting
date behind this paper, and any sentence that implies one is wrong.** Each figure is quoted with the clock
it was measured on.

---

*End of the Yellow Paper.*
