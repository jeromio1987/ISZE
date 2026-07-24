# BVP Parts — Where to Go
### Strategic deployment report · Internal ISZE prep

**Date:** 2026-05-28
**Author:** Jerome Van der Pluym (analysis support: Claude)
**Data source:** PRISM verified derived pipeline (`01_data/derived/`), CY2025 unless noted. Verification: 86 pass / 0 fail (`verify_derived_pipeline.py`, 2026-05-28).

---

## TL;DR

Across the network, **BVP has already won the contested basket — 83.5% of revenue** in parts that have both a genuine and a BVP option. The strategic question is therefore *not* "should we push BVP." It is **where BVP is pure incremental volume vs. where it would cannibalise high-margin genuine revenue during the Golden Window (2025–2032)**.

**Decision: proceed with Tier 1 (approved).** Deploy BVP hard where genuine revenue is already lost or absent, and where distributors are under-penetrated. Hold BVP back from the genuine strongholds (oil filter, ITUK/UTI).

---

## Two scope caveats (read before quoting any number)

1. **"Contested basket" = paired parts only.** The €4.38M / 83.5% BVP figures cover the universe of parts that have *both* a genuine and a BVP option (the genuine↔BVP crossref set, 7 families). This is the battleground subset — **not** total ISZE parts revenue. Genuine-only catalogue sits outside it.
2. **No BVP-specific GP figure is used.** BVP gross margin is structurally below genuine, but no hard BVP GP number exists in the data, so none is quoted. All margin logic here is directional (BVP < genuine GP), not a stated percentage.

---

## The picture (CY2025, verified)

### Contested basket — BVP dominance
| | Value |
|---|---|
| Contested basket revenue (7 families) | €4,377,992 |
| Network BVP share of € | **83.5%** |
| ITUK BVP share of € (the holdout) | **61.3%** |
| BVP-driven AIM/classification high-risk revenue | ~€9.8K (0.01%) — negligible |

### Penetration whitespace (addressable BVP PNs not yet sold)
**Distributor gaps:** ICELAND 0% · MALTA 3% · ROMANIA 12% · KAZAKHSTAN 12% · IUK 16% · CYPRUS 19%. *(ITUK leads at 50%.)*
**Subgroup gaps:** clutch_kit (24 PNs) · shock_absorber (20) · wheel_pin (19) · oil_filter (18) · clutch_disc (17).

### Substitution battleground — BVP unit share, head-to-head
| Status | Subgroups (BVP unit share) |
|---|---|
| **Conceded to BVP** | wiper_blade 81% · clutch_pressure_plate 74% · fuel_filter 65% *(155K units — top volume)* · clutch_disc 64% |
| **Genuine still competitive** | air_filter 56% · oil_filter 47% *(and rising)* · hub_bearing 42% · shock_absorber 38% · clutch_kit 30% *(228 genuine-only pairs)* |

---

## Recommendation — three tiers

### TIER 1 — GO HARD ✅ *(approved — incremental, zero genuine cannibalisation)*
- **The four 100%-BVP families** — Suspension_Chassis, Cab_Misc, Electrical, Belts_Cooling. Genuine revenue here is €0; every BVP unit is incremental. Push everywhere.
- **wiper_blade (81%), clutch_pressure_plate (74%)** — genuine already lost; BVP defends the volume.
- **Geographic fill:** ICELAND, MALTA, ROMANIA, KAZAKHSTAN, CYPRUS. Addressable catalogue exists, penetration is low, and these are not genuine strongholds — BVP captures aftermarket-lost volume, not our own genuine GP.

**Why it's safe:** none of Tier 1 trades away winnable genuine margin. AIM/compliance cost of expansion is effectively zero (€9.8K, 0.01%).

### TIER 2 — SELECTIVE *(decide per category)*
- **fuel_filter** — BVP winning (65%) on the largest volume in the book, but genuine still material. Let BVP run at price-sensitive distributors; protect genuine at the flagship.
- **clutch_kit** — biggest single whitespace (24 PNs) but 228 genuine-only pairs = genuine stronghold. **Open question:** is genuine winning on merit, or just absence of a credible aftermarket clutch alternative? That answer moves clutch_kit to Tier 1 (attack) or Tier 3 (leave alone).

### TIER 3 — HOLD, protect genuine *(Golden Window)*
- **oil_filter** — genuine is actively *reclaiming* this category (ITUK genuine capture 64% → 103%, 2023→2025). It appears as 18-PN whitespace, but that is a trap: filling BVP at non-genuine distributors is fine; **pushing BVP oil filters at ITUK / genuine strongholds reverses a live margin win.** Do not.
- **ITUK and UTI broadly** — genuine holdouts (under-index network BVP by ~15pp). ITUK is the Golden Window flagship. BVP stays a *targeted defensive tool* here, never a share-growth target.

---

## Core judgment

The Golden Window thesis (2025–2032 = peak *genuine* parts revenue for the ICE D-Max/N-series parc) makes the optimisation explicit: **maximise BVP where genuine € is already lost; starve it where genuine € is winnable.** Network-wide BVP share is the wrong KPI. Maximising BVP at ITUK would be the single most value-destructive move available — trading peak-window genuine GP for low-margin BVP volume.

---

## Open items
1. **Clutch_kit competitive read** — does a credible aftermarket clutch alternative exist for D-Max/N-series? (Decides Tier 2.)
2. **BVP GP benchmark** — a hard BVP-vs-genuine margin figure would let us quantify the cannibalisation cost in Tier 3 and prioritise Tier 1 geographies by € upside.

---
*Figures sourced from: `bvp_addressable_basket.csv`, `mix_genuine_bvp_by_family.csv`, `substitution_by_db_year.csv`, `aim_bvp_family_risk.csv`, `db_benchmark_mix.csv`, `pms_capture_by_db_year.csv`. Regenerate via `python scripts/build_strategic_contracts.py` then `python scripts/verify_derived_pipeline.py`.*
