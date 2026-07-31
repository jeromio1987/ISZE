# Portugal PMS — age-weighted wear-item deep dive

**Date:** 2026-07-28 | **Trigger:** Jerome — "you have VIN numbers right? ... do a very deep PMS study" | **Scope:** Portugal only, wear items (clutch + brake). Consumable/filter categories not materially affected — see Finding 1.

## Headline

The live PMS model (`pms_capture_by_db_year.csv`, CY2025) runs Portugal on a V19-derived UIO bucket split, flagged in its own brief as **"MED confidence — central v18 parc-model UIO (not own-registration)."** We now have real registration-level data (`Matriculas Isuzu SAP.xlsx`, Imotors' own SAP export, 14,413 chassis, 2005-2026). This note replaces the modeled bucket split with the real one, and — the actual new finding — adds real vehicle **age**, which the current model doesn't use at all for wear items.

**Bottom line: reported wear-item capture is understated by roughly 30-50% relative, because the model spreads expected clutch/brake demand evenly across the whole fleet, including trucks registered in the last 2 years that essentially never need either. Correcting for age doesn't fix the underlying problem — genuine clutch and brake capture is still very low — but it changes the size of the number you'd quote.**

## Method

1. Real annual registrations by vehicle class (lcv/D-Max, cv_std/N-series, f_series), from `Matriculas Isuzu SAP.xlsx`, sheets `2005-2019` + `2019-2026` (2026 excluded — partial year, file pulled ~2026-07-06).
2. Aged each registration-year cohort forward to CY2025 on the same survival curves already validated for the UIO work this session (LCV: 98/95/92/89/84/80/65/50/40/20/10/0% by age; CV-Developed for cv_std/f_series).
3. Reproduced the PMS engine's own formula exactly (`modules/pms_engine.py::expected_by_category_bucketed`, `modules/pms_capture_config.py`) — verified to the decimal against all 9 wear-item rows in `pms_capture_by_db_year.csv` before changing anything. Formula per category:
   `expected = UIO_cv_std×0.5×factor + UIO_f_series×0.6667×factor + UIO_lcv×1.0×factor_lcv`
   — where `factor_lcv` defaults to the same wear_factor, **except brake_pad, which has a genuine, already-confirmed LCV override (0.4, "front brake-kit basis, 50,000km" vs the general 0.5)**. This one took a first pass to find — my first attempt at this brief used one flat formula for all brake items and didn't reproduce brake_pad's reported number; the fix was finding this existing override in `pms_capture_config.py`, not changing the model.
4. Age-band sensitivity: recomputed expected demand **excluding the 0-2yr-old cohort** from the wear-item base. This is an illustrative floor, not a sourced replacement factor — presented as a bound, because a real age-vs-wear-probability curve doesn't exist yet (same gap flagged for GPS in `reference_gps_metric.md`).

## Finding 1 — fleet composition, real vs modeled (small effect)

| Bucket | V19 model (current) | Real (Matriculas, CY2025) | Δ |
|---|---:|---:|---:|
| lcv (D-Max/pickup) | 4,733 | 4,569 | −3.5% |
| cv_std (N-series) | 2,206 | 2,384 | +8.1% |
| f_series | 269 | 283 | +5.1% |
| **Total** | **7,208** | **7,235** | +0.4% |

Total barely moves (confirms the UIO work done earlier this session — 2025 wasn't the broken part of V19). Composition shifts a few points toward trucks. This alone moves expected demand for every category by about −1%, immaterial on its own.

## Finding 2 — age is the real story

Age distribution of the "addressable" service base (same weighted total the model already uses for oil filters and, by extension, clutch):

| Age band | Share of addressable base |
|---|---:|
| 0-2yr | 31.9% |
| 3-5yr | 30.7% |
| 6-8yr | 26.7% |
| 9yr+ | 10.7% |

By vehicle class, the 0-2yr share is uneven: **lcv 35.8%**, f_series 34.4%, cv_std 16.7%. Nearly a third of what the model counts as "due for a clutch or brake job this year" is a vehicle bought in the last two years — heavily weighted toward pickups, which is also where Portugal's registration growth has concentrated (2024 alone: 975 pickup registrations).

## Finding 3 — corrected expected demand and capture, all 9 wear items

CY2025, Portugal, total (genuine+BVP) actuals unchanged from the live model — only the denominator changes.

| Category | Current model exp. | Actual | Capture (current) | Real-bucket exp. | Capture (real) | Ex-0-2yr exp. (illustrative) | Capture (ex-0-2yr) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Clutch disc | 1,203 | 34 | 2.8% | 1,190 | 2.9% | 810 | **4.2%** |
| Clutch pressure plate | 1,203 | 46 | 3.8% | 1,190 | 3.9% | 810 | **5.7%** |
| Clutch kit | 902 | 69 | 7.6% | 892 | 7.7% | 608 | **11.4%** |
| Release bearing | 902 | 10 | 1.1% | 892 | 1.1% | 608 | **1.6%** |
| Pilot bearing | 602 | 0 | 0.0% | 595 | 0.0% | 405 | 0.0% |
| Clutch booster | 602 | 0 | 0.0% | 595 | 0.0% | 405 | 0.0% |
| Brake pad | 2,534 | 24 | 0.9% | 2,518 | 1.0% | 1,732 | **1.4%** |
| Brake shoe | 3,008 | 87 | 2.9% | 2,975 | 2.9% | 2,025 | **4.3%** |
| Brake rotor | 1,504 | 219 | 14.6% | 1,487 | 14.7% | 1,012 | **21.6%** |

Real-bucket alone (Finding 1) changes almost nothing. The age adjustment (illustrative — see caveat) lifts every capture rate by roughly 40-50% relative — e.g., clutch disc 2.8%→4.2%, brake rotor 14.6%→21.6%.

## Read

**This does not overturn the existing finding that clutch/brake capture is a real, genuine leakage problem, not a data artifact** (consistent with the prior network-level finding in memory). It resizes it. Even at the age-adjusted, more generous denominator, genuine clutch and brake pad capture sit at 1-6% — Portugal is barely selling genuine clutches or brake pads regardless of how the denominator is drawn. Brake rotor and clutch kit look meaningfully less catastrophic (11-22%) once near-new trucks are taken out of the base.

**Pilot bearing and clutch booster show zero actual sales at any denominator** — that's not a modeling artifact, that's a real zero. Worth checking with the distributor whether these are being fitted at all, or substituted by a BVP/aftermarket equivalent not in the genuine registry.

## Caveats

- The "exclude 0-2yr" cut is a judgement floor, not a sourced wear-probability curve. A real one (probability of clutch/brake replacement by vehicle age, ideally by class) doesn't exist anywhere in the current model — this is the same missing input flagged for GPS in `reference_gps_metric.md`. Treat the ex-0-2yr column as a directional bound, not a number to quote externally.
- Brake_pad's LCV override (0.4) was already correct and IML-sourced in the model before this note — the point above is that my first pass here missed it, not that the model was wrong.
- This is Portugal only. VIN shipment data (not registration data) is what's available for the other 6 markets, and carries the shipment-vs-registration lag caveat already documented in `project_uio_v20.md`.
- Not wired into the live pipeline. `uio_by_model_bucket.csv` (what `pms_engine.py` actually reads) still has Portugal on the V19 split. This note is an offline check — pushing it live would mean regenerating that CSV from Matriculas and deciding how to source an age curve, which is a separate, larger piece of work.

See [[project_uio_v20]], [[project_pms_model]].
