# 03 - What runs, what is open, and what is wrong

**As of:** 2026-09-19. This file is deliberately blunt. Every item here is a known limitation of the data or
the operation, stated so that a research answer does not accidentally promise something the data cannot
support.

---

## 1. What runs, and how often

**The sales pipeline.** A Python pipeline reads the SAP billing extracts, loads them into one sales table
(514,037 rows, billing through 2026-06-30), and rebuilds every derived figure in file 02. It ends with a
verification suite. **The rule is: never quote a figure unless that suite is green (0 failures).** It is
currently 143 pass / 0 warn / 0 fail.

**The monthly refresh.** A published runbook covers the monthly cycle: bring in the new SAP extract, land the
new files, rebuild, verify, then rebuild the dashboards that read the derived data. The cadence is monthly,
not continuous.

**The tender monitor.** Collects public tender notices from national portals and the EU portal, deduplicates
them, scores relevance, and publishes to one feed. Runs on a schedule. Last generation 2026-09-15.

**The analysis application.** An internal web application (locally, port 8503) holds the working surfaces:
fleet, spend per truck, service-demand cover, mix, early warning / account health, warranty, a forecast
surface, and an action plan. This is where analysis happens; the dashboards are for showing.

**The dashboards.** Static HTML files. They are generated from the derived data and published in two places -
a local build mirror and a repository used for sharing. Historically there was a public web address for these;
it now returns nothing and the mirror is kept local on purpose, because it still contains commercial data.
**Do not assume any ISZE dashboard is reachable on the public internet.** If a question asks someone to "look
at the dashboard", the realistic answer is a local file path, not a URL.

**The maintenance watch.** A verification and rebuild check for the aftermarket dashboard runs on an automatic
schedule (every ten minutes) overnight. It is maintenance, not a rebuild triggered by a conversation.

---

## 2. Open work - what is actually being built

In rough priority order. "Blocked on" names the one thing that moves it.

| # | Item | State | Blocked on |
|---|---|---|---|
| 1 | Calibrating the account-health thresholds so the early-warning list becomes a real call list | The model fires on 10 red and 6 amber of 17 markets; the thresholds are not yet a decision | Jerome - the amber/red thresholds |
| 2 | Signing off list price against what was actually pocketed, so price leakage can be quantified | Validation ran; the leakage euro stays internal until the year-matched joins are signed in writing | Jerome - written sign-off |
| 3 | Putting the volume forecast into live use | Built; median error about 49% by one measure | Jerome - sign off catalogue coverage and the override policy |
| 4 | National tender portal coverage | Analysis done: only about 8 of 29 footprint countries have a live national source; roughly 69% of collected opportunities are EU-portal only and below the national threshold | nothing - the work is wiring Spain, Italy and Germany |
| 5 | The air-filter interval assumption (0.5 per service) | Shipped on a provisional assumption | IML confirmation |
| 6 | The ITUK brake wear factor - 0.4 or 0.8 | 0.4 is in force; do not quote ITUK brake cover as locked | ITUK data |
| 7 | Generation-aware service intervals for the light commercial range | Schedules are on disk; mapping fleet years to the right schedule needs chassis and registration dates | the mapping data |
| 8 | Completing the part-number to diagram-key mapping | Live at 98.9% coverage | nothing |
| 9 | Residual gaps in the European price list | 24 part numbers plus administrative lines; a separate list of 925 part numbers worth about EUR 2.48M is billed on superseded numbers | nothing - the next slice is validation against the electronic parts catalogue |
| 10 | Reading mail text to extract actions and risks | Designed, no code | an approved route for company text (privacy and works council steps) |
| 11 | A live KPI service instead of static files | Not started | schema and credentials |
| 12 | Renaming dashboard files consistently | Blocked by design: build scripts hardcode the version in the filename | a rename plan |
| 13 | Improving tender collection quality | Relevance scoring, error column, a few portal-specific parsing failures | nothing - small items |

**Deliberately not on the list:** any new 0-100 score on any surface, and any revival of the old
dashboard sandbox. Both are closed decisions.

---

## 3. The FY2027 plan, and the monthly cycle

Everything else in this set is history. This section is the first and only place in the set where a forward
target appears.

### 3.1 The FY2027 plan by market

The names below are distributor names, not countries. File 01 section 5 carries the mapping from each name to its country and to the code used in the data files. Read that mapping before this table.

Source: `01_data/11_planning/FY2027  BP VP&ACC.xlsx`, sheet `VP FY27`, file date 2026-07-03. The figures are
vehicle-parts turnover in euro for the fiscal year.

| Market | FY2027 plan, EUR |
|---|---:|
| ITUK (UK trucks) | 6,974,170 |
| IUK (UK light commercial) | 6,062,956 |
| UTI (Israel trucks) | 3,098,114 |
| UMI (Israel light commercial) | 2,973,279 |
| ISD (Germany) | 2,913,663 |
| IBX (Benelux and Poland) | 2,296,577 |
| Imotors (Portugal) | 1,858,269 |
| RSA (Norway) | 1,764,800 |
| Isuzu Sverige (Sweden) | 1,464,302 |
| Isuzu Ireland | 1,267,443 |
| KTK (Komtranskomplekt) | 1,143,882 |
| Petros (Greece) | 574,432 |
| Loutsios (Cyprus) | 539,567 |
| MIDI | 357,733 |
| **Total, all lines** | **35,284,444** |

Those are the fourteen largest lines. The sheet also carries fifteen smaller named lines and one residual line
called OTHERS, which is EUR 4,591,445 and is a long tail rather than a market.

Two things about the shape. The plan is concentrated: ITUK and IUK together are EUR 13.0M, or 37% of it, and
the two Israel entities a further EUR 6.1M, or 17%. And the total includes MIDI, which file 01 treats as
outside ISZE's own totals by convention, so a reader comparing this total with a network figure in file 02
should take MIDI out first (EUR 357,733).

### 3.2 The plan by month

The plan is monthly, twelve columns running April to March. The first half of the fiscal year is almost exactly
level with the second half: EUR 17,698,617 against EUR 17,585,827. The months inside those halves are not
level with each other. ITUK shows the shape: EUR 599,343 in April, easing to the year's low of EUR 544,857 in
January, then the year's highest month at EUR 626,586 in March.

### 3.3 Where the plan came from

Source: `01_data/11_planning/FY2027 ISZE VP+IE Business Plan Waterfall 20263006.xlsx`, sheet `VP`, file date
2026-07-17. The FY2026 actual was **EUR 32,944,043** and the FY2027 plan is **EUR 35,284,444**, a rise of
EUR 2,340,401, or 7.1%.

The same sheet builds that rise lever by lever, from a small price increase at the bottom, through volume and
mix steps, to a remaining stretch at the top. The individual levers are deliberately not reproduced here. They
are planning assumptions that belong to the internal discussion, and a context file read by other people
should not carry them. What matters for reasoning is that the plan is not a flat continuation of the
historical trend: it assumes real growth, and it assumes it in named places.

### 3.4 The monthly cycle

`01_data/11_planning/(VP) Monthly report 2026-06.pdf`, file date 2026-07-05, 14 pages, is the monthly report.
There is one report per month, and this one covers June 2026, the third month of FY2027.

Its grain is **one row per market per month**, inside a fiscal-year-to-date table that carries the three months
of the quarter, the quarter total and the year-to-date total side by side. Each line carries: order amount,
sales amount, budget, sales target reached (the gap to budget as a percentage), original budget, original
budget reached, prior-year sales, and prior-year comparison. The markets with a page of their own are ITUK,
IUK, UTI, UMI, IBX, ISD, RSA, Imotors, Isuzu Sverige, Isuzu Ireland, BL. Ehf., Isuzu Danmark, Isuzu Finland,
GasanZammit, Petros, WAE, Isuzu Rom Auto, KIMA, Loutsios, Isuzu Armenia, Isuzu Kazakhstan and
Komtranskomplekt.

**Accessories are not covered in this report.** There is no accessory line and no accessory figure anywhere in
it. Every number on every page is vehicle parts. The accessory plan lives in a different file (see 3.6), and
the two should not be read as one report.

### 3.5 Target against actual, quarter one FY2027

From the same monthly report. Quarter one is April, May and June 2026, the first quarter of FY2027. Figures in
thousands of euro.

| Market | Q1 sales | Q1 budget | Versus budget |
|---|---:|---:|---:|
| ITUK | 1,390 | 1,716 | -19% |
| IUK | 1,663 | 1,473 | +13% |
| UTI | 1,037 | 753 | +38% |
| UMI | 644 | 723 | -11% |
| ISD | 696 | 708 | -2% |
| **ISZE total** | **8,611** | **8,596** | **+0.2%** |

The report's own quarter-one budget of EUR 8,596k is the same plan as the three plan months in the workbook
above: those three months add to 8,597 on the unrounded figures and print as 8,596 at the precision the report
uses, so the monthly plan and the quarter budget are the same plan.

Behind on the quarter, reading the whole report and not only the six rows above: ITUK at -19%, Finland at -27%,
Loutsios at -34%, Isuzu Rom Auto at -22%, WAE at -12%, UMI at -11%, Ireland at -8% and RSA at -7%. Ahead:
Isuzu Armenia at +101%, UTI at +38%, Isuzu Sverige at +24%, Petros at +15%, IUK at +13%, Komtranskomplekt at
+11% and IBX at +7%. The network closes the quarter EUR 15k ahead of budget, which is 0.2%, so the honest
reading of the quarter is level rather than ahead.

Two of the misses carry their own explanation in the report, and neither is a demand problem. ITUK came in
EUR 159k under budget on the month with EUR 165k of it sitting in work in progress that was invoiced on
1 July, so before that timing effect ITUK was at budget. UMI was held down by the halt of Shell lubricant
deliveries, which is a supply event rather than a verdict on the market. The one clear commercial win in the
quarter is UTI, where the first order under a special price agreement landed.

### 3.6 The accessory plan and its limits

Source: the same workbook as 3.1, sheet `ACC  FY27`, file date 2026-07-03. The FY2027 accessory plan is
**EUR 2,549,000** for the year. Only two markets are named: ITUK at EUR 30,000 and IUK at EUR 587,000. The
remaining **EUR 1,932,000**, or 76% of the plan, sits in one line called OTHERS.

So most of the accessory plan is a single unnamed line. A question that asks which market the accessory plan
is aimed at cannot be answered from this file, and accessory analysis by market is not possible on it. That is
a limit of the file, not a decision to hold anything back.

### 3.7 Operational targets

Source: `01_data/11_planning/ISZE_DB_KPI_Targets_FY2627_v1.xlsx`, sheets `Targets FY26-27` and `Assumptions`,
file date 2026-06-12. These are the service targets that sit beside the revenue plan.

- **Fill rate.** The network standard is **95%**, with a floor of **92%**. A market below 85% closes half the
  gap in FY2027 and reaches the standard in FY2028. Fill carries no macro adjustment.
- **Stock bands.** Days of stock are banded by how long parts take to reach the market: 60 to 75 days for a
  class A market within five days by road, 75 to 90 days for class B at five to twelve days by road or short
  sea, and 90 to 120 days for class C at three weeks or more by sea (Israel, Iceland, Malta, Cyprus,
  Palestine). A truck assortment carries 15 to 30 days more than a light commercial one because of range
  breadth. Above the band is idle working capital; below it is fill risk.
- **Dealer parts sales.** The FY2027 network target is **EUR 108,486,304** against **EUR 104,152,847**
  measured over the twelve months before the file was written, a rise of 4.2%. The file's own network total
  excludes the AIOS entity (Turkey), which is not an ISZE market.

### 3.8 What is deliberately not in this section

Four things are held out on purpose. Their absence is not an oversight.

- The EUR 661,000 of discounts and allowances in the FY2027 budget file
  (`01_data/11_planning/budget_per_DB_reviewed_24042026.xlsx`, file date 2026-07-03) is quotable as a total.
  The split behind it, which names individual distributors and the incentives each of them is on, is live
  negotiation material and stays internal.
- The parts gross margin for the plan year, and the accessory margin, sit in the planning workbook. They are
  not reproduced here.
- The individual levers inside the FY2026 to FY2027 waterfall are omitted. Only the two end figures are given.
- The per-customer competitive parts share that the monthly report prints on most distributor pages is not
  reproduced.

---

## 4. Decisions waiting on Jerome

These are not effort problems; each is a single answer. If a research answer needs one of these, the honest
answer is "this depends on a decision that has not been taken yet", not a guess.

| Ref | Decision | What happens without it |
|---|---|---|
| A | The ambition of the next price revision - about +4%, about +5%, or launch prices only | The revision stays a review list and never becomes a price move |
| B | What to assume for the 9,591 part numbers with no recent sales, when ranking by euro | Those part numbers stay out of every ranking |
| C | Whether to keep the current growth-factor assumption (about 1.24-1.25) | Forecast and allocation inherit an unsigned assumption |
| D | Guardrail policy: whether to hold automatically when a part is undercut by the independent aftermarket | Every exception stays manual |
| E | The account-health thresholds (same as open item 1) | The early-warning list stays advisory |
| F | Whether to go live on the forecast at 98.2% catalogue coverage, or wait | The forecast stays off |
| G | Who may adjust a forecast manually, and how that is audited | The forecast cannot go live even after F |
| H | The ITUK brake wear factor, 0.4 or 0.8 | Open item 6 stays open |
| I | Vintage labels for competitor price data shown to distributors | Shared output keeps mixed-vintage data unlabelled |
| J | An approved route for processing company mail text | Item 10 stays unbuilt |
| K | ITUK's real average annual mileage for the truck fleet. A draft mail to ITUK exists asking for it. Measured UK data says 16,688 km per year across classes and 35,478 for the 7.5-tonne class, against the 50,000 currently used | UK service demand stays presented on an overstated base (roughly 3x for the light class) |
| L | Access to the shared Sales and Parts mailboxes (a works council step) | The mail corpus stays half its potential size |

---

## 5. Closed - do not reopen

These were decided, or ruled out, or found to be dead ends. Re-proposing one of them costs credibility.

- **The Nordics tender API keys.** Done and verified. Do not raise it as an open item again.
- **Reviving the public web address for the dashboards.** The mirror holds commercial data and is kept local.
- **The old dashboard sandbox.** Closed.
- **Reading dealer sales as if it were end-customer demand across the network.** Only five distributors have
  shared dealer-level sales data. It is used where it exists, and its absence elsewhere is a source gap, not
  a finding.
- **A "no exceptions" statement where a source file is missing.** A missing file is an amber banner, never a
  clean result.
- **Treating the network total oil-filter capture as the story.** It is the best-covered category, not the
  problem.

---

## 6. Known problems with the data - the honest list

Read this section before answering any question that depends on the numbers in file 02.

**6.1 The fleet bases are not consistent between measures.**
The fleet count behind the target-spend ceiling and the fleet count behind spend-per-truck do not always
match for the same market and year. Ireland is the clearest case (2,161 versus 3,056 in 2025, which is why one
view shows 124% capture). Germany and ITUK also differ depending on whether the truck class split has been
applied. **Consequence: treat small differences in market ranking as provisional.** The direction and the
order of magnitude are reliable; the last few percent is not.

**6.2 The fleet forecast for 2026-2030 is not usable.**
The historical part of the fleet model (1990-2025) builds the fleet with a survival curve implying an average
vehicle life of about 9.9 years for trucks and 8.1 for pick-ups. The forecast part switches to a flat 3%
annual scrappage, which implies 33 years. So on 1 January 2026 the model has trucks suddenly living three
times longer, and the fleet grows in every market regardless of input. Three checks confirm it:

- Rebuilding Ireland from its own registration history reproduces the model exactly for 2025 (731 trucks),
  which proves the method is understood - and then the same engine run forward gives 1,645 light trucks for
  2030 against 1,382 on the proper method, 19% too high, and 3,174 pick-ups against 2,527, 26% too high.
- If Ireland registers 216 trucks a year forever, the fleet settles at about 2,100 under the survival curve
  and about 7,200 under the 3% rule.
- Measuring real scrappage from shipment data for the two markets that have real registration history gives
  about 10% a year (Ireland 13.3%, Portugal 7.4%), against the 3% assumed.

Also: the Israel fleet numbers are about a quarter too low in every year of the model, which was only found
when UTI shared government registration data. **Consequence: any statement about the fleet in a future year
is unsupported. Use the historical fleet only.**

**6.3 The euro service gap cannot be totalled externally yet.**
Any category where a market has zero actual sales books a zero gap - the worst outcome produces the
best-looking number. The file flags which cells are quotable; 39 of 252 cells in 2025 are not. Cover
percentages and unit counts are unaffected. See file 02 section 3.

**6.4 The price list exists at one date only.**
There is a single snapshot of the European price list (March 2026, 164,380 rows). Applying it backwards over
several years produces a series that looks like price leakage but is actually the 2026 price increase read in
reverse. **Consequence: any "revenue realisation" or "pocket price" waterfall is not leakage and must not be
presented as such.**

**6.5 About 15% of the billed book sits outside any price-list action.**
522 part numbers were billed with no price-list entry at all, worth EUR 4.96M - 15.1% of the 2025 revenue.
Another 800 part numbers worth EUR 1.82M were billed on numbers the list marks as superseded. These are data
problems, not pricing levers. Any price action discussed at network level cannot reach them.

**6.6 Dealer-level sales (what the dealer sold on to the customer) exists for five distributors only.**
Those five cover about 54% of the network's billed euro; with Germany, Belgium and Portugal they would reach
about 75%. **Consequence: end-market price elasticity cannot be measured for the network, and a distributor's
purchases measure their stocking behaviour, not customer demand.** Any claim about how customers respond to
price is an inference. Remember also that "sales to dealer" and "billed to distributor" are different things -
the first is what moved at dealer level, the second is what ISZE invoiced.

**6.7 Returns and credit notes.**
Credit and return lines are excluded from the parts base, the spend-per-truck figure and the service-demand
actuals. This is a **judgement call, not a confirmed rule** - the enterprise system has not confirmed it and is
not expected to soon. It is reversible. If someone later establishes that those codes mean something else,
the numbers move.

**6.8 The billing extract for the last quarter has no sales-type column.**
The April to June 2026 extract has no sales-type field, so the credit/return exclusion for that quarter is
based on value sign only. Coverage of that field overall is about 93%.

**6.9 Account-health data is five months behind.**
Its horizon is March 2026 while billing runs to June 2026, and the thresholds are uncalibrated. See file 02
section 8.

**6.10 Tender data is sparse in the two fields that matter most.**
315 of 376 opportunities have no deadline recorded and 374 have no value recorded. The useful subset is the
45 tagged as parts-relevant.

**6.11 One reference document in the workspace still carries the old 70% addressable-share assumption.**
The correct value is 100%. Nobody should compute cover from that document without checking. This is exactly
the kind of stale internal contradiction that makes a model's numbers disagree with the live pipeline.

**6.12 The part classification is complete, but its residual is real.**
Unclassified parts are now about 1.6-1.8% of revenue across 2024 and 2025 - about EUR 1.12M across 635 part
numbers, of which the top 100 are 90% of the value. Suggested classifications exist for them and have **not**
been applied; they need review. Do not treat them as fact.

**6.13 Where the same measure exists in two versions, the difference is usually a date, not a definition.**
The clearest example is the parts base (EUR 103.6M at 31 March 2026 versus EUR 112.1M at 30 June 2026 - same
method, one quarter apart). Before explaining a difference as a method change, check whether it is a cut-off
date change.

---

## 7. What would make the next answer better

If a research question needs one of these, say so plainly rather than working around it:

- A **measured per-model age-spend curve** from IML, to replace the flat EUR 250 placeholders that currently
  apply to eight of eighteen markets in the target-spend ceiling.
- A **fixed fleet projection method** (consistent survival curve), after which future fleet and future
  ceiling can be quoted.
- **Reconciled fleet counts** across the target-spend, spend-per-truck and service-demand models.
- **ITUK's measured annual mileage**, so the UK service-demand base stops being overstated.
- **Dealer-level sales for the remaining markets**, so end-market response becomes measurable rather than
  inferred.
- **Confirmation from the enterprise system** on whether credit and return lines should be excluded, turning
  a judgement call into a rule.
