# Room to raise, by part number: where the +5% can best come from

2 October 2026. Internal working note that feeds the pricing paper update. Nothing here changes a price, the price list, the proposal workbook or the market exercise.

**Question.** The market holds from the 30 September exercise give up about EUR 0.39M of the EUR 1.63M step (+5% on EUR 32.6M of parts billed, July 2025 to June 2026). The exercise's answer was to move the rest of the book about +7%. Can the gap be recovered more selectively, part by part?

**Short answer.** Yes, at the arithmetic level. Option B puts the whole gap on captive repair and body parts at about +3.7 points on top of their proposal move. Service parts carry nothing extra, and only 5 parts reach the "factory move + 5 points" ceiling. But the evidence that those parts really have room is thin. "Captive" here mostly means that **no competitor evidence was found**, not that competition was proven to be absent. Where we do have outside prices, they mostly argue against raising. The separate order-terms lever is about as large as the gap.

Terms used:
- **Reference dealer price** = our price list x 2.19 (provisional basis, Jerome 2 Oct). It is what a dealer customer pays at the counter after distributor and dealer margins.
- **Index** = outside price divided by our reference dealer price. Above 1.0, the outside seller is dearer than us.
- **Captive (strict)** = no competitor part number (confirmed or likely), no aftermarket price seen, no cheaper Isuzu BVP alternative, not in the "Competitive parts" family of the classification, and not measured as a category where the distributor sells under 80% of need.
- **Free lines** = sales lines that are not held by the market exercise and not CIS. Only free lines take extra.
- **Uplift** = euro above the 29/30 Sep proposal move.

All euros are parts billed in the proposal base (July 2025 to June 2026, volume held constant, before any dealer reaction), unless stated otherwise.

## 1. Is the data good enough? (step 0)

Base: 15,273 part numbers, EUR 32,595,853 (`room_to_raise_summary_2026-10-02.json` > `sufficiency`).

| Angle | Coverage: parts | Coverage: % of parts billed | Verdict |
|---|---:|---:|---|
| 1a Aftermarket shop price on file | 266 (1.7%) | 21.0% | **Partial**: a flag on top sellers, not a driver |
| 1b ...of which dearer than our reference dealer price | 46 | 1.4% (EUR 0.45M) | Thin |
| 1c Genuine Isuzu sold outside our network (grey) | 1,167 (7.6%) | 50.4% | **Partial**: one main source (Amayama, 1,093 parts); x2.19 basis provisional |
| 2a Competitor number, confirmed/likely | 78 (0.5%) | 15.4% | Thin |
| 2b Competitor evidence, brief definition (number or aftermarket price) | 294 (1.9%) | 24.5% | **Insufficient to prove captive**: captive = absence of evidence |
| 2c Family from approved release 2026-10-02 | 15,273 (100%) | 100% | Sufficient; used to exclude the "Competitive parts" family (4,146 parts, 44.4%) |
| 3 Order lines and slow movers | 15,273 (100%) | 100% | **Sufficient** |
| 4 Order type (stock / rush / off-road) | 100% | 100% | **Sufficient** for the order-terms lever |
| 5 Dealer response per part | 3,819 (25%) | 73.7% | **Partial**: per-part response is at noise level, so it is a flag only |
| 6 LCV vs truck | 12,522 (82%) | 97.7% | **Sufficient** for a split; part of it is inferred (see 6) |
| 7 P700 new-only parts | 14 in base | 0.002% | Not a lever this year |
| 8 UMI service parts | 903 parts, EUR 1.48M UMI service billing | — | A flag; the leasing share is unknown |

What this means: angles 3, 4 and 6 are solid. Angles 1, 2 and 5 cannot carry a part-by-part price decision across the book. Option C therefore ends up driven mostly by "captive", slow movers and urgent-order share, not by outside prices.

## 2. The three ways to recover the gap

Held by the market exercise, recomputed on line data here: **EUR 388,914**. The exercise published EUR 388,040. The difference is EUR +879 for UMI lighting, which the exercise named as a hold but did not count, and EUR -7 on UTI lighting, where the exercise used a rounded 6.35% (`summary.json` > `holds`). Holding UTI truck panels as well (228 parts, EUR 215,778 billed) gives up a further **EUR 13,795**, total EUR 402,709. CIS (Armenia, Kazakhstan) keeps its proposal move in every option. The 29 brake pad kits stay at 0%.

Every option lands on exactly EUR 1,629,793 (+5.00%). Source: `room_to_raise_scenarios_2026-10-02.csv`.

**Without the UTI panels hold:**

| | A: rest of book up proportionally | B: captive repair + body only | C: room-weighted (angles 1-5) |
|---|---|---|---|
| How | every free part x1.33 of its proposal move | +3.7 pts on 8,447 captive repair/body parts (EUR 10.6M) | +1.1 pts per score point on 12,741 parts (EUR 15.7M) |
| Average move on free lines | 7.04% | 7.04% | 7.04% |
| Uplift above proposal | EUR 396,568 | EUR 396,568 | EUR 396,568 |
| Share of uplift on captive parts (strict / brief definition) | 64% / 85% | 100% / 100% | 91% / 98% |
| Uplift on service / repair / body | 137k / 152k / 108k | 0 / 218k / 179k | 90k / 175k / 131k |
| Average move: service / repair / body (proposal: 4.2 / 6.3 / 6.0%) | 3.0 / 8.2 / 7.4% | 2.3 / 9.1 / 8.6% | 2.7 / 8.5 / 7.8% |
| **Ceiling: factory move + 5 pts**, parts at ceiling (billed) | 56 (EUR 263k) | 5 (EUR 242k) | 8 (EUR 247k) |
| Typical (median) part move | 8.5% | 10.1% | 9.7% |
| **Ceiling: 12% max**, parts at ceiling (billed) | 1,119 (EUR 735k) | 833 (EUR 486k) | 722 (EUR 381k) |

Under the 12% ceiling the proposal itself already exceeds 12% on 93 parts. Cutting them gives up EUR 16,079 that also has to be recovered, so uplift rises to EUR 404,993. Under "factory + 5 pts" only 5 proposal moves are cut (EUR 7,654).

**With the UTI panels hold** (proposed, not confirmed): average on free lines 7.11%, uplift EUR 410,363 (factory + 5) / EUR 418,787 (12% max). Parts at ceiling: A 57 / B 5 / C 11 (factory + 5) and A 1,132 / B 831 / C 1,027 (12% max). The split by captive share and segment barely moves (same CSV, `uti_panels_held = True`).

**By market**, average move on all lines including held ones, factory + 5 ceiling, no panels hold. Proposal shown first (`room_to_raise_scenarios_by_segment_market_2026-10-02.csv`):

| Market | Proposal | A | B | C |
|---|---:|---:|---:|---:|
| ITUK (UK trucks) | 5.05% | 6.62% | 5.79% | 6.15% |
| IUK (UK D-Max) | 5.05% | 3.56% | 4.13% | 3.77% |
| UTI | 4.73% | 5.88% | 5.49% | 5.90% |
| Germany | 4.85% | 3.46% | 4.00% | 3.67% |
| UMI | 5.08% | 2.11% | 2.28% | 2.14% |
| Belgium | 5.41% | 4.67% | 5.39% | 4.94% |
| Portugal | 5.13% | 6.81% | 6.30% | 6.75% |
| Norway | 4.70% | 3.95% | 4.64% | 4.26% |
| Sweden | 5.15% | 6.83% | 7.06% | 6.80% |
| Ireland | 5.25% | 6.90% | 6.35% | 6.59% |

All 21 markets are in the CSV.

## 3. What the scan shows

1. **B is the cleanest answer to "who carries the EUR 389k".** It moves no service part beyond its proposal move, which is where the complaints and the holds are. The ceiling barely binds (5 parts at "factory + 5"), and all of the extra lands on parts with no competitor evidence. The cost is a typical captive repair or body part moving about 10% instead of 6.3%.

2. **The outside prices we have point the other way.** Where an aftermarket shop price exists (266 parts, 21% of the euro), the rival sits at a median **0.56x** our reference dealer price (euro-weighted 0.44x). 182 of those parts, EUR 6.0M, are below 0.8x. Only 46 parts (EUR 0.45M) have a rival above us. Source: `summary.json` > `index_distribution`, ledger `01_data/00_derived/price_observations.parquet`. This is why C cannot be a strong "outside price" allocation: the data mostly names parts to hold, not parts to raise.

3. **Genuine Isuzu sold outside our network is dearer than us.** On 929 of 1,167 parts with a grey price (EUR 12.8M billed), the grey genuine price is at or above our reference dealer price (median 1.17x). It comes mostly from Amayama, an exporter's retail price. So on these parts a raise is not undercut by grey genuine, but this rests on the provisional x2.19 basis.

4. **"Captive" is mostly absence of evidence.** 71% of parts (46% of the euro) pass the strict captive test. Only 294 parts have any competitor evidence at all. Body parts look almost entirely captive (2,823 of 2,980), but body aftermarket (pattern parts) has simply not been searched. Treat B's "non-competitive body" as "no competitor found yet".

5. **The holds fall mostly on D-Max, so trucks carry more.** D-Max parts average 4.4% (A), 4.8% (B) and 4.5% (C), against 5.1% in the proposal. Truck parts average 6.4%, 5.8% and 6.2%, against 5.2%. B moves the most back onto D-Max, because captive D-Max repair and body parts are large (PM sensors, front bumper). The split comes from `vehicle_family_bands.csv` (456 parts), the APL part lists of 12 Aug (4,966 parts) and who buys the part (7,100 parts). Who buys it is an inference: 95%+ of its billing goes to LCV-only distributors (IUK, UMI, Nordics, Hungary, Romania) or to truck-only ones (ITUK, UTI). It agrees with the other two routes on 114 of 115 and 4,346 of 4,463 parts.

6. **Flag on IUK (UK D-Max).** IUK is the only market where dealers measurably bought less after the April 2026 rise (-1.08, plus or minus 0.90, `dealer_price_response_2026-09-29.json`). Only its service parts are held. B puts EUR 90k of extra on IUK repair and body (A: EUR 54k, C: EUR 68k). IUK Accident & Body parts that got a rise in April fell 13.5% against IUK's own median, on 166 parts (`dealer_response_by_category_2026-10-02.csv`). That is a noise-level reading, but it points at exactly the parts B raises.

7. **Order terms are a lever about the size of the gap, separate from the price list** (CY2025 lines x 2025 list, the exercise's method; `lever4_order_terms_2026-10-02.csv`; CIS left at 0):
   - (a) Narrowing the stock-order discount by 1 point everywhere: **EUR 213k**. EUR 111k of that is in markets without a service hold. Halving each market's gap to list: **EUR 452k**, mostly UTI EUR 188k (pays 86.0% on stock orders), UMI EUR 96k (91.4%), ITUK EUR 72k (96.2%), IUK EUR 47k (97.3%) and Norway EUR 28k (95.6%). UTI's and UMI's levels are customer conditions, and UMI and IUK are hold markets, so this is a negotiation, not a list change. Palestine adds EUR 7k (pays 62.6%).
   - (b) Rush and off-road surcharge +1 point: **EUR 46k**; +2 points: EUR 93k (urgent list value EUR 4.63M).

8. **Slow movers are many parts but little money.** 10,081 parts (66%) had 6 or fewer order lines in 12 months, but they are only 9.4% of the euro. They help C spread the uplift thinly. They do not fund the gap.

9. **P700 new-only parts are a next-price-list item.** Of 826, 135 were ever billed (EUR 253k, of which EUR 229k in 2023), 14 are in this year's base (EUR 660) and 7 billed EUR 98 in July and August 2026 (`p700_new_only_billing_2026-10-02.csv`). They need a first price, not an increase.

10. **UMI service (EUR 1.48M billed, 903 parts) depends on UMI's leasing share.** Leased double cabs must use genuine parts for two years. If leasing is most of UMI's volume, its service hold (EUR 65k of step in the exercise) could be lifted, which shrinks the gap by that much. Every UMI service part carries the flag "depends on UMI leasing share (unknown)".

11. **A has a side effect.** Scaling the factory-led move pushes hardest on parts whose factory price already jumped. Under "factory + 5" its largest move is 152%, on a part whose factory price more than doubled. B and C add points rather than multiplying.

## 4. How the room score (C) is built

This is a choice, not a measurement. Points per part: captive (strict) +2; aftermarket shop index of 1.0 or more +2, below 0.8 -2; grey genuine index of 1.0 or more +1, below 0.8 -1; slow mover +1; urgent orders 50%+ of its euro +1; volume fell after the April rise -1. The floor is 0. The score is forced to 0 for pad kits, lubricants and parts the proposal already holds because the distributor sells under 45% of need. Distribution: score 0 on 1,242 parts (EUR 13.8M), 2 on 3,757 (EUR 7.8M), 3 on 5,110 (EUR 6.5M), 4 on 2,869 (EUR 0.8M) (`summary.json` > `room_score_dist`).

## 5. Open points for Jerome

1. **UTI panels**: confirm the hold. As defined here it is the approved release `Accident & Body > Panels` on UTI lines: 228 parts, EUR 13,795 of step.
2. **UMI lighting**: the exercise named it but did not count it (EUR 879 of step, EUR 676 billed; one lamp's factory price more than doubled). Keep it in?
3. **CIS** = Armenia and Kazakhstan, as in the exercise. The proposal's own "CIS" market label also contains Ukraine, which here gets the normal treatment.
4. **Option A** is read as "scale every free part's proposal move", so the shape stays factory-led. It averages 7.04% on free lines, which excludes CIS. The exercise's 6.97% included CIS. Literal flat +7% per part was not run.
5. **B's body set** rests on "no competitor found". A quick pattern-part price check on the top 50 body parts would show whether "non-competitive" holds.
6. **Order terms**: should conditions be on the table for the paper at all, given UTI and UMI conditions are negotiated?

## Files

All in `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\price_5pct_proposal_2026-09-29\room_to_raise_2026-10-02\`:
- `build_room_to_raise_20261002.py`: the build. It re-derives the proposal move and asserts it equals `price_5pct_proposal_summary_2026-09-29.json` (k 0.9054, EUR 1,629,793).
- `room_to_raise_by_part_2026-10-02.csv`: one row per part number, every angle, room score, 12 scenario moves.
- `room_to_raise_by_part_market_2026-10-02.csv`: part x market, with billed, order lines, hold reason and scenario move.
- `room_to_raise_scenarios_2026-10-02.csv` and `room_to_raise_scenarios_by_segment_market_2026-10-02.csv`: the scenario tables.
- `lever4_order_terms_2026-10-02.csv`, `dealer_response_by_category_2026-10-02.csv`, `p700_new_only_billing_2026-10-02.csv`.
- `room_to_raise_summary_2026-10-02.json`: sufficiency, holds reconciliation, release id, index distributions and lever totals.

AIM classification: approved release **2026-10-02** (sha256 `0ac91379...`), read through `classification_paths.approved_release()`.
