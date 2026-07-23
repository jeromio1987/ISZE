# ITUK Brake Wear-Factor — IML Ask (2026-07-23)

Two open brake assumptions in the internal capture model, both flagged "needs IML, not a guess." Bundled into one ask since both are brake-wear-interval questions IML is best placed to answer together.

---

## Send this

> **Two questions on brake replacement patterns, for our internal service-capture modelling:**
>
> **1. Pad/shoe unit definition.** When a brake job is done as one paired front+rear event, does your data track that as **one `brake_pad` unit** (one job = one unit, regardless of axle count) or **one unit per axle** (front+rear = two units)? We're currently assuming the former; if it's actually the latter, we're undercounting expected pad/shoe demand by roughly half.
>
> **2. Rotor replacement interval.** Roughly how often are brake rotors/discs replaced relative to pads — every pad change, every second pad change, or less often? We've been assuming "every second pad change" as a placeholder with no real source.
>
> No target numbers needed — just the real-world pattern, so we can stop guessing.

---

## Why it matters (internal only — PRISM lane, do not quote to IML/ITUK)

Per [`00_docs/ITUK_PRISM_LANE_BRIDGE.md`](../../00_docs/ITUK_PRISM_LANE_BRIDGE.md): these are PRISM-internal capture-model figures (`pms_capture_by_db_year.csv`, CY2025), **not** the Model B/IML-facing numbers (35.1% oil-filter / €2.04M gap) IML has actually seen — Model B doesn't use a per-unit brake factor at all, and doesn't have a rotor category. This section is sizing for us, not material for the email.

**Q1 — pad/shoe factor, 0.4 (current) vs 0.8 (if per-axle), ITUK CY2025:**

| Category | Actual units | Actual revenue | Expected @0.4 | Capture @0.4 | Expected @0.8 | Capture @0.8 | Gap @0.4 | Gap @0.8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Brake pad | 3,404 | €302,550 | 4,672 | 72.9% | 9,344 | 36.4% | €112.7K | €528.0K |
| Brake shoe | 559 | €28,643 | 4,672 | 12.0% | 9,344 | 6.0% | €210.8K | €450.2K |
| **Combined** | | | | | | | **€323.5K** | **€978.1K** |

Actual sales/revenue are facts and don't move — only the expected-demand denominator and the resulting "gap" story change. **Swing: +€654.7K in modelled gap, and the capture headline we'd show internally roughly halves (72.9%→36.4% on pad) if 0.8 turns out to be right.**

**Q2 — rotor wear factor, 0.25 (current, unsourced "every 2nd pad change" guess) vs ~0.5 (data-implied), network CY2025:**

| | Expected | Actual | Capture | Gap |
|---|---:|---:|---:|---:|
| @0.25 (current) | 38,035 | 20,714 | 54.5% | €1.39M |
| @0.50 (see below) | 76,071 | 20,714 | 27.2% | €3.75M |

**Swing: +€2.35M in modelled network gap.** The 0.5 scenario isn't arbitrary: ITUK is the one market with real inspection-driven data (UK O-Licence), and its rotor sales already run at **197.7% of the current @0.25 expected demand** — i.e. ITUK sells almost 2× what the model expects. Back-solving the factor that would put ITUK at ~100% capture gives **≈0.494** — coincidentally close to the *same* 0.5 used as the global brake_pad default, i.e. "rotors wear about as fast as pads," not "half as fast." That's a data-grounded hypothesis, not a confirmed number — still needs IML.

**Source:** `01_data/00_derived/pms_capture_by_db_year.csv` (2025, `line_type='total'`), rescaled per `modules/pms_engine.expected_by_category_bucketed()` — expected_qty is exactly linear in the wear factor for both categories (confirmed: ITUK carries 0 LCV-bucket UIO, so the LCV-specific override path doesn't distort the pad/shoe rescale). Modelling script: `brake_scenario_model.py` (scratch, not committed).
