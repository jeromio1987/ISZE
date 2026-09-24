# PMS service-interval fix — what it is, what it breaks, and the one decision it needs

**Raised by Jerome:** 2026-09-18 evening. *"Fix the rates over all dashboards."*
**Status:** scoped, attempted, **rolled back the same evening.** Nothing is applied.

---

## 1. What is actually wrong

`modules/pms_engine.py`, `expected_by_category_bucketed()`, one line:

```python
expected[cat] = {"qty": base_cv * fac + base_f * fac + base_l * fac_lcv}
```

`base_cv` is the whole truck block, so **a 3.5 t N35 and a 7.5 t N75 are charged the same visit
rate.** They do not run the same service interval, so this is wrong, and Jerome is right that it
is wrong.

## 2. The intervals, from the authoritative sheets

Both sources agree, and the interval is a property of the **model**, not of the market — with one
market exception.

| Band | Model / engine | Service interval | Source |
|---|---|---|---|
| **N35** | NLR87 / RZ4E | **20,000 km** | Duncan deck slide 14 (2026-09-15); René GIDSS `N_MY24` p6-8 |
| N35 | NLR88 / 4JZ1 | indicator, max 40,000 km | René GIDSS `N_MY24` p1-2, note *2 |
| **N75** | NPR75 / 4HK1 | **40,000 km** | Duncan deck slide 14; René GIDSS `N_MY24` p3-5 |
| N75 | NPR88 / 4JZ1 | indicator, max 40,000 km | René GIDSS `N_MY24` |
| **N75 Israel** | NPR75 / 4HK1 | **22,500 km** | René GIDSS `N_MY24` — "Engine oil (Israel)" |
| F-series | 4HK1 | indicator-driven (MID) | René GIDSS `F_MY24` p1, market header: *Italy, Israel, Portugal, UK, Ireland* |
| LCV / D-Max | RG21 etc. | 20,000 km | owner's handbook, already in the pipeline |

So the interval table is **already correct and already per market**: N35 is half the N75 interval
everywhere, and Israel is the single market that differs (oil and fuel at 22,500 km).

## 3. Why changing it broke twelve markets — and it was the mileage, not the interval

The rate is `visits/yr = km a year ÷ km interval`. The interval is settled above. **The mileage is
where the pipeline is inconsistent**, and it holds two different assumptions at once:

| Where | Mileage assumption | Visit rate it implies for N75 |
|---|---|---|
| PRISM lane (`BUCKET_SERVICES_PER_YEAR.cv_std`) | **20,000 km/yr** (comment in the source) | 0.5 |
| IML v7 lane (ITUK, the published deck) | **50,000 km/yr** | 1.25 |

Both are in the workspace, for the same trucks, and nothing reconciles them. The 0.5 that every
non-ITUK market uses is therefore already about 60% too low against the 50,000 km convention that
the ITUK deck is built on — before any tonnage split is considered.

I attempted the fix using `warranty_cv_km_age_by_market.csv`, which carries measured odometer
deltas per market per band. That file is genuine and useful, but it exposed three problems that
make it unfit to re-base on **alone**:

1. **Its LCV column is a CV median.** For Greece I used `km_yr_all_median` on a 3,705-vehicle LCV
   fleet; that median rests on **one VIN at 1,590 km**. Greece's denominator fell 92% and capture
   ran to **1,156%**. That was my error, not an interval finding.
2. **Six markets have no measured mileage** (Belgium, Sweden, Norway, Denmark, Finland, Iceland),
   so they would have stayed on the old basis while twelve moved — a mixed-vintage league table.
3. **It contradicts the published IML figures.** ITUK's oil-filter denominator went 11,680 → 17,762
   and capture 116.4% → 77%, where **116.4% is the correct IML v7 figure**. Ireland +22% and
   Portugal +54% would have moved too — Portugal being the largest single mover in the set.

## 4. The one decision

**What mileage assumption does the network live on — 20,000 km a year, or 50,000?**

That is a business answer, not a data-cleaning one, and everything else follows from it:

- **If 50,000 km/yr is right**, then the PRISM lane is understated on every truck market, and the
  fix is large and must be done once, deliberately, with every published capture figure restated.
- **If 20,000 km/yr is right**, then the IML v7 deck is overstated for ITUK and its published
  65.9% / 35.9% figures need revisiting — a harder conversation.
- **Most likely** it is neither, and the honest basis is per band: N75 near 50,000, N35 near its
  measured 12,891 — which is the same shape as the UIO-FCAST mileage finding already open.

## 5. What a correct fix has to hold

1. One mileage basis, chosen, applied to every market and every lane.
2. Per-market intervals from René's sheets (N35 20,000 / N75 40,000 / Israel 22,500), not one rate.
3. No market re-based on an LCV median resting on hand-count VINs. Below a minimum sample the
   market keeps its current rate and says so.
4. ITUK checked against the IML v7 sheet at each step, so the published deck stays reconcilable.
5. Every capture figure that moves is listed before/after, market by market, for sign-off.
6. The two lanes (`IML v7 (ITUK)`, `PRISM network`) never blended — already enforced by a `lane`
   column in `pms_tonnage_model.csv`.

## 6. What was applied on 2026-09-18

**The N35 / N75 interval ratio.** `pms_capture_config.BUCKET_SERVICES_PER_YEAR` now carries a
per-market `cv_std` rate derived from the two factory intervals, expressed as a ratio so no mileage
assumption is needed and nothing is driven by an unmeasured input:

```
cv_std(market) = 0.5 × (1 + n35_share × (40,000 ÷ 20,000 − 1)) = 0.5 × (1 + n35_share)
```

Seven markets have a measured N35 fleet and moved; eleven did not; UTI is excluded by name because
its `cv_std` is an explicit 1.25 override and it has no 3.5 t fleet.

**The ratio touches the truck component only.** Expected demand per market and category is
`cv_std_uio × rate × category_factor + f_series_uio × rate × factor + lcv_uio × rate × factor`. The
N35 interval is a truck property, so only the `cv_std` slice is scaled. The first version of this
change scaled the whole total, which wrongly inflated the LCV block as well — Belgium, which is
9,480 light vehicles to 113 trucks, showed +91.8% when its true move is **+0.55%**. Jerome caught it
from the number alone. Corrected figures:

| Market | N35 share of trucks | cv_std rate | Expected demand | Capture move (2025 avg) |
|---|---|---|---|---|
| ITUK | 50.5% | 0.7526 | **+48.0%** | −16.8 pp |
| PORTUGAL | 62.0% | 0.8100 | +11.5% | −3.0 pp |
| MALTA | 36.9% | 0.6845 | +4.9% | −1.1 pp |
| IRELAND | 6.3% | 0.5315 | +1.3% | −1.1 pp |
| GERMANY | 22.0% | 0.6100 | +0.6% | −0.1 pp |
| BELGIUM | 91.8% | 0.9590 | **+0.55%** | −0.1 pp |
| CYPRUS | 5.3% | 0.5265 | +0.25% | −0.1 pp |

> **Superseded 2026-09-18 (later) — three shares and two bases in the table above were wrong.** The
> whole share file was audited against the source each row names. **IRELAND 6.3% → 30.9%** (the row
> was tagged SIMI but carried the JP VIN register figure; SIMI's scrap-adjusted parc is 464 of 1,502),
> so Ireland's true move is **+6.5%**, not +1.3%. **PORTUGAL 62.0% → 69.0%** (1,299 of 1,883
> N-series, not of all 2,111 register rows) → +12.8%. **BELGIUM 91.8% → 85.7%** (NLR 42 of 49) →
> +0.5%. **MALTA and CYPRUS are now marked `unmeasured` with their rate held** — both rested on
> reading NMR88 as an N35, and NMR88 is a 9.5 t truck; Cyprus holds zero 3.5 t in the register.
> Germany (153/697), ITUK and UTI confirmed unchanged. The whole-figure scaling bug this section
> describes did **not** recur. See `01_data/00_derived/n35_share_audit_20260918.csv`.

ITUK, 2025: oil filter expected 11,680 → 17,285, cover 116.4% → **78.7%**; fuel filter 157.0% →
106.1%; air filter 94.4% → 63.8%.

**Note on direction, because it reads as an increase and is not one.** Expected demand rising does
not mean more sales. It is the *denominator* of capture that rises, because an N35 needs twice the
services of an N75 over the same distance and the old model charged both the N75 rate. The actual
units billed are unchanged; the same sales are simply measured against a larger, more correct
requirement, so the capture percentage falls. ITUK's cover moving 116.4% → 78.7% means the market was
never above 100% — the old denominator was too small.

**The two lanes remain deliberately different, and that is not new.**

| Lane | Governing file | Oil-filter cover | Changed? |
|---|---|---|---|
| IML v7 (external, agreed) | `iml_v7_ituk_cy2025.yaml` | **35.1%** | **No** |
| PRISM lane (internal) | `pms_capture_by_db_year.csv` | 116.4% → **78.7%** | Yes |

The PRISM-lane contract in `verification_fixtures.yaml` was re-based with the change, from the 2025
band `1.15–1.28` to `0.74–0.84`, and the file now carries a scope note saying it governs the PRISM
lane only and explicitly not the IML v7 lane. The two figures print side by side in `isze_data.json`,
which is the honest presentation of two different bases.

**Not applied, deliberately:** the mileage re-base. Measured odometer data exists per market
(`warranty_cv_km_age_by_market.csv`) and disagrees with both lanes — UK N35 12,891 km against an
assumed 20,000, N75 35,478 against an assumed 50,000. Re-basing on it moved 12 of 18 markets,
contradicted the published IML figures, and drove Greece to 1,156% capture because that market's
LCV median rests on one vehicle at 1,590 km. It needs a minimum-sample guard and a chosen mileage
basis first.

**Sources of truth for the intervals — René's sheets are the reference.** Jerome's rule, 2026-09-18:
René's files stand unless a distributor says it is different. The sheets are on disk at
`01_data\03_PMS\service_schedules\` and are split by market themselves — the F-series MY24 sheet is
headed *Italy, Israel, Portugal, United Kingdom, Ireland*. The one market difference inside the
N-series sheet is Israel, where NPR75 oil and fuel run at 22,500 km rather than 40,000. That is
**not yet applied** and is the next piece, as is the corresponding split for the other markets'
N-series sheets.

## 7. State at the end of 2026-09-18

| Item | State |
|---|---|
| `pms_capture_config.BUCKET_SERVICES_PER_YEAR` | **changed** — N35 ratio applied, per market |
| `pms_capture_by_db_year.csv` | **rebuilt on the ratio**; backup `...bak_pre_n35_ratio_20260918` |
| `pms_summary_by_db.csv`, `isze_data.json` | regenerated from it |
| `verification_fixtures.yaml` | ITUK PRISM-lane band re-based to 0.74–0.84, scope note added |
| `pms_engine.py` | `expected_by_category_bucketed` unchanged — the ratio lands through the config it already reads |
| `modules/service_interval_rates.py` | written, **not wired** — for the mileage step |
| IML v7 lane, exec paper, hub | **untouched** (still 35.1% / €2.04M) |
| Pipeline verify | **143 pass / 0 warn / 0 fail** |
| Audit | `01_data\00_derived\pms_n35_ratio_applied_20260918.csv` — before/after on every row |
| Apply script | `01_data\91_build\pn_ammo_probe_20260918\_apply_n35_ratio.py` — **idempotent** (restores from backup first, and scales only the cv_std slice) |

### Two bugs found and fixed during this change, recorded so they are not repeated

1. **Whole-total scaling.** The first version multiplied `expected_qty` by the market factor, which
   inflated the LCV block as well as the truck block. Belgium read +91.8% when its true move is
   +0.55%, because 9,480 of its 9,593 vehicles are light. Caught by Jerome from the figure, not by
   any check here. The fix scales `cv_std_uio × rate × factor` only.
2. **Non-idempotent apply.** Running it twice compounded the ratio (Belgium reached +275%). The
   script now always restores the baseline backup before applying, so a rerun cannot compound.

A third, from the earlier abandoned attempt: **an LCV median resting on a handful of VINs** drove
Greece to 1,156% capture. Any future mileage step needs a minimum-sample guard.

**Greece is provably unchanged.** Expected demand 97,564 before and after; capture 40.3% before and
after.
