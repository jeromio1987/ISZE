# BRIEF FOR THE RESEARCH MODEL — service demand by tonnage band, on unique parts

**Version 4, 2026-09-22.** Hand this to the model with `00_READ_ME_FIRST.md`. Section 14 of the read-me records what changed in v4. **The data files did not change** — the tonnage layer was regenerated on 22 September and is current. Corrections since v1 are marked **[corrected]** and listed in full in `02_CORRECTION_LOG.md`. Nothing here has been published, mailed or sent to a distributor.

**[changed 22 Sep]** The tonnage layer was regenerated on billing through **August 2026**; it had been built on June. The exclusive share moved from 29.96% to **29.77%** and the tagged total from EUR 4,305,334 to **EUR 4,501,286**. The method did not change — two more months of billing came in.

---

## The question being worked

Can aftersales service demand (oil filter, fuel filter, air filter, urea filter, brake pad, brake shoe, brake rotor, clutch kit, clutch disc, clutch pressure plate, release bearing, pilot bearing) be read **by tonnage band** — 3.5 t, 5.5 t, 7.5 t, F-series — and does it move over time?

It matters because spend per truck, service cover and the target-spend gap are each one number per market today. A market that is half 3.5 t trucks and half 7.5 t trucks holds two different service businesses on two different intervals, and one number cannot manage both.

---

## The six things the model must not get wrong

**1. The billing has no vehicle.** `sales_fact.parquet` has no VIN, chassis or model. Tonnage is reachable only through **part number → which vehicles that part fits**. Any answer splitting billed volume by tonnage directly is wrong by construction.

**2. A part number that fits several bands is pooled, never split.** 154 of the 297 candidates fit more than one band and carry EUR 16.2M. Only **143 part numbers** sit on exactly one band, and only that slice gives a measured tonnage trend.

**2b. The two part populations overlap on only 91 part numbers. [corrected]** The 297 band candidates are **not** a subset of the 835 service parts — 206 candidates sit outside that worklist, and the two euro columns are on different bases and windows. Never add them, never quote one as a share of the other. The per-part-number bridge is `data_part_number_decode\14_part_population_bridge.csv`.

**2c. Spending per truck does not exist by band.** Parts billed does split by band (the exclusive slice). Spend per truck does not: the fleet splits by band, but the billed euro in the numerator has no vehicle to sit on. The panel called *"How much does each vehicle in service spend on parts"* is **per customer and per year, market level**. If a model produces a band-level spend-per-truck figure for the whole book, it has invented it.

**3. Never sum `11_nseries_band_evolution.csv`, and get the denominator right. [corrected]** Its `membership` rows are stacked views of the same book. The all-row sum is EUR 25.60M; the additive tagged total is EUR 4.50M. **[corrected in v4]** v3 printed EUR 24.48M and EUR 4.31M, which do not reproduce against the shipped file. **Filter `sums_to_n_series_total == "yes"`, then `membership == "single_band_only"`.** The exclusive share on that correct denominator is about **30%** — as the file carries it, **EUR 1,340,014 of EUR 4,501,286 = 29.77%** — not the 11% a v1 draft printed. **A defect found on 22 September inflates the exclusive set by EUR 2,645.43, so the true figure is 29.71% (−0.06 pt), and the file has not been corrected. State both.**

**4. Two service-interval lanes, never blended.** ITUK is the **IML v7** lane (filters 1.25 visits a year, clutch and brake 0.5, on a 22,389-vehicle DVLA fleet, brake factor 0.4). Every other market is the **PRISM** lane (trucks 0.5, F-series 0.667, LCV 1.0). Inside ITUK the N35 and N75 run different intervals, because 1.25 is the N75 rate.

**5. Lowering expected demand raises cover. [corrected]** Cover is `actual ÷ expected`. A v1 draft claimed the N35 interval correction would cut ITUK oil-filter cover from 116% to the 70s. **That is backwards and is withdrawn**: on the deck's own example the correction moves cover from 35.1% to 44.5%, i.e. up about 9 points.

---

## The three questions the model can genuinely help with

**A. Is the 143-part-number slice enough to carry a tonnage story?**

About **EUR 1.34M exclusive of EUR 4.50M additive, roughly 30%** of the tagged N-series service book over January 2023 to August 2026, running 27%–33% a year. As the file carries it that is **1,340,014 ÷ 4,501,286 = 29.77%**; a known defect of EUR 2,645.43 makes the true figure 29.71%, and the file has not been corrected. **Give both numbers.** Nearly all of it is the 7.5 t band — EUR 337,000 to EUR 383,000 in each of the three complete calendar years, on **34 exclusive part numbers**; 3.5 t is EUR 3,300 to EUR 5,200 a year on **10**. The 2026 figures are part-year. **[corrected in v4]** v3 printed 15–17 and 2–4 part numbers, which do not reproduce from the shipped file. Band-exclusive families: oil filter (8), fuel filter (4), clutch kit (19), clutch pressure plate (1), clutch disc (2). Air filter, brake pad, brake shoe and release bearing have **zero** exclusive part numbers.

**And say what it does not cover.** **Five service families have no tonnage candidates at all — 174 part numbers, EUR 5.99M**, including **brake rotor (109 part numbers, EUR 4.46M)**, the second-largest family by euro. For brake rotor this is a dead end rather than a fixable join: 92 of its 109 part numbers carry no vehicle reference at all, and the family holds one vehicle string, `N*R,N*S`, a wildcard that cannot become a band. **A tonnage story presented without that sentence would be misreading its own coverage.**

**B. Is the F-series question answerable?**

Heavy-truck family: 164 part numbers, EUR 174,832 of 2025 billing, on 1,238 vehicles in three markets. F-series parts shared with the N-series are pooled into `shared_across_families` (53 part numbers, EUR 4.16M), so "the F-series uses fewer service parts" would be an artefact of the pooling, not a finding. There is also **no 10 t band**, so a 7.5–10 t distinction cannot be made.

**C. Which parts of this could become a defensible ITUK-versus-UTI comparison?**

Not yet. The supplied groups have no separate 10 t band, so a 7.5 t grouping cannot establish an ITUK-vs-UTI mix difference. A fair comparison needs a common validated basket with the coverage outside it shown, zero only where source completeness establishes it, and missing records left unknown. Differences in billed euro also reflect price, mix and stocking, not only service volumes — the residual is not competitive leakage without more evidence. **Do not produce a performance winner from this data.**

---

## What the answer must look like

- **Euro first, never a unit count alone.** Every figure carries euro, the service family and the fleet denominator, or a rate per vehicle. A part-number count on its own is not a finding — for the sixteen rows in §14a that means "EUR 17,477.34, mostly fuel and oil filters, 0.39% of the tagged book, EUR 0.48 per truck in service", not "16 part numbers".
- **Say "measured" or "modelled" every time.** The exclusive slice is measured. `19_expected_vs_actual_by_band.csv` is modelled expected demand beside a market-level actual, and its `gap_eur_band_share` is a modelled allocation, never measured leakage.
- **Name the lane** beside any cover or capture figure.
- **State the period, one clock, and whether it is complete** on any year-on-year claim.
- **Admit the blank.** 50 of 120 model codes are unresolved, including the codes that would separate 3.5 t from 7.5 t.
- **Do not quote the withdrawn 30.02%. [v4]** The claim that the exclusive share rises to 30.02% under the `NMR` correction **double-counted six rows that are already `3.5t_N35 / single_band`** and **is withdrawn.** The share does not move for that reason, and the part-number count behind it does not move from 44. The `NMR` correction and the EUR 2,645.43 defect are on **disjoint part numbers and do not interact.**
- **Keep the residue visible, but do not overstate it. [corrected in v4]** The sixteen part numbers the candidate table calls exclusively 5.5 t are **not** an open weight conflict: **14 name `NKR` and only 2 name `NMR`**, and six are already `3.5t_N35 / single_band` in the live file today. `NKR` is the 3.5 t rung in Europe. What is genuinely unresolved is the two `NMR` rows, whose only evidence is the wildcard `NL*,NMR` and which carry EUR 0.00 — and separately whether the 5.5 t band should be published as a rung at all. **5.5 t holds 2 part numbers and EUR 0.00. Nothing here blocks the band.** Never count a wildcard as a band.

---

## What to ignore

- The withdrawn heavy-truck claim of "95 part numbers / EUR 1,955,749" — a substring bug where `F*` matched `TF*`, the D-Max pickup wildcard. It does not reproduce.
- The `Annual Mileage` column in `n35 mileages all.xlsx`. It divides odometer by a shrinking vehicle age, so the newest reading equals the odometer itself. Use `data_context\21_mileage_reference.csv`.
- **Mileage moved between distributors. [corrected]** The 14,494 km/yr figure is **IUK** (the UK light commercial Grafter fleet), not ITUK. ITUK's own measured figure differs. A v1 draft used the wrong label.
- Anything under `01_data\raw\` (line-level billing) and the full price list. Those cannot leave the internal workspace.
- **Treating a pass count as proof.** The pipeline report shipped in this pack reads **154 pass / 2 warn / 0 fail** (2026-09-22T16:44:37Z). Both warnings are live and informative: the lost-sales model is current only to 2026-06-30 while the billing runs to 2026-08-31, and two Denmark years are unfilled. The tie-out that was failing turned out to be a **stale model, not a broken number**. But 0 fail on arithmetic checks is not a cleared pipeline: **the `NMR` residue and the EUR 2,645.43 inflation of the headline (§14 of the read-me), the UTI 3.5 t inconsistency and the population bridge** are all still open, and no pass count closes any of them.

---

## Status gate

**Do not distribute new tonnage performance claims while the `NMR` residue, the known EUR 2,645.43 inflation of the headline, the UTI 3.5 t inconsistency and the population bridge remain unresolved.** Correct the evidence first; activate band-level comparison only for the scope the corrected evidence supports.
