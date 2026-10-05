# The two weak pillars: what a distributor would actually open

24 September 2026 · design only, nothing built · internal document

**The short answer.** Neither tool should start life as software. Both should start as a
one-page document that ISZE prepares, in the form described below, because a document is
all the strategy allows us to share until access control exists (strategy chapter 10.2).

- **Range & Campaign Planner.** A distributor would not open a range planner to learn
  something. Its own systems already show what it buys. It would open one for one reason:
  if filling it in is how it gets ISZE support money for an initiative. That money (the
  proposed €60,000 to €90,000 line in chapter 4) is not approved. Until it is, the planner
  is a nicer report that nobody asked for. There is a second limit, and it is binding. On
  the one file that splits Genuine and Best Value Parts by product line, only 4 of 366
  distributor-and-product-line combinations clear the proposed €150,000 minimum size. All
  4 belong to Isuzu Truck UK or UTI. Build it only once the money is approved and the
  minimum size is set so that it leaves real candidates.
- **Coordinated tenders.** The weekly tender list built today, plus the answer loop
  designed in the tender outcome memo, is already the whole product for repair-only
  contracts. The "coordinated" part (the vehicle and aftersales offer put together, with
  a decision brief for headquarters) applies only to vehicle-purchase tenders that bundle
  maintenance. In today's feed that is 27 notices not marked Ignore, 3 of them with a live
  deadline, and none publishing a fleet size or a value. A distributor would fill in a
  one-page support request only if ISZE can commit something it cannot get elsewhere: a
  parts price held for the length of the maintenance contract. Nobody has decided that
  ISZE will offer it. If ISZE will not, do not build this part.

**Terms used below.** *ISZE* is Isuzu's European parts company, which bills the
distributors. *AIM* is our parts classification and analysis model: every part number
sits in a family and a product line. *BVP* means Best Value Parts, the lower-priced Isuzu
parts range sold beside Genuine. *IDS* means Isuzu Dealer Standards, the dealer
self-assessment. *ITUK* is Isuzu Truck UK (trucks). *IUK* is the separate UK pickup
distributor. *UTI* is one of the two Israel distributors. *R&M* means repair and
maintenance. *TED* (Tenders Electronic Daily) is the EU's official tender journal. A
*national portal* is a country's own tender website. *Parts billed* means what ISZE
invoiced the distributor. *Sales to dealer* means what the distributor then sold on to its
own dealers.

**The two rules this design keeps throughout.** Nothing that could reach a distributor
carries an internal term (no PMS, GPS, capture, opportunity score, Attack/Selective/Watch,
Mode A/B, pillar percentages). A national vehicle total is never divided among dealers,
whether by sales, by filter share, by visits or by geography.

---

## What exists today, checked

| Thing | State | Can a distributor open it? |
|---|---|---|
| Strategy, chapter 2 and 7.1 | Planner described in one paragraph: products, participant or vehicle segment, Genuine/BVP positioning, a success test, a brief. Tenders described as qualify, then combined proposition, then decision brief. | n/a |
| Action Centre (`Isuzu Universe\ISUZU_UNIVERSE_Action_Centre_local_2026-09-24.html`) | Six internal review cases. The tender case reads the feed dated 22 Sep and records 0 outcomes. Brake-pad-front and blower-filter rates withheld until the classification is frozen. | No. Labelled internal mock, not access-controlled. |
| AIM Parts Atlas 2.0 (`Isuzu Universe\02_Atlas\AIM_Parts_Atlas_v2.0.html`) | Seven supplied families, not the full catalogue. ISZE to distributor, horizon 30 June 2026. Has a "Save view" button, which is where a planner selection would start. | No. Labelled "Internal working view". |
| IDS dealer pages (`02_dashboards\ids\IDS_2026_dealer_compare_*.html`) | One page per network: scores by section, question drill, map. | Yes. These are the only distributor-facing pages in this family today. |
| Range decision prototype (`Isuzu Universe\AIM_RANGE_DECISION_PROTOTYPE_2026-09-22.zip`) | A calculation engine for Genuine/BVP range economics: revenue, gross profit, break-even recovery. Synthetic inputs only, 87 tests. | No. Its own notes say the output carries costs and profit and must never go to a distributor. |
| Weekly R&M tender list (`04_tools\ISZE_Tender_Monitor_Install\rm_digest\2026-09-24\`) | 222 notices selected: 113 on ten distributor pages, 109 on an internal page with no distributor. One CSV per distributor with an empty outcome column. | Yes, by design. Nothing has been sent. |
| Tender outcome design (`00_docs\TENDER_OUTCOME_DESIGN_2026-09-24.md`) | Reply by number, one word, typed in by the ISZE market owner. | n/a |

The work order says no planner file exists. Strictly that is true: there is no planner.
But the range prototype above is the calculation that would sit behind the planner's
internal check, and it should be reused rather than rewritten.

---

## 1. Range & Campaign Planner

The strategy uses this as the tool name, so the name stays in internal documents. The
wording proposed for anything a distributor sees says **"range initiative"** or
**"offer"**, never the other word.

### 1.1 The first screen, and its one question

**Question: "Which of my product lines could carry a supported initiative this year?"**

The first screen is a single ranked table of the distributor's own product lines, from
its own purchases from ISZE, for the last two full calendar years (2024 and 2025). The
2026 half year is not used for any growth comparison. One row per product line (brake
pads, fuel filters, clutch kits and so on):

| Column (distributor wording) | Content |
|---|---|
| Product line | AIM product line name in plain words |
| Your purchases from ISZE, 2025 | Genuine and BVP together, in euro |
| Change from 2024, value | euro and % |
| Change from 2024, pieces | pieces and % |
| Of which Best Value Parts | BVP share of the 2025 euro, and its change |
| Large enough for support | "Yes", or "No, €X below the minimum" |

Sorted by 2025 value. Above the table sits one sentence: "Value and pieces are shown
separately because a fall in pieces can hide behind a stable value, and the reverse."
That is the strategy's own chapter 3 point, and it is the one thing on this screen the
distributor's own system probably does not show it.

The last column is the gate. It is the only reason this screen is more than a report.

### 1.2 What the user picks, and what comes back

The user makes five choices. Nothing is typed except dates and one sentence.

1. **One product line** from the first screen.
2. **The offer window.** Start and end date.
3. **How Genuine and BVP are positioned.** Three options: Genuine only; Genuine and BVP
   side by side; introduce the BVP alternative where the distributor does not yet buy it.
4. **Who it is for.** "My whole network" is always available. "Named dealers" is offered
   only where the distributor's sales to dealer arrive with dealer names. Today that is
   ITUK alone.
5. **What would show it worked.** Pick one: more pieces of this line bought from ISZE
   than in the same months a year earlier; the BVP alternative taken up by a stated share;
   the same pieces held while the price moves. One sentence of the distributor's own
   reasoning goes beside it.

What comes back, on the same screen and then as the one-page brief (section 1.4):

- **The exact parts in the line.** Every part number, grouped by product form (element,
  kit, housing, assembly), with 2024 and 2025 pieces and 2025 value. For each Genuine part
  there is its BVP twin from the catalogue pairing, or "no BVP alternative in the
  catalogue", and whether the distributor already buys that twin.
- **For whom, as measured.** With named dealers (ITUK only): the dealers that bought this
  line in 2025 and their pieces, and a separate list of dealers who bought other parts but
  none of this line, headed **"no recorded purchase"**. It is never headed "gap" or
  "opportunity", because the strategy says a product is not an opportunity merely because
  it was not bought. Vehicle types are shown only for parts whose fit to one vehicle band
  is established. A part that fits several bands says "fits several vehicle types".
- **The baseline.** The pieces and value in the same months of the previous year, frozen
  on the day the brief is saved. The result is later measured against this figure.
- **The size check.** Whether the line clears the minimum, and by how much.

Never shown to the distributor, but shown to ISZE on a separate internal page (section
1.4): past deep-discount buying on this line, the economics check, and any modelled
service demand.

### 1.3 Which files already hold the inputs

All paths below were checked on disk on 24 September 2026. The root is
`C:\Users\jerom\Desktop\claude\ISZE`.

| Input | File | What it gives, and its limit |
|---|---|---|
| Part to product line | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases\aim_pn_classification_release_2026-09-20.csv` | The frozen classification. Status in `RELEASES.json` beside it is **PENDING_APPROVAL**. No part list should reach a distributor until it is approved. |
| Part to product line (live) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv` | Current master, changed again today. Use for internal checks, not for a shared brief. |
| Genuine and BVP by distributor and product line | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_genuine_bvp_vs_price_2024_2025.csv` | 2024 and 2025 value, pieces and BVP share for 22 distributors. Covers €4,367,064 of 2025 billing, which is maintenance lines only and less than the €6.65M the strategy quotes for maintenance parts. It is the first-screen source for those lines. |
| Same, with 2023 | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\mix_genuine_bvp_by_subgroup.csv` | Year-by-year mix, for a longer view if wanted. |
| Genuine to BVP twin | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\genuine_bvp_crossref.csv` | Catalogue pairs, with vehicle model and engine type. |
| Twin already bought? | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\bvp_addressable_basket.csv` | Per distributor: Genuine part, its BVP twin, and a flag for whether the distributor already sells the twin. |
| Named-dealer sales to dealer | `C:\Users\jerom\Desktop\claude\ISZE\01_data\15_gpt_safe\Sales_to_Dealer_colleagues_20260924\Sales_to_Dealer_merged.csv` | 305,699 rows, 2023 to 2026. Only ITUK arrives with dealer names. IUK, Portugal, Ireland, UTI, Greece and Romania arrive as a network total per part, mostly pieces only. Read by a build script, never by hand. |
| ITUK dealer baseline | `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\06_Working\PILOT_BASELINE_ITUK_2026-09-24\baseline_ITUK_2025_monthly.csv` | Dealer by month, maintenance pieces and value, frozen today for the pilot. The planner's success test should use the same month-matched method. |
| Dealer names and places | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ids_dealer_network_cleaned_2026-09-20.csv` | Names, city and models sold, for the invitation list. It is not a denominator and not a sales figure. |
| Vehicle band per part | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\tonnage_capable_part_numbers.csv` | Part to vehicle band, with a column stating whether the fit is exclusive to one band. Only exclusive rows may name a vehicle type. |
| Distributor fleet, context only | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_spu_by_distributor.csv` | Vehicles in service per distributor and year. A single line of context at distributor level. It is never divided below that. |
| Past deep-discount buying (internal) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_campaign_suspect_by_db_family_2024_2025.csv` | Share of the line bought at least 20% under the reference price, by distributor. It checks the line has not already been pushed on price. |
| After-the-fact check (internal) | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_PMS_Campaign_Impact_Review_2026-09-23.html` | The method for spotting stock bought ahead of a price window and then digested. Reuse the method in the success test. |
| Economics (internal) | `C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\AIM_RANGE_DECISION_PROTOTYPE_2026-09-22.zip` | Revenue and gross-profit comparison, and the pieces needed to break even. Synthetic inputs only, no live adapter exists. Internal only. |

**Must not be used, by rule.**
`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\dealer_demand_ituk_2025_by_dealer_20260924.csv`
carries a column `trucks_apportioned` and an `expected_eur` built from it. It divides the
national ITUK fleet of 22,389 among the 64 dealers in proportion to each dealer's share
of oil-filter purchases. That is allocating a national vehicle total by sales, which the
constraint forbids. The file's own test also argues against it: in six of the seven
families where it could be checked, the oil-filter share ranks dealers slightly worse
than dealer size alone (`dealer_demand_ituk_2025_meta_20260924.json`, falsification
test). No "expected" or "gap" figure per dealer appears anywhere in the planner.

**Not found.** I found no file holding the price list, or a per-distributor net price,
under a name I could search for (`*price_list*`, `*PriceList*`, `*reference_dealer*`).
The ITUK baseline valued pieces at the median 2025 price billed per part, computed inside
its build script. The planner's value column can use the billed euro it already has. The
internal economics check needs a price input produced deliberately, and none exists yet.
Named-dealer sales to dealer exist for ITUK only. For every other distributor, "who is it
for" stops at "my whole network".

### 1.4 The output on one page

**The shared page: "Range initiative brief".** A4 portrait, one page, prepared by ISZE
and sent as a file. Six boxes, top to bottom:

1. **Header.** Distributor name, product line, offer window, date prepared, and the
   source dates in one line ("Your purchases from ISZE, full calendar years 2024 and
   2025. Sales to your dealers, 2025.").
2. **What is in the range.** A table of at most 25 part numbers, grouped by form, with
   columns part number, description, pieces 2024, pieces 2025, value 2025, BVP
   alternative (part number or "none in the catalogue"), "you already buy it" (yes/no).
   If the line holds more than 25 parts, the top 25 by value are shown and a line states
   how many more there are and the share of value they carry.
3. **What moved.** Two small bars side by side, value and pieces, 2024 against 2025,
   each split Genuine and BVP. One sentence under them states the direction in words,
   for example: "Value fell 13%, pieces fell 25%."
4. **For whom.** Either "Your whole network", or for named-dealer distributors: dealers
   that bought the line (count, top ten by pieces), and dealers with no recorded purchase
   of the line (count, listed). Vehicle types only where the part fit is exclusive.
   Nothing is shown per dealer that the dealer did not actually buy.
5. **The offer and how we will know.** The positioning chosen. The support requested
   (left blank until ISZE agrees an amount; never shown as a promise). The baseline
   figure for the same months last year. The success test chosen. And one fixed line:
   "We will also look at the month after the window, because stock bought ahead of an
   offer is not extra demand."
6. **What this brief does not say.** Three fixed lines: it is not a forecast; a product
   not bought is not a lost sale; it contains no resale price and asks for none.

Footer: evidence labels (measured for boxes 2 to 4, proposed for box 5) and the
classification release name once approved.

**The internal page, never shared.** Same header, then: the past deep-discount share on
this line (so ISZE does not fund a price move on a line already bought mostly on
discount); the minimum-size check against the agreed basis; the range prototype's
revenue and gross-profit comparison once live inputs exist; and the decision line (fund
or not, the amount, who decided, the date).

### 1.5 Why a distributor would spend time on it

Honestly: **not for the analysis.** The distributor's commercial lead already knows
which lines it sells. What it lacks is the Genuine and BVP view on one line, the
part-level detail behind a movement, and (for ITUK) which of its own dealers do not buy
the line. That is useful, and it is what the Atlas is for. It is not a reason to plan
anything.

The reason to spend an hour on the brief is money. If this page is the application for
ISZE support, and a completed page gets a yes or no within a stated time, a distributor
will fill it in. Everything else is secondary.

For it to be worth building, four things have to be true:

1. **The support line is approved**, with the application rule written down. Today it is
   a proposal (strategy 4.5 and 9.2).
2. **The minimum size leaves candidates.** On the Genuine/BVP file for 2025 (my
   arithmetic, on that file only), 4 of 366 distributor-and-product-line combinations
   clear €150,000: ITUK brake pads €302,366, ITUK fuel filters €195,343, UTI air filters
   €158,628, ITUK air filters €155,654. One level up, grouping lines into product groups,
   6 of 127 clear it: ITUK filters, IUK filters, ITUK brakes, UTI filters, IUK brakes,
   Ukraine filters. So the €150,000 floor, measured per product line, confines the tool
   to Isuzu Truck UK and one Israel distributor. That may be the intention. If it is,
   say so, because it means a tool for two customers, not a network tool. If it is not,
   the floor has to be defined on a wider basis (a whole product group, or a
   distributor's whole year) before the planner is built.
3. **The classification release is approved**, so the part list on the brief does not
   change after it is sent.
4. **Someone owns the after-the-fact measurement**, month-matched and with the
   stock-ahead check. Without it, the success test in box 5 is a promise nobody keeps.

If the support line is not funded, build nothing. Instead, add a "print this line as a
page" button to the Atlas once it is cleared for distributor use. That gives the
analytical part of the brief without pretending there is a planning tool behind it.

---

## 2. Coordinated tenders

### 2.0 Two different populations, which need two different answers

The feed (`tender_data.json`, built 22 September 2026) holds 619 opportunities. They split
into two groups that the design must not mix.

- **Repair and maintenance only, no vehicle purchase: 236.** General fleet repair
  contracts. None names Isuzu, and many name another make (the German and Romanian pages
  carry Mercedes-Benz service contracts). A dealer workshop bids as a workshop. There is
  nothing for "the Isuzu entities" to combine, so the coordinated tool does not apply.
  For these, the weekly list plus the reply-by-number loop in
  `00_docs\TENDER_OUTCOME_DESIGN_2026-09-24.md` is the whole product. This memo does not
  redesign either.
- **Vehicle purchases that bundle maintenance or parts.** This is the population the
  strategy means by a coordinated tender: a public buyer wants trucks or pickups plus a
  maintenance contract, often five years. Counted on the feed: product type truck,
  pickup or van, carrying an aftersales signal, not marked Ignore gives **27 notices (25
  trucks, 2 pickups)**. 3 have a deadline on or after today, 24 have none, 13 have no
  distributor assigned, and **none publishes a fleet size or a value**. By distributor:
  Belgium 6, Germany 5, Portugal 1, Romania 1, Malta 1, unassigned 13. These counts are
  before removing duplicates.

Three facts about today's list matter for this design. Each one is already recorded in the
tender outcome memo and none is redesigned here:

- **Duplicates.** The same tender often appears twice: once from the national portal with
  a deadline, once from TED without one. On the ten distributor pages, a strict title
  match finds at least 14 such pairs among the 113 lines (Belgium 5, Romania 4, Portugal
  3, Germany 2). The Belgian page's 13 lines are at most 8 distinct tenders. Three of
  the five Belgian pairs are vehicle purchases with maintenance bundled. A coordinated
  request must attach to the tender, not to one copy of it.
- **Vocabulary.** The distributor page asks for "pursue / pass / already known". The
  file and the store use other words. The outcome memo fixes this.
- **Internal shorthand on the shared page.** The scope line on every distributor page
  reads "R&M". It should read "Repair and maintenance".

### 2.1 The first screen, and its one question

The tool opens from one notice that the distributor has answered "pursue" on its weekly
list, and only if that notice includes vehicles. It does not open from the list itself.
Choosing what to pursue is the list's job.

**Question: "What does this bid need from Isuzu, and by what date?"**

The first screen shows the notice as published, pre-filled from the feed, and asks the
distributor to complete it. Buyer. Title in the original language. Link to the notice.
Deadline and days left, or "deadline not published, check the notice". Scope (vehicles,
maintenance, parts). Published value and published fleet size, each shown as "not
published" where absent. That is every one of the 27 today.

### 2.2 What the user picks or types, and what comes back

The distributor completes five things. The first four come from the tender documents,
which it has and the feed does not.

1. **Lots it will bid**, if the notice has lots.
2. **Vehicle offered**, picked from a short list: D-Max, N-series by weight band,
   F-series.
3. **Number of vehicles and contract term**, typed: vehicles, years, and distance per
   year if the tender states it.
4. **What it asks of ISZE**, ticked from a short list:
   - a parts price held for the contract term on the maintenance parts list;
   - BVP alternatives priced in the same list;
   - a named contact for the tender period.

   Delivery and availability terms are not on the list. They stay in the existing
   business, per the strategy's scope boundary.
5. **The date it needs an answer**, defaulting to ten working days before the deadline.
   That default is a proposal, not an agreed rule.

A sixth box, "What we ask the vehicle side", is free text. The tool records and passes it
on. It does not decide it. For ITUK the workspace notes record a direct relationship with
Isuzu Motors Limited in Japan on vehicle sales. For the other distributors I have not
verified which Isuzu entity prices the vehicles, so the design routes the request to "the
vehicle-side contact", to be named per distributor.

What comes back is the one-page request (2.4), with one computed section: **the
maintenance parts over the contract**. For the vehicle band chosen, it lists the
maintenance parts whose fit to that band is established, with their BVP twins. It then
multiplies: pieces per service × services per year × vehicles × years. This is labelled
**arithmetic on a stated service schedule, not a forecast**. The vehicles are the ones
in the tender, typed by the distributor. Nothing comes from a national fleet, and nothing
is split among dealers.

### 2.3 Which files already hold the inputs

| Input | File | What it gives, and its limit |
|---|---|---|
| The notice | `C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json` | Buyer, title, link, deadline, scope, published value and fleet (rarely filled), product type, aftersales signal, distributor code. Dated 22 Sep 2026. |
| The weekly list it opens from | `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\rm_digest\2026-09-24\` (per-distributor `.html` and `.csv`, `_run_report.json`) | The notice numbers the distributor answers against. Built today, unchanged by this design. |
| The pursue answer | `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\tender_outcomes.py` and `tender_outcomes.json` | Where "pursue" is stored, keyed on the opportunity code. Empty today. The request should hang off the same key, so won or lost later closes both. |
| Parts that fit the vehicle band | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\tonnage_capable_part_numbers.csv` | Part to band, with the exclusivity column. Only exclusive rows are listed as fitting. |
| Services per year, per band | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_tonnage_model.csv` | Visits per year and category factor per band (the network planning lane). It is an assumption, and must be printed as one. For a tender, the tender's own service interval, where stated, replaces it. |
| BVP twin | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\genuine_bvp_crossref.csv` | Genuine to BVP catalogue pairs with vehicle model and engine. |
| Which dealer would service | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\ids_dealer_network_cleaned_2026-09-20.csv`, with the feed's own dealer match | Named only where the buyer was matched to a dealer's area (the feed marks this with a confidence of 0.8 or higher). Otherwise the request names the distributor only. |
| Distributor identity | `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\data\sap_sold_to_mapping.csv` | Maps billing accounts to distributor codes, so the parts side and the tender side name the same company. |

**Missing, and no file on disk holds them:**

- vehicle prices or vehicle support terms;
- the winner of an awarded tender (the feed has award notices but no winner field);
- a per-distributor net price file for the parts list (the same gap as in 1.3);
- any distributor for the 13 unassigned vehicle-plus-maintenance notices and the 109
  unassigned repair notices.

Whether ISZE will hold a parts price for a multi-year term is a policy question. No file
answers it.

### 2.4 The output on one page

**The shared page: "Tender support request".** A4 portrait, one page. The distributor
completes it, ISZE answers on it, and it goes back to the distributor with the answer.

1. **Header.** Distributor, buyer, link to the notice, deadline, days left, "answer
   needed by" date.
2. **The tender as published.** Scope, lots, vehicles, term, value, with "not
   published" wherever the notice is silent.
3. **What we will bid.** Vehicle offered, number, term, lots. Typed by the distributor.
4. **Maintenance parts over the contract.** A table: category, Genuine part number, BVP
   part number, pieces per vehicle per year at the stated schedule, pieces over the
   term. Under it, in one line: "Arithmetic on the service schedule stated above, for the
   vehicles in this tender. Not a forecast."
5. **What we ask from ISZE.** One line per ask, each with a Yes / No / Partly box, the
   role that decided, and the date. This is the decision brief the strategy asks for:
   headquarters sees exactly what is being decided, in one place.
6. **What we ask the vehicle side.** Passed on, with the date sent. Not decided here.
7. **After the deadline.** One line: "Result: won / lost / not yet known", in the
   outcome memo's words, so the request and the outcome record never disagree.

**The internal annex, never shared.** The distributor's current billed prices on the
list; past deep-discount buying on those lines; and, once a live adapter exists, the
range prototype's gross-profit check on holding the price for the term. It also carries
one line on competition law: the request compares nothing between distributors and
carries no resale price. Strategy 10.3 requires that review before any shared use, and
it has not been done.

### 2.5 Why a distributor would spend time on it

**For repair-only contracts** (236 of the 279 repair notices), the honest answer is that
a distributor will read a short list in its own language and reply with a number and a
word, if it is asked plainly and sees its answer come back. That is the outcome memo's
design. Anything more elaborate would not be used, and nothing more should be built.

**For vehicle tenders with maintenance bundled**, the distributor has a real problem:
to bid a five-year maintenance contract it must price five years of parts, and it buys
those parts from ISZE at prices ISZE can change. A parts price held for the contract term
is the one thing only ISZE can give. With it, the request is worth an hour of the
distributor's time on every such tender. Without it, the distributor fills in a form in
order to be told what it already knew. It would not do that twice.

So, for this part to be worth building:

1. **ISZE decides whether it will hold a parts price for a tender term**, on what list,
   for how long, and who signs it off. That decision does not exist.
2. **The duplicates are merged** so a request attaches to one tender.
3. **The 13 unassigned vehicle-plus-maintenance notices get a distributor**, or they
   stay internal.
4. **The competition-law review in strategy 10.3 is done** before the first request is
   answered in writing.

The volume should decide the form. Today there are 3 live-dated vehicle-plus-maintenance
notices in the whole feed, so there will be a handful of requests a month at most. That
calls for a document template filled by hand, not software. Handle the first two requests
by hand from the page described above. Only then decide whether anything needs building.

---

## Noticed on the way (outside this brief, not acted on)

- The Portugal IDS page, `02_dashboards\ids\IDS_2026_dealer_compare_Portugal.html`, is
  titled as a pack for the Portuguese distributor. Its subtitle carries "GPS Capture
  63.3% (genuine parts share capture, locked meeting figure)". That is an internal term
  and figure on a page meant for a distributor.
- `RELEASES.json` records hashes for the classification files. The live classification
  file was changed again at 19:20 today by the cab-assembly class. The
  "2026-09-24-candidate" hash in that file may no longer match the live file. I did not
  check.

## What I read

- The strategy, `Isuzu Universe\01_Strategy\ISUZU_UNIVERSE_3_0_2026-09-23.md`, in full.
- The Action Centre page text and case data.
- The AIM Parts Atlas 2.0 page text.
- The Portugal IDS dealer page text.
- The range prototype's START_HERE, SCHEMA_AND_RULES and INTEGRATION_BRIEF.
- The Belgian tender list page, the digest README, the run report and all ten CSVs.
- `tender_outcomes.py`.
- `tender_data.json`, parsed by script for the counts above.
- The pillar board state and the builder's condition tests.
- The tender outcome memo written today.
- Headers only of every file in the two input tables.
- The ITUK dealer-demand metadata.
- The 2025 totals in `pms_genuine_bvp_vs_price_2024_2025.csv` for the minimum-size count.

No raw sales files and no line-level billing were opened. Nothing was built or changed.

## What I could not establish

- Where the price list or a per-distributor net price is held as a file.
- Which Isuzu entity prices vehicles for each distributor other than ITUK.
- How "eligible billing" for the €150,000 minimum is meant to be measured. My count uses
  one file's product lines, which cover €4.37M of 2025 maintenance billing.
- Whether ISZE would hold a parts price for a tender term.
