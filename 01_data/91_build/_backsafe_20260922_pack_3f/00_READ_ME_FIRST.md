# Tonnage bands and unique parts — where this stands

**Version 4, 2026-09-22.** Supersedes v3 of 22 September. v4 corrects the `NMR` / `NKR` section (§7), records the withdrawn figure, and states a known defect in the headline (§14). **No number in the data files changed** — the layer was regenerated on 22 September and is current. This version regenerates the tonnage layer on the billing through **August 2026**; v1/v2 were built on billing through June. Corrections to the earlier packs are in `02_CORRECTION_LOG.md` and flagged inline as **[corrected]**.

**[changed today] The headline numbers moved, because the data moved.** The tonnage layer was built on 19 September from billing through June 2026. It was regenerated on 22 September on billing through **August 2026**. The old exclusive share was 29.96%; it is now **29.77%**. The tagged N-series total rose from EUR 4,305,334 to **EUR 4,501,286**, entirely from the two new months. Nothing in the method changed — the same file simply had two more months of billing to include, and it had been stale against its own declared source for three days.

**A second change, later on 22 September — v4.** Two evidence passes finished after v3 was written and overturned three things it asserted about the same numbers. Full working in §14 and in `02_CORRECTION_LOG.md`.

1. **The sixteen-row mapping conflict is not a 5.5 t blocker, and v3 overstated it.** Fourteen of the sixteen name `NKR` and only two name `NMR`. It was an `NKR` mislabelling in a retired probe dictionary, not an open weight question, and six of the sixteen are already `3.5t_N35` in the live file today. The money at stake is EUR 17,477.34 in total — 0.39% of the tagged N-series book.

2. **A figure v3's working notes carried is withdrawn.** The claim that the exclusive share **rises to 30.02%** under the `NMR` correction **does not survive and is withdrawn.** That arithmetic double-counted six rows that are already `3.5t_N35 / single_band` in the file; their EUR 11,381.95 is most of the EUR 14,198.10 the calculation starts from. The `NMR` correction and the band-union defect in §14c are on **disjoint part numbers and do not interact.**

3. **The headline as written is inflated, and the file has not been corrected.** `EUR 1,340,014 of EUR 4,501,286 = 29.77%` is what the file carries. A defect found on 22 September inflates the band-exclusive set by **EUR 2,645.43**, so the true figure is **29.71% (−0.06 pt)**. Both numbers belong beside each other until someone rebuilds the file.



**Prepared for:** Jerome van der Pluym, VP Vehicle Parts Sales, Isuzu Motors Europe.
**Purpose:** bring a research partner up to speed on the "service demand by tonnage band, on unique parts" exercise. What is measured, what is modelled, what is not known, and the traps that produce a wrong answer.

**Read this file first, then `01_BRIEF_FOR_THE_MODEL.md` (one page), then `04_FILE_CATALOG.csv`.**

---

## 1. The state in one paragraph

Tonnage applicability is now sourced for **297 part numbers**, and only **143** of them fit exactly one band. Every part number that fits more than one band is pooled and never split. On the correct denominator — the additive slice, excluding the non-additive applicability views — the band-exclusive share is about **30% of the tagged N-series service book** — EUR 1,340,014 of EUR 4,501,286, which is **29.77%** as the file carries it — across January 2023 to August 2026. The known defect in §14c inflates that exclusive set by **EUR 2,645.43**, so the true figure is **29.71% (−0.06 pt)**. The file has not been corrected, so quote both: the number it carries and the size of the defect. The monthly pattern runs roughly 27% to 33% per year. That exclusive slice is the **only** place a *measured* tonnage trend can be read. Everything else labelled "by tonnage" is modelled expected demand sitting beside a market-level actual, because the billing has no vehicle.

**[corrected]** v1 printed the exclusive share as about 11%. That was wrong, and wrong for a specific reason: the denominator I used was the sum of **every** row in the band file, which includes the `also_fits_band` applicability views. Those repeat purchasing already counted elsewhere. On the correct additive denominator the 2025 calendar figure is **31.8%**, not 11.4%. The arithmetic is in `data_nseries_bands\10_additive_billing_partition.csv`.

## 2. Why that is the state — the mechanism

**The billing has no vehicle.** `sales_fact.parquet` carries `billing_date, sold_to_sap, sold_to, part_number, description, billed_qty, net_sales_value, saty, year, material, fig_key, fig_key_source`. There is no VIN, no chassis, no model. No volume of billing can be split by tonnage directly, however the query is written.

The only route from billing to a band is **part number → which vehicles that part fits**:

    part number
      -> EPC editions / the parts cross-reference: which model codes it appears under
      -> model code (NLR, NMR, NPR, NQR, NNR, FRR, TFR ...)
      -> tonnage band (via a sourced model-code-to-tonnage table)

**Four defects were found and fixed on the way, and a model re-deriving this will hit them again:**

1. **The original conversion was an unsourced regex dictionary** (`SERIES_TO_GVW` in `03_analytics/Isuzu/pms-pilot/parse_epc_results.py`). Malta and Cyprus both rested on reading `NMR88` as a 3.5 t truck, with no source. It was replaced by `data_part_number_decode\17_model_code_to_tonnage.csv`, one row per model code with the evidence and quote attached.

2. **`F*` matched `TF*`.** `TF*` is the D-Max pickup wildcard. A bare substring test read the blower filters (model string `TF*,UC*`) as heavy truck and produced a "95 heavy-truck part numbers, EUR 1,955,749" figure. That figure **does not reproduce and must not be quoted**. The corrected measurement: the heavy-truck family holds **164 part numbers** and **EUR 174,832** of 2025 billing on a **1,238-vehicle** fleet.

3. **A part number fitting several bands was being apportioned across them.** It is now pooled and never split.

4. **[corrected] Two decoding outputs disagree on some part numbers, and the disagreement is still live.** Six part numbers are band-exclusive `5.5t` in one table and `3.5t_N35` in the other, both carrying the same euro. The cause is traceable: the older probe script hard-coded `NKR → 5.5t`, while the sourced series table places `NKR` at 3.5 t (JP VIN register, `model_dimension.csv`) and leaves `NHR` unresolved. These six must not be used as approved exclusive assignments in either band until the mapping owner rules. See §7.

## 3. The numbers

### 3a. How far the tonnage question is answerable

**[corrected]** v1 presented the 297 as though it sat inside the 835. It does not. They are two different populations that overlap on only 91 part numbers.

| Population | Distinct part numbers | Euro on its own stored basis |
|---|---:|---:|
| Service worklist (`pms_category` present) | **835** | 20,647,863 |
| Band candidates (a band was read) | **297** | 24,745,761 |
| — of those, fits exactly one band | **143** | 7,821,707 |
| — of those, fits more than one band | 154 | 16,924,054 |
| Intersection of the two populations | **91** | — |
| Candidates **outside** the service worklist | **206** | — |
| Worklist rows that never got a band read | **744** | — |
| Families with **no** band candidates at all | **5 families, 174 PNs, EUR 5,990,933** | see §3f |

**The two euro columns are not comparable.** The candidate table's euro is total `sales_fact` billing for that part number on every line, every market, every year; the worklist universe is a different window and basis. Neither is a clean subset of the other. Do not add them and do not quote one as a share of the other. The per-part-number bridge is `data_part_number_decode\14_part_population_bridge.csv`.

### 3b. Which band combinations exist (candidate table, all years)

| Bands the part number fits | Part numbers | Euro | Note |
|---|---:|---:|---|
| 3.5 t + 5.5 t + 7.5 t | 87 | 12,877,246 | the largest block; **no tonnage signal** |
| 7.5 t only | 119 | 7,536,827 | the strongest single band |
| 3.5 t + 5.5 t | 62 | 3,965,018 | |
| 3.5 t only | 8 | 267,403 | |
| 5.5 t + 7.5 t | 5 | 81,790 | |
| 5.5 t only | 16 | 17,477 | **14 of these 16 name `NKR` and 2 name `NMR`; six are already banded `3.5t_N35` in the live file (§14a)** |

**[corrected, and corrected again in v4]** v1 said nothing is exclusive to 5.5 t "in the whole service list". That was wrong as written: the candidate table carries 16 part numbers labelled exclusively 5.5 t. **v4 changes why.** The label rests on a retired probe dictionary that mapped `NKR` to 5.5 t; **14 of the 16 name `NKR` and only 2 name `NMR`**, six are already `3.5t_N35 / single_band` in the live file, and the two `NMR` rows rest only on the wildcard `NL*,NMR`. So the accurate statement is narrower still — **the strict in-scope N-series decode carries no exclusive 5.5 t record, and 5.5 t is not measurable on this table:** it holds 2 part numbers and **EUR 0.00**, and the honest verdict for those two is `unresolved`, not 5.5 t. See §14a.

**[corrected in v4] The six euro figures in §3b above did not reproduce against `13_band_candidates_297_parts.csv` as shipped beside them** — the part-number counts did, and the euro now do. The heading block of the table above is unchanged at EUR 24,745,761 for the 297 candidates.

### 3c. The band-exclusive slice, on the correct additive denominator **[corrected]**

| Clock | Period | Additive tagged billing | Band-exclusive | Exclusive share | Non-additive views (exclude) | All-row sum (wrong) |
|---|---|---:|---:|---:|---:|---:|
| CY | 2023 | 1,193,265 | 388,020 | **32.5%** | 2,101,227 | 3,294,491 |
| CY | 2024 | 1,272,656 | 341,381 | **26.8%** | 2,447,935 | 3,720,591 |
| CY | 2025 | 1,212,326 | 385,666 | **31.8%** | 2,176,726 | 3,389,052 |
| CY | 2026 (part) | 823,039 | 224,948 | **27.3%** | 1,574,627 | 2,397,666 |
| FY | 2024 | 1,343,081 | 389,527 | **29.0%** | 2,529,958 | 3,873,039 |
| FY | 2025 | 1,133,480 | 367,080 | **32.4%** | 1,986,052 | 3,119,532 |
| FY | 2026 | 1,340,258 | 364,068 | **27.2%** | 2,611,509 | 3,951,768 |
| FY | 2027 (part) | 442,073 | 120,290 | **27.2%** | 819,641 | 1,261,714 |

Whole window, one clock at a time: **EUR 1,340,014 exclusive of EUR 4,501,286 additive, which is 29.77% as the file carries it** — identical on CY and FY because they are two representations of the same book. **The known defect in §14c inflates the exclusive set by EUR 2,645.43, so the true figure is 29.71% (−0.06 pt). The file has not been corrected.** **Never add CY to FY.**

Inside the exclusive slice the 7.5 t band carries nearly all of it — **between EUR 337,000 and EUR 383,000 in each of the three complete calendar years**, against EUR 3,300 to EUR 5,200 for 3.5 t — on **34 and 10** exclusive part numbers respectively (in-family, whole window). The 2026 figures are part-year. Read the euro from `data_nseries_bands\10_additive_billing_partition.csv` per period rather than from an annual average. A real, narrow, usable series, and not enough on its own to carry a commercial case.

**The same cut by service family** (band-exclusive part numbers versus pooled, and the euro on each side):

| Service family | Part numbers | Band-exclusive | Pooled | Euro exclusive | Euro pooled |
|---|---:|---:|---:|---:|---:|
| clutch kit | 33 | 19 | 14 | 658,994 | 120,122 |
| oil filter | 11 | 8 | 3 | 4,122 | 953,881 |
| fuel filter | 10 | 4 | 6 | 13,413 | 274,559 |
| clutch pressure plate | 2 | 1 | 1 | 56,649 | 166,419 |
| clutch disc | 4 | 2 | 2 | 42 | 171 |
| ~~air filter~~ | 6 | **0** | 6 | 0 | 319,491 |
| ~~brake pad~~ | 3 | **0** | 3 | 0 | 1,520,104 |
| ~~brake shoe~~ | 7 | **0** | 7 | 0 | 88,790 |
| ~~release bearing~~ | 2 | **0** | 2 | 0 | 2,829 |

**Air filter, brake pad, brake shoe and release bearing have zero band-exclusive part numbers** — no tonnage trend is measurable for them, however the book is cut. That is the single most useful fact in this table and the reason a tonnage story cannot be built around brakes.

### 3f. Five service families have no tonnage candidates at all — scoped on 22 September

| Family | Part numbers | Euro | In the family file | Family file's own verdict |
|---|---:|---:|---:|---|
| **brake rotor** | 109 | **4,457,248** | 109 | **92 of 109: "no vehicle reference"**, confidence low |
| blower filter | 7 | 1,349,479 | 7 | 6 single-family, 1 no vehicle |
| urea filter | 7 | 134,108 | 7 | 5 no vehicle, 2 pooled |
| clutch booster | 48 | 47,151 | 48 | 37 single-family, 11 no vehicle |
| pilot bearing | 3 | 2,947 | 3 | 2 single-family, 1 pooled |
| **TOTAL** | **174** | **5,990,933** | | |

**Brake rotor is the honest answer and it is a dead end for tonnage.** Of its 109 part numbers, the family file resolved **92 as having no vehicle reference at all** — 92 rows at low confidence, 16 from the EPC, **1** from the cross-reference, and precisely **one** vehicle string in the whole family: `N*R,N*S`, which is a wildcard, not a model code. A wildcard cannot be turned into a band. So brake rotor's EUR 4.46M is not blocked by a fixable join — **there is no evidence on disk that says which vehicle these rotors fit.**

**Why the other four are different.** Clutch booster (28 cross-reference hits), blower filter (3) and pilot bearing (2) do have some vehicle evidence and are plausibly recoverable. The routes are: the current EPC decode, the cross-reference's own `vehicle_model` string, or the family file's registry model tag. The candidate table is produced by a probe that reads the **first route only**, which is the mechanical reason these families are absent from it.

**Per-family route evidence** (kept in the workspace rather than in this pack, to stay inside the 20-file limit, at `01_data\00_derived\tonnage_missing_families_scope_20260922.csv`):

| Family | Part numbers | Euro | Via the EPC decode | Via the cross-reference | Via the family file |
|---|---:|---:|---:|---:|---:|
| brake rotor | 109 | 4,457,248 | 8 | 1 | 109 (92 with no vehicle) |
| blower filter | 7 | 1,349,479 | 0 | 3 | 7 |
| urea filter | 7 | 134,108 | 0 | 1 | 7 |
| clutch booster | 48 | 47,151 | 0 | 28 | 48 |
| pilot bearing | 3 | 2,947 | 0 | 2 | 3 |

**What this means commercially, and it should not be buried.** The tonnage view as it stands covers filters and clutch. It has no brake rotor, and brake rotor is the second-largest service family in the service list by euro. **A tonnage story presented without that sentence would be misreading its own coverage.**

### 3d. Spending per truck by band does not exist, and cannot be built from the billing

Parts billed divided by trucks in service. The **fleet** side splits by band. The **billed** side does not, because it has no vehicle. So no band-level spend-per-truck figure exists for the book as a whole. The panel on the tonnage page headed *"How much does each vehicle in service spend on parts"* is **per customer and per year, market level**.

Two further warnings on this ratio:

- Even a defensible version — *selected exclusive-parts billing per truck in the supported band* — is **not** total spend per truck by tonnage. It is a narrow numerator over an estimated denominator.
- **[corrected] The denominator is a fixed 2025 estimate held flat across every year**, in the demand model. It cannot be shown as historical measured spending per vehicle. And **UTI records 3.5 t purchases — EUR 4,135 on the exclusive slice, EUR 471,921 on the pooled view — while the model supplies no UTI 3.5 t fleet at all.** That is a real inconsistency in the pack, not a rounding issue. The fleet zero rests on 2,360 CV warranty VINs showing no NLR/NMR/NKR; that establishes absence from the *warranty sample*, not necessarily from the whole fleet in service. Do not invent a fleet count and do not delete the purchases.
- **A band-exclusive numerator must not be divided by a whole-category expected demand and called total service cover.** The scopes have to match.

### 3e. The bands in the source, and what they are not

| Band label in the file | Weight label on the page |
|---|---|
| `3.5t_N35` | 3.5 t (N35 Grafter) |
| `5.5t_N50_N55` | 5.5 t (N50 / N55) |
| `7.5t_N50_N62_N75` | 7.5 t (N50 / N62 / N75) |

**[corrected] There is no 10 t band, and the 7.5 t grouping cannot separate 7.5 t from 10 t.** So it cannot establish an ITUK-versus-UTI difference between a 7.5 t mix and a 7.5–10 t mix. Do not relabel it as a precise weight distribution, and do not infer a finer fleet split from a coarse part-to-model association.

Two further groupings are not bands: **`shared_across_bands` (118 part numbers, EUR 3,229,690)** and **`series_unresolved` (4 part numbers, EUR 122,962)**. The decode also carries **`no_series_found` (32 part numbers, EUR 220,164)**. Those three figures are corrected in v4 to the shipped file; v3 printed EUR 3,010,701 / EUR 116,097 / EUR 206,139, which do not reproduce.

**A different thing again, and do not add it to the above:** `data_context\22_vehicle_family_by_part.csv` splits by **family**, not by band — 103 part numbers in the N-series truck family carrying EUR 5,022,235, 164 in the heavy-truck family, 104 light vehicle, and **54 pooled across more than one family carrying EUR 4,434,662**, plus 413 with no vehicle reference at all. **v3 printed "53 part numbers, EUR 4,158,264" as `shared_across_families`; those two figures do not reproduce from either file, and the correct pair is 54 / EUR 4,434,662.**

## 4. THE TRAP — never sum the band file

`data_nseries_bands\11_nseries_band_evolution.csv` is **stacked views, not adding blocks.** The `membership` column has four values and the same euro appears in more than one:

| `membership` | Rows | Euro summed | Additive? |
|---|---:|---:|---|
| `also_fits_band` | 316 | 16,601,029 | **NO** — repeats purchasing already included |
| `pooled_all_bands` | 106 | 5,636,293 | yes |
| `single_band_only` | 180 | 2,680,028 | yes |
| `series_unresolved` | 95 | 686,252 | yes |
| **Sum of every row** | **697** | **25,603,602** | about six times the true total |

**The additive partition is the three rows marked yes, and it equals EUR 4,501,286 — the tagged N-series total.** The file carries a `sums_to_n_series_total` column (`yes`/`no`) for exactly this purpose. The build asserts it: `tie_out.delta_eur = 0.0`.

**Rule: select one clock, one period, and `sums_to_n_series_total == "yes"`, then take `membership == "single_band_only"` as the exclusive numerator.**

## 5. THE SECOND TRAP — two service-interval lanes, never blended

| Lane | Markets | Rates |
|---|---|---|
| **IML v7** | **ITUK only** | filters 1.25 visits a year, clutch and brake 0.5, on the 22,389-vehicle DVLA fleet, own brake factor 0.4 |
| **PRISM network** | every other market | trucks 0.5, F-series 0.667, LCV 1.0 |

The band file carries a `lane` column; the tonnage page build **fails on purpose** if any market carries two lanes in one row. Keep the external ITUK standard and the internal network method separate, and never combine their cover percentages into a ranking.

**Inside ITUK the N35 and N75 run different intervals** — this was Jerome's correction. The 1.25 rate is the N75 rate (40,000 km interval over a 50,000 km year). The N35 runs a 20,000 km interval, so on its own mileage its visits a year is a different number.

**[corrected] And the direction I gave in v1 was backwards.** Cover is `actual ÷ expected`. **Lowering expected demand raises cover, not lowers it.** Worked direction test on the deck's own oil-filter example:

| | Expected (derived) | Cover |
|---|---:|---:|
| Flat 1.25 applied to both bands | 27,986 | **35.1%** |
| Band-specific intervals | 22,045 | **44.5%** |

So the N35 correction **raises** ITUK oil-filter cover by about 9 points, it does not cut it from 116% to the 70s. v1's sentence was wrong and is withdrawn. Any proposed ITUK change needs the before/after actual units, fleet scope, mileage, interval and reporting basis stated together — and no re-base may be applied silently.

**[corrected] Mileage provenance.** v1 attributed 14,494 km/yr to "ITUK N35" in one place and "IUK N35" in another. **The 14,494 km/yr figure is IUK — the UK light commercial Grafter fleet** (9,006 mi median from odometer deltas). ITUK's own measured figure in the market table is a different number. Do not move mileage evidence between distributors. `data_context\21_mileage_reference.csv` now carries every measured mileage figure with its market, class, sample size and source.

## 6. The modelled table — what it may and may not be used for

`data_modelled_demand\19_expected_vs_actual_by_band.csv` compares modelled expected demand with an actual, by market x band x service category x year. Its limits are in the meta file and must travel with any number taken from it:

- **The actuals are the whole market's, not the band's.** Every row carries `actual_is_market_level = True`. **Never sum them down the band rows, never allocate them by fleet share, and never compute band service cover as a market actual over a band expectation.**
- **[corrected] `gap_eur_band_share` is a modelled allocation**, not observed missing band purchases. Audit it before use. It must never become a measured band leakage figure, a colour-coded performance ranking, or an externally totalled gap.
- The fleet vintage is a fixed **2025E** estimate for every year, so expected demand is flat by construction. Only billing and capture move.
- F-series exists as a fleet in three markets only (ITUK, Portugal, Ireland), 1,238 vehicles, with expected demand but almost no attributable billing.
- AIM level 1 resolves on 99.3% of billed euro; the remainder is reported as Unclassified rather than dropped.

Three things must be kept visibly separate, in data and in any interface: **recorded purchasing attributed through validated exclusive applicability** (distributor purchases of selected parts — not observed service events and not proven vehicle end use); **expected service demand by band** (modelled from fleet, mileage and schedule); and **market-level actual purchasing** (market level even when displayed beside a band expectation).

## 7. What the sixteen-row conflict actually was — `NKR`, not `NMR`

**Short version: this is not a 5.5 t blocker, and v3 overstated it.** The conflict was an `NKR` mislabelling in a retired probe dictionary, not an open weight question. Full working in `01_data\90_INBOX\NMR_ruling_impact_20260922.md` and in §14a below.

`13_band_candidates_297_parts.csv` carries **16 part numbers labelled exclusively 5.5 t, worth EUR 17,477.34.** Reading the vehicle string on each of them in the cross-reference:

| What the sixteen actually name | Part numbers | Euro |
|---|---:|---:|
| `NKR` only — no `NMR` anywhere | **14** | 17,477.34 |
| `NL*,NMR` — a wildcard plus `NMR` | **2** (`5876103150`, `8983053050`) | 0.00 |
| named both | 0 | — |

So the 5.5 t label on fourteen of them comes from the retired probe dictionary `SERIES_BAND` in `01_data\91_build\pn_ammo_probe_20260918\_tonnage_capable.py`, which hard-codes `NKR → 5.5t`. Both newer tables place `NKR` at **3.5 t**, and Isuzu's own UK material puts `NKR` in category N1, "not exceeding 3500kgs GVM". The candidate table is stale; the band file is right. **Six of the sixteen are already `3.5t_N35 / single_band` in the live file today, carrying EUR 11,381.95** — and that EUR 11,381.95 is the largest part of the EUR 14,198.10 3.5 t exclusive total the headline itself rests on.

**The money is small, and worth putting beside a fleet.** The whole sixteen are EUR 17,477.34 — **0.39% of the tagged N-series book** — which is **EUR 0.48 per truck in service** across the 36,793 CV-standard N-series trucks in this model's 18 markets (2025E). This is a relabelling question, not a band at risk.

**5.5 t is not measurable on this table.** After the correction it holds **2 part numbers and EUR 0.00** — and even those two rest only on the string `NL*,NMR`. `NL*` is a wildcard and a wildcard is never a band, so their exclusivity claim has no supporting evidence in either direction. **The honest verdict for those two is `unresolved`, not 5.5 t.** The 5.5 t truck's parts spend is real — EUR 2,782,168 of N-series billing sits on part numbers that also fit 5.5 t — but it is *shared* with 3.5 t and 7.5 t and cannot be separated by tonnage from this file.

**Is `NMR` a 5.5 t truck? In Europe, yes — and only in Europe.** Isuzu's own German data sheet plates `MODELL NMR88L` at **5,500 kg**, Isuzu's own German range page sells the 5.5 t class as **N55 / NMR** with the 7.5 t class as **N75 / NPR**, and a Swiss type approval for `NMR85` gives 5,500 kg. **But the letter group fixes a cab, not a weight:** the same letters are 5.2 t in the Gulf, 6.0 t on the 2026 German range leaflet and 6.5 t in Taiwan. **Never state a weight for `NMR` without the European scope label.**

| Source | What it says about `NMR` |
|---|---|
| the retired probe dictionary `SERIES_BAND` | **5.5 t** — and `NKR` at 5.5 t, which is the error that produced this whole section |
| `16_series_token_to_band.csv` | band **5.5t_N50_N55** |
| `17_model_code_to_tonnage.csv` | band **7.5t_N50_N62_N75**, while its own weight label on the same row reads **"5.5 t GVW (N50 / N55 ladder)"** — one row telling two stories |
| public evidence, manufacturer and regulator, European scope | **5.5 t in Europe** for `NMR85` and `NMR88` |

**The rules that stay, and they are why the arithmetic in this pack holds.** A series is matched as a whole token and never as a substring. A wildcard (`N*R`, `N*S`, `NL*`, `NQ*`) is recorded and **never** converted into a band. A part number that fits more than one band is pooled whole and never split. And no row whose only evidence is a wildcard enters an approved exclusive total. The correction above changes the story told about these numbers, not the numbers.

## 8. Time coverage — what `months_in_period` actually counts **[corrected]**

**[corrected] v1 described all non-ITUK 2025 rows as eleven months. The file does not support that** — 2025 values run across 1, 2, 3, 5, 6, 7, 9, 10, 11 and 12 depending on the market.

**I have now closed the question the external review left open, by reading the builder.** `build_nseries_tonnage_bands.py` computes `months = ("m", "nunique")` over the billing rows — the number of distinct months in which the selected parts were **actually billed** — and then sets `period_is_complete = months_in_period >= 12`. So it counts **purchase activity, not source coverage**.

That has a real consequence: **a complete source with no purchase of those parts in some months is labelled an incomplete period.** `period_is_complete` and `comparable_to_previous` are therefore conservative in a way that conflates "we did not buy this" with "we do not have the data", which is exactly the distinction the pack needs. Flagged as a defect to fix at source, not to paper over downstream. Until then, retain the supplied completeness and comparability flags, and never infer a missing file from zero purchases.

January to June 2026 stays separate from complete years. A prior-year half-year comparison needs the same months, source coverage, exclusions and part universe on both sides. Do not double a half-year, and do not apply a full-year expected-service denominator to it without an approved method.

## 9. What is genuinely NOT known

- **50 of 120 model codes are unresolved**, including `NN`, `NP` and `NHR` — exactly the codes that would separate 3.5 t from 7.5 t.
- **5.5 t is not measurable on this table.** It holds **2 part numbers and EUR 0.00**, and those two rest only on the wildcard `NL*,NMR`, so the honest verdict for them is `unresolved` rather than 5.5 t (§14a). Whether the band should be published as a rung at all is a separate decision.
- **No 10 t band exists**, so a 7.5–10 t distinction cannot be established from this data.
- **Spend per truck by band does not exist** (§3d).
- **UTI carries 3.5 t purchases with no 3.5 t fleet in the model** (§3d).
- **The F-series question — "does the F-series have different service parts?" — is not settled.** Measured: 164 heavy-truck part numbers, EUR 174,832 of 2025 billing, 1,238 vehicles. But F-series parts shared with the N-series are pooled into `shared_across_families` (53 part numbers, EUR 4.16M), so "fewer parts for F-series" would be an artefact of the pooling rather than a finding.
- **The fleet denominator is a fixed 2025 estimate.** A band trend is a billing trend, never a per-vehicle trend.
- **A band is not a model.** "7.5 t" contains NPR75, NPR88, NQR, NNR and NPS.

## 10. How to use these files without producing a wrong answer

**Do:** pick one clock and one period first; filter `sums_to_n_series_total == "yes"`; take `membership == "single_band_only"` as the exclusive numerator; quote euro with the band, the service family and the fleet, or as a rate per vehicle; name the lane; state whether a figure is measured or modelled; keep the bridge visible when comparing populations.

**Don't:** sum the band file or add two membership blocks; add CY to FY; add the candidate euro to the worklist euro; split a market actual across bands; divide a band-exclusive numerator by a whole-category expectation; present a modelled `gap_eur_band_share` as measured leakage; use the candidate table's 5.5 t labels as approved, or count a wildcard as a band; treat `period_is_complete` as a source-coverage statement; move mileage figures between distributors; quote the withdrawn heavy-truck figure (95 part numbers / EUR 1.96M).

**Mileage, correctly sourced.** IUK N35 Grafter **14,494 km/yr** (odometer deltas, 9,006 mi median). UTI Israel N75 **51,680 km/yr** (CV warranty odometer, aligns with the market's own 50,000). Europe pooled medians **N35 12,165 / N75 35,217 / F-series 45,630**, with sample sizes 12,160 / 3,600 / 1,851 VINs. **Never use the `Annual Mileage` column in `n35 mileages all.xlsx`** — it divides odometer by a shrinking vehicle age, so the newest reading equals the odometer itself. Full table with market, class, sample and source: `data_context\21_mileage_reference.csv`.

## 11. Anchor honesty

`data_context\24_verification_report.json`, generated **2026-09-22T16:44:37Z**: **154 pass / 2 warn / 0 fail, `ok: true`.** One more check than the 20 Sep run reports, because the freshness check below was added.

| Check | Result | Plain meaning |
|---|---|---|
| `lost_sales.billed_ties_to_parts_base` | **pass**, delta **EUR 0.00** at the 2026-06-30 cut-off | Was failing at **EUR 5,511,194.53** when the pack was first written. **It was a stale model, not a broken tie-out.** |
| `lost_sales.model_is_current` | **warn** | The model ties the base but stops at 2026-06-30; billing runs to 2026-08-31. **EUR 5,511,194.53 of later billing is not in it.** Rebuild `scripts/build_lost_sales_model.py` to bring it current. |
| `freshness.no_stale_derived` | **pass** | 28 declared inputs checked; no derived file is older than an input. **This check did not exist before 22 September** — see §13. |
| `uio_year.historical_gaps` | warn | DENMARK 2012 and 2013 unfilled. Long-standing, harmless. |

**Note the shape of the tie-out entry.** It **passes** while a separate check **warns** — deliberately, because those are two different facts and collapsing them is what caused the original false alarm. Tying the base to the cent is not the same as being up to date.

**What that failure actually was.** The reported "delta" was exactly the Jul–Aug 2026 billing the model predated. The check compared the model against *all* billing on file, so the moment the next monthly billing landed, a correct model looked broken. The tolerance was never at fault: the model ties the parts base to the cent at **EUR 112,089,306.89** on the billing it was built from. Fixed on 2026-09-21: the tie-out is measured at a declared cut-off (`billing_cutoff: 2026-06-30`, frozen deliberately and the same value `metrics_snapshot.json` publishes), a model behind it is reported as **stale** naming the builder, and a model that ties no month-end at all still fails.

**Do not read this as "0 fail therefore the tonnage pack is verified."** The tonnage tie-out, the population bridge and the mapping conflicts are **arithmetic and definition checks at the scope they cover**. Passing those is not a cleared pipeline, and it does not touch the mapping conflict in §7, the UTI 3.5 t inconsistency, or the missing families in §3f.

## 13. What changed on 22 September — the layer was stale, and now is not

This section exists because the pack went out on the 20th with numbers that were correct for the data it had, and the data had already moved.

**What happened.** The tonnage layer was built **19 September** from billing through **June 2026**. The underlying billing source was then rewritten on **21 September** and now ran to **August 2026**. Nothing detected it: the pipeline verifier reads a file's *contents*, so a file that is internally consistent and behind its own input passes every check it has. A page was even rebuilt on the 21st that consumes the stale layer.

**What was done.** The layer was regenerated in dependency order on the 22nd and the tie-out re-verified. The chain and its inputs:

| Step | File | Built by |
|---|---|---|
| 1 | `22_vehicle_family_by_part.csv` | `prism/scripts/build_vehicle_family_bands.py` |
| 2 | `19_expected_vs_actual_by_band.csv` | `prism/scripts/build_pms_tonnage_model.py` |
| 3 | `11_nseries_band_evolution.csv` + `15_band_by_part_number.csv` + `16_series_token_to_band.csv` | `prism/scripts/build_nseries_tonnage_bands.py` |
| 4 | `13_band_candidates_297_parts.csv` | `01_data/91_build/pn_ammo_probe_20260918/_tonnage_capable.py` |
| 5 | the tonnage page and the family page | `02_dashboards/sales/_build/` |

**The tie-out held at EUR 0.00**, which is the check that matters: bands plus pooled plus unresolved still equal the tagged N-series total. A rebuild that had silently lost a family would have failed here.

**What actually moved, and why.** Only the two new months. Every period except CY2026 and FY2027 is byte-identical to the 20 September version, because those months are complete and untouched.

| | 20 Sep (through June) | 22 Sep (through August) | change |
|---|---:|---:|---:|
| Tagged N-series total | 4,305,334 | 4,501,286 | **+195,953** |
| Band-exclusive, whole window | 1,289,762 | 1,340,014 | +50,252 |
| Exclusive share | 29.96% | **29.77%** | −0.19 pt |

**And a second instance of the same problem, found by the new check.** `metrics_snapshot.json` was **3.9 days behind `sales_fact.parquet`** — it read as-of 17 September against billing through August. It has been rebuilt and now reports the real horizon. Two of these in one day is the argument for the check, not an accident.

**The check now exists.** `freshness.no_stale_derived` compares every declared derived file against its declared inputs and warns when one is older. It reads the pairs from `verification_fixtures.yaml` → `freshness.pairs` (8 pairs, 28 inputs). It warns rather than fails on purpose: some staleness is deliberate, and a hard fail would block the pipeline for a monthly refresh. Visible is what it was not.

**Two things to carry forward from building it.** First, the check's first version keyed off `_deep_billing_cache.parquet` and immediately produced a false alarm — the family-page build rewrites that cache with identical content on every run, so an mtime comparison against it is not meaningful. It now keys off `sales_fact.parquet`, which is the real input. Second, a QA script guarding the tonnage page (`qa_pms_tonnage_evolution.py`) had been printing **FAIL and exiting 0** — it collected failures and never returned them, so it could never fail a gate. That is worse than no check, and it is fixed: the labels it looks for had also drifted from the page's deliberately plainer wording.

## 12. What is still waiting on a person

1. **The `NMR` residue in §14a** — the two `NMR`-named part numbers whose only evidence is the wildcard `NL*,NMR`, and whether the 5.5 t band should be published as a rung at all. **`NKR` itself is settled:** it is the 3.5 t rung in Europe, and the retired probe dictionary that put it at 5.5 t is where the sixteen-row conflict came from.
2. **The UTI 3.5 t inconsistency** — the model carries no fleet, the billing carries purchases. The source assignment needs investigating; the fleet must not be invented and the purchases must not be deleted.
3. **ITUK intervals** — re-base onto the same N35 ratio as the other six markets, or keep the July convention with the difference labelled?
4. **The population bridge** — which of the two populations is authoritative for reporting, and the bridge from it to its parent service-parts population.
5. **The `months_in_period` defect** (§8) — fix at source so source coverage and purchase activity stop being conflated.

## 14. What changed in v4 — the `NMR` question answered, and a defect in the headline

Two evidence passes finished after v3 was written on 22 September and overturned three things v3 asserted. **Nothing in the data files changed:** the tonnage layer was regenerated on 22 September and is current. What changed is what these documents say about it. The five items below are recorded in full in `02_CORRECTION_LOG.md`; the sources are in `01_data\90_INBOX\` — `NMR_ruling_impact_20260922.md` and its CSV, `NMR_blast_radius_20260922.md`, `band_union_audit_20260922.md`, `isuzu_n_series_public_weights_20260922.md` and `NMR_MAPPING_DECISION_NOTE_20260922.md`.

### 14a. The sixteen-row conflict was an `NKR` mislabelling. It does not block the band

Fourteen of the sixteen name `NKR` and only two name `NMR`. The `5.5 t` label on the fourteen comes from a retired probe dictionary that mapped `NKR → 5.5t`; both newer tables and Isuzu's own UK material put `NKR` at 3.5 t. Six of the sixteen are already `3.5t_N35 / single_band` in the live file, carrying EUR 11,381.95. **What moves if the mapping is corrected is about EUR 118,000 of band movement at the very most** (EUR 117,946.78 over all years on the 7.5 t band, EUR 36,578.17 in calendar 2025) — the whole sixteen are EUR 17,477.34 on the candidate table's own basis. 5.5 t survives at **2 part numbers and EUR 0.00**, both resting on the wildcard `NL*,NMR`, verdict `unresolved`. Full rewrite in §7.

**`NMR` is a 5.5 t truck in Europe.** That is now sourced — Isuzu's own German data sheet (`MODELL NMR88L`, 5,500 kg) and a Swiss type approval for `NMR85` — and it is a European answer only. The letter group fixes a cab, not a weight: 5.2 t in the Gulf, 5.5 t in Europe, 6.0 t on the 2026 German range, 6.5 t in Taiwan. **Never state a weight without the European scope label.**

### 14b. A figure v3's working notes carried is withdrawn

**Withdrawn figure, in the words the correction uses: "The claim that the exclusive share rises to 30.02% under the NMR correction is withdrawn. That arithmetic double-counted six rows that are already `3.5t_N35 / single_band` in the file today; their EUR 11,381.95 is most of the EUR 14,198.10 the NMR pass starts from."**

The six rows were never in the 5.5 t pool. They are `in_n_series_family = yes`, `band_status = single_band`, `band_count = 1`, `tonnage_band = 3.5t_N35`, and the file's recorded reason on each is *"One band from the series named on this part number: NKR."* Adding them to the 3.5 t exclusive total again counts them twice. **The headline does not move for that reason, and the part-number count behind it does not move from 44 either.**

**And the `NMR` correction and the defect in 14c do not interact.** They concern disjoint part numbers: 16 and 4 respectively, 20 distinct, intersection empty. Neither one's arithmetic may be borrowed to explain the other.

### 14c. The headline as written is inflated by EUR 2,645.43, and the file has not been corrected

The current headline is the band-exclusive share, **EUR 1,340,014 of EUR 4,501,286 = 29.77%**. A defect found on 22 September inflates the exclusive set by **EUR 2,645.43**, so the true figure is **29.71%, a fall of 0.06 pt**. The band-exclusive part of the file has **not** been rebuilt, so it still says 29.77%. **The pack therefore states both: the number the file carries, and the known defect with its size and its cause.**

Two causes, both at source, and neither of them in the union step:

1. **`series_to_tonnage.csv` has no suffixed rows.** `NMR85` has no entry at all, so it never resolves to a band — the build writes that token into its `series_unresolved` column on **24 rows**. On 23 of those 24 the loss is invisible because the row also names the bare series `NMR`, which does resolve. On one row it is not invisible.
2. **A cross-reference string is separated by U+3001, the ideographic comma.** The row reads `NKR、NMR,NLR`. The build's splitter is `[,\s]+`, which does not recognise U+3001, so the first field arrives as `NKR、NMR`, fails the anchored whole-token test, and **both `NKR` and `NMR` are silently lost.** `NLR` survives, and the row is called exclusive 3.5 t.

**The affected rows.** `5878320470` is a brake shoe carrying **EUR 2,645.43 — the whole euro of this defect**; `5876103260` is the same cross-reference row and carries EUR 0. 3.5 t drops from 10 exclusive part numbers to 9, and 5.5 t gains the euro as `also_fits` and never as exclusive. Nothing is apportioned: the row is pooled whole, per the rule in §2.

| | Before | After | Movement |
|---|---:|---:|---:|
| Band-exclusive numerator | EUR 1,340,013.94 | EUR 1,337,368.51 | **−EUR 2,645.43** |
| Exclusive share | **29.7696%** | **29.7108%** | **−0.0588 pt** |
| 3.5 t exclusive | EUR 14,198.10 | EUR 11,552.67 | −2,645.43, part numbers 10 → 9 |
| 5.5 t exclusive | EUR 0.00 | EUR 0.00 | unchanged |
| 7.5 t exclusive | EUR 1,325,815.84 | EUR 1,325,815.84 | unchanged |
| N-series total | EUR 4,501,286.47 | EUR 4,501,286.47 | unchanged |

**The direction is the dangerous one: the defect currently flatters the headline.** EUR 2,645.43 across 36,793 trucks is **EUR 0.07 per truck in service**, all years combined, and it lands entirely in one service family — **brake shoe**, one part number, 3.5 t. The 7.5 t band, which is 98.9% of the exclusive numerator, is untouched in either direction.

**Do not quote `8983615742` as the money, and v3 named it wrongly.** It is the right *shape* — it names `NMR85` without the bare `NMR`, so it is the one row of the 24 where the missing table entry is the sole 5.5 t evidence — but it carries **EUR 0.00 in this model**. Its EUR 75,052 sits in `sales_fact.parquet`, a different universe covering every market and every line, and it does **not** sit inside the band-exclusive set. The euro is on `5878320470`.

### 14d. A source defect worth recording, so it does not mislead the next reader

**`03_analytics/Isuzu/prism/scripts/build_nseries_tonnage_bands.py` prints the token list unconditionally on the single-band branch.** On `8983615742` the file's own `band_reason` reads *"One band from the series named on this part number: NMR85, NNR, NPR, NQR."* That sentence reads like a union that returned one band. It is not: **the union step at the bander's lines 479–483 is correct**, and it was never given `NMR85` at all, because the loss happened **upstream** in `series_to_tonnage.csv` — no suffixed rows — and in the cross-reference splitter at lines 313–319, which does not recognise U+3001. The reason text is a print of the raw token list, not a statement about what the union did.

**This misled one audit already.** Anyone diagnosing this from the reason text alone will call it a union bug and change the wrong lines. Recorded here, and in `02_CORRECTION_LOG.md`, so the next reader does not.

### 14e. One open lead, recorded and not resolved

**Part number `5876100771`** — clutch kit, `in_n_series_family = yes`, **EUR 52,174.49** over the whole window — carries a registry tag of **7.5 t**, a `band_count` of **1**, and a blank `tonnage_band`, with `band_status = no_series_found`. The reason is that the branch which would use the registry tag never runs when no series was named, so the tag is never read. **It does not inflate the headline** — on the band file the row has no band and is not counted as exclusive — so it is a lead, not a finding. It is recorded here and **not traced or fixed in this pass**.

**Do not distribute new tonnage performance claims while the reconciliation and approval conditions above remain open.**
