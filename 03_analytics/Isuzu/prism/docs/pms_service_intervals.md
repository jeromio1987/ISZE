# PMS Service Intervals & Capture Factors — what they are, where they come from

**Status: these are MODELLING ASSUMPTIONS, not measured intervals.** Read this before quoting any
capture %. Last updated 2026-07-02 (air_filter 1.0 → 0.5 provisional — integrity flag C).

---

## 1. Straight answer to "where did the factors come from?"

- **They are NOT derived from ITUK data.** No distributor's service records were used to fit them.
- The **numerator** of capture (actual parts sold) is real billing data. The **denominator**
  (expected demand) is built from these assumed factors. So capture % = *real sales ÷ assumed demand*.
- The factors below were **pre-set in `pms_capture_assumptions.yaml`** as placeholders pending IML
  service-interval input (the file header literally says *"Edit when IML supplies service-interval ratios"*).
- **`brake_rotor: 0.25` was added by Claude on 2026-06-15** as a **provisional** assumption — see §4.
  It is flagged provisional in the YAML and in `FACTS.md`. It is **not** an IML or ITUK figure.

So when capture reads e.g. "ITUK oil filter 172.7%", the 172.7% is *real oil-filter units sold ÷
an assumed annual demand*. If the assumed demand is wrong (and it varies by country — see §5), the %
moves. **The actuals are solid; the intervals are the soft part.**

---

## 2. How expected demand is built

```
base            = UIO_units × services_per_year × addressable_pct
consumables     expected = base × consumable_factor          (filters)
wear parts      expected = base × wear_factor                (brakes, clutch, rotor)
capture_rate    = actual_qty ÷ expected_qty                  (uncapped)
```

**`services_per_year` (by parc scope)** and **`addressable_pct`** — also assumptions:

| Scope | services_per_year | Applies to | addressable_pct |
|---|---|---|---|
| N75 (CV truck) | **0.5** | ITUK, UTI, most EU DBs | **70%** |
| LCV (D-Max/pickup) | **1.0** | IUK, UMI | 70% |
| N35 blend | 0.75 | (default/other) | 70% |

These live in `parc_config` defaults (`pms_engine.DEFAULT_PARC_CONFIG`) / `pms_capture_assumptions.yaml`.

> ⚠ The factor is **not** a literal km/month interval — it's an annual expected-replacement multiplier
> per addressable unit. Real mechanical intervals (oil ~yearly, rotor every 2nd pad set, etc.) must be
> translated into a factor (formula in §6). That translation is the IML/country input still missing.

---

## 3. The factor template — ALL current values + basis

**Consumables** (`consumable_factor`):

| Category | Factor | Implied annual rate (N75: ×0.5×0.70) | Basis / confidence |
|---|---:|---:|---|
| oil_filter | 1.00 | 0.35 /UIO/yr | Assumption (1 element per addressable service). **Pending IML.** |
| fuel_filter | 1.00 | 0.35 | Assumption. Pending IML. |
| **air_filter** | **0.50** | **0.175** | **Claude provisional 2026-07-02** — air element ~every 2nd service vs oil every service (flag C interval-aware fix; was 1.0 flat, which deflated air capture ~2×). Confirm with IML. |
| urea_filter | 1.00 | 0.35 | Assumption. Pending IML. |
| blower_filter | 0.25 | 0.09 | Assumption (cabin filter less frequent). Pending IML. |

**Wear parts** (`wear_factor`):

| Category | Factor | Implied annual rate (N75) | Basis / confidence |
|---|---:|---:|---|
| brake_pad | 0.50 | 0.175 | Assumption (pads ~every 2nd service). Pending IML. |
| brake_shoe | 0.50 | 0.175 | Assumption. Pending IML. |
| **brake_rotor** | **0.25** | **0.0875** | **Claude provisional 2026-06-15** — rotors ≈ every 2nd pad change = ½ × brake_pad. Confirm with IML. |
| clutch_disc | 0.20 | 0.07 | Assumption. Pending IML. |
| clutch_pressure_plate | 0.20 | 0.07 | Assumption. Pending IML. |
| clutch_kit | 0.15 | 0.0525 | Assumption. Pending IML. |
| release_bearing | 0.15 | 0.0525 | Assumption. Pending IML. |
| pilot_bearing | 0.10 | 0.035 | Assumption. Pending IML. |
| clutch_booster | 0.10 | 0.035 | Assumption. Pending IML. |

None of the above is an empirical fit. All are editable in `pms_capture_assumptions.yaml`.

---

## 4. Why brake_rotor = 0.25 (the one I added)

- Rotors (discs) are replaced roughly **every second brake-pad change** on these vehicles.
- brake_pad factor = 0.50 → rotor ≈ **0.50 × ½ = 0.25**.
- It is a **reasoned engineering default, not data.** I flagged it provisional everywhere it lands
  (YAML comment, FACTS.md, this file). One IML number replaces it.
- Sensitivity: at 0.25, network brake_rotor capture sits mid-range; halving the factor (0.125) doubles
  the capture %, halving the gap. So the factor materially drives the rotor gap — worth confirming.

---

## 5. Country-specific intervals (your point — different countries, different intervals)

Correct: a Nordic winter fleet, a Greek/Cyprus hot-climate fleet, and a UK urban fleet do **not**
service on the same interval. The model now supports **per-distributor overrides** in
`pms_capture_assumptions.yaml` under `country_overrides` (empty by default → current global behaviour):

```yaml
country_overrides:
  # Override services_per_year and/or individual factors per distributor.
  # Empty/omitted = use the global values in §2/§3. Fill from IML when available.
  # NORWAY:  { services_per_year: 0.60 }                      # harsher duty cycle → more services
  # GREECE:  { services_per_year: 0.45, factors: { air_filter: 1.5 } }  # dust → air filters sooner
  # ITUK:    { factors: { air_filter: 0.5 } }                 # category-specific only
```

- `services_per_year` override replaces the scope default for that distributor.
- `factors: {category: value}` overrides a specific consumable/wear factor for that distributor only.
- Anything not listed falls back to the global value — so this is additive and safe.

**To populate it:** ask each IML/distributor for their **genuine service interval per category**
(km or months) and the **average annual mileage** of the parc, then convert with §6.

---

## 6. Converting a real interval → a factor (so IML input is plug-in)

Given a real replacement interval and parc mileage:

```
replacements_per_year   = annual_km / interval_km            (or 12 / interval_months)
factor                  = replacements_per_year / (services_per_year × addressable_pct)
```

Example (oil filter, N75, addressable 0.70, services_per_year 0.50):
- If genuine interval = 30,000 km and parc averages 30,000 km/yr → 1.0 replacement/yr
- factor = 1.0 / (0.5 × 0.70) = **2.86** (vs the current placeholder 1.0 → today's model under-states oil demand)

This is exactly why the current capture %s are provisional: the placeholder factors ≠ real intervals.

---

## 7. What to do next (IML ask)

1. Get genuine **service interval per category** + **avg annual km** per country/distributor.
2. Fill `country_overrides` (and/or revise the global factors) using §6.
3. Re-run `run_pipeline_and_verify.ps1`; capture, gaps, briefs, dashboard and the FACTS anchor
   update together (drift-enforced).

Until then: **capture % is directional. The actuals and the missing-PN fix (€978K + brake_rotor) are
solid; the interval factors are the assumption layer on top.**

_Files: `data/pms_capture_assumptions.yaml` (values + overrides) · `modules/pms_capture_config.py`
(loader) · `modules/pms_engine.py` (`services_per_year`, expected-qty) · `FACTS.md` §2 (constants)._
