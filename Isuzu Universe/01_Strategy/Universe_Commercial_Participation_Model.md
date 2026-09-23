# Universe Commercial Participation Model

## Core proposition

The commercial model should be a **two-sided value exchange**: the
existing distributor kickback gets the minimum data flowing, but
Universe earns deeper participation by returning analyses and commercial
support that distributors and dealers can actually use.

> **ISZE asks for the minimum information needed to understand how parts
> move through the authorised network. In return, Universe converts that
> information into commercial actions, comparisons and support that the
> distributor could not produce from its own data alone.**

The kickback is the ignition mechanism, not the end-state.

------------------------------------------------------------------------

## Minimum sales-to-dealer data standard

The mandatory requirement should remain deliberately narrow and
**price-free**. It should describe *what part moved, to which authorised
dealer, when and in what quantity*. It should not attempt to recreate
the distributor's ERP.

  -----------------------------------------------------------------------
  Requirement                         Minimum standard
  ----------------------------------- -----------------------------------
  Distributor                         Stable ISZE distributor identifier

  Dealer                              Stable dealer identifier agreed
                                      between distributor and ISZE

  Dealer site                         Separate stable site identifier
                                      where a dealer has multiple
                                      physical locations

  Part                                Isuzu part number as transacted

  Quantity                            Units supplied, including negative
                                      quantities where
                                      corrections/returns are supplied

  Date                                Transaction date; daily preferred,
                                      monthly period sufficient for
                                      reporting

  Transaction type                    Sale, return, credit/correction
                                      where available

  Record identifier                   Stable transaction/line identifier
                                      so corrections can be reconciled

  Reporting period                    Explicit calendar month/year

  File version                        Submission version and creation
                                      date

  Coverage declaration                What dealer population, channels
                                      and transaction types are
                                      included/excluded
  -----------------------------------------------------------------------

### Frequency

Monthly. A sensible operating standard is submission within ten working
days after month-end. Universe should analyse monthly movement; it does
not need a real-time feed to deliver most of the commercial value.

### Stable identifiers

Stable identifiers matter more than extra fields. A dealer should not
appear as "Smith Trucks", "Smith Truck Centre" and "Dealer 142" in three
successive submissions. The distributor maintains the dealer identity;
Universe maintains the cross-period mapping. Closed, renamed and
transferred dealerships retain their historical identifier.

### Declared coverage

Coverage must be declared, not guessed. Every submission should carry a
small control record containing:

-   number of active dealer sites represented;
-   known excluded dealers or channels;
-   first and last transaction date;
-   whether returns/credits are included;
-   whether the file covers the complete Isuzu parts range or only part
    of it;
-   any system or organisational change that affects comparison with
    earlier periods.

This prevents one of the most dangerous Universe behaviours:
interpreting missing data as missing business. Absence of dealer-level
information is a source gap, not evidence of weak sales.

### Corrections

Corrections should be reversible and visible. A distributor should be
able to resubmit a period. Universe retains the original, marks the
newer version as the active version and shows which results changed.
There should be no silent overwriting of history.

------------------------------------------------------------------------

## What the distributor receives back

Universe must return considerably more than a dashboard containing the
distributor's own numbers.

### Purchasing-pattern explanation

For every dealer, Universe should explain **what changed and what drove
it**.

Not:

> Dealer 172 is down 14%.

But:

> Dealer 172 purchased fewer brake and clutch parts during the period,
> while filter activity remained broadly consistent with its previous
> pattern. The change is concentrated in N-Series applications rather
> than across the complete range.

Where the evidence does not support an explanation, Universe says so.

The distributor should be able to move from:

**market → dealer → AIM family → part → historical purchasing pattern**

without losing the selected period or context.

### AIM --- Aftermarket Intelligence Model analysis

Universe combines the distributor's sales-to-dealer information with
AIM's classification of the parts range.

That gives the distributor a commercial view unavailable from raw ERP
exports:

-   service and maintenance families;
-   wear and repair families;
-   Genuine/BVP positioning;
-   vehicle/application relevance where validated;
-   regular versus intermittent purchasing;
-   dealers with materially different family patterns;
-   parts or families where purchasing has disappeared or changed.

A missing purchase should never automatically become an "opportunity".
Universe first distinguishes **observed purchasing behaviour** from an
inferred commercial opportunity.

### Genuine versus BVP

The distributor should see where the network is using Genuine parts,
BVP, both, or neither in applicable categories.

The useful discussion becomes:

> This dealer buys the Genuine brake range regularly but has almost no
> BVP activity in categories where BVP is available.

rather than:

> BVP penetration is 8%.

Universe should then allow the distributor to investigate applicability,
commercial positioning or local competition before somebody labels the
gap an opportunity.

### Competitor-market evidence

ISZE can add information that individual distributors cannot easily
assemble themselves:

-   documented competitor pricing;
-   independent aftermarket alternatives;
-   product availability;
-   tender evidence;
-   market observations;
-   relevant price comparisons.

These should always carry source and date. A competitor price observed
in another country should be presented as **market evidence**, not as
proof of the local dealer's competitive situation.

This is one of the strongest reasons for a distributor to participate:
it receives information from outside its own four walls.

### Dealer-network comparison

Universe can show a dealer how its purchasing pattern differs from
**comparable peers**, without turning this into a simplistic league
table.

For example:

> Dealers with a similar commercial-vehicle profile generally purchase
> five periodic-maintenance families. This dealer currently purchases
> three.

This is preferable to:

> Dealer rank: 37/48.

Comparison groups should be explainable and sufficiently large to
protect confidentiality.

### Relevant PRISM fleet context

Where the fleet evidence is robust enough, Universe can put the dealer
or distributor's parts activity beside the relevant trucks in service.

The useful question becomes:

> Does the purchasing pattern appear broadly consistent with the vehicle
> population we know exists in this market?

not:

> These 2,000 trucks should have generated EUR X and therefore the
> dealer lost EUR Y.

Measured activity and modelled expectation remain separate.

### IDS follow-up

Isuzu Dealer Standards (IDS) is a **dealer self-assessment**, not an
ISZE audit.

Universe should connect the dealer's declared IDS priorities with
relevant commercial evidence.

For example:

**Dealer says:** BVP awareness should improve.\
**Universe shows:** which applicable BVP families the dealer currently
purchases and where Genuine/BVP comparisons could support that
discussion.

Or:

**Dealer says:** parts availability is an issue.\
**Universe shows:** unusual purchasing interruptions or relevant family
patterns, but does not pretend sales-to-dealer data proves dealer stock
availability.

IDS therefore becomes a follow-up mechanism rather than another score
layered onto the dealer.

### Tender opportunities

Where public tender evidence is relevant to the distributor's vehicle
population or parts activity, Universe can surface it directly.

It should answer:

-   What is the opportunity?
-   Which fleet or vehicle family appears relevant?
-   Which parts families may matter?
-   What action is required, and by when?

The distributor gets something commercially actionable in exchange for
contributing data.

### Better-supported SPA and commercial-support requests

A distributor asking ISZE for a Special Price Agreement (SPA) can
support the request with evidence from Universe:

-   dealer or fleet involved;
-   relevant part family;
-   historical purchasing;
-   competitive evidence;
-   expected incremental volume;
-   Genuine/BVP alternative where relevant;
-   documented tender or customer context.

Instead of:

> We need a better price on these parts.

the case becomes:

> This request concerns this identifiable competitive situation, this
> existing business and this incremental opportunity.

That helps both sides.

------------------------------------------------------------------------

## What remains outside the mandatory requirement

The minimum standard should **not expand simply because Universe
technically could consume more data**.

  Data                                  Position
  ------------------------------------- ---------------
  Distributor selling price to dealer   Not mandatory
  Dealer selling price to customer      Not mandatory
  Distributor margin                    Not required
  Dealer margin                         Not required
  Distributor stock                     Not required
  Dealer stock                          Not required
  Customer names                        Not required
  Fleet/customer account data           Not required
  VIN                                   Not required
  Workshop repair orders                Not required
  Technician information                Not required
  Customer invoices                     Not required
  Customer personal data                Not required
  Competitor invoices                   Not required

This boundary is strategically important.

If Universe begins by requesting the distributor's prices, margin,
stock, customers, vehicles and workshop activity, it will feel like
**ISZE trying to see through the distributor**, rather than ISZE helping
the distributor manage the authorised network.

------------------------------------------------------------------------

## Additional data should be earned, not demanded

The next layer should work differently:

**First show the limitation. Then show the additional value. Then ask
whether the distributor wants to participate.**

  --------------------------------------------------------------------------------
  Optional contribution   Universe demonstrates   Distributor gets back
                          first                   
  ----------------------- ----------------------- --------------------------------
  Dealer stock            "We can see purchasing  Slow/fast movement review,
                          interruptions but       stock-range discussions,
                          cannot distinguish      potential availability
                          stock availability from exceptions
                          demand."                

  Retail-price samples    ISZE provides existing  Local price-position comparison
                          competitor/reference    and better SPA evidence
                          evidence first          

  Workshop activity       Universe first shows    Comparison between service
                          the expected service    activity and parts purchasing
                          families                

  VIN/fleet information   Universe shows existing Better local fleet/application
                          market-level PRISM      relevance
                          context first           

  Tender/customer context Universe identifies     Tender-specific range and
                          relevant public tenders pricing support
                          first                   

  Lost-sale reason codes  Universe first          Competitor/availability/reason
                          identifies families     analysis instead of inferred
                          where purchasing has    explanations
                          changed                 
  --------------------------------------------------------------------------------

The transaction becomes:

> **"Give us this additional evidence and we can answer this specific
> question for you."**

not:

> **"Universe needs more data."**

A distributor should be able to run a small pilot with one dealer group
or one data field, see the result and decide whether the exchange is
worthwhile.

That is how the data relationship matures voluntarily.

------------------------------------------------------------------------

## Preventing Universe from feeling like ISZE surveillance

This needs to be designed into the product rather than added later as a
disclaimer.

### Every finding has provenance

A user should be able to see whether something comes from:

-   distributor-provided data;
-   ISZE parts billed;
-   AIM classification;
-   PRISM fleet evidence;
-   IDS dealer self-assessment;
-   public tender information;
-   competitor evidence;
-   a modelled expectation.

These must not visually collapse into one apparent "truth".

### Challenge and correction rights

Every material finding should have something equivalent to:

**Add context / challenge / correct**

Examples:

-   Fleet contract moved between dealers.
-   Dealer temporarily closed.
-   Customer performs maintenance internally.
-   New branch opened in April.
-   Data extraction excluded credits.
-   BVP range not applicable to this fleet.

That context becomes part of the commercial record.

Universe therefore says:

> **"This is what the evidence currently indicates."**

rather than:

> **"ISZE has determined that this dealer is underperforming."**

### No misleading dealer rankings

Universal dealer rankings should generally be avoided.

Dealer A and Dealer B may have different fleets, territories, customer
profiles, ages, workshop capabilities and data coverage.

Use comparisons such as:

-   your history;
-   comparable dealer group;
-   country pattern;
-   relevant vehicle population;
-   specific AIM family.

Rank only where the underlying metric genuinely supports ranking.

### Distributor-controlled interpretation

ISZE can supply evidence and analysis, but the national distributor
remains closest to its network.

Universe should therefore allow the distributor to classify a finding:

-   **Investigate**
-   **Explained**
-   **Opportunity**
-   **No action**
-   **Data issue**

and attach its explanation.

That transforms the platform from HQ judgement into a shared commercial
workspace.

### Confidentiality between distributors

One distributor should never be able to reconstruct another
distributor's commercial information.

Cross-market comparisons should therefore use:

-   anonymised peers;
-   aggregated benchmarks;
-   published competitor evidence;
-   sufficiently large comparison groups.

No dealer-level commercial data should cross distributor boundaries.

### Dealer agency

A dealer should be able to see the evidence being used in a discussion
about that dealer.

Where appropriate, it should be possible for the distributor to invite
the dealer to:

-   review its own purchasing pattern;
-   see the relevant comparisons;
-   add an explanation;
-   acknowledge an action;
-   connect an IDS follow-up;
-   identify a commercial opportunity.

The dealer should not merely become a coloured dot on a map controlled
by ISZE.

------------------------------------------------------------------------

## Distributor proposition

> **Share a simple monthly, price-free record of which Isuzu parts move
> to which authorised dealers. Universe combines it with ISZE's parts
> knowledge, vehicle context, competitor evidence, dealer
> self-assessments and tender information to explain purchasing patterns
> and identify commercial actions.**
>
> **You receive dealer and parts-family analysis, Genuine/BVP
> comparisons, relevant peer benchmarks, fleet context, tender leads and
> stronger evidence for pricing and commercial-support discussions. You
> retain the right to correct the data, explain local circumstances and
> decide which findings should become actions. Your commercially
> sensitive prices, margins, customer data, VINs and stock remain
> outside the minimum requirement.**

This is considerably stronger than "provide a file to receive 20% of the
kickback."

------------------------------------------------------------------------

## Dealer proposition

The dealer proposition has to be different because the dealer receives
no kickback from ISZE.

> **Universe should help your distributor and Isuzu support your
> business with evidence relevant to your own dealership. It shows how
> your parts purchasing is developing, which product families you use,
> where Genuine and BVP alternatives are relevant, what vehicle
> population may sit behind the demand, and which IDS follow-ups or
> commercial opportunities deserve attention.**
>
> **It is not an ISZE dealer audit or league table. You can see the
> evidence behind a discussion, correct incorrect information, add local
> context and participate in deciding the action.**

For the dealer, the value is **better commercial support and fewer
generic HQ conversations**, not "giving ISZE more data."

------------------------------------------------------------------------

## Participation model

### Core participation --- kickback-linked

Price-free monthly sales-to-dealer data meeting the minimum standard.

**Return:** complete core Universe analysis.

### Collaborative participation --- voluntary

Selected additional data provided because the distributor wants a
specific additional analysis.

Examples include stock for an availability study, retail-price samples
for a competitiveness study, or local vehicle information for more
precise fleet analysis.

**Return:** clearly defined additional output.

### Strategic participation

Universe becomes part of the distributor's normal commercial process:

-   network reviews;
-   IDS follow-up;
-   tender preparation;
-   BVP positioning;
-   SPA requests.

At this point the incentive becomes almost irrelevant.

------------------------------------------------------------------------

## Long-term success condition

The real test is **not whether distributors submit the file while 20% of
an incentive depends on it**.

Success is reached when the counterfactual becomes credible:

> **If the sales-to-dealer requirement disappeared from the kickback
> tomorrow, distributors would continue supplying the data because
> withdrawing it would make their own Universe output materially
> worse.**

Measure this through behaviour rather than survey scores:

-   distributors correct and improve files voluntarily rather than
    merely sending minimum-compliance extracts;
-   optional fields begin to be shared for defined business cases;
-   distributors use Universe evidence in their own dealer reviews;
-   dealers contribute explanations and actions;
-   SPA requests arrive with Universe evidence attached;
-   tender opportunities move from Universe into distributor action;
-   IDS follow-ups use commercial evidence from Universe;
-   distributors ask ISZE to add missing data or analyses because they
    want a better answer;
-   data arrives reliably even when nobody reminds them about the
    kickback.

The strongest single signal would be **voluntary data enrichment**. A
distributor giving ISZE something that was explicitly *not required*
because the previous exchange produced value is evidence that Universe
has crossed from compliance tool to commercial infrastructure.

The model is therefore not:

**20% incentive → data**

It should evolve into:

**minimum data → useful answer → trusted action → demonstrated value →
voluntary richer data → better answer**

That feedback loop should be one of the central design principles of
Universe.
