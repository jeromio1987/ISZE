# CURSOR TASK — Rebuild the ISZE Tonnage Model Attribution and Service-Demand Logic

## Objective

Repair the tonnage model so that it can answer the commercial question correctly:

> For each market and vehicle group, what service demand should the fleet generate, what ISZE purchasing can genuinely be attributed to that vehicle group, and what remains shared or unmeasurable?

The rebuilt model must not manufacture tonnage attribution from billing that does not contain a vehicle identifier.

This is a **model correction task**, not a dashboard redesign task.

The final output must make a strict distinction between:

1. **vehicle / tonnage applicability** — which vehicles a part can fit;
2. **expected service demand** — modelled from fleet, mileage/service intervals and service basket;
3. **measured ISZE purchasing** — actual ISZE-to-distributor billing;
4. **exclusive attributable purchasing** — billing for parts proven to fit one defined vehicle group only;
5. **shared purchasing** — billing for parts fitting several vehicle groups and therefore not allocable without further evidence.

Do not turn shared purchasing into measured tonnage purchasing by proportional allocation.

---

# 1. Core issue to fix: tonnage attribution

The current model contains conflicting applicability evidence.

A reference may be classified as single-band in one derived file while another source says the same part fits more than one tonnage group. The existing ~30% exclusive attribution therefore cannot automatically be treated as final.

## Required correction

Create a single authoritative applicability layer at **part number × vehicle/model × exact GVW / reporting group** level.

Do not start with the tonnage band and work backwards. Start with the vehicle evidence.

For each part number retain:

- part_number
- vehicle_family
- series_token
- model_code
- exact_gvw_t where known
- commercial_tonnage_group
- engine / schedule family where available
- evidence_source
- evidence_strength
- source_priority
- valid_from / valid_to if known
- unresolved_flag
- conflict_flag
- conflict_reason

## Source precedence

Use the strongest vehicle-specific source first.

Preferred evidence order should be approximately:

1. Isuzu workshop / maintenance manual with explicit model code
2. official VIN / vehicle register with model code and GVW
3. EPC application/decode with explicit series/model applicability
4. validated genuine/BVP cross-reference application
5. derived token inference

Do not let a weak derived mapping override an explicit official model/GVW mapping.

If two authoritative sources genuinely disagree, keep the part unresolved and write the conflict into an exceptions table.

## Important rule

A part is **exclusive to a tonnage group only if every supported application that is in scope belongs to that same group**.

If the part fits 3.5 t and 5.5 t, it is shared.

If it fits 3.5 t and an unresolved N-series token, it is **not proven exclusive** until the unresolved token is resolved.

If it fits 3.5 t and 7.5 t, it is shared.

If it fits 3.5 t, 5.5 t and 7.5 t, it is shared.

Never allocate shared billing by fleet share, expected demand share or another arbitrary ratio and then describe the result as measured actual purchasing.

---

# 2. Separate exact GVW from reporting group

The current files mix exact vehicle weight evidence with commercial reporting bands.

This must be separated.

Create at least these dimensions:

- `exact_gvw_class`
- `service_schedule_cluster`
- `commercial_reporting_band`

Example conceptually:

- NLR may be 3.5 t
- NMR may be 5.5 t
- NPR may be 7.5 t

but some NLR/NMR/NPR models can still share the same engine and maintenance schedule.

That does **not** make them the same tonnage.

It does mean they may have the same or nearly the same expected service spend per vehicle for the categories governed by that maintenance schedule.

This distinction is critical.

---

# 3. Correct the 3.5 t / 5.5 t target-spend logic

Do **not** assign target spend per truck simply because a vehicle is called 3.5 t, 5.5 t or 7.5 t.

Target spend must be built from the service requirement.

The current business context has used class-level target-spend assumptions such as N35 and N75 rates. These were already corrected once when a large part of the ITUK fleet had incorrectly been priced at the 7.5 t rate.

The next correction is to calculate the target from the underlying service basket rather than from the tonnage label alone.

## Required method

For each `service_schedule_cluster` calculate expected annual spend per vehicle as:

`sum(expected annual replacement quantity for category/part × applicable reference price)`

The expected annual replacement quantity should be based on the best available service schedule and mileage assumptions.

Then map that schedule-level target to the exact vehicle groups that use the schedule.

### 3.5 t and 5.5 t rule

If the 3.5 t and 5.5 t models:

- share the same maintenance schedule;
- use the same service basket for the modelled categories;
- have the same service frequency at the same mileage;
- and use the same applicable parts/prices;

then their modelled maximum spend per truck **must be identical**.

If the schedule is the same but some service parts differ by model, their maximum spend should be **close but not forcibly identical**. Calculate the difference from the actual part basket.

If their mileage assumptions differ by market or class, apply the mileage difference explicitly rather than embedding it in the tonnage label.

The model must therefore expose:

- target_spend_per_vehicle_base_schedule
- target_spend_per_vehicle_after_mileage
- reason_for_difference_vs_adjacent_tonnage

A difference between 3.5 t and 5.5 t must be explainable by actual schedule, basket, price or mileage differences. It must never arise merely because one row says 3.5 t and another says 5.5 t.

---

# 4. Fix the actual-purchasing logic

This is the second major issue.

Billing contains no VIN / chassis / serviced vehicle. Therefore actual billing is normally measured at market level, not tonnage level.

The existing expected-vs-actual file repeats the market actual beside multiple tonnage rows. Those repeated actuals must never be summed and must never be divided separately by each band's expected demand as though each row contained a measured band actual.

## Required output structure

For every market/category/year create two distinct tables/views.

### A. Market-level actual purchasing

One row per:

- market
- year/period
- service category

Fields:

- actual_qty_market
- actual_eur_market
- market_average_price
- source_period

This is the measured purchasing observation.

### B. Band-level expected demand

One row per:

- market
- year/period
- exact_gvw_class or reporting band
- service category

Fields:

- fleet_units
- mileage_basis
- visits_per_year
- replacement_factor
- expected_qty_band
- expected_eur_band
- service_schedule_cluster

Do not duplicate market actuals into this table except as clearly marked context fields.

---

# 5. What can and cannot be measured by tonnage

Create three explicit purchasing measures.

## Measure 1 — exclusive attributable purchasing

Actual billing from references proven to fit one vehicle group only.

This can be called measured attributable purchasing by tonnage.

## Measure 2 — shared purchasing pool

Actual billing from references that fit more than one tonnage group.

Keep this separate.

This is real measured purchasing, but **not measured by tonnage**.

## Measure 3 — unresolved purchasing

Actual billing where applicability evidence is incomplete or contradictory.

Keep this separate until evidence is resolved.

The following identity must reconcile:

`exclusive attributable + shared + unresolved + out-of-scope = total selected billing population`

No double counting.

---

# 6. Do not invent a tonnage capture rate from market actuals

A proper measured tonnage-level service-demand cover rate can only be calculated where the numerator is genuinely attributable to that tonnage.

For each band, allow:

`exclusive_cover = exclusive attributable actual / expected demand for exclusively represented basket`

but only where numerator and denominator refer to the **same part/category universe**.

Do not compare:

- a small exclusive subset of actuals

against

- the entire service basket expectation

and call that total tonnage capture.

If full actual tonnage purchasing is not measurable, show:

- expected demand by tonnage;
- exclusively attributable purchasing by tonnage;
- shared actual purchasing at market level;
- unresolved actual purchasing;
- attribution coverage %.

This is much more honest and commercially useful than creating a false capture percentage.

---

# 7. Fix the historical fleet problem

Yes, this can be fixed.

The current service-demand file uses the **2025E fleet for every historical year**, which makes expected demand flat through time by construction.

That is not suitable for historical trend analysis.

The historical fleet model is usable through 2025. The forecast from 2026 onward is not usable in its current form and must not be used.

## Required rebuild

For each historical calendar year use the actual historical fleet in service for that year.

At minimum rebuild:

- 2023 expected demand using 2023 fleet
- 2024 expected demand using 2024 fleet
- 2025 expected demand using 2025 fleet

Do not use 2025 fleet as the denominator for 2023 or 2024.

For 2026:

- do not use the broken 2026–2030 fleet forecast;
- if a valid observed 2026 fleet snapshot exists for the relevant market, use it and label the as-of date;
- otherwise leave 2026 historical fleet-dependent ratios unavailable or use the latest verified historical fleet only as a clearly labelled scenario, never as measured 2026 fleet.

## Important reconciliation

There are currently multiple fleet counts in circulation for some markets and measures.

Before regenerating the model, build a `fleet_basis_reconciliation.csv` containing:

- market
- year
- measure/model
- fleet_count
- source
- class split available yes/no
- selected_authoritative_count
- reason

Examples requiring attention include ITUK, Ireland, Germany and Israel.

All models should then reference one authoritative fleet table rather than embedding separate fleet values.

---

# 8. Repair the service-demand denominator

The deep review found cases where the market-level expected denominator does not reconcile with the sum of the supplied band-level expectations.

Do not paper over this difference.

For each market × category × year produce a reconciliation table:

- expected_market_source
- sum_expected_bands
- difference_units
- difference_pct
- reason
- status

Possible reasons may include:

- excluded vehicle classes
- different eligible fleet universe
- different schedule lane
- configuration exclusions
- class-specific service factors
- stale fleet basis
- duplicated / omitted band

Do not choose one denominator automatically simply because it produces a more plausible capture rate.

The source lineage must decide which denominator is correct.

---

# 9. Keep ITUK and PRISM demand standards separate

The existing model has intentionally different service-demand standards.

ITUK uses the IML v7 basis.

The wider PRISM network uses its own standard.

Do not average these standards together.

Store a `demand_standard_id` on every expectation row.

A comparison between markets must therefore disclose whether the demand standard is identical.

---

# 10. Time-period integrity

Never compare a partial period with a full year as growth or decline.

Every table must carry:

- period_start
- period_end
- months_in_period
- complete_year flag
- calendar/fiscal clock

2026 actual billing and demand must use the same cutoff within a comparison.

If billing is through August 2026, do not compare it with a January–June fleet/service-demand extract without explicitly aligning the period.

---

# 11. Price basis for expected spend

Expected EUR demand should not silently use one current price snapshot as though it were historical pricing.

Create explicit price modes:

- `current_reference_price_scenario`
- `historical_price` where historical price evidence exists
- `unpriced` where no valid price is available

For historical service-demand cover, quantity is the safer primary metric unless historical comparable prices are available.

Do not turn missing price into zero EUR opportunity.

---

# 12. Required output files

Please rebuild and output at least:

### `tonnage_vehicle_master.csv`
One authoritative vehicle/model/GVW/schedule mapping.

### `part_vehicle_applicability.csv`
Every supported part-to-vehicle application with evidence and source priority.

### `part_tonnage_attribution.csv`
One row per part with:

- exclusive band if proven
- all applicable bands
- shared/unresolved status
- conflict status
- reason
- evidence strength

### `fleet_basis_by_market_year_band.csv`
Authoritative historical fleet by market/year/vehicle group.

### `fleet_basis_reconciliation.csv`
All competing fleet counts and selected source.

### `service_schedule_cluster.csv`
Maintenance schedule logic independent from tonnage label.

### `target_spend_per_vehicle.csv`
Target spend by schedule/model/tonnage, including explanation for differences.

### `expected_service_demand_by_band.csv`
Historical expected demand using the correct fleet year.

### `actual_purchasing_market.csv`
Measured market-level actual purchasing with no repeated fake band actuals.

### `actual_purchasing_exclusive_band.csv`
Only purchasing genuinely attributable to one band.

### `actual_purchasing_shared_pool.csv`
Shared multi-band purchasing.

### `actual_purchasing_unresolved.csv`
Unresolved applicability population.

### `demand_denominator_reconciliation.csv`
Source market expectation vs sum of band expectations.

### `tonnage_model_validation_report.json`
Machine-readable validation results.

### `TONNAGE_MODEL_CORRECTION_REPORT.md`
Human-readable explanation of every correction, remaining limitation and before/after effect.

---

# 13. Validation tests — mandatory

The rebuild is not complete unless these tests pass.

## Attribution tests

- No part labelled exclusive has more than one resolved in-scope tonnage group.
- No unresolved alternative application can remain hidden inside an exclusive classification.
- Shared references are never apportioned into measured actual tonnage purchasing.
- The exclusive + shared + unresolved + out-of-scope partition reconciles exactly to the selected billing population.

## Fleet tests

- Historical expected demand for 2023 uses 2023 fleet.
- Historical expected demand for 2024 uses 2024 fleet.
- Historical expected demand for 2025 uses 2025 fleet.
- No 2026–2030 forecast fleet is used unless a corrected forecast methodology has separately been validated.
- Each market/year has one selected fleet basis for a given measure.

## Demand tests

- Market actual purchasing appears once per market/category/period.
- Market actuals are never additive down tonnage rows.
- Band expectation sums reconcile to the market expectation or are explicitly flagged with a reason.
- ITUK and PRISM standards are never averaged.

## Target-spend tests

- Target spend differences are explainable by schedule, basket, price or mileage — not merely by tonnage label.
- Where 3.5 t and 5.5 t have identical schedule + basket + price + mileage assumptions, target spend per vehicle must match exactly.
- Where they differ, output the exact components causing the difference.

## Period tests

- Full-year and partial-year comparisons cannot be presented as YoY unless periods are matched.
- Every 2026 metric carries an explicit cutoff.

---

# 14. Specific investigation: 3.5 t versus 5.5 t

Treat this as a priority diagnostic.

Produce a table comparing every 3.5 t and 5.5 t model in scope:

- model code
- exact GVW
- engine
- maintenance schedule
- annual mileage assumption
- service interval by category
- expected annual quantity by category
- applicable reference basket
- basket price
- target annual spend per vehicle

Then answer explicitly:

1. Are the 3.5 t and 5.5 t models on the same service schedule?
2. Are the modelled service categories identical?
3. Are their applicable parts identical?
4. If not, which references differ?
5. Does mileage differ?
6. What is the justified target-spend difference?

Do not force a difference merely because their GVW is different.

If the evidence shows they have effectively the same maintenance requirement, merge them into the same **service-demand cluster** while retaining separate **GVW labels**.

This is likely the correct conceptual architecture:

`vehicle model -> exact GVW -> service schedule cluster -> expected service basket`

rather than:

`tonnage label -> arbitrary EUR target`

---

# 15. What not to do

Do not:

- allocate shared parts by fleet share and call the result actual;
- repeat market actuals next to every tonnage and calculate independent capture rates;
- use 2025 fleet for all historical years;
- use the existing 2026–2030 fleet forecast;
- blend ITUK and IUK;
- blend UMI and UTI;
- infer end-customer demand from distributor purchases without stating that it is inferred;
- treat zero purchasing as zero opportunity when expected demand is positive;
- use a missing price as EUR 0;
- use a current price snapshot as historical realised price without labelling it;
- silently overwrite conflicting source evidence;
- call a modelled gap measured lost sales.

---

# 16. Business interpretation required at the end

After the rebuild, write a concise conclusion answering:

- How much of the selected N-series billing can now be attributed exclusively to 3.5 t, 5.5 t and 7.5 t?
- How much remains shared?
- How much remains unresolved?
- Has the 3.5 t / 5.5 t service-demand target converged once the schedule logic is corrected?
- What remaining evidence prevents full tonnage-level purchasing measurement?
- Which commercial conclusions are now safe to publish?
- Which still need to remain modelled or directional?

Do not optimise for a high attribution percentage. Optimise for **defensible attribution**.

A lower but correct exclusive share is better than a larger invented one.

---

# Existing business rules / known context

Use these as constraints when rebuilding:

- Billing measures ISZE-to-distributor purchasing, not end-customer demand or workshop servicing.
- Billing contains no VIN/chassis/model identifier.
- Multi-band parts must remain pooled unless another measured source resolves their destination.
- Historical fleet data through 2025 is usable.
- The current fleet forecast beyond 2025 is not usable and must not be quoted.
- Target spend per truck is modelled, not measured.
- Spend per truck is measured from billing and fleet.
- Service-demand cover uses measured purchasing against modelled expected demand.
- 2026 must never be compared as a full year with 2025.
- Market cuts are preferred to network averages.
- ITUK and IUK are separate distributors and fleets.
- UMI and UTI are separate distributors and fleets.

The current target-spend model already documents that an earlier ITUK error assigned a large 3.5 t population the 7.5 t target. That correction materially reduced the modelled ceiling. The rebuild must prevent this type of error structurally by deriving target spend from the service schedule / basket rather than from a loose tonnage label.

---

# Deliverable standard

Do not just patch the final CSV.

Fix the logic at source and make the build reproducible.

Include:

- scripts changed;
- files regenerated;
- validation tests;
- before/after reconciliation;
- remaining unresolved cases;
- explicit evidence lineage for every tonnage assignment.

The final model must be able to explain **why** a reference belongs to a tonnage, **why** two tonnages have the same or different target spend, and **why** an actual purchasing number can or cannot be attributed to that tonnage.
