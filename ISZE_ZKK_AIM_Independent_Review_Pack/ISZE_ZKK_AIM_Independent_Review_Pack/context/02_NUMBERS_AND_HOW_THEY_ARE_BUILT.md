# 02 - The numbers, and how they are built

**As of:** 2026-09-19. Everything below is quoted from the files named in each section. Where a figure has an
as-of date, use that date when you write about it - never present a number as current without it.

---

## 0. The order of authority

If two sources disagree, the higher line wins:

1. `01_data/00_derived/_verification_report.json` - must be green before any figure is quoted
2. `01_data/00_derived/metrics_snapshot.json` - the headline figures, machine-readable
3. `FACTS.md` (workspace root) - the narrative and the pinned anchors

Decks, mail, memory notes and older context files do **not** override these. When a deck disagrees with
`FACTS.md`, the deck is wrong.

**Current verification status: 143 pass / 0 warn / 0 fail**, generated 2026-09-18 20:22 UTC. The underlying
sales table has 514,037 rows and billing runs from 2026-01-03 to **2026-06-30** — that is the horizon.
Anything after 30 June 2026 is not in these numbers.

---

## 1. The revenue base (what we billed)

| Figure | Value | What it is |
|---|---:|---|
| Raw total in the sales table | EUR 117,536,189 | 514,037 rows, 2023-01-03 to 2026-06-30. Includes internal codes, credit notes and returns. **Do not quote this as revenue.** |
| GPS-facing, all lines | EUR 113,640,105 | After distributor exclusion, credit notes and returns removed |
| **The parts base** | **EUR 112,089,307** | Parts only, same basis. **This is the figure to use as "the parts business".** |

The parts base is a snapshot cut at the data horizon. A second published figure, EUR 103,573,715, is the
**same method cut at the earlier date of 2026-03-31**. They are not two competing definitions; they differ by
one quarter of billing (EUR 8.5M). When someone compares "EUR 103.6M" with "EUR 112.1M" and calls it growth or
a discrepancy, they are comparing two dates, not two methods. Both are reproduced by the pipeline.

**By calendar year (parts billed, net):**

| Year | Parts billed | Note |
|---|---:|---|
| 2023 | EUR 29,282,086 | full year |
| 2024 | EUR 33,145,516 | full year |
| 2025 | EUR 32,381,312 | full year |
| 2026 | EUR 9,184,979 | **partial - first half only.** Do not compare with a full year. |

Source: `01_data/00_derived/gps_spu_by_distributor.csv`.

**Excluded from the parts base, deliberately:** transport, rebate and late-payment interest lines
(EUR 1.14M over 2023-2025), plus service fees, demurrage and e-credit lines outside Europe. Credit notes and
return lines are excluded. The return exclusion is a documented judgement call, not an ERP-confirmed rule -
see file 03.

---

## 2. Service-demand cover - did we sell the parts the schedule implies?

**Definition.** For each market, year and service category:

```
expected units = trucks in service x services per year x addressable share x interval factor
cover          = actual units sold / expected units
```

- **Addressable share is 100%** (decided July 2026). An older note in one reference document still says 70%.
  If a model has that file and computes with 70%, every cover percentage it produces is about 43% too high.
- **Services per year** by vehicle scope: N75 trucks 0.5, light commercial (D-Max and light N-Series) 1.0,
  N35 blend 0.75.
- **Interval factor** for consumables: oil, fuel and urea filters 1.0; air filter 0.5 (**provisional**, waiting
  for IML to confirm, because an air element is roughly every second service); blower filter 1.0. Wear parts
  (brake, clutch) carry their own wear factor of 0.5.
- Capture above 100% is **valid** on the total line, because a part number can be sold into more than one
  fleet (multi-segment parts, cross-brand sales). Never force a rate below 100%.

Source: `01_data/00_derived/pms_capture_by_db_year.csv` (3,024 rows), `line_type = total`, year 2025.
For units and euro this is the right file. **For euro gaps there is a restriction - see section 3.**

**Network, calendar 2025, total line - actual units against expected, and the euro gap:**

| Service category | Actual units sold | Expected units | Cover | Gap |
|---|---:|---:|---:|---:|
| Clutch disc | 1,697 | 31,760 | 5.3% | EUR 3,142,767 |
| Brake pad | 18,408 | 65,154 | 28.3% | EUR 2,780,016 |
| Brake shoe | 7,097 | 77,671 | 9.1% | EUR 2,469,688 |
| Clutch pressure plate | 1,943 | 31,760 | 6.1% | EUR 1,982,854 |
| Blower unit filter | 24,725 | 158,799 | 15.6% | EUR 1,421,877 |
| Brake rotor | 20,714 | 39,700 | 52.2% | EUR 1,394,154 |
| Fuel filter | 70,829 | 158,799 | 44.6% | EUR 1,018,496 |
| Clutch kit | 2,299 | 23,820 | 9.7% | EUR 957,623 |
| Urea (AdBlue) filter | 1,988 | 158,799 | 1.3% | EUR 916,329 |
| Clutch booster | 32 | 15,880 | 0.2% | EUR 700,953 |
| Air filter | 40,948 | 79,399 | 51.6% | EUR 650,458 |
| Release bearing | 1,019 | 23,820 | 4.3% | EUR 428,962 |
| Oil filter | 92,035 | 158,799 | 58.0% | EUR 319,619 |
| Pilot bearing | 275 | 15,880 | 1.7% | EUR 27,302 |

**The shape of this is the single most useful insight in the whole data set.** Oil and fuel filters - the
parts everyone assumes are the problem - are the *best* covered categories. The gap is concentrated in wear
parts (clutch, brake) and in filters that are not on the standard service sheet (urea, blower). If someone
argues the problem is "cheap oil filters from the independent aftermarket", this table disagrees.

**By market and category the gaps are more actionable than the network total.** The largest single cells in
2025, each with the fleet base beside it:

| Market | Category | Gap | Cover | Fleet | Gap per truck in service |
|---|---|---:|---:|---:|---:|
| IUK (UK light commercial) | Clutch disc | EUR 1,338,473 | 4.5% | 47,783 | EUR 28 |
| IUK | Brake pad | EUR 806,882 | 24.1% | 47,783 | EUR 17 |
| IUK | Brake shoe | EUR 694,105 | 5.6% | 47,783 | EUR 15 |
| IUK | Clutch pressure plate | EUR 565,154 | 6.5% | 47,783 | EUR 12 |
| IUK | Fuel filter | EUR 485,078 | 16.0% | 47,783 | EUR 10 |
| IUK | Blower filter | EUR 470,253 | 18.4% | 47,783 | EUR 10 |
| UTI (Israel trucks) | Brake pad | EUR 456,181 | 7.0% | 10,336 | EUR 44 |
| UTI | Clutch booster | EUR 388,140 | 1.8% | 10,336 | EUR 38 |
| Belgium | Brake shoe | EUR 344,450 | 6.7% | 9,593 | EUR 36 |
| ITUK (UK trucks) | Urea filter | EUR 342,356 | 7.6% | 23,068 | EUR 15 |
| UMI (Israel LCV) | Brake pad | EUR 332,399 | 8.7% | 18,542 | EUR 18 |
| Germany | Clutch disc | EUR 319,817 | 3.1% | 13,780 | EUR 23 |

Note the per-market totals: IUK EUR 5.8M, UTI EUR 1.86M, Germany EUR 1.86M, UMI EUR 1.76M, Belgium EUR 1.38M,
ITUK EUR 1.32M. **IUK alone is about a third of the whole network's service gap**, which is why the UK light
commercial market carries an action plan of its own.

---

## 3. The euro gap: read this before quoting any number from it

The service gap in euro is the most requested number and the easiest to get wrong.

- **Cover percentages (%) and unit counts are safe to quote.**
- **Euro gap totals are NOT safe to quote externally yet.** Several cells book a zero gap where a market has
  zero actual sales - the worst real outcome produces the best-looking number. The file carries a
  `revenue_gap_quotable` flag: in 2025, 213 of 252 cells are flagged quotable and 39 are not. Summing only
  the quotable cells gives [RESTRICTED INTERNAL NETWORK TOTAL OMITTED] network-wide. **That is an internal working total, not a published
  figure.** Do not present it to a distributor or to IML as the size of the prize.
- **The external ITUK figure is a different number on a different basis** - see section 4.

---

## 4. ITUK exists in two versions on purpose

ITUK (the UK truck distributor) has two correct service-demand numbers, built on different denominators for
different audiences. Both are right. Never show them side by side without explaining the denominator, and
never average them.

| | **External standard** (what ITUK and IML see) | **Internal network view** |
|---|---|---|
| Trucks in service | 22,389 - full DVLA register, March 2026 | 23,068 - the real split across truck classes |
| Services per year | Filters 1.25, wear parts 0.5 | Filters 0.5, wear parts 0.5 |
| Oil filter cover | **35.1%** | **100% capped** (116% uncapped) |
| Service revenue gap | **EUR 2,038,471** across five categories | not quotable as a network total |
| Use it for | IML papers, ITUK correspondence, business cases, external decks | network league tables, ranking ITUK against other markets, trend work |

The two fleet counts are within 3% of each other, so the 35% versus 100% difference is **entirely the service
frequency assumption**, not a data discrepancy.

External ITUK breakdown, calendar 2025: oil filter 35.1% cover and EUR 140,602 gap; fuel filter 65.1% and
EUR 127,440; air filter 13.2% and EUR 736,037; clutch 7.8% and EUR 392,559; brake 35.3% and EUR 641,833.
Weighted cover 35.9%.

**The story this tells is a real workshop capture gap on the maintenance schedule, with the largest euro
leaks in air filter and brake/clutch wear - not in filters in general.** That is the opposite of the
intuitive answer and is worth holding on to.

---

## 5. Spend per truck in service

**Definition:** parts billed in a market, divided by the trucks in service for that market and year. Net
parts sales after exclusions.

Source: `01_data/00_derived/gps_spu_by_distributor.csv`.

**Calendar 2025:**

| Market | Parts billed | Trucks in service | Spend per truck |
|---|---:|---:|---:|
| Ireland | EUR 1,187,459 | 3,056 | EUR 389 |
| UTI (Israel trucks) | EUR 3,331,512 | 10,336 | EUR 322 |
| ITUK (UK trucks) | EUR 5,564,544 | 22,389 | EUR 249 |
| Finland | EUR 277,921 | 1,204 | EUR 231 |
| Belgium | EUR 2,109,332 | 9,594 | EUR 220 |
| Iceland | EUR 85,282 | 406 | EUR 210 |
| Portugal | EUR 1,709,794 | 8,176 | EUR 209 |
| Malta | EUR 206,502 | 1,040 | EUR 199 |
| Germany | EUR 2,535,932 | 12,855 | EUR 197 |
| Cyprus | EUR 428,443 | 2,308 | EUR 186 |
| UMI (Israel LCV) | EUR 3,319,344 | 18,542 | EUR 179 |
| Norway | EUR 1,416,552 | 7,929 | EUR 179 |
| Denmark | EUR 148,221 | 851 | EUR 174 |
| Romania | EUR 175,218 | 1,071 | EUR 164 |
| Sweden | EUR 1,278,462 | 8,443 | EUR 151 |
| Greece | EUR 520,304 | 3,742 | EUR 139 |
| IUK (UK light commercial) | EUR 6,131,920 | 47,783 | EUR 128 |
| Hungary | EUR 330,031 | 3,734 | EUR 88 |
| **Network** | **EUR 32,381,312** | **163,459** | **EUR 198** |

Caveats that must travel with this table:

- Ireland's fleet count in this file (3,056) is larger than the fleet count used in the target-spend model
  (2,161) for the same year, which pushes its spend per truck down in one view and pulls its capture above
  100% in the other. The two fleet bases have not yet been reconciled. Treat Ireland's exact ranking as
  provisional.
- ITUK and Germany also have two fleet counts in circulation (22,389 versus 23,068; and 12,855 versus 13,780)
  depending on whether the class split has been applied. Small ranking differences between markets should not
  be over-interpreted until the fleet bases are unified - see file 03.
- Ukraine, Palestine, Armenia and Kazakhstan have revenue but no fleet register. Do not compute a per-truck
  figure for them.

---

## 6. The target-spend ceiling and the gap

**Definition.** Take the fleet in service in a market and multiply it by a defensible euro target per truck
per year for each vehicle class (EUR 296 for an N35 light truck, EUR 739 for an N75, EUR 887 for heavy,
EUR 250 for a D-Max light commercial). That gives the **ceiling** - the total service spend the fleet should
generate. What ISZE actually billed is the **captured** figure. The remainder is the **gap**.

The ceiling is a maximum and an assumption, not a forecast. It is flat across vehicle age, and the addressable
share is 100% by convention.

Source: `01_data/00_derived/wallet_waterfall.csv`.

**Network, calendar years:**

| Year | Trucks in service | Ceiling | Captured | Capture | Gap (ceiling less captured) |
|---|---:|---:|---:|---:|---:|
| 2023 | 151,715 | EUR 51,007,517 | EUR 28,313,839 | 55.5% | EUR 22,693,678 |
| 2024 | 160,125 | EUR 54,126,834 | EUR 31,958,636 | 59.0% | EUR 22,168,198 |
| 2025 | 163,198 | EUR 55,253,312 | EUR 30,756,772 | 55.7% | EUR 24,496,540 |

Note what happened in 2025: the fleet grew, the ceiling grew, and captured revenue **fell** - so the gap
widened by about EUR 2.3M. That is the single most important number in this file.

(One accounting note so the arithmetic reconciles: the market table below shows the file's own `uncaptured`
column, which sums to EUR 24,727,686, slightly more than the EUR 24,496,540 above. The difference - about
EUR 231,000 - is where a market billed *above* its own ceiling. The excess is not netted off against another
market's gap, so the market column adds up a little higher than the network subtraction. Neither figure is
wrong; they answer slightly different questions.)

**Calendar 2025 by market** (18 markets; sorted by the gap):

| Market | Trucks in service | Ceiling | Captured | Capture | Gap | Gap per truck |
|---|---:|---:|---:|---:|---:|---:|
| ITUK | 23,067 | EUR 12,212,051 | EUR 5,564,544 | 45.6% | EUR 6,647,507 | EUR 288 |
| IUK | 47,783 | EUR 11,945,750 | EUR 6,131,920 | 51.3% | EUR 5,813,830 | EUR 122 |
| UTI | 10,336 | EUR 8,271,300 | EUR 3,331,512 | 40.3% | EUR 4,939,788 | EUR 478 |
| UMI | 18,542 | EUR 4,635,500 | EUR 3,319,344 | 71.6% | EUR 1,316,156 | EUR 71 |
| Germany | 13,780 | EUR 3,808,128 | EUR 2,535,932 | 66.6% | EUR 1,272,196 | EUR 92 |
| Portugal | 7,208 | EUR 3,052,087 | EUR 1,709,794 | 56.0% | EUR 1,342,293 | EUR 186 |
| Belgium | 9,593 | EUR 2,453,507 | EUR 2,109,332 | 86.0% | EUR 344,175 | EUR 36 |
| Sweden | 8,443 | EUR 2,110,750 | EUR 1,278,462 | 60.6% | EUR 832,288 | EUR 99 |
| Norway | 7,929 | EUR 1,982,250 | EUR 1,416,552 | 71.5% | EUR 565,698 | EUR 71 |
| Ireland | 2,161 | EUR 956,313 | EUR 1,187,459 | 124.2% | EUR 0 | - |
| Greece | 3,742 | EUR 953,593 | EUR 520,304 | 54.6% | EUR 433,289 | EUR 116 |
| Hungary | 3,734 | EUR 933,500 | EUR 330,031 | 35.4% | EUR 603,469 | EUR 162 |
| Cyprus | 2,308 | EUR 676,267 | EUR 428,443 | 63.4% | EUR 247,824 | EUR 107 |
| Malta | 1,040 | EUR 378,827 | EUR 206,502 | 54.5% | EUR 172,325 | EUR 166 |
| Finland | 1,204 | EUR 301,000 | EUR 277,921 | 92.3% | EUR 23,079 | EUR 19 |
| Romania | 1,071 | EUR 267,750 | EUR 175,218 | 65.4% | EUR 92,532 | EUR 86 |
| Denmark | 851 | EUR 213,239 | EUR 148,221 | 69.5% | EUR 65,018 | EUR 76 |
| Iceland | 406 | EUR 101,500 | EUR 85,282 | 84.0% | EUR 16,218 | EUR 40 |

Four things to notice:

- **The gap is highly concentrated.** The top five markets hold 81% of the network gap. ITUK alone is 27%.
- **Per truck, UTI is the worst market in the network** at EUR 478 of uncaptured service spend per truck,
  nearly four times IUK's rate. UTI is the market where an hour of work is worth most.
- **Ireland captures more than its ceiling** (124%). That does not mean the ceiling is wrong in principle;
  it means Ireland's fleet count in this model is lower than its fleet count in the spend-per-truck model.
  Until those are reconciled, cite Ireland's rate with that caveat.
- **This ceiling is bigger than the parts business by a factor of about 1.7** (EUR 55.3M against
  EUR 32.4M billed). That ratio is the whole commercial argument, and it needs a caveat: the ceiling is
  modelled and full-gap, not winnable. Discount it heavily and the asymmetry still holds.

**Two separate caveats about this model.**

First, eight markets out of eighteen have their vehicle targets still on a flat EUR 250 placeholder for the
light commercial class rather than a measured rate per model, because the per-model age-spend curve is still
pending from IML. Eight markets sit at exactly EUR 250.0 per truck - IUK, UMI, Sweden, Norway, Hungary,
Finland, Romania and Iceland - and together they are **40.3% of the 2025 ceiling, EUR 22.28M**. The next three
markets (Denmark at EUR 251, Greece at EUR 255, Belgium at EUR 256) are only just above the placeholder, so
the modelled rather than measured share of the ceiling is closer to 46%. A finer per-class split was applied
to the UK truck fleet in September 2026, but the eight at EUR 250 are still on the flat rate. So the *level*
of the ceiling is partly assumption. The *ranking* of markets and categories is far more robust than the level.

Second, the EUR per-truck targets were corrected on 2026-09-17 after the UK truck fleet was found to be priced
at the 7.5-tonne rate when 10,900 of its 22,389 trucks are actually 3.5-tonne. The correction reduced ITUK's
ceiling from EUR 17.18M to EUR 12.21M and its capture from 32.4% to 45.6%, and reduced the network ceiling
from EUR 60.22M to EUR 55.25M. **Any document quoting a network ceiling of EUR 60.22M, a network capture rate
of 51.1%, an ITUK ceiling of EUR 17.18M or an ITUK rate of 32.4% is out of date.** The same class of error
has since been found and fixed in other markets' light truck labels as well.

---

## 7. Original parts versus value parts (the mix)

ISZE sells two tiers: original Isuzu parts, and a value line called BVP. The mix measure answers: of the
original plus value parts billed in a part family, how much by euro is the value line.

Source: `01_data/00_derived/mix_genuine_bvp_pms.csv`. There is **no capture rate for the value line** - it is
a mix measure, not a demand-cover measure.

**Calendar 2025, by market:**

| Market | Original EUR | Value EUR | Value share of the two |
|---|---:|---:|---:|
| ITUK | 873,901 | 158,377 | 15.3% |
| IUK | 496,586 | 148,502 | 23.0% |
| UTI | 63,419 | 407,967 | **86.5%** |
| Ukraine | 129,786 | 113,953 | 46.8% |
| Ireland | 177,442 | 62,487 | 26.0% |
| Belgium | 130,909 | 92,086 | 41.3% |
| Portugal | 88,486 | 122,663 | 58.1% |
| Norway | 181,834 | 26,129 | 12.6% |
| Germany | 146,968 | 52,841 | 26.4% |
| UMI | 30,382 | 134,814 | **81.6%** |
| Sweden | 140,142 | 18,351 | 11.6% |
| Armenia | 44,290 | 64,000 | 59.1% |
| Greece | 61,238 | 46,848 | 43.3% |
| Cyprus | 48,809 | 56,575 | 53.7% |
| Kazakhstan | 7,284 | 71,777 | 90.8% |
| Hungary | 36,707 | 15,244 | 29.3% |
| Romania | 28,241 | 5,935 | 17.4% |
| Finland | 27,330 | 2,617 | 8.7% |
| Denmark | 22,497 | 3,291 | 12.8% |
| Malta | 24,462 | 276 | 1.1% |
| Iceland | 11,307 | 344 | 3.0% |
| Palestine | 346 | 1,795 | 83.8% |
| **Network** | **2,772,366** | **1,606,872** | **36.7%** |

**How to read this, because it is easy to read wrongly.** This is a mix *within the parts we sold*, not a
share of the market. A high value share is not automatically bad: it means the customer stayed inside the
Isuzu catalogue rather than going to an outside brand. In Israel the value line is the volume line (UMI 82%,
UTI 87%), which is a commercial strategy, not a failure. In Sweden (11.6%), Malta (1.1%) and Iceland (3.0%)
the value line is barely present at all - that is where the question to ask is whether the value offer has
been introduced to the market rather than whether the mix is "wrong".

The 36.7% network figure is a euro-weighted average dominated by the mix of the markets in it. Never use it
as a target.

---

## 8. Account health

Source: `01_data/00_derived/defection_alerts.csv`. One row per market x service category, with the months
since the last order and the trailing twelve-month revenue at stake.

**This file's data horizon is March 2026** - it is five months behind the billing data and is due a refresh.
State the horizon whenever you use it.

- 265 rows total, of which **25 are active alerts**: 203 rows are at distributor level and 62 at dealer level.
- The trailing twelve-month revenue sitting on the 25 active alerts is **EUR 50,504**. The large majority of
  those alerts carry **zero** trailing revenue, which means the category has already stopped completely.
  Those are not recoverable revenue, they are a list of what has already been lost.
- The pattern is wear parts and clutch: Sweden brake pad (33 months silent), Finland clutch kit (26), Hungary
  pilot bearing (26), Iceland clutch pressure plate (19), Finland clutch pressure plate (16), Germany clutch
  disc (14), Norway release bearing (13).
- The alerts that *do* carry revenue are small and recent: Ireland urea filter (EUR 2,593, 5 months),
  Iceland brake pad (EUR 1,486, 5 months), UKRAINE clutch disc (EUR 976, 6 months), UMI clutch kit (EUR 997,
  11 months).

**Honest reading:** on this data, the recoverable list is short and small. The interesting part is not the
euro at risk, it is that the silent categories are the same wear families that the service-demand table shows
as the biggest gaps. The two measures agree with each other, which is a reason to trust both.

The alert thresholds in this model have **not been calibrated** by Jerome. Treat the list as a conversation
starter, not as a decision.

---

## 9. Tender pipeline

Source: `01_data/14_dashboards/tender_data.json`, generated **2026-09-15 04:20 UTC**. This is the only
permitted tender feed - there is a second copy of the same file and they should not diverge.

- 402 raw notices collected, 376 deduplicated opportunities.
- Coverage: 26 countries. Largest by notice count: Germany 176, Poland 49, France 31, Norway 19,
  Portugal 14, Romania 13, Belgium 12.
- Assigned decisions: 1 "attack", 15 "selective", 57 "watch", 303 "ignore".
- 28 opportunities have a deadline within 14 days. 315 have no deadline recorded and 374 have no value
  recorded - so the pipeline is much less complete than the counts suggest.
- 45 opportunities are tagged as relevant to aftersales (parts), which is the subset that matters here.
- 20 duplicate families were detected and 2 notices were flagged as low evidence.

**How to use it honestly:** the value of this feed is the 45 parts-relevant items and the 28 with a near
deadline, not the 376 headline. Almost 70% of collected national opportunities are TED-only (the EU portal)
and sit below the threshold that would trigger a national notice, so the coverage of national portals is a
known gap - only about 8 of 29 footprint countries currently have a live national source.

---

## 10. Warranty

Commercial warranty data sets were published on **2026-09-18** (thirteen files plus a workbook). This is new;
older documents generally do not have a warranty layer at all.

- **Truck parts turnover on warranty: EUR 4,655,881.** Emissions components alone are EUR 2,838,570, which
  is **61%** of the truck warranty parts turnover. Power steering gear is roughly EUR 1.15M.
- A currency error was found and fixed on the day of publication. The truck claim file's currency column
  carries two tokens - "EUR GBP" means pounds and "JPY EUR" means yen - and summing it raw mixes three
  currencies. This means any truck warranty figure published **before** 2026-09-18 that quotes EUR 2,826,045
  for parts turnover, EUR 1,819,033 for emissions (64%), or EUR 800,191 for power steering is wrong. The same
  error does not affect the D-Max figures.
- Netting rule: 11,956 of the lines are UK pounds and they are the largest single block, so the pounds
  conversion drives the total. The audit file names the rate applied line by line.

**What warranty is for in this business:** it is a second signal on the same fleet. A component family that
dominates warranty claims is usually also a part family with a service or quality question. Emissions at 61%
of truck warranty parts is a large, concentrated number that deserves to be looked at beside the
service-demand table.

---

## 11. Fleet data

The fleet model (referred to internally as UIO v19) is an Excel workbook, `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx`.
It gives fleet size by market, vehicle class and model type, with one column per year from 1990 to 2030.

- Grand total including the MIDI regional entity: 2024 actual 252,710; 2025 estimate 258,594; 2026 forecast
  269,314; 2030 forecast 309,125.
- **Excluding MIDI** (which is the convention for ISZE's own targets, because MIDI is not an ISZE customer):
  2024 160,125; 2025 163,199; 2026 forecast 172,379; 2030 forecast 205,357.
- The file's own switch for including or excluding MIDI is currently set to *include*, which is the opposite
  of the stated policy. Anyone reading the headline row off that workbook is reading the wrong number.

**The forecast half of this workbook (2026 onward) should not be quoted.** The fleet projection for future
years is built with a 3% annual scrappage assumption, while the historical part of the same file uses a
survival curve that implies about 10%. The two methods are inconsistent by a factor of three, and the
forecast therefore grows the fleet in every market no matter what is fed in. Three independent checks
confirmed this (see file 03). **The historical part (1990-2025) is usable. The forecast part is not, until
the method is fixed.**

---

## 12. What is not quotable yet

Stated so that no model repeats a wrong number confidently:

| Figure | Why not |
|---|---|
| The EUR 2.04M ITUK gap, applied to any market other than ITUK | It is built on ITUK's own denominator |
| The EUR 18.2M network service gap | Working total from flagged-quotable cells only; not a published figure |
| Any network fleet forecast for 2026-2030 | The projection method is internally inconsistent (file 03) |
| Any per-truck figure for Ukraine, Palestine, Armenia, Kazakhstan | No fleet register |
| "Revenue realisation" or "pocket price" leakage | The price list exists at one date only; applying it backwards measures the price increase, not leakage |
| Any oil-filter capture rate under 50% for ITUK | Legacy denominator; superseded |
| Truck warranty totals published before 2026-09-18 | Currency mixing error |
