# The Universe Yellow Paper

### From parts data to a decision somebody owns

**Version 0.5 · 22 September 2026 · internal · proposed**

---

## How to read this

This edition is a rebuild, not a revision. It replaces v0.2 for every purpose except the evidence rules, which it keeps almost intact. The reason is in the review of v0.2 that sits beside it: v0.2 was a careful rulebook that could not show a single decision, and it claimed the material behind one did not exist when it did.

Three things changed.

It carries a real case, worked from source, with the parts named and the numbers reproducible. It states what surfaces an opportunity, ranks it and caps the list — which v0.2 left undefined. And it puts one working screen in the reader's hands rather than describing four destinations.

Everything in the data sections is labelled by how it was obtained: **measured** (counted in a file I read), **inferred** (a conclusion from measured data), **external** (a published source outside ISZE), or **proposed** (a recommendation awaiting a decision). Nothing is asserted as measured because a narrative said so.

Fourteen pages of argument, then annexes for the reader who wants to check a number.

---

# 1. The ask

Two decisions, and one thing to look at.

**First decision.** Name one person to receive and answer a distributor's question, with hours in the week, and a named deputy. The whole product is redeemed at the moment a distributor asks something and gets a usable answer. Today there is no case register at case level anywhere, no name against any response class, and a question to the ITUK parts director drafted on 18 September 2026 that has still not been sent. Until that person exists, nothing that leaves ISZE can be promised.

**Second decision.** Pin one classification release, by file name, version and build date. Three candidate files exist at roughly 165,000 part numbers each with no authority declared between them. Until one is named, no part-family label may be printed outside ISZE. This is the only blocker that ISZE can close entirely on its own, and it takes a day.

**The thing to look at.** Page 2 of this paper is a finding that was already sitting in our own files and that nobody had asked for: one dealer's wheel and hub fastener purchasing stops dead in the middle of 2025 while every other dealer in the country keeps buying the same five part numbers. Seven tests were run on it. Three eliminated alternatives; four could not be tested and say so. What is left is a real commercial question, and it is the shape of everything Universe should do.

Everything else in this paper is machinery for finding more things like it.

---

# 2. The worked case

**This is the screen. It is also a real finding, reproduced from `dealer_sellout_long_ITUK_CY2025.csv` and the AIM parts master.**

## Commercial signal

**Warrington Vehicle Centre Ltd — wheel and hub fasteners.** Five part numbers fall from **452 units** in the first half of calendar 2025 to **40 units** in the second half, a fall of 91%, against an account whose total purchasing moved only from 7,813 to 5,988 units (**−23%**). *(measured)*

| Part number | Description | H1 | H2 | Year | Months active |
|---|---|---|---|---|---|
| `8973598100` | NUT; WHEEL, RR AXLE | 112 | 8 | 120 | 5 of 12 |
| `8973598060` | NUT; WHEEL, INNER, RR AXLE | 104 | 6 | 110 | 5 of 12 |
| `8973598050` | NUT; WHEEL, INNER, RR AXLE | 92 | 6 | 98 | 5 of 12 |
| `8973598090` | NUT; WHEEL, RR AXLE | 88 | 8 | 96 | 4 of 12 |
| `8971684572` | PIN; WHEEL, FR AXLE | 56 | 12 | 68 | 4 of 12 |
| **Total** | | **452** | **40** | **492** | |

The five numbers stop on the same date. The last month with any of them is **August 2025**; there is nothing in September, October, November or December.

## Financial scale

**Not computable, and that is stated rather than papered over.** The dealer-level purchasing file carries quantity only — no value column, no price, no discount. There is no price in the file to multiply by, so this paper does not give the gap a euro figure. *(measured)*

What the same five numbers are worth across the whole billed book over the last twelve months is **€26,170.09**, from the parts master. That is a network figure and is not this account's loss. *(measured)*

**No euro total is stated for this case, because the evidence does not support one.**

## The family around it

The five numbers sit in **Wheels Hub / Wheel Rim / Wheel** in the parts tree: 574 part numbers network-wide, 43 of them active at this account in 2025. *(measured)*

| | H1 | H2 | Year |
|---|---|---|---|
| The five fastener numbers | **452** | **40** | 492 |
| The other 38 family numbers at this account | **385** | **78** | 463 |
| Whole family at this account | 837 | 118 | 955 |

**Read the second line carefully, because it decides the interpretation.** The surrounding family nearly halved and then halved again — so this account genuinely slowed its wheel-and-hub buying. But the surrounding numbers never stopped: they carried activity into **every remaining month** and ended at 4 and 5 units in November and December. The five fasteners stop dead and never come back. *(measured)*

## The elimination record

Seven tests. Three eliminated an alternative explanation; four could not be run and say why. This is the part of the page that makes it a decision rather than a chart.

| # | Test | Result | What it means |
|---|---|---|---|
| 1 | Did the fleet base fall as much? | **NOT TESTABLE** | No dealer-level vehicle population exists anywhere in the estate. The fleet file holds one national figure, repeated across dealers. A per-dealer rate cannot be computed. |
| 2 | Is a contributing part number superseded? | **PASSED — none is** | Checked against the parts master and the replacement table. Five current numbers, no successor. |
| 3 | Is the stop network-wide (supply) or account-specific? | **ACCOUNT-SPECIFIC** | The five numbers kept selling across the rest of the network all year: **3,660 units** in the second half across the other dealers, against **3,324** in the first. A supply withdrawal stops every dealer. |
| 4 | Is the first half inflated by one large order? | **PARTIAL** | May carries 212 of the 452 first-half units, 47%. Remove May entirely and 240 units remain across five months, against 40 in the whole second half. The step survives, but its size depends on May. |
| 5 | Do the other family numbers move the same way? | **SAME DIRECTION, DIFFERENT SHAPE** | They halve and continue; the five stop. The shape difference is the signal. |
| 6 | Did a price change coincide? | **NOT TESTABLE** | The file has no price. A price history for these numbers over 2025 would settle it. |
| 7 | Is this inside normal variation? | **NO** | All five are active in five months or fewer, and all five fall silent in the same two months. Ordinary variation does not synchronise five part numbers onto one stop date. |

## Diagnosis

**Something changed in how this account sources wheel fasteners, in or around August 2025, and it is specific to this account rather than to the part or the supply chain.** *(inferred)*

The two explanations that survive are: a stocking cycle that has been allowed to run down and has not yet been rebuilt, and the fastener requirement moving to another supplier or another workshop that reports its purchases elsewhere. **The data cannot choose between them.** *(inferred)*

One reading is explicitly excluded: it is **not** evidence that this dealer under-services its trucks. The account carries one of the higher self-assessment scores in its market, and no link between a servicing workshop and a buying account exists for these part numbers, so the fitted-versus-bought comparison cannot be made. *(measured on the score; see §10 for why the score proves nothing)*

## Confidence

Not a score. Seven named dimensions, each with its state and the reason.

| Dimension | State | Basis |
|---|---|---|
| Purchasing quantity | **strong** | Twelve months, all present, quantity-only rows, one account, one year |
| Coverage | **strong** | 66,018 monthly rows reconcile to 223,897 units; this account carries all twelve months |
| Identity | **strong** | One exact match between the buying account and an account name, one-to-one verified |
| Applicability of the family | **medium** | Family assigned from the parts master, which is a **candidate** release, not a pinned authority |
| Fleet base | **absent** | No dealer-level vehicle population exists. Nothing about intensity can be claimed |
| Price | **absent** | No price in the file |
| Trend | **absent** | One dealer-level year exists. No year-on-year is possible |

**Overall: publish the observation, do not conclude the cause.** The recommended action is a question, not a decision.

## Recommended action

**Raise one scoped question with ITUK's parts function, and set a review date.**

> For Warrington Vehicle Centre, five wheel and hub fastener numbers fall from 452 units in January–June 2025 to 40 units in July–December, with no activity after August, while the same five numbers continued across the rest of the network. Is this a stocking position that has not been rebuilt, or has the requirement moved to another supplier or another workshop? Nothing else is needed — no prices, no margins, no stock value, no customer detail.

- **Owner.** The ISZE commercial owner raises it; the ITUK parts function answers it. No person is named today, which is the gap.
- **Expected observable result.** Either purchasing resumes on those five numbers in the next three months, or the answer tells us where the requirement went. Both are useful. Neither requires a price decision.
- **Review basis.** The next three months of units on those five numbers, against the same period and the same five numbers at the other 54 dealers using them.

**Explicitly not recommended:** a price change. There is no price evidence for these part numbers, and the elimination record shows no price movement was observable. Recommending a discount here would be a guess dressed as analysis.

## What this page proves about the product

It is built entirely from files ISZE already holds. It took no new data collection, no distributor request and no new system. It produced one specific question that currently has no owner, on a real account, worth a defined and small amount — and it correctly declined to conclude the interesting-sounding thing.

**And it took the parts tree to find it, which is exactly why §1's second decision matters.** Family assignment came from the parts master — a candidate release. That is why applicability is marked *medium* and why no family label in this paper goes outside ISZE.

---

# 2a. The smallest version that is already worth having

**One market. One year. One account. One page. Everything in §2 is built from files ISZE holds today** — no new data, no distributor request, no new system, no hosting decision. That is the MVP, and it is already running on the page beside this paper.

## In the first release

| Element | Why it is in |
|---|---|
| The opportunity page, filled in, for a real account and a real family | It is the product. Everything else is scaffolding around it |
| The surface rule from §6, written down even though it is crude | Without it the list is either empty or infinite |
| The elimination record, mandatory on every finding | It is what separates a decision from a chart |
| A queue capped at 25, ranked by the three stated fields | Prevents the thing becoming a reading list |
| The finding template, so a second case can be built by someone else and come out in the same shape | Otherwise every case is bespoke and nothing scales |
| The confidence dimensions, shown as states and never as one score | Three of seven are absent in the first case; a score would hide that |
| The action record: question, owner, decision, review date, answer, outcome | The loop is the product's whole claim |
| The honest unavailable state: what it cannot show, why, and what would change it | A page that cannot say "I do not know this" is not trustworthy |

## Deliberately excluded from the first release

Dealer self-assessment linkage, because no assessment date exists. The service-demand model, because no approved schedule exists. Price simulation, because no volume response has been agreed. Any second market. Any dealer-facing page. Tender support. Any hosting or external-access decision, because there is no application and the folder is not safe to publish as it stands. Alternative-part substitution recommendations, pending technical validation.

## Definition of done

One named person at ISZE can open the page, reproduce the numbers from the source file without help, explain the case to the ITUK parts function without leaving the screen, have one point of it challenged, correct the underlying record, and see the case and the numbers update. **That is the whole test, and it is deliberately small enough to fail.**

---


# 3. What changed because we looked

Four things came out of the same files, and none of them needed a new system.

## 3.1 The anchor case that already exists and had never been published

The programme already holds a fully verified worked case: **Cordwallis Commercials (Heathrow)**, engine filters, calendar 2025. It passes 104 checks with zero failures, and a second independent pass over the original workbook reproduced twelve of twelve headline figures. *(measured)*

| | Value |
|---|---|
| Trucks serviced in calendar 2025 | **72** on all lines, **70** on part-bearing lines |
| Jobs | **269** |
| Workshop lines | **1,627** |
| Engine-filter lines | **148** |
| Family units fitted | **148** on the consumable family, **147** on the twelve named numbers |
| Engine filters bought by the matched account | **719** on the twelve, **836** on the consumable elements, **852** on the family |
| Parts value at the workshop | **27,543.79** in an undeclared currency |

**The comparison everyone wants does not exist, and this is the single most important sentence in the paper.** The fitted figure and the bought figure cannot be put on one page and read against each other. No link exists between a servicing workshop and a buying account. The difference is not a gap, not a leak and not a shortfall — it is two files with different populations and different units of account. *(measured)*

## 3.2 A family total that moves by more than half depending on the definition

On the same Portuguese file, the same year, the same oil-filter family, measured three ways:

| Definition | Units 2025 | Part numbers |
|---|---|---|
| Pipeline service-category model registry | 2,360 | 5 |
| Catalogue family | 3,711 | 55 |
| Catalogue family, elements only | 3,595 | 23 |

The spread between the widest and the narrowest reading is **57.2%**. *(measured on the file, by the pilot workstream)* Every family number in that market is arguable until one definition is chosen and written down.

## 3.3 The price position we can actually measure, and what it says

Sixteen observed competitor listings carry a match to a part number we sell, covering **8 distinct part numbers**, from **one** UK competitor on **one** capture date. Our dealer price is in euro; the competitor listings are quoted in the currency the competitor published, in the column it published it. **The index is what to read — the currency is a property of the observation, not a common basis, and the two are never blended.** *(measured)*

| Our part number | Description | Our dealer price | Competitor genuine | Competitor non-genuine | Index vs genuine | Index vs non-genuine |
|---|---|---|---|---|---|---|
| `8975439050` | OIL FILTER | €10.73 | €15.00 | €12.00 | **0.611** | 0.764 |
| `8983752250` | FUEL FILTER | €16.97 | €20.00 | — | **0.725** | — |
| `8970622940` | AIR FILTER ELEMENT | €49.98 | €55.00 | €30.00 | **0.777** | **1.424** |
| `8976739570` | AIR FILTER | €48.98 | £50.00 | £35.00 | **0.837** | 1.196 |
| `8980370110` | FUEL FILTER ELEMENT | €16.21 | £13.00 | £10.00 | **1.066** | 1.385 |
| `1313100120` | CLUTCH RELEASE BEARING | €122.50 | £90.00 | — | **1.163** | — |
| `8971482700` | OIL FILTER ELEMENT | €19.81 | £13.50 | £7.50 | **1.255** | 2.259 |

**The same part number gives opposite answers depending on which reference you choose.** On the air filter we sit 22% *below* the competitor's genuine listing and 42% *above* its non-genuine one. On two oil filters and a fuel filter we are 25–39% below the comparable genuine part. So the commercial question is not "are we too expensive" — it is **which reference is the right one for this fleet and this application**, and that is a range, positioning and equivalence question, not a list-price question.

*(measured. Five of the seven rows carry the competitor listing in euro and two in sterling, exactly as the source published them — the source holds a single conversion factor that has not been applied here, and the two sterling rows are marked. The index column is computed from the published figure and the published index in the source, not from a conversion.)*

## 3.4 The market context that says the same thing from outside

Independent published research agrees with what our own file shows, and this is the first time this paper has used it. *(external)*

- The independent aftermarket holds **62%** of the EU parts market by revenue, €73bn of €118bn in 2023, excluding labour (Roland Berger for FIGIEFA, October 2024). But in the visible crash-parts segment the manufacturer share is **69%** (European Commission, Wolk After Sales, September 2021). Two-thirds of the market and two-thirds of body parts belong to opposite sides, and which one you quote decides the story.
- The OES-versus-independent premium is **not one number**. ADAC measured a range from **6.8% to 36.7%** across fifteen models on the same seven components in Germany. In Sweden, Volkswagen cut nearly 8,000 part prices by 22% on average and then found the residual gap to the largest alternative supplier averaged about **9%** — and some original parts were cheaper. *(external)*
- **Price is not the first lever in the buying decision.** A German workshop survey in 2026 (n=200) found the triggers for buying outside the primary channel were unavailability **91%**, specialist parts **79%**, quality requirements **68%**. US workshop data found availability chosen first by **59%** of shops, price **10%**, brand **0%**. And in UK fleet data the independent share of service jobs **plateaus at 35–42% from year two onward** and has actually slipped since 2021 — the ageing story that independents win with vehicle age does not hold for fleets. *(external)*
- **Commercial vehicles are structurally more OEM-friendly than cars.** The independent aftermarket is roughly two-thirds of CV workshops, but published research states explicitly that OEM parts share in the CV independent aftermarket is comparatively high. *(external)*

**Why this matters to the paper.** It says the same thing our Cordwallis and fastener cases say: the gap that needs explaining is usually a fitment, availability or identification gap before it is a price gap. That is not an argument against pricing work. It is an argument about which lever to reach for first.

---

# 4. The problem, and what it costs

ISZE holds the evidence. It does not hold it in one place, and it does not hold it at the level the decisions need.

**What we can already see.** Parts billed across 22 distributors, €117.6m from 2023-01-03 to 2026-08-31 on the GPS-facing basis; 514,037 rows in the billing table. Twelve or more derived sales-to-dealer extracts from seven national senders. A parts master at roughly 165,000 part numbers with a family tree. A fleet file at 18 markets. A dealer self-assessment round of 519 records across 19 country lists. Competitor price observations from eight sources. *(measured)*

**What we cannot see, and it is the same gap every time.** A link between a dealer's name and the account it is billed under. This is the join that turns a national total into a dealer conversation, and it does not exist. Measured states:

- The two columns a join would need are blank on **all 66,018 rows** of the ITUK monthly purchasing file. *(measured)*
- **0 of 3** ITUK purchasing accounts are mapped to a dealer site. All three are the distributor's own accounts. *(measured)*
- Of the 64 dealer names, **32 match a workshop name one-to-one**, each still needing individual inspection; roughly **20 have no plausible match**. *(measured)*
- **65,619 rows** of the dealer-grain replenishment comparison read *not computable at dealer grain*. *(measured; this is a different file from the 66,018 — see the annex)*
- No dealer-level or territory-level vehicle population exists anywhere, so **no per-dealer rate may be computed at all**. *(measured)*
- **0 of 57** assessment records carry an assessment date. The workbook has the label rows and the value cells are blank. *(measured)*
- **0 of 10** IDS-to-parts links are approved. *(measured)*

**And a trap inside the gap.** A single text search for one dealer's name returns its sibling sites and a total roughly **two and a half times** the correct figure for one account, because nothing in the source distinguishes the sites except the name itself. Three Cordwallis entities appear on the same twelve part numbers at 719, 555 and 470 units. Until ITUK rules on the site list, no figure may be presented as that dealer's position. *(measured)*

**The consequence in one line.** Every dealer-level commercial claim in the programme is blocked behind one list of 64 names and their account numbers. That list is a one-hour answer for the distributor.

---

# 5. The product, in one screen

**One market. One family. One account. One page that ends in a question with an owner.**

The screen in §2 is the product. Everything below is what surrounds it.

**What the user opens.** Universe Home answers one question: *what requires attention?* It is a capped list of findings, not a dashboard. Each row carries the account or market, the family, the observed movement, the size, the confidence states, and the owner if one exists.

**What a finding carries.** The eight elements of §2, in that order: signal, scale, family or context, the elimination record, diagnosis, confidence by dimension, recommended action with an owner and a review basis. A finding without an elimination record is not publishable — that single rule is what separates this from a chart pack.

**What the reader can do.** Open the evidence behind any figure in one step to a named file and a stated period. Recommend an action, assign it to a person, set a review date, record the answer, and see the action return to the analysis it came from. Export the page with its scope, period, measure basis, coverage and source versions attached.

**What it refuses to do.** Set a price. Rank dealers. Show a fleet rate where no per-dealer fleet exists. Draw a continuous line through an unreported month. Render a missing value as a zero. Call a reference valuation sales revenue.

**The four destinations, kept from v0.2 because they are right.** Portfolio (parts and the genuine/alternative split), Network (validated accounts, sites and assessment context), Commercial review (evidence and trends), Actions (owner and review). They are kept, but they are not the contribution. The contribution is §2.

---

# 6. What surfaces a finding, and what suppresses it

v0.2 had no rule here at all. It said prioritise where the signal is material and never defined material. This is the rule. **It is proposed, it is crude, and it is arguable — which is the point.** A wrong threshold can be argued with; no threshold cannot.

## 6.1 The surface rule

A part family at a distributor, account or market level enters the queue when **all four** hold:

1. **Size.** The family moved by at least **150 units** *or* **€10,000 of billed value** between two comparable six-month windows, in one transaction flow. Both floors, either one sufficient.
2. **Shape.** The movement is concentrated: at least **half** the change sits in **five or fewer part numbers**, or the family's active part-number count moved by at least a quarter.
3. **Stability.** The applicable fleet base did not fall by as much as the purchasing, where a fleet base exists for that scope. Where it does not exist, the finding may still surface but the fleet dimension prints as *absent* and no intensity claim may be made.
4. **Coverage.** All months in both windows carry a row, or the missing months print as missing and the finding is marked *partial coverage*.

## 6.2 The queue

**Maximum 25 open findings**, ranked by a stated order and not by a composite score:

1. Billed value at stake in the affected part numbers, descending.
2. Number of elimination tests that could be run and passed.
3. Whether an accountable owner already exists for the affected scope.

An opacity check applies: if a reader cannot reconstruct the rank from those three fields, the ranking is wrong. **A composite score is not permitted.** v0.2's instinct here was right and is kept.

## 6.3 The suppression list

A candidate is suppressed, or routed away from the commercial queue, when any of these hold:

- **Small.** Below both floors in 6.1.
- **Broad.** The movement is spread across more than half the family's part numbers with no concentration — that is drift, not an event.
- **Explained by fleet.** The applicable fleet base fell at least as much as the purchasing.
- **Superseded.** A validated replacement pair accounts for the movement once re-attributed.
- **Supply.** A known supply constraint or a backorder position covers the period. Route to the supply question, not the commercial queue.
- **One-off.** A single month or a single order carries more than half the change, and the residual does not clear the floor.
- **Thin evidence.** Fewer than half the elimination tests could be run at all.
- **Repeated.** Already open, with the same scope and the same cause.
- **Coverage.** The affected part numbers sit under unresolved identity or an unpinned classification release. Route to the data-quality task list. **A data gap becomes a data-quality task and never a sales opportunity with a number attached.**

## 6.4 The elimination sequence

Run in this order. Each test either eliminates an explanation or records that it could not be run, with the reason. **No test may be skipped silently** — an unrun test prints as unrun.

1. Fleet base.
2. Supersession and replacement mapping.
3. Network versus account scope (is the stop everywhere, or here?).
4. One-off order inflation.
5. Surrounding-family shape.
6. Price movement.
7. Coverage and identity integrity.

**A finding may only reach a price conclusion if tests 1 to 5 all ran and none explained the movement.** In the §2 case, three ran and eliminated, four did not, and the honest output is a question rather than a price decision.

---

# 7. Pricing, honestly

**We can tell you where we sit. We cannot tell you what happens if we move.**

## 7.1 What exists

The evidence in §3.3 — a real index against two reference levels on eight part numbers, from one source on one date. And a commercial basis discipline that v0.2 got right and this keeps: use the actual ISZE net price, cost, currency, effective date and support terms; never substitute a reference valuation for monetary evidence; state which volume is incremental, which is displaced and which is uncertain; and never count genuine volume replaced by an alternative part a second time as new business.

## 7.2 The volume response, stated rather than avoided

There is **no defensible published price elasticity for European vehicle replacement parts.** The ranges that circulate in aftermarket pricing material have no traceable primary source, and the best available empirical work concludes that the value is category-specific and quality-tier-specific, so a single coefficient misleads. That is an external finding and it is a warning. *(external)*

**So the assumption is printed rather than hidden.** *(proposed)*

> For any price change, declare an expected volume response as a range before the decision, with the source of the range named — an observed prior intervention in this programme, a comparable market's response to a recorded change, or an explicit judgement labelled as one. Where no response can be stated, the decision is a judgement call and the paper must say so on the same page as the price. **No price change is presented with a profit effect that rests on an unstated volume assumption.**

## 7.3 The arithmetic

Baseline gross profit = baseline quantity × (baseline net price − baseline unit cost).
Scenario gross profit = scenario quantity × (scenario net price − scenario unit cost).
Change = scenario − baseline.

For one comparable part with unchanged cost and a positive supported unit margin, the quantity needed to hold gross profit flat is:

> baseline quantity × baseline unit margin ÷ supported unit margin.

Zero or negative supported margin means more volume is not the answer. A lower margin percentage can coexist with higher gross profit, and the calculation has to show which applies.

## 7.4 The honest limit

There is **no approved budget, no measured baseline of the existing process and no evidenced euro return** anywhere in this programme. A search for an approval record found none. So this paper does not present a return. It presents the cost of entry and one case.

---

# 8. What the distributor gets

**A staged exchange with a defined return at each level. Nothing is demanded before it is earned.**

The recorded starting point: part of the distributor support payment is linked to sales-to-dealer information, with distributor and dealer selling prices excluded from that requirement. The applicable agreement and its exact conditions are not held in this programme and are not inferred here. *(measured as a recorded position, not as contractual terms)*

**The honest finding, which belongs here rather than in a footnote.** The existing arrangement is strong enough to get a file and not strong enough to get a good one. A file sent to satisfy a condition is the minimum that satisfies that condition. That is why the product has to earn the good one.

## The five levels

| Level | The distributor contributes | What comes back | What it costs them |
|---|---|---|---|
| **0 — ISZE data only** | Nothing | The monthly review from our own billed data: the family, the trend, the genuine/alternative split, their own assessment results, the tender panel | Nothing |
| **1 — the minimum file** | Dealer identifier, part number, period, quantity, and a coverage declaration. **No prices.** | Everything in Level 0 plus what moved onward, stocking position and geographic weak spots | A monthly extract they already produce |
| **2 — identity** | The dealer-name-to-account-number list | Dealer-attributed purchasing, and the fitted-versus-bought question becomes answerable | One hour, once |
| **3 — commercial context** | A structured reason per movement: competitor quote, availability, tender, customer requirement, existing stock, fitment mismatch | The reason behind the movement, and a reason library over time | A few lines a month |
| **4 — optional operational** | Selected stock and open orders for agreed parts and locations | A replenishment and availability review for the agreed scope | Ongoing, and only where they choose it |

**The minimum ask is three things:** the monthly file at Level 1, the one-column list at Level 2, and one agreed action per review. Nothing else is requested until the return on those three is visible to the distributor.

**Boundaries that are promises, not preferences.** The minimum quantity feed never silently becomes a request for selling prices, margins, stock, customer identities, vehicle identifiers, workshop records or end-customer sales. Optional information has a defined additional return and an agreed use, and **the moment an optional input becomes a condition of access to the core review, the review stops being a product and becomes a form.**

**No data-access fee, ever.** The return comes through actions — better targeted support, better genuine/alternative placement, geographic weak spots, closed follow-ups, converted opportunities — never through charging a distributor to see its own data. That decision is closed.

**What must never be built:** dealer league tables and compliance scores. And the dealer must not become a coloured dot on a map controlled by ISZE.

**Data-protection line, stated once.** Aggregate and benchmarked commercial data is not automatically anonymous: a group-level statistic from which one participant's position can be deduced can still be personal data under the draft European guidance now out for consultation. Any peer comparison is designed on the assumption that the stricter reading applies, and it is index-form, above a stated minimum number of participants, and never broken down to identify one party.

---

# 9. The pilots

**Two pilots, two different proofs. Neither validates the other.**

## Pilot 1 — ITUK, dealer-level

**The hypothesis.** A distributor will change a decision because this review shows it something it could not see from its own files.

**What exists.** One year at dealer grain: 101,341 rows, of which 66,018 monthly rows carrying 223,897 units across 64 named dealers and 5,559 part numbers. All twelve months present. 60 of the 64 dealers complete for the year. 399 monthly rows carry negative quantities, totalling −651 units. 5,556 of 5,559 part numbers resolve to a family; the three that do not carry 7 units. *(measured)*

**What does not exist.** A dealer-level fleet. A link from a dealer to a buying account. A second year, so no dealer-level trend. An assessment date. *(measured)*

**What it can demonstrate.** A monthly review at dealer grain; a real decline explained to part numbers with a documented elimination record; two purchasing flows shown side by side and never added; a correction exercised end to end; a question routed to a named person and answered.

**What it must not claim.** Any per-dealer rate. Any dealer ranking. Any statement that a dealer under-serviced its fleet. Any joined assessment score. Any year-on-year at dealer level.

## Pilot 2 — Portugal / I Motors, national

**The hypothesis.** A market will engage with a national review without dealer attribution, and the review will change how ISZE defines a parts family.

**What exists.** A complete national sales-to-dealer file for 2025 and 2026 to August: 51,363 monthly units in 2025 across 5,712 part numbers, **with no dealer name in any row**. Sixteen dealer self-assessments with dated site visits between 31 March and 30 April 2026, questionnaire version 2026, 280 points across 196 scoreable items, average 86.92%, range 74.64 to 99.29 — and an independent-assessor block that is **empty on all sixteen sheets**, so the round is the dealer's own answers plus a site visit and no independent rating. Two of the sixteen are the distributor's own retail sites. *(measured)*

**The one contradiction worth keeping.** Parts and accessories is the **highest-scoring section** in that assessment round at 89.66%, in a market whose measured parts capture against the modelled ceiling is under half. Both are true, nothing on disk explains the gap, and explaining it is the best commercial use of the self-assessment material anywhere in this programme. *(measured on both figures; the explanation is open)*

**What it can demonstrate.** That a family total moves by more than half depending on the definition (§3.2); that replacement mapping changes the story on a market that looks like it stopped buying three part numbers and has in fact moved to their current versions; that a market is reviewable nationally without any dealer attribution.

**What it must not claim.** Any dealer-level purchasing. Any share of the national total attributed to a site. Any statement that the assessment contradicts or confirms the purchasing position.

## What neither pilot may assume

Passing the national review says nothing about whether a dealer-level join is possible. Passing the dealer review does not create Portuguese dealer attribution. **The period for the first review is calendar 2025.** The 2026 file is kept for the repetition test, because the workshop record ends in March 2026 and pairing a current purchasing view with it would present two different clocks as one picture.

**Both pilots share five gates, and none is passed by the gate before it.**

| Gate | Passes when | Does **not** pass |
|---|---|---|
| **G-1** First internal demonstration | A review built from source, walked end to end with account, period and evidence intact, producing one documented question | A document that satisfies a source file's existence, a synthetic prototype, a page that renders |
| **G-2** First participant-facing use | Contents inspected element by element against the permitted-data list, with a named responder in place | A login, a hidden menu, a filter, a folder shared without inspecting its contents |
| **G-3** First delivered response | Submission, assignment, first substantive answer, next update and resolution recorded as separate stamps, answering authority named | An acknowledgement. A request for more data. A drafted answer never issued |
| **G-4** First correction handled | Replacement identified, prior version traceable, identical-rerun test showing no net change, affected results named to the people who used them | Editing the previous result so only the new number exists |
| **G-5** First genuinely repeated exchange | Two submissions from the same source reconciled, change visible, participant effort recorded | A file that reappeared. A re-export of the same round |

**There is no "pilot complete" milestone.** The five achievements arrive at five different times, and collapsing them into one status is how a programme reports success it has not had.

## Go / no-go criteria

Three dimensions, measured separately, because combining them hides all three. Every one is checkable by a person rather than by a system.

**Data reliability.** Can a second person reproduce the headline numbers from the source file without asking anyone? Is the coverage position printed on every result? Is every missing month shown as missing and every declared zero shown as a zero? Does reprocessing the same submission change nothing? Does a correction restate the affected results and keep the earlier version?

**Use.** Did the review reach the recipient, and did they engage with a specific part number? Was at least one question answered by a named person within an agreed date? Was one correction received from the distributor rather than requested by ISZE? Did the second month's file arrive without a reminder?

**Commercial.** Was at least one decision recorded with a reason, an owner and a date? Can its effect be observed in the following months' numbers, against a comparable family as an approximate control? Did the first support or range discussion arise from the review rather than from a distributor's complaint?

**The single question that decides it, stated so it can fail.**

> If the incentive that currently produces the file were removed tomorrow, would the distributor keep sending it?

Everything above is evidence for that question. If the answer is no after two quarters, and the programme cannot name one decision that changed and one question answered by a named person, **it stops.** The detailed stop condition is in §12.

---


# 10. Who this is for, and what happens after an action

## 10.1 Four users, and the task that disappears

| User | What they do with it | What stops |
|---|---|---|
| **ISZE parts analyst** | Prepares the monthly review; builds a finding from the surface rule; runs the elimination record | Rebuilding the same pivot, and discovering three days later that coverage does not support it |
| **ISZE pricing owner** | Places our position against a stated reference on named part numbers; states a volume response before a decision | Arguing a discount from a single competitor listing with no basis stated |
| **Distributor parts manager** | Opens the monthly review, sees what changed, examines the contributing part numbers, discusses a response | Rebuilding the explanation in a separate presentation, and asking ISZE for support without evidence |
| **ISZE commercial owner** | Assigns, decisions, reviews. Owns the answer and the review date | Chasing a question with no owner and no date against it |

**A fifth role is deliberately absent from the product and present in the governance:** the technical authority for fitment and application. **No commercial case owner can confirm fitment.**

## 10.2 After the action, and the honest limit

Every action records: the question, the owner, the evidence, the decision, the date, the reason, the next review, and the outcome. The states are: received, assigned, awaiting evidence, under review, answered, closed — plus a real *no action, and here is why*, which is a storable outcome.

**And then the limit, stated rather than blurred.** A before-and-after increase is an observation, not proof that the action caused it. Incremental profit cannot be observed, because every version of it requires knowing what would have happened instead. **No measurement of an alternative that did not occur exists anywhere.**

What can be done, and is proposed: for a bounded intervention, compare the treated part numbers against **a comparable family of similar size and seasonality in the same market over the same window**, agreed before the intervention rather than after. That is not proof. It is a defensible observation, and without it the programme will accumulate decisions with no results attached.

**What must never be used as a measure of benefit:** logins, page views, uploaded row counts, the number of findings generated, the modelled value of opportunities found, or the reference value of workshop lines.

---

# 11. What we know, what we infer, what we do not know

## Measured

What ISZE billed to each distributor, by part number and month, €117.6m across 22 distributors from 2023-01-03 to 2026-08-31. What one distributor's 64 named dealers bought, by part number and month, calendar 2025, 223,897 units on monthly rows. That five named part numbers at one account fell from 452 to 40 units while the same five kept selling everywhere else. That one family total moves 57.2% depending on the definition. That our position against one competitor on eight part numbers ranges from 25–39% below to 25% above, depending on which reference is chosen. That the two columns a dealer-to-account join needs are blank on all 66,018 rows of the purchasing file, and none of three buying accounts maps to a dealer site. That no dealer-level fleet exists anywhere. That the assessment round has one round and no per-dealer date.

## Inferred

That the fastener stop is a change in how one account sources, not a supply or price event — from the elimination record, not from a price or stock file. That a market buying only the alternative part number and never the genuine one is making a range or channel decision rather than a price decision. That a decline confined to two months and one account is more likely a stocking or ordering event than a demand change. That the gap between our position and the independent aftermarket is, on the published evidence, more often an availability and identification gap than a price gap.

## Not known, and printed on the screen as such

Whether a dealer-level rate per vehicle is good, bad or normal. Whether a stock position caused an ordering gap. Whether a competitor listing reflects what anyone actually paid. Whether a price change would recover volume, to any degree. Whether a service interval is being met. Whether an intervention worked. What a dealer sold onward. Whether the current level of support activity is adequate — **nobody has measured how many questions are asked today, how long they take to answer, or how often the answer changes anything.**

---

# 12. Cost, effort and the stop condition

## What is measured

One cost object is observable today and the rest are not: **cost per source-year prepared and corrected**, per market, per cycle. *(measured)*

| Observed fact | Value |
|---|---|
| ITUK dealer-level file, calendar 2025 | 101,341 rows (66,018 monthly + 35,323 annual control) |
| The same source at network grain, same year | 28,483 rows |
| Five further national extracts | 24,360 / 19,244 / 7,774 / 21,636 / 1,827 rows |
| One classification release | 164,907 rows, 27 columns |

## What is proposed, and labelled as proposed

An initial operating team of **1.5 to 2.5 full-time equivalents** at **€90–130k fully loaded**, once two or three markets are live. This is a reasoning aid and not a quotation, and it recurs annually. *(proposed)*

A support ceiling has been discussed but **no approval record exists for it** and **no return is calculated against it**. A return calculation needs two measurements on the same basis, before and after, and the starting measurement has not been taken. Until it is, a return figure would be an invention. Two comparables were examined and both refused: a modest distributor support payment, and the coming price revision — the latter is a decision about the price list on the same part numbers and **must never be presented as a return from this programme.** *(measured as a position; refused as a return)*

**Seven cost categories are all unmeasured today:** source preparation, analysis, coordination, response, correction, maintenance, and the participant's own effort.

## The stop condition

v0.2 had delivery gates and no stop rule. This is the rule.

> If, two quarters after the first participant-facing use, the programme cannot name **one decision that changed** because of a review, and cannot show **one question answered by a named person within an agreed window**, it stops. Not pauses. Stops. A prettier merge is not a result.

---

# 13. The next ninety days

| Item | Owner role | Depends on | Completion test |
|---|---|---|---|
| Send the one-column dealer-name-to-account request to ITUK | Business owner | Nothing but the decision to send | 64 names each appearing once, each account once, collisions returned as groups, unresolved marked not blank |
| Pin one classification release by file, version and build date | ISZE classification owner | Nothing | One file named; family labels become printable outside ISZE |
| Name one receiver and one deputy for the response classes, with hours in the week | Business owner with the receiving function | Nothing | A person's name against each role, not a role or a team |
| Measure the existing process: how many questions, how long, how often the answer changes anything | ISZE analysis with the business owner | Nothing | A written baseline with an observed task count |
| Declare the workshop workbook's currency, or drop the money claim | Workshop source owner | One word from the source | Quantities are unaffected either way |
| Produce the ITUK dealer review for calendar 2025 | ISZE analysis | Classification release for the family label only | Monthly rows reconcile to the stated total; the annual control rows stay out of the monthly sum; sibling accounts are not pooled by a text search |
| Produce the Portugal national review | ISZE analysis | As above | Every figure carries its period and grain; no dealer is named where the source names none; the missing assessment date prints as missing |
| Raise the fastener question from §2 and set a review date | ISZE commercial owner | A named responding person | A case record with submission, assignment, answer and resolution as separate stamps |

**The critical path in one sentence.** Confirm the two reviews, record who receives and answers a question, decide the audience and reduce what is sent, the first participant-facing use, the first delivered response, the first correction, the first repeated exchange. Everything else runs in parallel off that sequence, and **no step may be skipped by passing the step before it.**

## What is ready, and what is not

Every capability classified by what it actually needs. **Nothing in the first block needs a decision from anybody.**

| Capability | Ready now | Pilot ready | Data work needed | Logic validation needed | Future |
|---|---|---|---|---|---|
| ISZE billing by distributor, family and month | ✔ | | | | |
| Three-flow separation and the coverage rules | ✔ | | | | |
| Minimum data contract for the monthly quantity feed | ✔ | | | | |
| The finding template and its confidence dimensions | ✔ | | | | |
| The opportunity page and its elimination record | ✔ | | | | |
| ITUK dealer-level review, calendar 2025 | | ✔ | | | |
| Portugal national review | | ✔ | | | |
| Matched price position, 8 part numbers, stated limits | | ✔ | | | |
| Correction and restatement end to end | | ✔ | | | |
| Named receiver and answering person with hours | | | ✔ | | |
| Dealer-name-to-account join | | | ✔ | | |
| Classification release pinned | | | ✔ | | |
| Currency declared for the workshop workbook | | | ✔ | | |
| Assessment date for the dealer round | | | ✔ | | |
| A second dealer-level period, for any trend | | | ✔ | | |
| Dealer-level vehicle population | | | ✔ | | |
| Size floors, surface rule and queue cap | | | | ✔ | |
| Elimination sequence | | | | ✔ | |
| Price volume-response assumption | | | | ✔ | |
| Outcome measurement with a control family | | | | ✔ | |
| Predicted response to a price change | | | | | ✔ |
| Service-demand model (blocked on the schedule) | | | | | ✔ |
| Dealer-facing pages and the access model | | | | | ✔ |
| Tender panel | | | | | ✔ |
| Hosting and external access | | | | | ✔ |
| Second and later markets | | | | | ✔ |

**How to read it.** Everything in the top block needs nothing but somebody's afternoon. Everything in *data work needed* needs a person rather than a system — pinning a classification release is one file, declaring a currency is one word, sending the account-number request is one email. Everything in *logic validation needed* is where v0.2 had nothing at all, and it is the block that decides whether this becomes a decision product or another dashboard.

---


# 14. Annex — how to check a number

## Fourteen things this paper will not do

1. Add ISZE billing to sales-to-dealer activity. Three flows, never summed.
2. Treat a missing file as a zero month. A zero must be asserted.
3. Compute a per-dealer rate where no dealer-level fleet exists.
4. Merge the two ITUK purchasing files, or average them, or reconcile them by assumption.
5. Print a family label outside ISZE while no classification release is pinned.
6. Present a fitted-versus-bought difference as a gap or a leak. Different populations, different units.
7. Label a workshop money figure with a currency no source declares.
8. Draw a continuous line through an unreported month.
9. Show an unknown as a zero.
10. Rank dealers, or score them, or build a league table.
11. Present a reference valuation as revenue or margin.
12. State a price change's profit effect without a stated volume assumption.
13. Present a modelled ceiling multiplied by a recovery percentage as a return.
14. Change a price automatically.

## Source register

| Ref | What it is | Where it is | Status |
|---|---|---|---|
| S1 | ITUK dealer-level sales to dealer, calendar 2025 | `01_data/00_derived/dealer_sellout_long_ITUK_CY2025.csv` | Read; 101,341 rows; 66,018 monthly + 35,323 control |
| S2 | AIM parts master with the family tree | `01_data/00_derived/AIM_Master_PN_Categories_Figkey_20260921.csv` | Read; 165,213 rows. **Candidate release, not pinned** |
| S3 | Billing and fleet position | `01_data/00_derived/gps_spu_by_distributor.csv` | Read; 88 rows, 22 distributors, €117,813,008 |
| S4 | Portugal national sales to dealer | `01_data/00_derived/dealer_sellout_long_PORTUGAL_CY2025.csv` | Read; 21,636 rows, dealer column empty on all |
| S5 | Competitor price observations | `01_data/01_Pricing/_raw/ks_aftermarket_price_compare_20260819.csv` | Read; 105 rows, 16 matched, 8 distinct part numbers, one source, one date |
| S6 | The verified worked case | `_MERGED_MASTER_2026-09-21/05_WORKED_CASE_ITUK_CORDWALLIS.md` and the case return | Read; 104 checks, 0 failures |
| S7 | The operational plan | `06_Working/DELIVERY_ROADMAP_20260921/` | Read; the gates, milestones, item buckets and cost categories |
| S8 | External research | Published sources, named inline | Consulted 2026-09-22; see below |

**Corrections carried into this edition, including two against the review that preceded it.**

- The **66,018** figure is the monthly purchasing file. The **65,619** figure is the dealer-grain replenishment comparison. They are different files and both numbers are correct in their own place. The review of v0.2 conflated them.
- The competitor panel is **8 distinct part numbers** behind 16 matched rows, from one source on one date — not 43 and not 16 part numbers.
- The parts tree family used in §2 is a **candidate** release. This paper does not treat it as an authority.

**External sources consulted for §3.4, by claim.** Roland Berger for FIGIEFA, "European Independent Automotive Aftermarket Panorama", October 2024 (IAM share, €73bn of €118bn). European Commission / Wolk After Sales, "Market structure of motor vehicle visible spare parts in the EU", September 2021 (69% OEM share in visible parts). ADAC, Germany, test data 2009 published 2010 (6.8%–36.7% premium range across fifteen models). Volkswagen Sweden price reduction and residual gap, reported in Swedish trade press. Wolk & Nikolic, "Spare Parts Purchasing — German Workshops", 2026, n=200 (91/79/68% triggers). IMR, US, 500 independent shops (availability 58.9%, price 10.4%, brand 0%). Epyx 1link and FN50, UK fleet data (independent share 30→40% by vehicle age, then plateau). Claims are attributed, not independently reproduced by ISZE, and are labelled external wherever they appear.

**Regulatory position, stated once and not as legal advice.** Under the Motor Vehicle Block Exemption Regulation, which applies to commercial vehicles as well as cars and runs to 31 May 2028, a manufacturer may reserve warranty-covered work to genuine parts but may not condition non-warranty work on network membership or on the OEM brand. Collecting genuinely public advertised prices is not in itself an infringement; sharing a peer price index with distributors, or any mechanism that could read as enforcement of where a dealer's price sits, is where the enforcement cases are. Peer comparisons are therefore index-form, aggregated, never forward-looking, and never accompanied by a target or a consequence. The Commission's own evaluation of the regime was published on 25 June 2026 and the decision on renewal is open.

---

*Written 22 September 2026. Replaces v0.2 for all purposes except the evidence rules, which are retained. Nothing was rebuilt, sent or overwritten to produce this edition. The opportunity page and the Cordwallis figures were reproduced from the source files named above on the date of writing.*

*Companion documents: the working opportunity page (`Universe_Opportunity_Page.html`), the adversarial review of v0.2 (`Universe_Yellow_Paper_v0.2_REDTEAM_REVIEW_2026-09-22.md`), and the operational plan at `06_Working/DELIVERY_ROADMAP_20260921/`.*
