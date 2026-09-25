# Which purpose the aftermarket work should serve

**Written:** 24 September 2026. Internal. A recommendation for Jerome, not a decision: `DECISIONS.md` was not edited, no list was re-sorted and no dashboard was touched.

**I recommend option (c), the maintenance-parts campaign: sort the competitor work by the maintenance parts (oil filters, fuel filters, air filters, brakes and clutch), because that is where we measure a real service gap and where the competitor evidence we already hold is densest.** The UK truck book and the next price revision should not drive the list now.

**Is the data good enough to choose?** Yes, for choosing and for re-ordering the list. No, for measuring whether a campaign works: no distributor sends us sales to dealer by dealer after December 2025 (section 4). One ordering input is also not anchored yet (section 2).

Terms used below. **Isuzu Truck UK (ITUK)** is the UK truck distributor; **Isuzu UK (IUK)** is the UK pickup distributor, and the two are never mixed. **PMS** means periodic maintenance service: filters, brakes and clutch. Lubricants are a separate track and are not part of it. **AIM** is our part classification master. **BVP** is our own lower-priced value line. **Tier A** is the top 491 lines by euro billed in the twelve months to the latest billing date. They are the top of the 16,511-line ranked list the competitor search works through (`04_tools/aftermarket_intelligence/state/seed_reach_tierA.csv`).

---

## 1. Why this purpose and not the other two

### Our competitor evidence is already concentrated in maintenance parts

I split the Tier A file by part family. In AIM terms, maintenance parts are the Maintenance Service, Brakes and Clutch families. That is 199 of the 491 lines, worth €6,347,744 of €21,312,526 billed.

| Can we search for it today? | Maintenance parts, share of their € | All other real parts, share of their € |
|---|---:|---:|
| A real competitor price exists | **51.0%** (38 parts, €3,236,112) | 17.1% (39 parts, €2,392,406) |
| A rival's number, no price | 1.7% | 1.8% |
| Only inside our own brand (BVP line) | 15.3% | 5.8% |
| Nothing to search with | **32.0%** (122 parts, €2,030,151) | 75.4% (213 parts, €10,552,100) |

"All other real parts" leaves out seven lines worth €961,301 that cannot carry a competitor price in any case: three lubricant and chemical lines, a transport charge, a diagnostic tool and two service fees. Source: `seed_reach_tierA.csv`, grouped by `aim_level_1` and `reach` (my aggregation, 24 September).

So **57.5% of all the Tier A euro that has a usable competitor price today sits in maintenance parts**. And **85% of the euro with nothing to search with sits outside them**. A maintenance purpose uses the evidence we have. The other two purposes are mostly held back by evidence we do not have.

The one competitor price collection still scheduled every week was built for this purpose. Its task is named `ISZE_PMS_IAM_Refresh`, and it is the maintenance-parts refresh against the independent aftermarket (`00_docs/AUTOMATION_REGISTER.md` line 74). According to the work order's coverage brief, one of the two sources it still fetches works only by maintenance category.

### There is a measured gap to go after

At ITUK, on the IML (Isuzu Motors Limited, Japan) service-schedule standard adopted on 2 July 2026, weighted cover across the five maintenance categories is **35.9%**. The revenue gap is **€2,038,471** for calendar 2025. The largest pieces are air filter (€736,037), brake (€641,833) and clutch (€392,559). Source: `FACTS.md` section 1. That is one of two correct ways to read ITUK maintenance capture. FACTS section 1b is the other, and a figure from one must never be quoted as the other.

A campaign is also something the business already does and already reviews. `02_dashboards/pricing/ISZE_PMS_Campaign_Impact_Review_2026-09-23.html` exists for that. Neither of the other two purposes has an equivalent.

### Why not the next price revision (b)

- **Pricing is yours to start, not this work's to steer.** The price ambition was closed permanently on 22 September. Your standing instruction of 19 September says no pricing value moves on the strength of an agent's question (`DECISIONS.md`, entries of 2026-09-22 and 2026-09-19). A competitor list built to feed the next revision would be exactly that kind of pressure. This recommendation does not reopen either entry.
- **The filed revision is not waiting on competitor evidence.** It measures +5.9616%, and every market lands between +4.85% and +5.92%. The pricing roadmap says there is no band decision to make on this measurement (`00_docs/roadmaps/pricing.md` sections 1 and 2.1).
- **The evidence cannot carry a revision.** Only 16.47% of the priced book has a usable competitor price (`pricing.md` section 1). A model that predicts a competitor price from our list price is typically 46% off, against 48% for one flat ratio (`04_tools/aftermarket_intelligence/state/RATIO_MODEL_REPORT.md` line 33). How volume responds to price is not identified on our data (`pricing.md` section 2.5). A revision needs the whole book, and that is where we are weakest.

### Why not defending the UK truck book (a)

ITUK is the largest truck book we have. In 2025 we billed it €5,564,544, which is 18.1% of the €30,756,772 captured across the network. That is 45.6% of the modelled parts spend of its fleet (`01_data/00_derived/wallet_waterfall.csv`; the network figure is anchored in `metrics_snapshot.json`, and 45.6% matches `FACTS.md`). It matters. But it fails as the sorting key for three reasons:

- **I found no written record in the workspace of a current threat to defend against.** `DECISIONS.md` and the roadmaps name none, and "defend" needs something to defend against if it is to rank parts.
- **The UK competitor evidence is thin and old.** The UK workshop survey dates from 2023 and reaches 24 Tier A parts. The one UK shop we search by our own number answers about 21% of the time (`00_docs/agent/AFTERMARKET_INTELLIGENCE_STATE_20260924.md` sections 2 and 4).
- **What a defence would actually do is maintenance work anyway.** The ITUK pilot baseline is built on maintenance units by dealer, with lubricants excluded (`Isuzu Universe/06_Working/PILOT_BASELINE_ITUK_2026-09-24/PREREGISTRATION.md`). The ITUK gap in FACTS is a maintenance gap. Choosing (c) keeps everything useful in (a) without sorting a network-wide list by one customer.

---

## 2. What changes

**The ranked list.** Today the competitor search list ranks all lines by euro billed, over every family. Under (c):

1. **Scope:** only the five maintenance categories, meaning oil filter, fuel filter, air filter, brakes and clutch (AIM families Maintenance Service, Brakes, Clutch). Lubricants, non-part lines and every other family leave this list. They are not deleted, just not ranked here.
2. **First sort key: the maintenance category, ordered by the size of its capture gap in euro.** This is the input that is not anchored. Gap by category and distributor exists in `01_data/00_derived/pms_capture_by_family.csv`, but only ITUK's gap is in `FACTS.md`. The network ordering has to be anchored before anyone quotes it.
3. **Second sort key: euro billed.** Third: the reach grade, with parts that have a competitor price today placed first, because they are the ones a campaign can be priced against without guessing.

**Which parts rise.** The 199 maintenance lines currently sit at a median rank of 331 out of 491. Under (c) they become the list. Before the category ordering is applied, sorted on euro billed alone, the top of the new list is:

- front brake disc `8983767550`: rank 3 today, €639,266, competitor price held
- air filter `8974995480` (rank 9), front brake pad kit `8982447940` (rank 11), oil filter element `8982705240` (rank 13, 67 competitor brands) and fuel filter element kit `8981596930` (rank 14, 125 brands), all with a competitor price held
- filter assembly `8982878080` (rank 8), matched only to our own BVP line

The biggest climbs among the high-value lines are oil filter element `1876102890` (rank 25 to 8, nothing to search with), fuel filter element kit `5876150170` (38 to 10, price held), clutch kit `5876102320` (45 to 12, nothing to search with) and front brake pad kit `8975546610` (56 to 16, price held). The two with nothing to search with become the first named gaps. All figures come from `seed_reach_tierA.csv`.

**Which parts leave the top.** Ranks 1, 2, 4 and 5 today are the steering unit `7552348290` and three exhaust sensors: particulate sensors `8978808250` and `8978808270`, and NOx sensor `8983528481`. Together they are worth €2,708,597, and none of them has anything to search with. Rank 6 is a transport charge and rank 7 is a lubricant line. None of these belongs on a maintenance list.

**The working view.** I would make PRISM's maintenance capture page the working view: the Streamlit app on port 8503, page `3_PMS.py`, which is the canonical product under `DECISIONS.md` 2026-08-18. It shows where the gap is, by distributor and category. Two companions go with it: the frozen ITUK pilot baseline, to show whether the gap moves, and the campaign impact review of 23 September, to tell a real sale from a dealer buying ahead.

**What stops being shown in this work.** The whole-book coverage headline ("63.5% of Tier A has nothing to search with") stops being the number that leads. For this purpose, the number that matters is 32.0% of maintenance euro. The pricing pages (the flat 5% simulation and the weighted price comparison) are not part of this work's view. They stay as they are and remain yours.

---

## 3. What I would drop to make it happen

- **The price revision as a customer of this work.** No list sorted by revision weight, no feeding competitor prices into the pricing stack, and no further work on the price-prediction model. Nothing in `pricing.md` is touched.
- **A UK-book defence as its own track.** No ITUK-only ranked list and no more searching by our own number on the UK shop. ITUK stays in the work as the pilot site only, because it is the one distributor that has ever sent sales by named dealer.
- **Chasing the Tier A parts with nothing to search with outside maintenance:** 213 real parts, €10,552,100. This changes the weight of the coverage decision. For this purpose the gap to close is 122 maintenance lines worth €2,030,151, not 342 lines worth €13.5M. That makes a paid cross-reference licence far less urgent.

---

## 4. What this does not settle

- **Nothing can be measured until ITUK sends monthly sales to dealer by dealer and part number for the period after December 2025.** The pilot pre-registration records this as a dependency with no date. Until it arrives, a campaign can be run but not judged.
- **Campaigns can make dealers buy ahead instead of selling more.** The 23 September review states that about 8% of maintenance euro in 2025 was billed at 20% or more under reference. It also shows buying ahead on IUK (pickup) blower filters. Both figures come from that page and are not anchored in `FACTS.md`.
- **The discount depth of any campaign is a pricing call, and it stays yours.** This recommendation sets no price.
- **What would change my answer:** a written, current threat to the ITUK book, such as a lost dealer group or a competing supply offer. That would make (a) the purpose, and the list would then sort by ITUK billed euro.

---

### Sources for every figure

| Figure | File |
|---|---|
| Tier A split by family and reach, part ranks, 57.5% / 85% | `04_tools/aftermarket_intelligence/state/seed_reach_tierA.csv` (my grouping, 24 Sep) |
| ITUK weighted cover 35.9%, gap €2,038,471, category gaps | `FACTS.md` section 1 |
| ITUK 2025 billed €5,564,544, 45.6% of modelled spend | `01_data/00_derived/wallet_waterfall.csv`; 45.6% also in `FACTS.md` changelog 2026-09-17 |
| Network captured 2025 €30,756,772 | `01_data/00_derived/metrics_snapshot.json` (`waterfall.network.captured_eur_2025`) |
| +5.9616%, market range, 16.47% evidence cover | `00_docs/roadmaps/pricing.md` sections 1, 2.1 |
| Model 46% off vs flat 48% | `04_tools/aftermarket_intelligence/state/RATIO_MODEL_REPORT.md` line 33 |
| UK survey 24 Tier A parts, UK shop 21% | `00_docs/agent/AFTERMARKET_INTELLIGENCE_STATE_20260924.md` sections 2, 4 |
| Price ambition closed; pricing standing instruction | `DECISIONS.md` 2026-09-22 and 2026-09-19 |
| Campaign-shaped selling about 8% of maintenance euro (not anchored) | `02_dashboards/pricing/ISZE_PMS_Campaign_Impact_Review_2026-09-23.html` |

The numbers anchors were checked on 24 September: `_verification_report.json` shows 164 pass, 1 warning (Danish fleet 2012–2013), 0 fail.
