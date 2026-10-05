# UTI truck panels: losing sales on price or on availability? (2 Oct 2026)

**Verdict: mainly availability, not price.** A real price complaint exists, but billing data shows no measurable volume lost to price. Holding UTI panels at today's price would not fix what UTI complained about.

Supporting tables: `t1`–`t12` CSVs and `_numbers.json` in this folder; script `uti_panels_analysis.py`.

## Data sufficiency
| Evidence | Verdict |
|---|---|
| What UTI said | Sufficient (Outlook threads, read only) |
| Billing trend | Sufficient (`sales_fact.parquet` to 31 Aug 2026) |
| Availability | Partial: one back-order snapshot on disk (1 Jul 2026); weekly UTI back-order lists WK2–WK40 are only in the mailbox |
| Order type | Blank in `sales_fact` for all markets Apr–Jun 2026 (pipeline gap) |
| Israeli copy-panel prices (trucks) | None in the price ledger |
| Lost sales | Not visible in our data; only UTI can supply |

## What UTI said
- Availability: 11 Jun, many back orders on body/panel parts; "38 order rows in BO (body parts)", "4 wk to 16 wk" order-to-shipping, "same p/n in BO every month 2-5/2026". 27 May, front side bumper 8978862500 "out of stock all the time"; parts taken off other trucks to repair damaged ones (14 Jun). 1 Oct: asks ISZE to stock P700 items to raise fill rate.
- Price: 25 Feb, three body parts "compete aftermarket and used": grille 8974289771 (+3%), front panel 8981226950 (+16%), door 8982606020 (+16%). July: P700 collision package costs EUR 679–2,144 more than the old model (a model change, not the April price change).

## Panel billing (approved AIM release 2026-10-02, Accident & Body > Panels)
- Jan–Aug 2026 vs Jan–Aug 2025: EUR 165,232 → 135,548 (−18.0%); units 5,081 → 5,627 (+10.7%).
- 53% of the euro drop is one F-series grille (8972670504, 38 → 6 units): a 2025 stock build being used up.
- Same parts in both periods: euro −5.3%, units +9.5%. UTI non-panel parts −11.8%; other markets' panels +7.6%. UTI's own panel sales to its customers held (~562 vs ~594 units/month).

## Availability
- Back orders 1 Jul 2026, panels: 21 lines, 98 units, EUR 13.9k at list, open up to 125 days (front side bumpers by sea freight). Roof panel open 139 days; front inner lid ordered four times (normal, rush, off-road) and still open.
- Urgent (rush + off-road) share of panel lines: 5.3% (2025-H1) → 15.6% (Jan–Mar 2026); also rising outside body parts.

## Price
- Same panels: UTI paid a median +4.0% in 2026 vs a median list rise of +12.4%; UTI pays 74% of list on panels (79% in 2025).
- Bigger price rises did not lose more volume (rank correlation +0.10, 123 parts).
- UTI's cost on P700 body parts is ~25% of its selling price, so a 6.4% step adds at most ~1.6% to UTI's shelf price.
- Two of the three named parts fit a price story: front panel 20 → 7 units, grille 28 → 12 units.

## Increase at stake if UTI panels are held
- Panels only: **EUR 13,795** (door 3,790, panel 3,369, step 2,579, grille 1,901, bumper 1,551, fender 604).
- Upper bound, all body except lighting: EUR 19,760 (1.2% of the EUR 1,629,793 total increase).

## Questions for UTI (draft, not sent)
1. Are lost panel jobs lost to waiting on back orders (customer took used/copy part, or insurer settled) or to a too-high quote? Roughly how many of each in six months?
2. Send lost jobs with part number, date and reason, plus "AM parts samples.xlsx" (local copy price vs ours) for P700 bumpers, grilles, front panel, doors.
3. Are copy or used P700 panels on sale in Israel yet, or is genuine the only option today?
4. If ISZE stocks UTI's P700 forecast list, does the volume come back at today's price, and will UTI commit to quantities?

## Back-order trend and copy prices (added 2 Oct)

**Data:** all 39 weekly UTI back-order lists WK2–WK40 2026 saved from Outlook (read only), plus Eran's annotated 9 Jun list and his 14 Jul files. Same layout every week (WK32–33 lack the "Confirmed Qty" column only); sold-to 1799 only. Sufficient for a trend. Saved in `01_data/90_INBOX/UTI_backorders_2026/` with `manifest.csv`. Script `uti_backorder_trend.py`; tables `t13_uti_bo_body_lines_wk2_wk40.csv` (tidy: week, part, description, qty, order date, order type, days open, value), `t13b` weekly summary, `t13c` recurring parts, `t13d` Eran's marked lines, `t14` copy prices.

Caveats: "order date" is the list's requested-delivery date (no order-creation date in the lists); days open = list date minus that date. Value = open qty × today's price list (the lists carry no price), so it is not the price in force that week. Three body parts have no price-list price (75 of 1,415 body lines), so value is slightly understated. Check: WK27 panels (21 lines, 98 units, EUR 13,903) equals the 1 Jul snapshot above.

**Panels (release Accident & Body > Panels), weekly average**
| Weeks | Lines | Units | Value EUR (at list) | Lines open > 60 days | Urgent lines (rush + off-road) |
|---|---|---|---|---|---|
| WK2–13 | 22.3 | 152 | 4,000 | 5.3 | 3.8 |
| WK14–26 | 28.8 | 121 | 6,175 | 7.6 | 8.1 |
| WK27–40 | 18.9 | 89 | 9,516 | 4.2 | 6.7 |

Peak 35 lines in WK23 (3 Jun), when Eran complained. WK40 (30 Sep): 14 lines, 79 units, EUR 9,094, median 24 days open, oldest 62 days; joint-lowest line count of the year (WK7 also 14).

**All body (panels + other body + body parts the release files elsewhere, e.g. roof panel, cowl, inner lid, cab mounting members):** lines 29 → 47 → 33 per week across the three periods; value EUR 4,896 → 10,305 → 20,469 (the H2 rise is a few expensive lines: front doors 8982605971/8982606011, cab mounting members, one service cab 7552044930 at EUR 7,677). Median days open (all body lines pooled) 27 → 34 → 35. Urgent share of body lines 17% → 24% → 37%.

**Recurring parts:** 116 body parts on 238 distinct order lines over the 39 weeks; 33 parts sat on 13 or more weekly lists, 9 on 20 or more. Top: air dam 8972692190 (29 weeks, 6 orders), roof panel 7552077720 (29 weeks, one off-road order, up to 202 days open), upper cowl panel 7475447681 (27 weeks), front side bumper 8978862500 (24 weeks, 4 orders, up to 166 days) and its pair 8978862770 (22 weeks), front panel 7552194470 (20 weeks, 5 orders), front inner lid 7552895450 (20 weeks, 5 orders), centre bumper 7552923240 (18 weeks, 5 orders, still open WK40). This backs Eran's "same p/n in BO every month".

**Eran's 9 Jun list:** the same 167 lines as ISZE's WK24 list, with two columns added. He marked 29 lines with total weeks waiting: 4–16 weeks, median 13 (his "4 wk to 16 wk"); 18 of them panels (median 9.5 weeks), 8 lighting.

**Copy prices (Eran's "AM parts samples.xlsx", 14 Jul):** UTI's sheet gives the local copy supplier price (EUR), what UTI says it pays ISZE ("Genuine fob ISZE"), and UTI's own monthly copy sales qty. Set against the price list and the reference dealer price (price list × 2.19, provisional):
| Part | UTI desc. | Copy EUR | UTI pays ISZE (UTI's figure) | Price list | Ref. dealer price | Copy vs what UTI pays | Copy units/month |
|---|---|---|---|---|---|---|---|
| 8974289771 | grille | 44.00 | 122.00 | 142.21 | 311.44 | −64% | 3.7 |
| 8981226950 | front cover | 39.71 | 190.00 | 247.82 | 542.73 | −79% | 6.0 |
| 8980302303 | front cover | 56.78 | 308.00 | 402.52 | 881.52 | −82% | 5.0 |
| 8974060399 | panel fr. | 38.71 | 53.00 | 70.09 | 153.50 | −27% | 6.0 |
| 8974056285 | bumper 7.5T | 48.00 | 134.00 | 175.09 | 383.45 | −64% | 3.7 |
| 8974259070 | bumper 10T | 102.46 | 199.76 | 260.64 | 570.80 | −49% | 13.8 |
| 8980430610 | mirror | 8.47 | 19.60 | 22.08 | 48.36 | −57% | 35.8 |
| 8980430601 | mirror | 26.64 | 75.93 | 85.41 | 187.05 | −65% | 13.5 |
| 8982413230 | head lamp | 84.57 | 85.93 | 96.65 | 211.66 | −2% | 16.8 |
| 8981554580 | lamp side | 13.70 | 26.57 | 29.42 | 64.43 | −48% | 21.8 |

- On the body parts the copy sells at 27–82% below what UTI pays ISZE, and 93–94% below the reference dealer price on the two front covers. A 6.4% step on the price list does not move that gap; the price complaint is real but it is a copy-versus-genuine gap, not one the April step created.
- Two of the three parts Eran named on 25 Feb (grille 8974289771, front panel 8981226950) are on this sheet; UTI's column "AM qty. sales per month" shows 3.7 and 6 copies a month (whose sales, UTI's or the market's, is not stated).
- All 31 rows (incl. service parts) are in `t14`. Three rows look like a unit mismatch, not a real price: brake linings 1883113430 / 1883113850 show the copy above genuine (+260% / +138%); wiper blade 8971345612 shows UTI's genuine price at 2.1× the price list. Not used.
- "p700 colission parts est..xlsx" is UTI's P700 collision/radar sales Jan–Jun 2026 and its year-end estimate (95 parts); it carries no prices. Saved, not analysed further.

**What it says:** panel back-order lines and units peaked in May–June and have eased since July (value at list rose because the open lines are pricier), but the same body parts keep coming back and urgent orders are a growing share. Copies undercut genuine by roughly half to four-fifths on bumpers, grilles and front covers. Both points stand; neither is caused by the planned step.
