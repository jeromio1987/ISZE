# Isuzu Universe without a discount

**The route if management does not approve the Excellence Partner discount: what we implement, what it costs, and what it can and cannot deliver** · White paper · internal draft v1 · 9 October 2026

Prepared by the ISZE parts-sales team with AI assistance. For management decision. It is the second of two papers: the first, *Isuzu Excellence Partner Program* (9 October 2026), sets out the discount. Our earlier papers called this route Plan B; in this paper it is called the Universe route.

---

## 1. Executive summary

**The decision.** If management does not approve a discount on stock orders, ISZE still needs sales-to-dealer data from its distributors, and it still needs a reason for them to send it. This paper proposes how to get both without paying more: ISZE implements Isuzu Universe, the programme that returns analysis to the distributor in exchange for a monthly file, and it uses the yearly rebate (the kickback) that already exists as the condition. Management is asked to approve the route, not a budget. The route needs no new cash in its base form. **[P]**

**Our recommendation, in one sentence.** Build the same foundation for both routes now, and decide on the discount later, with evidence from a trial, because most of the work is identical and only the incentive differs. The data standard, the intake and checking of files, the monthly return to each distributor and the quarterly check are needed whether or not a discount exists. A discount decision taken before the trial has produced any data would be taken blind. **[I]**

**What the Universe route is.** Three things are asked of a distributor: one price-free file a month (dealer, part number, period, quantity), a list that links each dealer name to a customer account, once, and one agreed action per review. In return the distributor gets a monthly review of its own business, built from data ISZE already holds, the dealer standards results of its own network in a form it can use, and a fixed set of rules on what ISZE will not do with the data. ISZE does not pay for the data. **[P]**

**Six numbers that decide how far this can go.**

| Number | Value | Source |
|---|---:|---|
| Parts billed to the 19 distributors in scope, FY2026 | €31.78M, of which stock orders €22.38M (70.4%) | `sales_fact.parquet` **[M]** |
| Share of that billing that sits with the nine distributors that have a kickback | 71.7% (74.1% of stock orders) | same, with the list of nine from the first paper **[M]** |
| Rebate credits booked in FY2026 | €430,030, of which €288,030 to eight of the nine kickback distributors and €142,000 to Isuzu Truck UK, which has no kickback | same **[M]** |
| What the data condition puts at risk today, if it is 20% of the kickback | about €57,600 a year (not €86,000, see 2.4) | arithmetic on the line above; the 20% and the contract are not in the workspace **[U]** |
| Distributors with a sales-to-dealer file in the workspace for FY2026 | 5 of 19, holding 55.3% of billing; only 3 of the 9 kickback distributors | `billed_vs_std_warranty_fy2026.csv` **[M]** |
| Universe's own score for the chance a distributor joins as designed | 55 out of 100 (dealer: 45) | Universe 3.0, chapter 8; a judgement, not a measurement **[M]** |

**What this means.** The condition we already have is real but small. It reaches the distributors that hold 72% of billing, and the money behind it averages about €7,000 per distributor a year. That is enough to get a file; it is not enough to get a good one. Isuzu Truck UK, the largest distributor (21.4% of billing), is outside it, and ten of the nineteen distributors have no condition at all. The Universe route therefore cannot rest on the condition alone. It rests on what the distributor receives each month, and on a short list of requests that cost nothing. It will deliver less participation than a discount would, and it will deliver it at a cost of internal time only. **[I]**

**What we recommend.**

1. **Approve the Universe route as the base route for FY2028** at no new cash, and run the January to March 2027 trial under it. **[P]**
2. **Authorise ISZE to rewrite the data condition in the kickback** for FY2028 so that it is paid on a written data standard, checked every quarter, instead of on a one-off submission. This needs the contract text and Japan's agreement, neither of which is in the workspace. **[P]**
3. **Approve recognition without a discount:** a named place in the programme and a short award session at the European aftersales meeting, with IMG in support. **[P]**
4. **Hold the €100,000 Universe cash route back** until the trial shows that distributors take part and a campaign can be named. At that point it is a separate, small decision with its own hurdle (chapter 7). **[P]**
5. **Name the people who answer.** Universe fails on the response, not on the data. Without a named owner and time for the monthly return, the route does not start (chapter 11). **[P]**

**What is not known.** There is no measured sales uplift from data sharing anywhere in the workspace. The contract text of the kickback is not here. No distributor has seen the Universe return or accepted it, and Universe's tests with real people are parked. A hosted shared service and real sign-in for Universe do not exist. A legal review has not been done. **[U]**

---

## 2. Purpose, scope and how to read this paper

### 2.1 Purpose

Management needs enough to decide whether the discount is the only way to get sales-to-dealer data, and what the alternative costs and cannot do. The same paper tells the developer what has to exist by April 2027.

### 2.2 Scope

In scope: the 19 distributors outside the CIS markets, parts only, euros, fiscal years. FY2026 is 1 April 2025 to 31 March 2026. FY2027 is 1 April 2026 to 31 March 2027. The first year of the programme is FY2028 (1 April 2027 to 31 March 2028). Out of scope: Ukraine, Armenia and Kazakhstan; the MIDI markets; accessories; the value of air freight.

UTI and UMI are never blended. Isuzu UK pickup (IUK) and Isuzu Truck UK (ITUK) are never blended. Ireland is not IUK. **Billed** means the parts invoiced to the distributor in the fiscal year, without credit notes, freight, service fees and rebate lines. **Stock orders** are the replenishment order type, the one a discount or a rebate would normally be tied to.

### 2.3 Evidence labels

| Label | Meaning |
|---|---|
| **[M]** measured | Counted in a named source file |
| **[I]** inferred | A conclusion drawn from measured data; the reasoning is shown |
| **[A]** assumption | A value we chose; it is not evidence |
| **[P]** proposal | A design or decision not yet taken |
| **[U]** unknown | Recorded as unknown, not filled with a guess |

An unlabelled number is an error in this paper.

### 2.4 What this paper corrects

Three points in earlier notes of ours are corrected or settled here. The first changes the case.

1. **The money at risk for data is about €57,600, not €86,000.** The first paper took 20% of all €430,030 of rebate credits. But €142,000 of that is Isuzu Truck UK, which has no kickback; its credit includes €30,000 for the dealer-defence programme. The kickback distributors received €288,030. Twenty percent of that is €57,606. Ireland is on the list of nine kickback distributors, but no rebate credit line for Ireland appears in FY2026 billing. Why is not known. **[M]/[I]**
2. **The workspace register is out of date, not the field.** The workspace holds a FY2026 sales-to-dealer file for five distributors. The August 2026 sales-review minutes record monthly files from Germany since May 2025 and agreements from Portugal, Greece and Ireland. Both statements can be true. The first job of this route is to find out which. **[M]**
3. **The kickback condition is described in two ways.** The Universe 3.0 paper says a share of the rebate is tied to a major-KPI submission. The Universe Yellow Paper and Jerome describe it as tied to sales-to-dealer information. Only the contract can settle which. **[U]**

---

## 3. The problem this route has to solve

### 3.1 What ISZE cannot see

ISZE sees what it bills to a distributor. It does not see what the distributor sells on. Without sales to dealer, ISZE cannot tell stock movement from lost sales, cannot see which dealer or part family is weak, and plans stock orders to Japan and Thailand on what distributors ordered, not on what dealers bought. Price reaction can only be measured from distributor to dealer, and only with two years of data, according to the decision of 11 August 2026; today two years exist nowhere. **[M]** (`DECISIONS.md`)

Three examples from the workspace show what the data changes.

- **Isuzu UK pickup, FY2026.** ISZE billed €5.95M and sales to dealer was €5.98M. The gap in the GPS figure (GPS is what we bill divided by the target spend per truck) was not destocking: €1.34M of the billing was warranty. Without sales to dealer the year looks like a decline; with it, it is not. **[M]** (`billed_vs_std_warranty_fy2026.csv`)
- **Isuzu Truck UK, brake pads.** Billing in the brake-pad category fell from €347,390 in calendar 2024 to €302,366 in 2025, down 13.0%, while recorded quantity fell 25.4%. Value fell less than volume, so a revenue-only reading suggests a demand problem and a quantity-only reading a pricing problem. **[M]** (Universe 3.0, chapter 3)
- **Portugal, clutch kits.** Combined Genuine and BVP billing rose 5.8% while Genuine alone fell. (BVP is Isuzu's value parts line, which is still ISZE revenue.) A Genuine-only view would have called for a recovery campaign on a line that grew. **[M]** (same)

### 3.2 What the route must achieve

The aim is not data for its own sake. It is a distributor that takes part, sends a file worth reading, and uses what it gets back to decide something. Universe states the test in one sentence, and we adopt it: **if the condition that produces the file disappeared tomorrow, would distributors keep sending it, because stopping would make their own review worse?** A route that only buys the minimum file fails that test. **[M]** (Universe Yellow Paper, D7)

---

## 4. The lever we already have

### 4.1 What sales-to-dealer data we hold

{{CHART:reach}}

The workspace holds a sales-to-dealer file for FY2026 for five distributors: Isuzu UK pickup (12 months), Ireland (12), Isuzu Truck UK (9, April to December 2025), Greece (9) and UTI (8, from August 2025). Together they hold €17.56M, or 55.3%, of billing. Only three of them have a kickback. The other six kickback distributors, Germany, Benelux, Norway, Sweden, UMI and Portugal, hold €12.50M of billing and have no FY2026 file in the workspace. **[M]**

Only one file anywhere carries dealer detail: Isuzu Truck UK for calendar 2025, with 64 dealers. Its 2026 file fell back to a network total. Isuzu Truck UK has no kickback. A condition is therefore not the only thing that produces data, and why that file arrived is not known. **[M]/[U]**

### 4.2 The kickback today

The billing ledger carries credit lines labelled "Rebate Material". In FY2026 they total **€430,030**, 1.35% of billing. **[M]** The credits split as follows.

| | Distributors | Credit lines FY2026 | Share of billing FY2026 |
|---|---:|---:|---:|
| Kickback distributors with a credit line | 8 | €288,030 | 71.7% of billing for the nine |
| Ireland, a kickback distributor with no credit line | 1 | €0 | (inside the 71.7%) |
| Isuzu Truck UK, no kickback | 1 | €142,000 | 21.4% of billing |
| Nine other distributors | 9 | €0 | 6.9% of billing |

The budget workbook that splits the kickback from other incentives is not in the workspace. The ITUK credit includes the €30,000 dealer-defence credit. **[M]**

Jerome states that the kickback is normally described as carrying a 20% share tied to the data. At the €288,030 the kickback distributors actually received, that is **about €57,600** for all of them, or **€3,400 to €19,000 each** (Isuzu UK pickup the largest at €19,000, then Norway at €9,400). It is 0.18% of billing. If the 20% is wrong, so is every figure in the next chapter that rests on it. **[I]/[U]**

{{CHART:stake}}

### 4.3 What this lever can and cannot do

It reaches nine distributors and 71.7% of billing. It does not reach the largest distributor and it does not reach the ten smaller ones. For those the only tools are a request, a return and recognition. For the nine it is a real condition, but small: a distributor with a €20,000 credit risks €4,000 for not sending a file that costs it staff time every month. Universe says this itself: a file sent to satisfy a condition is the minimum that satisfies it. **[I]**

One fact changes the starting point of the route. For six of the nine kickback distributors there is no FY2026 file in the workspace, even though 20% of their kickback is meant to depend on one. Either the files do not arrive, or they arrive and do not reach this workspace. If the existing condition is not being followed, a new one will not be either. This has to be settled before anything is tightened. **[I]**

---

## 5. What Universe is, and what exists today

### 5.1 The idea

Universe connects four things ISZE already holds: product knowledge and category pricing (AIM), the composition of the parts business, the dealer standards self-assessment (IDS, the dealer standards round) and market and fleet context (PRISM, the market and fleet model). It turns them into five tools a distributor or dealer opens by choice. The commercial argument is not that analysis is good. It is that the participant receives something it wants and therefore keeps supplying the context that makes the next answer better. **[M]** (Universe 3.0, executive summary)

| Tool | The question it answers |
|---|---|
| AIM Commercial Atlas | What is really changing in my parts business, and where? |
| IDS Development Studio | What should I improve, and what has moved? |
| Range & Campaign Planner | Which products belong in this initiative, and for whom? |
| Pricing & Margin Lab | What does this commercial trade-off do to revenue and margin? |
| PRISM Market Intelligence | Where should we concentrate effort? |

### 5.2 The boundary that makes it an offer

Routine availability enquiries, ordinary part and BVP lookups, quotation handling and day-to-day support stay in the existing business. They are not rewards for taking part and not bargaining instruments. The sentence that changes how a distributor reads the request is: *we are not asking you to feed a support desk, and the support desk does not get better or worse depending on what you send us.* The written rules of the route must say it. **[M]** (Universe 3.0, 1.2)

### 5.3 What exists

{{CHART:build}}

On 7 October 2026, 90 of 96 build tasks were technically verified, one more was implemented and five had not started. The five are the tests with real people. Technically verified means a named check was run and its output recorded, on made-up data; it does not mean a person accepted the result, and nothing is deployed. **[M]** (`progress.json` on the main branch, written 7 October 2026)

The internal version now also reads real data: tender notices, national fleet figures from PRISM, and the real dealer standards answers for Isuzu Truck UK (Ferndown) and Portugal (Astara Lisboa). Its "finished bar" was met on 7 October on the rules written for it. For competitor prices, the internal version relies on survey prices from Eucon (the price-comparison data source we already hold) and shows an honest note where shop prices are missing; by the evening of 7 October, 58 comparable UK shop offers for oil filters and brake pads and 162 for the wider range had passed the 50-row sufficiency bar. Stock is out of the first version, because it cannot be inferred from billing. **[M]** (`UNIVERSE_DECISIONS_2026-10-07.md`, `UNIVERSE_FINISHED_BAR_2026-10-07.md`, `UNIVERSE_EVENING_STATUS_2026-10-07.md`)

What does not exist is everything that makes Universe usable by someone outside ISZE. It is a single file opened on one machine. A small local server for case records was built and tested on made-up data, but there is no hosted shared service, no real sign-in (the request to IT is drafted and has not been sent) and no attachment storage. The tool says on every record that its identity is development-only. A browser-side check is not access control, and the prototype refuses an authenticated identity rather than inventing authority. No real distributor or dealer has used it, the tests with real people are parked, and the distributor premiere is still "no". Until sign-in and hosting exist and are independently reviewed, the first shared use is document-based and led by the distributor: files made per distributor, sent by a person. **[M]** (`DRAFT_IT_real_signin_request_20261007.md`; Universe 3.0, 10.2; finding F08 in `progress.json`)

---

## 6. The design of the Universe route

The route has six moves. The first costs nothing and has to come first.

### Move 1. Find out what the existing condition has already delivered

Before changing any rule, establish for each of the nine kickback distributors whether a sales-to-dealer file is sent, how often, in which shape, and where it lands. Germany is recorded as sending a file monthly since May 2025; Portugal, Greece and Ireland agreed to send monthly; none of this is in the register of files we hold. Update the register, then compare it with the credit lines paid. If the condition has not been applied, say so to ourselves before saying it to anyone else. **[P]**

### Move 2. One data standard

The standard is the one already specified for the discount route, because it costs nothing to share. One file per distributor per month: distributor, dealer and site identifiers, Isuzu part number, quantity (negative for returns), period, transaction type and file version, with a short declaration of what the file covers (dealer sites included, known exclusions, date range, whether returns are included). **No prices.** Received within ten working days after month-end. Dealer-level detail is a target for the first two quarters and a condition from the third. The full technical specification, with 18 validation rules, is in `TECH_SPEC_Partner_Intake_Phase0_2026-10-09`. **[P]**

Three things are not asked: selling prices, margins, customer names, chassis numbers, workshop orders or stock. They cost trust, are not needed, and prices raise a competition-law risk. **[M]**

### Move 3. Tighten the condition where one exists

For the nine kickback distributors, the proposal is to write the data condition into the kickback for FY2028 as a standard checked every quarter, with the share unchanged. The test is a quality standard (complete, on time, per dealer, declared), never a count of rows. This needs three things we do not have: the contract text, the incentive budget sheet (`budget_per_DB_reviewed_24042026.xlsx`), and Japan's approval, since bonuses follow Japan's approval and are scaled to targets. **[P]/[U]**

### Move 4. Ask the other ten, formally, and give something back

For the ten distributors without a kickback, including Isuzu Truck UK, the lever is a formal request together with the monthly return. There is a precedent in the workspace: Romania sent eight months of files two days after Jerome's formal request of 15 September 2026. It is one case, and Romania buys almost nothing as stock orders (under €1,000 of €185,934 billed), so it cost them little to say yes. **[M]/[I]**

### Move 5. Recognition, not a discount

A status for every distributor that meets the data standard for two consecutive quarters, shown at the European aftersales meeting with IMG, without a ranking and without a prize for the largest. Universe's rule is that status must not become a league table. Recognition costs time and no cash. Whether it moves a distributor is not known. **[P]/[U]**

### Move 6. Return first

The distributor must receive something in the same month it sends a file. One page per distributor already exists for all 19 in scope (22 files with the three CIS markets): what ISZE billed and what was sold on, genuine and BVP mix in euros, maintenance-parts coverage, IDS position. The monthly return adds dealer detail as it arrives, shows the distributor's own figures beside an anonymous network average, never ranks a distributor or a dealer, and never names another distributor. A distributor can correct what it reads and a correction replaces its predecessor with the change visible. **[M]/[P]** (`DISTRIBUTOR_ONE_PAGERS_2026-09`)

For dealers, the opening is not a request. It is their own dealer standards answers, in the real question wording, with a development priority they choose. Of 519 dealers on file, 490 have a recorded score (mean 79.3) and 29 recorded no answers; that is the one place where ISZE holds something a dealer will want to look at. Dealers are approached only through their distributor. **[M]** (Universe 3.0, chapter 8)

### Who goes first

| Where | Why | Condition today |
|---|---|---|
| Isuzu Truck UK | The only per-dealer file; real dealer standards answers on the internal tool; 21.4% of billing | None. Formal request and return |
| Portugal (I-Motors) | Dealer standards answers on the internal tool; clutch-kit case; agreed in principle on 29 July 2026 to send monthly | Kickback; €20,000 credit |
| Isuzu UK pickup, Ireland, UTI | Already have FY2026 files (12, 12 and 8 months) | Kickback; Ireland shows no credit line |
| Germany | Recorded in the minutes as sending monthly since May 2025; nothing in the workspace | Kickback |

**[M]/[P]** Isuzu Truck UK and Portugal are also the two markets Universe itself uses for its pilot.

---

## 7. What it costs

### 7.1 Cash

| Item | Cost | Note |
|---|---:|---|
| New discount | **€0** | None in this route |
| Kickback and defence credits | unchanged, €430,030 in FY2026 | The rewrite changes the condition, not the amount **[P]** |
| Build | **€0 cash** | In-house; the intake and checking of files runs on files and scripts, as in the technical specification |
| Universe cash route | **€0 in the base route** | The €100,000 route is held back (7.3) |

The cost of the team's own time is **not counted** and is not small. It is named in chapter 11.

### 7.2 Against the discount

{{CHART:cost}}

The first paper put the discount as the deck proposes it at €0.93M a year in year 3, 2.2 times today's rebates, and the small hybrid at €0.29M, 0.7 times. The deck design does not pay for itself in any of our three benefit cases, and the small hybrid pays back only in the High case. The Universe route adds no recurring cash. **[M]/[I]** (first white paper, ROI model; not recalculated here)

The saving is real and it is the only advantage that can be put in euros. What it buys is smaller too: participation is expected to be lower and thinner than a discount would buy, and recognition and returns cannot be checked against the kickback in the way a payment can.

### 7.3 The €100,000 Universe route, and why it waits

Universe proposes cash inside its €100,000 route: campaign support of €60,000 to €90,000 (with a minimum campaign of €150,000 of eligible billing), dealer enablement of €15,000 to €25,000 and an independent evaluation of €10,000 to €15,000. Its own hurdle is arithmetic on a hypothetical €2,500 contribution per qualifying action: 24 to 36 qualifying actions before internal cost to cover the campaign line, and about 40 to cover the whole €100,000. Universe says no realised return is evidenced, and the pilot is expected to produce a first measurement of how many qualifying actions occur, not a return. **[M]** (Universe 3.0, chapter 4)

We propose to leave it unfunded until the trial shows two things: that distributors take part, and that a named campaign meets the size filter. It then becomes a separate decision. This is the one place where the Universe route could cost money, and the paper does not ask for it now.

---

## 8. What it can deliver, and what it cannot

### 8.1 What to expect from distributors

Universe scores its own design, and the scores are the best expectation we have. They are judgements, not measurements. **[M]**

{{CHART:funnel}}

The gap between 75 (a distributor accepts the opening) and 45 (it uses the review) is the whole problem. The condition covers the first step. The second needs a review that answers a question the distributor already had. For dealers, the first prepared review scores 55, and the chance of a second eligible task only 30, with no cash and no recurring trigger. Sharing anything beyond a correction scores 20. Universe says it plainly: habit does not form on goodwill alone. **[M]**

### 8.2 What it cannot prove

Sales uplift cannot be proven within three years with the distributors we have, whatever the route. A distributor's billing moves by itself far more than the programme could cause: growth between distributors had a spread of 13.8 to 25.5 percentage points over FY2025 and FY2026, and a distributor that grew fast one year was no more likely to grow fast the next (correlation −0.11). With eight distributors in each of two groups, the smallest difference a one-year comparison could tell from noise is 19% to 29% of billing; the effects in question are 0.5% to 3%. **[I]** (first white paper, chapter 7; carried, not recalculated)

So the route is judged on what can be observed: files on time, dealers identified, valid part numbers, files that match billing, per-dealer detail, and **decisions taken on the data**, each logged with an owner, a date and the scope. Experiments below the distributor (half of a distributor's dealers or part families against the other half) are where a return could eventually be shown, and they need per-dealer data first. **[P]**

### 8.3 What the data is worth, without a promise

The price revision of +5% is worth €638,000 to €726,000 a year, depending on the weighting. Better dealer-level evidence could improve the next revision, but the size of that effect is not known. We do not attribute any share of it to Universe. **[M]/[U]** (`UNIVERSE_300K_GUARANTEE_TERM_SHEET`)

---

## 9. Delivery

### 9.1 Timeline

{{CHART:timeline}}

| When | What | Owner |
|---|---|---|
| Oct–Nov 2026 | Management decision on the route. Move 1: find out what the kickback condition has delivered. Get the contract text and the incentive sheet | Jerome |
| Nov–Dec 2026 | Legal review of the written rules. Data standard v1 to the distributors that already agreed to send monthly. Update the register of files we hold | Jerome, with legal |
| Dec 2026–Feb 2027 | Intake, checking of files and receipts built (prompts P01–P03). Fix one named version of the parts classification file. Two prepared views: product range and dealer standards profile | Developer, with AI |
| Jan–Mar 2027 | Trial with three or four distributors, under this route and without a discount: do clean per-dealer files arrive monthly, and what do we send back? | Jerome, Bart Symons |
| Mar 2027 | Written rules final; kickback wording agreed; recognition format agreed with IMG | Jerome, IMG, Japan |
| 1 Apr 2027 | Route starts (FY2028) | Jerome |
| End Jun 2027 | First quarterly check of the data condition (prompts P04–P06: reconciliation to billing, the check, the monthly return) | Jerome |
| Autumn 2027 | Review against the indicators. Decide: carry on, narrow, or return to the discount question with the trial's evidence | Management |

**[P]**

### 9.2 What is the same as the discount route

The first three build prompts (validator and receipts, intake and ledger, feed status) and the fourth to sixth (reconciliation to billing, quarterly check, monthly return) are common to both routes. The one difference is the output of the quarterly check. Under the discount it feeds a proposal for a credit. Under the Universe route it states whether the kickback's data condition is met. Nothing is posted in either; people post. **[P]** (`CURSOR_PROMPTS`)

### 9.3 What implementing Universe takes

Universe's tool is largely built on made-up data. What is left is mostly not engineering: decisions, a few lists, and people. In this order. **[P]**

| # | Step | Who | Why it comes here |
|---|---|---|---|
| 1 | Send the request to IT that asks how a real person is identified and how access is withdrawn (drafted on 7 October, not sent) | Jerome | Nothing can be shared outside ISZE before IT answers |
| 2 | Fix one named version of the parts classification file, with its build date | Developer, Jerome | Three candidate files exist and none is declared the authority; no family label may be shown to a distributor until one is |
| 3 | Make two prepared views for each pilot market: the product range and the dealer standards profile | Developer | The dealer's opening is its own answers, not a request. The real answers for Ferndown and Astara Lisboa are already in the internal tool |
| 4 | Get the dealer-name-to-customer-account list once for each pilot distributor | Distributor | It closes the gap that blocks any per-dealer view. For Isuzu Truck UK only 16 of 44 dealer standards names match the 64 names in the sales-to-dealer file exactly |
| 5 | Keep competitor prices to what can be stated: continue shop prices only where a page states delivery; otherwise show the Eucon-only note | Developer | Inventing a delivery cost would put a wrong price in front of a distributor |
| 6 | Run Universe's own tests with real people, in its fixed order (document review, one internal decision, two participant tasks, a later exchange, a handover), after the trial | Jerome names the people | Parked since 7 October; the names are deliberately blank |
| 7 | Ten dealers across two markets, approached through their distributor | Jerome, distributors | It is Universe's own first measurement: correction, usefulness, effort and reasons for not using it |
| 8 | Only then: hosting, real sign-in in production and the €100,000 route | Management, IT | They cost money and need evidence from steps 6 and 7 |

**[M]/[P]** (`UNIVERSE_ACCEPT_PARTICIPANT_ROSTER_2026-10-07.md`, `DRAFT_IT_real_signin_request_20261007.md`, Universe 3.0 chapter 9; the 16 of 44 match is in `SYNERGIE_Excellence_Partner_x_Universe_2026-10-09`)

Not in the first version, by decision: stock (it cannot be inferred from billing and no real stock file exists), routine availability enquiries (they are outside Universe by its own boundary), and anything that needs a distributor to sign in.

---

## 10. Measuring, and when to stop

### 10.1 Indicators, checked every quarter

| Indicator | Threshold we propose |
|---|---|
| Distributors that sent three consecutive clean monthly files | At least half of the first group after two eligible quarters |
| Per-dealer detail | At least four distributors by the end of FY2028 |
| File matches billing for the same months, with warranty shown apart | Within a tolerance to be agreed |
| Share of stock orders placed at quarter end (the early warning for buying ahead) | 31.8% in FY2026 against 25% if even (carried from the first paper); no rise |
| Decisions taken on the data, logged | At least two per participating distributor |
| Voluntary enrichment: something given that was not required | Counted, not required. The strongest signal Universe names |

**[P]** All thresholds are proposals to be agreed.

### 10.2 The stop condition

The route stops, or goes back to the discount question, if after two eligible cycles no participant can name a decision the data changed, or fewer than half of the first distributors deliver clean files, or a confidentiality or legal weakness appears that cannot be closed. It does not broaden the group to look for a better result, and it does not add a report. **[M]/[P]** (Universe 3.0, 9.3)

### 10.3 What would send us back to the discount

If the trial shows that distributors send the minimum and nothing else, or that the ten without a kickback do not respond to a formal request, then the discount is the only remaining lever, and management will then decide with a measured result in hand instead of a forecast. If the trial shows that distributors with a kickback deliver clean files and the others do too, the discount is not needed for data and the question disappears. **[I]**

---

## 11. Risks

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| 1 | The kickback condition is too small to matter (about €3,400 to €19,000 per distributor) and files stay minimal | high | high | Return first; the monthly return is the reason, not the condition | Jerome |
| 2 | The largest distributor and ten others have no condition | certain | high | Formal request with a return; recognition; the trial shows whether this works | Jerome |
| 3 | The existing condition is not being applied | medium **[U]** | high | Move 1, before any rule is rewritten | Jerome |
| 4 | Nobody answers: the monthly return and corrections have no owner or time | high | high | Name an owner and a time allocation before the route starts; Universe's own weakest link | Management |
| 5 | The kickback rewrite is not approved by Japan or conflicts with the contract | medium **[U]** | high | Contract text first; if not possible, the route continues as request-and-return only | Jerome |
| 6 | Competition-law challenge on a condition tied to data | low–medium **[U]** | high | Objective rules announced beforehand, no exclusivity, no price information, legal review | Legal |
| 7 | A distributor reads Universe as ISZE looking through it | medium | high | No prices, margins or stock; conduct rules in writing; the distributor controls interpretation | Jerome |
| 8 | Universe is not ready for outsiders: no hosted service, no real sign-in, tests with real people parked | certain | medium | Document-based first use; files made per distributor; the IT request for real sign-in is sent | Developer |
| 9 | Dealer data is poor or incomplete at first | high | medium | Declared coverage; gaps are source gaps, not weak sales | Developer |
| 10 | Participation stays at Universe's own 45 to 55 out of 100 | medium | medium | Indicators and the stop condition; the discount remains available | Management |

---

## 12. Decisions and open items

### 12.1 Decisions requested

1. **Approve the Universe route as the base route for FY2028.**
   *What it does:* it commits ISZE to ask for the data standard, return a monthly review and recognise participants, with no new discount. *Why:* it gives ISZE a way to start in April 2027 whatever happens to the discount. *Euro effect:* no new cash; the credits already paid (€430,030 in FY2026) continue. *Our recommendation:* yes, and run the January to March 2027 trial under it.
2. **Authorise rewriting the data condition in the kickback for FY2028.**
   *What it does:* it ties the 20% share (if that is the share) to the written data standard, checked every quarter. *Why:* today the condition buys a file, not a good file. *Euro effect:* none on the amount; at stake is about €57,600 a year in total. *Needs:* the contract text and Japan's agreement. *Our recommendation:* yes, once Move 1 shows what the current condition has delivered.
3. **Approve recognition at the European aftersales meeting, without a discount.**
   *What it does:* it names the distributors that meet the standard, without a ranking. *Why:* it is the only reward available at no cash cost. *Our recommendation:* yes, with IMG.
4. **Do not fund the €100,000 Universe route yet.**
   *What it does:* it leaves campaign support, dealer enablement and independent evaluation unfunded until the trial. *Why:* the hurdle is 24 to 36 qualifying actions and nothing yet shows that qualifying campaigns exist. *Euro effect:* €60,000 to €90,000 not spent now. *Our recommendation:* hold; revisit after the trial.
5. **Name the people who answer.**
   *What it does:* it gives the monthly return, corrections and distributor questions an owner and time. *Why:* the mileage question to Isuzu Truck UK was drafted on 18 September 2026 and, as of 21 September, had still not been sent; a response gap, not a data gap. *Our recommendation:* decide before the trial starts.

### 12.2 Open items

| # | Item | Needed from |
|---|---|---|
| 1 | Kickback contract text and the actual wording of the data condition (submission or sales to dealer); whether the share is 20% | Jerome |
| 2 | The incentive budget sheet, to separate kickback from other credits; why Ireland shows no credit line | Planning |
| 3 | Which distributors already send monthly files and in what shape; update the register of files we hold | Sales review team |
| 4 | Japan's position on rewriting the data condition | Jerome, Japan |
| 5 | Legal review of the written rules, including whether ISZE is dominant in any relevant market, non-EU regimes and the 2022 vertical guidelines | Legal |
| 6 | Where the files are dropped and who holds the access list | IT |
| 7 | Whether tests with real participants (parked on 7 October) start after the trial | Jerome |
| 8 | The cost of the team's own time, if management wants it shown | Jerome |

---

## Appendix A. Data standard, in short

One file per distributor per month, CSV or Excel, price-free. The mandatory fields: distributor identifier, dealer identifier, site identifier where relevant, Isuzu part number (leading zeros kept), quantity (negative for returns), reporting period (`YYYY-MM`), file version and a coverage declaration. Optional: transaction date, transaction type, a line identifier for corrections. Not asked: prices, margins, customer names, chassis numbers, workshop orders, dealer stock. A correction replaces its predecessor for the affected scope; an identical re-import adds nothing; annual controls are never added to monthly rows. The full specification, the 18 validation rules and the receipts are in the technical specification. **[P]**

## Appendix B. What the distributor gets back

| Return | Frequency | Decision it supports |
|---|---|---|
| Monthly review of billed against sold on, genuine and BVP mix in euros, maintenance parts covered | Monthly, after a usable file | Which accounts and ranges deserve attention |
| Product detail behind a movement | On a chosen case | Which references explain a change |
| Dealer standards profile per dealer | On request of the distributor | Where to direct network development |
| Tender opportunities qualified | On a qualified opportunity | Whether to pursue and what support to ask for |
| A receipt for every file | Every file | What to correct and how to resend |

**[P]** (Universe 3.0, 8.2; the technical specification, chapter 7)

## Appendix C. The two routes side by side

| | Discount route (first paper) | Universe route (this paper) |
|---|---|---|
| New cash | €150k in FY2028 rising to €400k (ceilings); small hybrid €0.29M in year 3 **[P]** | €0 in the base route; €60–90k later, if funded **[P]** |
| Reaches | All distributors in principle | Nine with a kickback by condition; ten by request |
| What buys participation | A payment | A return each month, recognition, and for nine a small condition |
| Expected participation | Higher, in our expectation: a payment buys the file **[A]** | Lower and thinner, in our expectation **[A]**; Universe scores 55 for distributors, 45 for dealers |
| Risk of paying for the minimum file | High | High, and cheaper to be wrong |
| Legal exposure | Rebate design, progressive bonus | Condition tied to data; no exclusivity |
| What is the same | The data standard, intake, checks, monthly return, quarterly check | |
| What we learn that we do not know today | Whether a payment moves participation | Whether a return moves it |

## Appendix D. Sources, and what was not read

**Measured in this paper** (script `plan_b_numbers.py`, from parquet and derived files, reproducible): billing by distributor and order type for FY2026, rebate credit lines, the split between kickback and other distributors, and the months of sales-to-dealer data per distributor. The totals reproduce the first paper's: €31,781,080 billed, €22,381,429 in stock orders, €430,030 in rebate credits. Files: `sales_fact.parquet`, `distributor_dimension.csv`, `billed_vs_std_warranty_fy2026.csv`, and the per-distributor table `planb_basis_fy2026.csv` next to this paper.

**Carried from other documents, not recalculated here:** the discount designs and their costs (`Excellence_Partner_White_Paper_2026-10-09`, the ROI model); the detection arithmetic (same, chapter 7); Universe's scores, hurdles and cash route (`ISUZU_UNIVERSE_3_0_2026-09-23`); the term sheet and the price revision (`UNIVERSE_300K_GUARANTEE_TERM_SHEET_2026-09-21`); the build progress (`05_AIM_Universe/progress/progress.json` on the main branch, 7 October 2026; the working folder on this machine was one merge behind and was not used for it); the decisions and status notes of 7 October 2026; the minutes of the August 2026 sales reviews and of 29 July 2026 with Portugal.

**Not read, and unknown:** the kickback contract; the budget workbook with its incentive sheet; the legal position on a condition tied to data outside the EU motor-vehicle block exemption (valid to 31 May 2028 as extended); the cost of the team's time; any distributor's reaction to Universe.

## Appendix E. Plain terms

**Kickback:** the yearly rebate paid to certain distributors on parts purchases. **Sales to dealer:** what a distributor sells on to its dealers, without prices. **Stock order:** the replenishment order type. **GPS:** what ISZE bills divided by the modelled target spend per truck. **BVP:** Isuzu's value parts line. **IDS:** the dealer standards self-assessment round. **PRISM:** the market and fleet model. **AIM:** the product classification and category-pricing work. **Receipt:** the answer sent for every file received. **Fiscal year (FY):** 1 April to 31 March.
