# Isuzu Excellence Partner Program

**The case, the economics and the design** · White paper · internal draft v1 · 9 October 2026

Prepared by the ISZE parts-sales team (Jerome, Bart Symons) with AI assistance. For management decision and for the developer who builds what the programme needs. Language rules, sources and the prompt that produced this paper are in the appendices.

---

## 1. Executive summary

**The decision.** Management is asked to approve three things: the concept of an Excellence Partner Program for independent, multi-brand distributors; a cost ceiling per year; and a staged start on 1 April 2027 (the first day of FY2028), released stage by stage on measured indicators. It is not asked to approve a proven return, because none can be shown today.

**What the programme is.** ISZE offers distributors a discount on **stock orders only** in return for taking part: sending monthly sales-to-dealer data and KPIs, running the dealer-standards round (IDS), and following the trainings. Level 1, Partner, is about −2.5% on stock orders. Level 2, Excellence Partner, is about −5% and adds a result score. Eligibility is checked every quarter, and the discount code is then set in SAP. It comes on top of the kickback that exists today. Distributors are independent and sell several brands, so ISZE cannot force them; the discount is the one lever it has. **[P]**

**Four numbers that decide the case.**

| Number | Value | Source |
|---|---:|---|
| Stock orders of the 19 distributors in scope, FY2026 | €22.4M of €31.8M billed (70%) | `sales_fact.parquet` **[M]** |
| Cost of the discount as the deck proposes it, year 3, all 19 in | €0.93M a year, 2.2 times the €0.43M of rebates paid today | model, rebate credits in billing **[M]/[P]** |
| Extra sales the deck design must create to pay for itself | 6.7% of the participants' billing, on top of a plan that already grows about 5% | model **[I]** |
| Normal year-to-year swing in a distributor's billing | ±14% to ±26% | `gps_clean_all_fy_v2.csv` **[M]** |

**What this means.** The discount as written in the deck does not pay for itself on any benefit assumption we can defend, and the benefit cannot be proven inside three years, because a distributor's own yearly movement is several times larger than the effect the programme could cause. The honest framing is that the discount **buys participation**, and participation is what makes ISZE's analysis possible. That is a cost-of-capability decision, not a return-on-investment decision, and management should be shown it as one.

**What we recommend.**

1. **Approve the concept, with a progressive "small hybrid" instead of the flat discount.** A small flat part (0.5% level 1, 1% level 2) keeps a visible reward for taking part; a progressive bonus on growth only (bands of 0–5%, 5–10% and above 10%, each paying a higher rate on the stock orders inside that band) links most of the money to results. Year-3 cost is €0.29M, 0.7 times today's rebates; break-even is 2.0% extra sales. **[P]**
2. **Set a cost ceiling and release it in stages:** up to €150k in FY2028, €350k in FY2029, €400k in FY2030, each year released only when the previous year met its measured indicators (chapter 11). **[P]**
3. **Start with the seven distributors that already send data,** run a no-discount trial with three or four of them in January–March 2027, and launch level 1 on 1 April 2027. Level 2 follows after the first full year. **[P]**
4. **Make the data standard part of the offer.** Price-free sales to dealer per dealer and per part, monthly within ten working days, with a declaration of what the file contains. Without that standard, the discount buys the minimum file. **[P]**
5. **Measure what can be measured.** Sales uplift cannot be proven statistically (chapter 7). Measure data quality, dealer coverage, mix, order-type shift, and evidence of decisions taken on the data, and run dealer-level or part-family experiments where the data allows it. **[P]**

**What is not known.** There is no measured uplift from data sharing anywhere in the workspace; the Low, Base and High benefit cases are our assumptions. The contract text of the kickback and the budget workbook with its incentive sheet are not in the workspace. The cost of internal time is not counted. Air-freight savings from moving rush orders to stock orders are left out on purpose. A legal review has not been done.

**Companion material.** The ROI model (Excel, live formulas), the 90-second film and the earlier analyses sit in the same folder. They agree with this paper; where an earlier analysis said otherwise, chapter 3 and appendix G say what changed.

---

## 2. Purpose, scope and how to read this paper

### 2.1 Purpose

Two readers use this paper. Management needs enough to decide, and enough to defend the decision to Japan and to distributors. The developer needs to know what has to exist by April 2027 and why. Chapters 1–8 and 10–11 are for the first reader; chapter 9 and appendices A, B and E are for the second.

### 2.2 Scope

In scope: the 19 distributors outside the CIS markets, parts only, stock orders only, euros, fiscal years. FY2026 is 1 April 2025 – 31 March 2026. FY2027 is 1 April 2026 – 31 March 2027. The programme's first year is FY2028 (1 April 2027 – 31 March 2028). Out of scope: Ukraine, Armenia and Kazakhstan; MIDI markets; rush and VOR orders; accessories; the value of air freight; the kickback's own terms.

UTI and UMI are never blended. Isuzu UK pickup (IUK) and Isuzu Truck UK (ITUK) are never blended. Ireland is not IUK.

### 2.3 Evidence labels

Every substantive claim carries one of five labels, borrowed from the discipline used in the Universe papers.

| Label | Meaning |
|---|---|
| **[M]** measured | Counted in a named source file |
| **[I]** inferred | A conclusion drawn from measured data; the reasoning is shown |
| **[A]** assumption | A value we chose; it is not evidence, and the paper says what changes if it is wrong |
| **[P]** proposal | A design or decision not yet taken |
| **[U]** unknown | Recorded as unknown, not filled with a guess |

An unlabelled number is an error in this paper and should be read as one.

### 2.4 What this paper corrects

Two earlier statements by the same team are corrected here. First, an earlier synergy note said no sales-to-dealer file exists for Germany, Benelux, Sweden, Norway and UMI. That described the **workspace register**, not reality: the August 2026 sales-review minutes record that Germany (ISD) sends part number, quantity and date monthly since May 2025, and that Greece, IUK, Ireland and Portugal agreed to monthly feeds without prices. The register is out of date; chapter 3 sets out what is known and unknown. Second, the first version of the ROI model assumed a €100,000 running cost; that is set to zero because the programme is built and run in-house, and the paper states the cost of internal time as not counted.

---

## 3. The problem

### 3.1 A weak lever on independent distributors

ISZE sells parts to distributors that are independent businesses and sell several brands. A distributor can order Isuzu parts, buy from an aftermarket supplier, or do both, and it decides what to stock, what to push at its dealers, and what to report. ISZE can ask for data, and for part of the distributors it ties a share of the rebate to it. It cannot require good data, correct data or timely data in any way that a distributor cannot satisfy at minimum effort. Universe's own papers put it precisely: a file sent to satisfy a condition is the minimum that satisfies that condition.

### 3.2 What the data is for

ISZE sees what it bills to a distributor. It does not see what the distributor sells on. Without sales to dealer, ISZE cannot tell stock movement from lost sales, cannot see which dealer or which part family is weak, cannot measure how price changes reach the dealer, and plans stock orders to Japan and Thailand on what distributors ordered, not on what dealers bought. The decision of 11 August 2026 allows price reaction to be measured only from distributor to dealer, and only with two years of data; today that is not possible anywhere. **[M]** (`DECISIONS.md`).

One example from the workspace shows what the data changes. For Isuzu UK pickup in FY2026, ISZE billed €5.95M and sales to dealer was €5.98M. The gap in the GPS figure was not destocking: €1.34M of the billing was warranty. Read without sales to dealer, that year looks like a decline; read with it, it is not. **[M]** (`billed_vs_std_warranty_fy2026.csv`).

### 3.3 What ISZE has today

| Distributor | Kickback today | Sales to dealer in the workspace | What the sales-review minutes say (Aug 2026) |
|---|---|---|---|
| Isuzu Truck UK | no | Per dealer, 2025 only (64 dealers, 224,001 units); 2023, 2024 and 2026 are network totals | not in the minutes read |
| Isuzu UK pickup | yes | Network total, 2025 and 2026 to July | Automated monthly feed, part number and quantity, no customer or price, from January 2025 |
| Ireland | yes | Network total, 2025 and 2026 to July | Sent to 20 Nov 2025; to resend and continue monthly |
| UTI | yes | Network total, 2025 (Feb–Jul missing) and 2026 | not in the minutes read |
| Portugal | yes | Network total, 2025 and 2026 | Agreed in principle (29 Jul 2026), once the extraction is confirmed |
| Greece | no | Network total, 2025 | Agreed ask: part number, quantity and date, no prices, monthly, from January 2025 if possible |
| Romania | no | Network total, 2026 January–August | Sent after the formal request of 15 Sep 2026 |
| Germany | yes | **Nothing in the register** | Monthly from May 2025: part number, quantity, date |
| Benelux, Sweden, Norway, UMI | yes | Nothing in the register | **[U]** not in the minutes read |
| Cyprus, Hungary, Finland, Malta, Denmark, Iceland, Palestine | no | Nothing | **[U]** |

**[M]** for the workspace columns (`dealer_sellout_long_*.csv`, `DATA_MANIFEST.md` §05); **[M]** for the minutes (`05_memory/briefs/sales_reviews_Koen_2026-08-05_06.md`, `MINUTES_ISZE_Astara_Portugal_2026-07-29.md`).

{{CHART:coverage}}

Three things follow. **[I]**

1. **Per dealer, ISZE has one year of one distributor.** Everything else is a total for the whole network of a distributor, which cannot show which dealer or which part family is weak.
2. **ITUK shows the risk of a one-off file.** The 2025 file had dealer detail; the 2026 file fell back to a network total. Dealer detail is not yet a habit anywhere.
3. **The register does not reflect the field.** Several distributors have agreed to monthly feeds that are not yet in the workspace. Closing that gap costs nothing and should come before any discount is promised.

### 3.4 The kickback today

The billing ledger carries credit lines labelled "Rebate Material". In FY2026 they total **€430,030**, 1.35% of the €31.8M billed to the distributors in scope. **[M]** (`sales_fact.parquet`).

| Distributor | Rebate credits FY2026 | As % of billed |
|---|---:|---:|
| Isuzu Truck UK | €142,000 | 2.1% |
| Isuzu UK pickup | €95,000 | 1.6% |
| Norway | €47,136 | 3.2% |
| UTI | €34,000 | 1.1% |
| Germany | €29,600 | 1.1% |
| Benelux | €25,200 | 1.2% |
| Portugal | €20,000 | 1.1% |
| UMI | €20,000 | 0.7% |
| Sweden | €17,094 | 1.3% |
| **Total** | **€430,030** | **1.35%** |

These lines mix the kickback with other incentives: ITUK's €142,000 includes the €30,000 credit of the dealer-defence programme. The budget workbook with its incentive sheet (`budget_per_DB_reviewed_24042026.xlsx`) is not in the workspace, so the split cannot be made. The sales-review minutes add that bonuses follow Japan's approval and are scaled to targets; one distributor's bonus is quoted at about €37,000 with a stretch of +1.8% above base. **[M]**

Jerome states that the kickback is normally described as carrying a 20% share tied to sales-to-dealer data. At €430,030 that is **about €86,000** a year that ISZE already puts at risk to obtain the data. The contract text is not in the workspace, so this is stated, not verified. **[U]**

Distributors that do not provide the data are due to lose the kickback; that condition is still being communicated to them. The Excellence programme is the carrot that goes with that stick.

### 3.5 How big the prize is

Three numbers set the size, and none is a forecast.

- Network parts billed in calendar 2025 were €30.8M against a modelled target spend per truck of €54.4M, a GPS of 56.5%. The €24.0M difference is a ceiling, not recoverable sales. **[M]** (`wallet_waterfall.csv`, `FACTS.md`)
- The modelled revenue gap in service parts (PMS) in 2025 is €20.1M across 18 distributors; the same caveat applies. **[M]**
- The price revision of +5% is worth €638,000 to €726,000 a year, depending on the weighting. **[M]** (`UNIVERSE_300K_GUARANTEE_TERM_SHEET_2026-09-21.md` §2)

A programme that raised capture by one percentage point of the €24.0M ceiling would add €240,000 in billing. That is the order of magnitude, and it is the reason the case rests on participation and not on promised euros.

---

## 4. The proposal as received

### 4.1 What the deck proposes

The deck "Isuzu Excellence Partner Program" has 13 slides. It builds one recognition model on seven pillars worth 100 points: dealer standards and brand representation (20), parts business performance (20), training and knowledge (15), digitalisation (15), Kaizen (15), customer support and aftersales (10), collaboration and reporting (5). Five mandatory gates (all mandatory trainings; a complete IDS evaluation of the network; monthly KPI and SPI reporting; a documented Kaizen plan with evidence; no critical compliance or safety issue) must all be met, and the score must be at least 85. Below 84 a distributor is a Development Partner. From 85 to 94 it is an Excellence Partner with 2.5% off stock. From 95 to 100 it is an Outstanding Performance Partner with 5% off stock. Targets are market-adjusted, the assessment separates what the distributor controls from what ISZE or Japan controls, and status is reassessed every year. A parts competition rewards winners; the partner status rewards every distributor that qualifies. All criteria are proposals pending ISZE approval.

### 4.2 What is strong

- It joins things that run separately today: IDS (action-plan rows 67–72), distributor training (23–26), the parts competition (27–33), genuine share (34–51), KPI (52–53) and the yearly incentive (7–8). **[M]** (`vpacc_fy2027_action_plan_july.parquet`)
- Gates come before points. Strong sales cannot make up for missing training or standards.
- It separates a competition from a status. A status that every distributor can earn is a better tool for broad participation.
- It names fairness: targets set per market, controllable outcomes separate from the rest, yearly reassessment.

### 4.3 What does not work yet

| Issue | Evidence | Consequence |
|---|---|---|
| **The 85-point bar excludes the people we want to attract** | IDS network average 81.1%; three distributors at or above 85% today (Malta 89.3%, Portugal 86.8%, Hungary 86.4%) | In year 1 almost nobody qualifies. A programme meant to bring distributors in must have an entrance they can reach. |
| **IDS is a self-assessment** | Parsing rules in `IDS_2026_LOGIC_CHECK.md`; ITUK has totals only; August 2026 scan found no defensible link between IDS score and parts sales | Tying money to a score the distributor writes invites a higher score. IDS must count as improvement and follow-up, not as a raw score. |
| **IDS did not run everywhere** | No IDS 2026 for Germany, Ireland, UTI, Sweden, Finland, Iceland; none for the CIS markets | A gate of "complete IDS evaluation" fails Germany (€2.7M billed) and Ireland (€1.1M) because of ISZE's planning, not their performance. |
| **Parts performance weighs only 20 of 100** | | A distributor with falling parts sales can reach Excellence. |
| **Double counting** | IDS in pillar 1, pillar 5 and a gate; genuine/BVP in pillars 2 and 6; EQ-Hit and EDI in pillars 3 and 4 | A criterion should score once. |
| **Training did not exist** | Curriculum "started" (row 23); contents, trial and rollout not yet started | Resolved by the decision that it is ready in April 2027. |
| **Several criteria have no scale** | "Active business development", "constructive cooperation" | Each criterion needs a definition, source, owner, frequency, evidence and scale (appendix B). |
| **Inconsistencies** | Slide 5 says 70% IDS participation, slide 8 a complete IDS evaluation; 84–85 gap between levels; "critical compliance" undefined | Corrections listed in appendix B. |

**[M]/[I]** from the deck, `study_payload.json` files and the action plan.

### 4.4 Fill rate and stock cover

Fill rate and months of stock (MOS) are the two operational KPIs the deck uses. First fill rate, average of available months: UMI 97.0%, Norway 95.9%, ITUK 94.9%, IUK 93.8%, Romania 88.5%, Malta 87.7%, Benelux 84.5%, Greece 60.0%. Portugal, Hungary and Cyprus have no KPI row. MOS runs from 47 days (Benelux) to 147 days (UMI). **[M]** (`kaizen_db_posture/study_payload.json`). Two cautions. A high fill rate with 147 days of stock rewards overstock. And part of a distributor's fill rate depends on ISZE's own supply from Japan and Thailand, which the deck acknowledges but does not yet turn into a rule.

---

## 5. The design

The concept is settled by Jerome's decisions of 9 October 2026: the discount applies to stock orders only; it comes on top of the kickback; it is ISZE's concept with IMG in support; all distributors in principle, CIS out; no budget ceiling set by management yet; training ready by April 2027; no extra cash running cost. What follows is the design we propose within that concept. **[P]**

### 5.1 Two levels with different jobs

| | Level 1, Partner | Level 2, Excellence Partner |
|---|---|---|
| Purpose | Be in: take part in what ISZE cannot force | Be good: take part and deliver a result |
| Discount on stock orders | Small flat part plus progressive bonus on growth (see 6.2) | Larger flat part plus larger progressive bonus |
| Measured by | ISZE, from what arrives: dates, completeness, validity | ISZE (billing, business plan) with IMG support for IDS |
| Checked | Every quarter | Every year; level 1 conditions keep being checked every quarter |
| Entry | Gates only, no score | Level 1 plus a score of at least 85 on results |

The point of the two levels is that the entrance is reachable. A distributor that sends clean data, reports its KPIs, completes the IDS round that ISZE planned for it and follows the trainings is in. Only then does a result score decide who earns the larger reward.

### 5.2 Level 1: the gates

All four must be met in the quarter checked.

1. **Sales to dealer, monthly.** One file per month in the data standard (appendix A), received within ten working days after month-end, covering all dealers, price-free, with a declaration of what it contains. For the first two quarters per-dealer detail is a target; from the third it is a condition.
2. **Dealer list, once and then kept up to date.** Dealer identifier, site identifier, name, location and the SAP customer number where one exists. Closed or renamed dealers keep their identifier.
3. **KPIs, monthly.** First fill rate, MOS, stock value and open back orders by part.
4. **IDS and trainings.** The IDS round that ISZE and IMG planned for that distributor, with at least 70% of its dealers; the mandatory trainings followed by the named staff (from April 2027).

What the distributor can count on: if ISZE has not planned IDS for a distributor, that is not held against it.

### 5.3 Level 2: the result score

A distributor at level 1 enters the result score, 100 points, 85 to qualify. The deck's seven pillars are kept in the sense that every one of them is either a gate or a scored block, but each criterion counts once.

| Block | Points | What | Source |
|---|---:|---|---|
| Parts performance | 35 | Parts sales against the reviewed business plan (20); genuine share in euros not lower than last year (10); fill rate corrected for ISZE's own supply, with MOS as a limit (5) | Billing, business plan, KPI file |
| Dealer network | 20 | IDS improvement since the last round (10); share of dealers with closed improvement actions (10) | IDS, follow-up sheet |
| Knowledge and digital | 20 | Right order types, stock against rush (5); EDI or equivalent active (5); training passed on to dealers (10) | Billing, ISZE IT, training register |
| Kaizen | 15 | Yearly plan with at least three actions, owner, date and evidence, scored on closed actions | Kaizen template (to build) |
| Aftersales and collaboration | 10 | R&M, extended warranty and roadside, step by step; one agreed action per review with its follow-up | Distributor reporting |

IDS counts as improvement and follow-up, not as an absolute self-score. A sample of dealers can be visited by IMG; where the visited score differs strongly from the self-score, the visited score counts. **[P]**

### 5.4 The data standard

The mandatory data stays narrow and price-free. It says what part moved, to which authorised dealer, when and in what quantity. It does not try to rebuild the distributor's ERP. The full specification is appendix A; the principles are these.

- **Identifiers matter more than extra fields.** A dealer must not appear as three different names in three months. The distributor keeps the dealer identity; ISZE keeps the mapping across periods.
- **Coverage is declared, not guessed.** Each file carries a small control record: number of dealer sites, known exclusions, first and last date, whether returns are included, whether the full range is covered, and any change that affects comparison with earlier months. Missing data is a source gap, never a weak result.
- **Corrections are visible.** A period can be resubmitted; the original is kept and the new version marked active.
- **Not asked:** selling prices, margins, customer names, chassis numbers, workshop orders, dealer stock. These cost trust, are not needed, and prices raise a competition-law risk. Further data is invited, not required, and only when ISZE can say what it returns (chapter 8).

### 5.5 What the distributor gets back

Participation is only kept if it pays back in the same month. Each month the distributor receives, in the format of the existing distributor one-pagers: what ISZE billed and what was sold on; the genuine and BVP mix in euros; maintenance-parts coverage; IDS position; and, once dealer detail arrives, the same per dealer. It shows the distributor's own figures beside an anonymous network average. There is no ranking of distributors and no ranking of dealers. A distributor can correct what it reads, and a correction replaces its predecessor with the change visible. **[P]** (`Universe_Commercial_Participation_Model.md`, `UNIVERSE_VALUE_EXCHANGE_MODEL_2026-09-21.md`).

### 5.6 The quarterly check and the SAP condition

Every quarter a job reads what arrived, applies the gates, and produces an eligibility table per distributor: gate by gate, with the evidence. Jerome approves the table; exceptions are written down with a reason. The result becomes a discount code in SAP for the following quarter. A distributor that stops meeting a gate loses the discount from the next quarter, which is the one pressure ISZE can apply without forcing anything.

One decision is open: whether the discount is an invoice condition (the net price falls) or a credit note after the quarter (the list price stays). The cost is the same. The effect on reporting is not: an invoice condition lowers billed euros and therefore GPS and the %GM reading of the price list; a credit note leaves them intact and follows how rebates are already treated, outside the parts base. We recommend the credit note. **[P]**

### 5.7 Guards against gaming

| Risk | Guard **[P]** |
|---|---|
| Forward buying: a distributor stocks up before a quarter ends | Discount applies to stock orders up to 120% of the trailing four-quarter average; the quarter-end share of stock orders is monitored (31.8% in FY2026 against 25% if even) **[M]** |
| Returns after the discount | A credit note within 90 days reverses the discount on those lines |
| Moving rush or VOR orders to stock orders only for the discount | Rush and VOR margin is higher (49.0% and 54.1% against 45.9% for stock orders **[M]**, Q1 FY2027 SAP cost, one quarter); track the shift in order mix per quarter |
| Inflated IDS self-scores | IDS counts as improvement and follow-up; sample visits |
| A file that satisfies the format but carries no information | Validation checks (appendix E): dealer coverage, valid part numbers, reconciliation to billing within a tolerance |
| Warranty in the base | Warranty lines excluded from the discountable base; to confirm with SAP owners **[U]** |

### 5.8 Rules of conduct and competition law

The Universe papers set conduct rules that this programme adopts: no exclusivity in exchange for information, no price coordination between distributors, no resale-price instruction, no direct approach to a dealer without the distributor, no public league table. The discount is not a condition on ordinary service: delivery times, BVP availability, quotations and standard support stay equal for every distributor. That sentence belongs in the written rules of the programme.

**Legal position.** The EU motor-vehicle block exemption (Regulation 461/2010) was extended by Regulation 2023/822 to 31 May 2028, and the Commission began its evaluation on 18 January 2024. Quantity rebates tied only to volume are not in themselves treated as abusive under the case law the research found (Post Danmark II); loyalty-inducing rebates by a dominant firm are treated far more strictly, and effects are assessed on all circumstances, including the criteria that govern the grant. Our design pays on stock orders and on growth, and requires data and standards that are objective, announced in advance and the same for every distributor; it contains no exclusivity or share-of-purchase condition. Whether ISZE is dominant in any relevant market, how the UK, Norwegian, Israeli and other non-EU regimes apply, and what the 2022 vertical guidelines say on non-linear pricing were **not read** and are **[U]**. Nothing here is legal advice. Legal must review the written rules before they reach a distributor. (Sources: appendix G.)

---

## 6. The economics

### 6.1 The base we calculate on

| Item | Value | Source |
|---|---:|---|
| Billed to the 19 distributors in scope, FY2026 | €31.78M | `sales_fact.parquet`, credit notes, transport and rebates excluded **[M]** |
| of which stock orders (SaTy SOR) | €22.38M, 70.4% | same **[M]** |
| other order types | production-type PRD 11.6%, VOR 11.4%, rush 6.3% | same **[M]**; the meaning of PRD could not be confirmed **[U]** |
| Share of the four largest in stock orders (ITUK, IUK, UTI, UMI) | 60% | same **[M]** |
| Gross margin on billed, Q1 FY2027 | 46.8% (stock orders 45.9%) | `q1fy2027_export_with_saty.csv`, SAP cost, one quarter **[M]**, indicative |
| Rebate credits booked FY2026 | €430,030 (1.35% of billed) | billing lines **[M]** |
| Plan growth, reviewed business plan FY2027 against FY2026 billed | about +4.7% | `bp_fy27_reviewed.json` **[M]** |

The 46.8% rests on one quarter and on a SAP cost that is not complete for every line; treat it as indicative.

### 6.2 Five ways to pay

All five are modelled on the same participation plan: seven distributors in year 1 (FY2028), thirteen in year 2, nineteen in year 3, with level 2 for some from year 2. The plan is illustrative and editable in the model. **[A]**

1. **Deck:** a flat 2.5% (level 1) or 5% (level 2) on all stock orders.
2. **Growth only:** the same rates, only on stock orders above last year's.
3. **Hybrid small:** flat 0.5% / 1.0% on all stock orders, plus a progressive bonus on growth. Each band pays a higher rate, and only on the stock orders inside that band, like tax brackets. Level 1 pays 2%, 3% and 5% for growth of 0–5%, 5–10% and above 10%; level 2 pays 4%, 6% and 10%.
4. **Hybrid bigger:** flat 1.5% / 3.0%, bonus rates 3%, 5%, 8% (level 1) and 5%, 8%, 12% (level 2).
5. **Tiered:** a rate on **all** stock orders that steps up with the distributor's own growth: 1% below 0%, 2% to 5%, 3.5% to 10%, 5% above.

{{CHART:ladder}}

The chart shows why design 5 is not what it seems. It pays on everything, with a jump at each limit, so a distributor whose growth lands just above a limit earns a lot more than one just below. Between distributors the yearly growth differs by about 14 percentage points (chapter 7); where a distributor lands is therefore partly luck, and the programme would pay out on noise.

### 6.3 Cost

{{TABLE:designs}}

**[P]** for all rows; the cost is arithmetic on FY2026 stock orders. The growth-based designs (2–5) assume stock orders grow at the planned rate and measure growth year on year. Cost excludes internal time and any build cost, both set to zero by decision.

{{CHART:cost}}

Against the €430,030 of rebates paid today, the deck design costs 2.2 times as much in year 3; the small hybrid 0.7 times; the bigger hybrid 1.6 times. At the share Jerome states as tied to the data (20%, about €86,000), the small hybrid's year-3 cost is 3.4 times what ISZE puts at risk today for the data.

### 6.4 Benefits and why they are assumptions

There are three channels, and all three are **[A]**.

1. **Extra sales beyond plan.** Participants buy more than they would have, because better analysis gives better campaigns, better ranges and better Genuine/BVP positioning. Low, Base and High are 0.5%, 1.5% and 3% of the participants' billing in a year at full effect, ramped to 25% in year 1, 60% in year 2 and 100% in year 3. The margin on an extra euro is 46.8% minus the discount cost rate of the design chosen.
2. **Better price decisions.** The value of the +5% price revision is €638,000–€726,000 a year (midpoint €682,000). Better dealer-level evidence might raise the quality of the next revision; Low, Base and High attribute 0%, 5% and 10% of its value to better data, in proportion to participants' share of billing. Price reaction can be measured only from distributor to dealer and needs two years; the benefit starts late.
3. **Other.** Left at zero: air-freight savings, stock-scrap avoidance and forecast improvements have no evidence in the workspace, and stock orders alone are the scope.

What exists as evidence is thin. Distributors that send sales-to-dealer data today grew **less** than the others (4.4% a year against 10.2%, FY2024–FY2026), which proves nothing in either direction because the groups differ. ITUK's oil-filter capture moved from 56% to 79% between 2024 and 2025 without any programme (`FACTS.md` §1b), which shows that capture moves a lot on its own. **[M]**

### 6.5 Result

{{TABLE:results}}

{{CHART:net}}

Reading it. **[I]**

- The **deck design** loses €1.2M to €1.9M over three years in every case. It needs extra sales of 6.7% of the participants' billing in year 3, on top of a plan that already grows 4.7%.
- **Growth only** pays back in all three cases, with a break-even of 0.3%. It gives a distributor whose stock orders stay flat no reason to send data, which defeats the purpose.
- **Hybrid small** pays back in the High case and loses €0.2M in the Base case, with a break-even of 2.0%. It keeps a visible reward for taking part.
- **Hybrid bigger** and **tiered** lose in every case.
- The result is more sensitive to the design of the discount than to the benefit assumptions. Moving from the deck design to the small hybrid improves the Base case by €1.4M; moving from the Low to the High benefit case improves it by about €0.7M.

{{TABLE:sensitivity}}

### 6.6 Isuzu Universe on top

Universe proposes cash inside its €100,000 route (Universe 3.0 §4.5): campaign support €35,000–€50,000, dealer enablement €15,000–€25,000 and independent evaluation €10,000–€15,000. We took the midpoints, €75,000 a year, €225,000 over three years. The DLOD defence programme (about €90,000 for three markets, a separate costed design) is left in the model at zero. Universe's own hurdle is arithmetic on a hypothetical €2,500 contribution per qualifying action: about 30 qualifying actions a year to cover €75,000. With 10, 25 and 50 actions a year (our assumption, below Universe's own break-even of about 40 at €100,000) the three-year net of Universe alone is −€179,000, −€109,000 and +€6,000. Together with the small hybrid, the Base case is −€319,000. Universe says itself that no realised return is evidenced. Some of the extra sales counted on the Excellence side and the campaign contribution counted here may be the same euros. **[A]**

### 6.7 What is not counted

Internal time of the team; air-freight cost of rush and VOR orders; the value of the data standard, the IDS Studio, tender support and PRISM as tools; any effect on kickback compliance; any loss of share to other brands if the programme does not exist; legal and IT security costs. The last two are not small and are named so that nobody assumes they were zero.

---

## 7. Can the return be proven?

**Short answer: not by sales, within three years, with the distributors we have.** The reason is arithmetic, not pessimism.

### 7.1 How much a distributor moves by itself

For the twelve larger distributors with three full years of billing (Israel excluded because UTI and UMI changed split), billing growth was:

| | FY2025 vs FY2024 | FY2026 vs FY2025 |
|---|---:|---:|
| Median | +8.5% | +1.1% |
| Spread between distributors (standard deviation) | 25.5% | 13.8% |

**[M]** (`gps_clean_all_fy_v2.csv`). The correlation between a distributor's growth in the two years is −0.11: a distributor that grew fast one year is not more likely to grow fast the next. There is no persistence that a comparison could use to remove noise. Part of the movement is warranty, campaign stock builds and system changes (for example Greece's SAP go-live in 2026), none of which is the programme.

### 7.2 What a pilot could detect

If we compared participating with non-participating distributors over one year, the smallest effect that could be told from noise (80% power, 5% significance) is roughly 2.8 times the standard error, which is the spread times the square root of 2 over the number per group:

{{CHART:power}}

With eight distributors in each group the smallest effect that can be detected is 19% of billing if the spread is as low as in FY2026, and 29% at the two-year pooled spread. The effects in the Low, Base and High cases are 0.5% to 3%. **A one-year comparison between distributors cannot confirm a return of the size that decides whether the programme pays.** **[I]**

### 7.3 What can be measured instead

1. **Process indicators**, which move quickly and can be checked every quarter: share of files on time; share of dealers identified; share of valid part numbers; reconciliation of sales to dealer against billing; number of distributors with per-dealer detail; share of IDS actions closed.
2. **Mix and order behaviour:** genuine and BVP share in euros; the share of stock orders against rush and VOR; quarter-end concentration of stock orders (the forward-buying alarm).
3. **Decisions taken on the data**, logged with owner, date and the scope they touch. The test borrowed from Universe's stop condition: can a participant name a decision the data changed?
4. **Experiments below the distributor.** A campaign or a price test can be run on half of a distributor's dealers, or on half of a part family, and read against the other half over the same months. With dealer-level data, the number of units is large and the noise much lower than between distributors. This is where return can be shown, and it needs per-dealer data first. The ITUK 2025 file (64 dealers, 5,559 part numbers) is the only existing base; how large the noise is at dealer level is unknown until a second year exists. **[U]**
5. **Additional-only baselines.** For any campaign or concession, measure contribution against a documented baseline on the same scope before, during and after, including returns. This is Universe's own rule and it applies here.

### 7.4 What this means for the decision

Management cannot be shown a proven return, and should not be shown an invented one. It can be shown a bounded cost, a mechanism that pays for itself at a stated threshold, indicators that tell within two quarters whether the mechanism works, and stop conditions (chapter 11). That is a smaller promise and a more defensible one.

---

## 8. Excellence Partner and Isuzu Universe together

### 8.1 Why they belong together

Universe asks distributors for data and returns analysis, tools and rules. Excellence gives distributors a reason to take part. Universe scores its own chance that a distributor joins as designed at 55 out of 100, and that it shares more than today's report at 35. Excellence addresses exactly that gap. In the other direction, Excellence on its own pays for compliance: the distributor sends the minimum and receives nothing of its own. Universe supplies the data standard, the return and the rules. **[M]** (`ISUZU_UNIVERSE_3_0_2026-09-23.md` §8).

| | Excellence Partner | Universe |
|---|---|---|
| Strength | Simple to explain; a real incentive; can start in April 2027 without IT | A written data standard; analysis tested on real numbers; rules that stop it feeling like surveillance |
| Weakness | Pays for compliance, not quality; nothing comes back | No reason for a second step; no platform; nothing tested with a real participant |
| Gives the other | A reason to take part | The standard, the return and the rules |

### 8.2 What to merge and what to park

Merge: the data standard, the monthly return, the conduct rules, the "ask only what you can return" test, and the stop condition. Park: the platform part of Universe (a shared application with sign-in, a server and the €300,000 route). There is no server, real sign-in is parked until IT is involved, and the acceptance tasks still wait for real participants. The analysis and documents work without a platform, as files made per distributor. **[M]** (`00_docs/ISZE_ROADMAP.md`, Universe engineering programme).

### 8.3 Where they conflict

| Universe says | Excellence does | Resolution |
|---|---|---|
| Do not pay per record or per field; do not count uploads as participation | Pays for taking part | Pay for meeting a quality standard per quarter (complete, per dealer, on time, declared), never for the number of rows; at level 2 count what happens with the data |
| No ranking of dealers, no compliance scorecard on IDS | A yearly status and an award, IDS in the score | No ranking of distributors either; status without a 1-2-3; IDS as improvement; dealers never ranked |
| Ordinary service never depends on contribution | Development partners get no discount | Discount and extra programmes are not ordinary service; the written rules say ordinary service is equal for all |
| Never approach a dealer directly | | All through the distributor |
| Budget €100,000–€300,000, no evidenced return | Up to €1.1M a year in the deck design | Use the small hybrid and staged ceilings (chapters 6 and 11) |
| If the incentive disappeared tomorrow, would they still send? | | Adopt as the success test of Excellence |

### 8.4 Plan B if management does not approve the discount

1. Tighten the existing kickback condition to the data standard, starting with the distributors already on it. Cost: nothing extra; needs the kickback terms to be adjustable.
2. A formal request with a monthly return in exchange. Romania sent eight months two days after Jerome's formal request of 15 September 2026.
3. Status and an award at the European aftersales meeting, without a discount, with IMG in support.
4. Universe tools as the attraction, not as enforcement. Universe's own estimate is modest without an extra incentive.

What we would not do is build Plan B on tools that force data. A tool cannot force anything, and the platform such a tool needs does not exist.

---

## 9. Implementation and technical requirements

### 9.1 Timeline to 1 April 2027 and after

{{CHART:timeline}}

| When | What | Owner |
|---|---|---|
| Oct–Nov 2026 | Management paper; concept and ceiling decision; confirm kickback terms and get the incentive sheet | Jerome |
| Nov–Dec 2026 | Legal review of the written rules; data standard v1 to the distributors that already agreed to feeds; update the register with feeds already received | Jerome, with legal |
| Dec 2026–Feb 2027 | Phase 0 intake and validator; dashboard of received files; eligibility job in draft | Developer, with AI |
| Jan–Mar 2027 | No-discount trial with three or four distributors: do clean per-dealer files arrive monthly, and what do we send back? Shadow level 2 score on FY2027 data | Jerome, Bart Symons |
| Mar 2027 | Written rules final; SAP condition set up; trainings ready | Jerome, SAP owners, IMG |
| 1 Apr 2027 | Programme starts (FY2028), level 1 | Jerome |
| End Jun 2027 | First quarterly check; first discount for the quarter after a clean first quarter | Jerome |
| Oct 2027, Jan 2028 | Second and third checks; mid-year review against the indicators | Jerome |
| Apr–May 2028 | Level 2 assessed on FY2028; award at the European aftersales meeting | Jerome, IMG |

### 9.2 What the developer needs to build

Detailed requirements are in appendix E. In short, in two phases so that April 2027 does not depend on a platform.

**Phase 0, by 1 April 2027: files, a validator and a report.** A secure drop per distributor (a shared folder or equivalent with separate access per distributor); a validator that checks every file against the data standard and sends a receipt with what passed and what did not; storage with versions; the existing sales-to-dealer pipeline in `12_raw/dealer_sales` and the canonical long format as the target; a quarterly eligibility job that produces the table the discount code is set from; a monthly return per distributor in the existing one-pager format.

**Phase 1, after the first two quarters, if the indicators say so:** a web upload with sign-in; a dealer-identity service; the monthly return as a page; case records for decisions taken on the data. Sign-in and hosting need IT and cannot be assumed.

### 9.3 Interfaces and dependencies

- **SAP:** a discount condition per distributor and quarter, or a credit-note job (chapter 5.6). Owner and effort **[U]**.
- **Existing pipeline:** PRISM loaders already read the canonical long format; a fix in 2026 stopped them summing year totals and monthly rows twice. Reuse, do not rebuild.
- **Billing reconciliation:** monthly sales to dealer against billing for the same months, with warranty shown apart, as the BI framework requires.
- **IDS follow-up sheet:** the pull scaffold of the 0.4 feedback sheet is empty today and is the natural base for the follow-up score.

---

## 10. Risks

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| 1 | Distributors take the discount and send the minimum | high | high | Quality standard, not row counts; monthly return; per-dealer detail a condition from quarter three | Jerome |
| 2 | The discount costs more than any benefit | high on the deck design | high | Small hybrid; staged ceilings; stop conditions | Jerome |
| 3 | Management wants a return figure that does not exist | high | medium | Present as cost of capability with indicators, not as ROI; this paper | Jerome |
| 4 | Forward buying at quarter end | medium | medium | 120% cap on discountable stock; quarter-end monitor | Jerome |
| 5 | Competition-law challenge | low–medium, **[U]** | high | Objective rules announced beforehand, no exclusivity or share condition, legal review | Legal |
| 6 | Overlap with the kickback pays twice | medium | medium | Level 1 asks more than the kickback does today; read the kickback terms first | Jerome |
| 7 | IDS self-scores inflate | medium | low | Improvement not score; sample visits | IMG |
| 8 | Dealer data is poor or incomplete | high at first | medium | Declared coverage; validator; gaps treated as source gaps, not weak sales | Developer |
| 9 | Sign-in, hosting and IT security are not available | medium | medium | Phase 0 runs on files; Phase 1 only with IT | Developer |
| 10 | Small distributors earn too little to bother | medium | low | Practical benefits (for example free transport on stock orders) rather than a percentage | Jerome |
| 11 | Romania, Iceland and others order nothing as stock orders and gain nothing | certain | low | Tell them; moving to stock orders is itself good for planning | Jerome |
| 12 | Discount distorts GPS and the %GM reading | medium | medium | Credit note, not invoice price | Jerome, finance |
| 13 | Internal time of the team is not enough | medium | high | The programme is the team's second project beside Universe; name the time and drop what does not return | Jerome |

---

## 11. Decisions, open items and stop conditions

### 11.1 Decisions requested

1. Approve the concept and the two levels. **[P]**
2. Approve the small hybrid as the design to start with, and the staged ceiling of up to €150k in FY2028, €350k in FY2029 and €400k in FY2030.
3. Approve the no-discount trial in January–March 2027 and the launch of level 1 on 1 April 2027.
4. Confirm that the discount is paid as a credit note per quarter and that SAP sets it up.
5. Confirm that Universe's platform is parked and its data standard, return and rules are adopted.

### 11.2 Release conditions, year by year

| Release | Condition, measured by ISZE |
|---|---|
| FY2028 (€150k) | Concept approved; legal review done; written rules sent |
| FY2029 (€350k) | At least six of the seven first distributors delivered three consecutive clean monthly files; per-dealer detail from at least four; quarter-end share of stock orders not above 33%; at least two decisions per participating distributor logged with scope |
| FY2030 (€400k) | Per-dealer detail from at least eight distributors; at least one dealer-level or part-family experiment read against a control; no forward-buying signal; the Low-case threshold (2.0% extra sales for the small hybrid) judged plausible on that evidence |

**[P]** The thresholds are proposals to be agreed.

### 11.3 Stop conditions

The programme stops, or goes back to Plan B, if after two eligible quarters fewer than half of the first distributors deliver clean files, or if no participant can name a decision the data changed, or if a legal or confidentiality weakness is found that cannot be closed. It does not broaden the population to look for a better result.

### 11.4 Open items

| # | Item | Needed from |
|---|---|---|
| 1 | The kickback terms and the 20% share tied to data | Jerome, contract text |
| 2 | The incentive sheet (`budget_per_DB_reviewed_24042026.xlsx`), to split kickback from other incentives | Planning |
| 3 | Which distributors already send monthly files; update the register | Sales review team |
| 4 | What order type PRD is; whether discountable base excludes warranty | SAP owners |
| 5 | Credit note or invoice condition | Finance |
| 6 | Whether ISZE is dominant in any relevant market; non-EU regimes; the 2022 vertical guidelines on non-linear pricing | Legal |
| 7 | Cost of internal time, if management wants it shown | Jerome |
| 8 | Air-freight and handling cost of rush and VOR orders, if the shift to stock orders is ever to be valued | Logistics |

### 11.5 What would change the recommendation

Evidence of a measured uplift from data sharing would move the benefit cases and could justify the bigger design. A kickback that already pays most of what the data is worth would argue for Plan B. A legal reading that restricts progressive bonuses would argue for the flat part and practical benefits.

---

## Appendix A. Data standard for sales to dealer (proposal)

One file per distributor per month. CSV or Excel, UTF-8, one row per dealer, part and period. Price-free.

| Field | Rule |
|---|---|
| Distributor ID | The ISZE distributor code, stable |
| Dealer ID | Stable code agreed between distributor and ISZE; kept after closure, rename or transfer |
| Dealer site ID | Separate code where a dealer has several sites |
| Part number | The Isuzu part number as sold, with leading zeros kept; ten digits where the number allows |
| Quantity | Units; negative for returns and corrections |
| Date | Transaction date; a month is enough |
| Reporting period | Calendar month, `YYYY-MM` |
| Transaction type | Sale, return, credit or correction where known |
| Record ID | Stable line ID so that corrections can be matched |
| File version and creation date | A resubmission replaces its predecessor visibly |
| Coverage declaration | A control record: dealer sites included; known exclusions; first and last date; returns included or not; full range or part; changes that break comparison |

**Deadline:** ten working days after month-end. **Not asked:** selling prices, margins, customer names, chassis numbers, workshop orders, dealer stock. **Per-dealer detail** is a target for the first two quarters and a condition from the third.

## Appendix B. Level 2 scorecard: criteria and the six fields

Each criterion needs: definition, source, owner, frequency, evidence, scale. A criterion without all six does not enter the first-year score. The scale below is a proposal, the same for every criterion: 0%, 50% or 100% of the points, with the evidence named.

| Criterion | Points | Definition | Source | Owner | Frequency | Evidence | Scale |
|---|---:|---|---|---|---|---|---|
| Parts sales against plan | 20 | Billing of the FY against the reviewed business plan, warranty shown apart | Billing, business plan | ISZE sales | Yearly, tracked quarterly | Billing extract | ≥100%: 100%; 95–100%: 50%; below: 0 |
| Genuine share in euros | 10 | Genuine euros ÷ genuine plus BVP euros against last FY | Billing, classification | ISZE sales | Yearly | AIM release pinned | Not lower: 100%; −1 point: 50%; lower: 0 |
| Fill rate with MOS limit | 5 | First fill rate on parts ISZE delivered on time, MOS within a limit | KPI file | Distributor, ISZE | Monthly | KPI file | To define |
| IDS improvement | 10 | Change in comparable questions since the last round | IDS | IMG | Per round | IDS report | To define |
| Closed improvement actions | 10 | Closed actions ÷ agreed actions | Follow-up sheet | Distributor | Quarterly | Sheet with evidence | ≥80%: 100%; 50–80%: 50% |
| Right order types | 5 | Stock orders against rush and VOR | Billing | ISZE | Quarterly | Billing | To define |
| EDI or equivalent | 5 | Digital ordering active | IT | ISZE IT | Yearly | Test | Yes/no |
| Training passed on | 10 | Dealers reached by trained staff | Training register | Distributor | Yearly | Register | To define |
| Kaizen plan | 15 | At least three actions, owner, date, evidence; scored on closed actions | Kaizen template | Distributor | Yearly | Template | By closed share |
| R&M, extended warranty, roadside | 5 | Step reached | Report | Distributor | Yearly | Step list | Per step |
| One agreed action per review | 5 | Action with owner and date, follow-up | Review record | Both | Per review | Record | Done / not done |

**Corrections to the deck to make before it is shared:** "Demonstratable" to "Demonstrable"; "< 84" to "0–84"; one definition of IDS participation; a definition of "critical compliance" or its removal.

## Appendix C. Model: structure, formulas and assumptions

The ROI model is `Excellence_Partner_ROI_Model_2026-10-09.xlsx`. Blue cells are inputs; yellow cells are key assumptions or missing numbers.

- Discount cost per year, design 1: stock orders level 1 × 2.5% + stock orders level 2 × 5%.
- Design 2: the same × planned stock-order growth.
- Designs 3 and 4: stock orders level 1 × (flat + expected bonus) + stock orders level 2 × (flat + expected bonus). The expected bonus uses a normal distribution for the distributor's growth, mean = planned growth, spread = 13.8%: expected growth inside each band = E[(g − lower)+] − E[(g − upper)+].
- Design 5: stock orders × expected tier rate, same distribution.
- Margin on an extra euro = gross margin − discount cost ÷ billed of participants.
- Benefit, scenario s, year t = uplift_s × ramp_t × billed_t × margin_t + price share_s × €682,000 × ramp_t × billed_t ÷ in-scope billed + other.
- Net = benefit − discount cost − running cost − build cost.
- Break-even extra sales in year 3 = total cost ÷ (billed × gross margin − discount cost).

Assumptions that are ours, not evidence: the participation plan per year, the ramp (25%, 60%, 100%), Low/Base/High uplift (0.5%, 1.5%, 3%), the price-decision share (0%, 5%, 10%), the normal distribution of growth, the tier limits and rates, the flat and bonus rates of the two hybrids, Universe's action counts (10, 25, 50).

## Appendix D. Evidence per distributor

{{TABLE:distributors}}

## Appendix E. Requirements for the developer

Priority: **M** must, **S** should, **C** could. Size: S, M, L are our guesses for the developer to replace with real estimates. **[A]**

| # | Requirement | Priority | Phase | Size |
|---|---|---|---|---|
| E1 | Per-distributor secure drop with separate access; no distributor sees another's files | M | 0 | M |
| E2 | Validator against the data standard: schema, period, duplicate keys, negative quantities flagged not rejected, valid part numbers, stable dealer IDs, coverage declaration present | M | 0 | M |
| E3 | Reconciliation: total quantity and valued quantity (at ISZE billed average price) against billing for the same months, warranty apart; tolerance configurable | M | 0 | M |
| E4 | Receipt per file: what passed, what failed, what to correct, route to resubmit | M | 0 | S |
| E5 | Versioning and corrections: original kept, new version active, changed results marked | M | 0 | M |
| E6 | Normalise into the canonical long format; reuse the existing adapters and loaders; no parallel calculation | M | 0 | M |
| E7 | Quarterly eligibility job: gates per distributor with evidence; manual override with a written reason; output for the SAP condition or credit-note job | M | 0 | M |
| E8 | Monthly return per distributor in the existing one-pager format; own figures beside an anonymous network average; no rankings | S | 0 | M |
| E9 | Dealer identity table with history (rename, merge, close, transfer); mapping to IDS names and, where it exists, to SAP customer numbers | S | 0–1 | L |
| E10 | Audit trail of every state change; retention and backup | M | 0 | S |
| E11 | Monitoring: files late, files invalid, quarter-end stock-order share, order-type shift | S | 0 | S |
| E12 | Data classification: price-free by design; reject rows that carry prices or personal data | M | 0 | S |
| E13 | Web upload with sign-in, roles, and hosting approved by IT | C | 1 | L |
| E14 | Case record for decisions taken on the data: owner, date, scope, before/after on the same scope | S | 1 | M |
| E15 | Experiment support: assign dealers or part families to groups, read results over the same months | C | 1 | L |
| E16 | Access rule: each distributor sees only its own data; dealers see only their own record; enforced by the application and by the contents of exports, not by hidden menus | M | 1 | L |

**Security and privacy.** The standard is price-free and carries no customer names, chassis numbers or personal data. Dealer names are company names. Even so, the files are commercially sensitive: encrypt in transit and at rest, keep the access list short, log access, and do not copy files into shared repositories. Raw billing never leaves the secure area.

## Appendix F. Glossary

| Term | Meaning |
|---|---|
| Sales to dealer | What a distributor sells on to its dealers, part number and quantity, no prices |
| Stock order (SOR) | The order type for regular replenishment from ISZE; the base of the discount |
| Rush, VOR | Faster order types; out of scope |
| Rebate credit | Credit lines "Rebate Material" in the billing ledger; the kickback and other incentives |
| Level 1, level 2 | Partner; Excellence Partner |
| %GM | Gross margin as a percentage |
| FY | Fiscal year, April to March; FY2026 = 1 Apr 2025 – 31 Mar 2026 |
| GPS | Billed parts against target spend per truck |
| IDS | Isuzu Dealer Standards, a dealer self-assessment |
| BVP | Best Value Parts |
| MOS | Months of stock |
| StD | Sales to dealer |

## Appendix G. Sources read, and what was not read

**Read in the workspace:** the proposal deck; `INDEX.md`, `AGENTS.md`, `FACTS.md`, `ISZE_BI_FRAMEWORK.md`; `sales_fact.parquet`, `distributor_dimension.csv`, `q1fy2027_export_with_saty.csv`, `gps_clean_all_fy_v2.csv`, `wallet_waterfall.csv`, `pms_opportunity_matrix.csv`, `bp_fy27_reviewed.json`; the IDS 2026 payloads and logic check; the sales-to-dealer files, registry and standing rule; the August 2026 sales-review minutes; the FY2027 action plan; `DECISIONS.md`; the Universe 3.0 paper, value-exchange model, participation model, pilot evidence pack, €300k term sheet and DLOD rollout; the earlier analyses in this folder.

**Read on the web (9 October 2026):** the Commission's competition pages and law-firm notes on the extension of Regulation 461/2010 to 31 May 2028 by Regulation 2023/822 and the 2024 evaluation (for example [Cuatrecasas](https://www.cuatrecasas.com/en/global/art/eu-commission-prolongs-motor-vehicle-block-exemption-regulation), [EUR-Lex 2023/822](https://eur-lex.europa.eu/eli/reg/2023/822/oj), [Commission review page](https://competition-policy.ec.europa.eu/sectors/motor-vehicles/review-motor-vehicle-block-exemption-regulation_en)); the Commission's page on the vertical block exemption (Regulation 2022/720, [Commission page](https://competition-policy.ec.europa.eu/antitrust-and-cartels/legislation/vertical-block-exemptions_en)); and discussions of rebate case law (Post Danmark II, Intel, Michelin).

**Not read:** the text of the Supplementary Guidelines and the 2022 Vertical Guidelines on rebates and non-linear pricing; the 2026 Commission evaluation of Regulation 461/2010 (SWD(2026) 174); the kickback contract; the budget workbook; any non-EU competition rules. **Not verified:** that the 20% share is as stated; the meaning of order type PRD; the SAP configuration options.

**Not done:** a legal review; a costing of internal time; a test with a real distributor.

## Appendix H. The prompt

The prompt that defines this paper, and from which the next edition can be written, is `MEGAPROMPT_Excellence_Partner_Paper_2026-10-09.md` in the same folder.
