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
