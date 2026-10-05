# isze_pricing

Pricing engine for ISZE. Two models, one config, every run logged.

Implements `ISZE_Pricing_Spec_v1.md`. No raw billing data is required to run,
test or modify it — which is deliberate: under the Tier 0 rule the tool travels
to the data, not the reverse.

## Install / run

```bash
pip install pandas numpy pyyaml tabulate
python -m isze_pricing.cli launch --model dmax_22
python -m isze_pricing.cli alloc  --set allocation.target=0.03
python -m isze_pricing.cli sweep
```

## Files

| File | What it is |
|---|---|
| `config.yaml` | **Every dial.** Nothing is hardcoded in the code. Change here, re-run, compare |
| `launch_parts.csv` | Parts catalogue for launch pricing. The file Jerome populates |
| `engine.py` | Allocation core — index solver, two-gate sign rules, evidence tiering |
| `theta.py` | Momentum — θ_parc from the corrected car park, with its provenance gate |
| `launch_book.py` | New-model lifecycle model — parc, capture erosion, discounted GP |
| `runlog.py` | Run registry and reproducibility |
| `cli.py` | Entry point |
| `runs/` | One folder per run + `REGISTRY.csv` |

## Modifying it

**Change a number** → edit `config.yaml`. Nothing else.

**Try a variant without editing the file** → `--set dotted.key=value`:

```bash
python -m isze_pricing.cli --set allocation.policy_premium=2.0 alloc
python -m isze_pricing.cli --set launch.discount_rate=0.10 launch --model p700
```

**Add a launch tactic** → add a block under `launch.scenarios`. It is picked up
automatically; no code change.

**Add parts** → append rows to `launch_parts.csv`.

**Move to PN-level** → `engine.run()` takes any frame with `weight, zone,
isze_premium, evidence_n, evidence_tier, theta_bucket`. Write an adapter
alongside `from_action_map()`; the engine does not care about granularity.

## Run logging

Every invocation writes `runs/<UTC>__<kind>__<scenario>/` containing the resolved
config, sha256 of every input file, all output tables, and a `summary.md`. One
line per run lands in `runs/REGISTRY.csv`.

Any number this engine produces traces back to the exact config and input bytes
that produced it.

## What is measured vs assumed

Everything tagged `[ASSUMPTION]` in `config.yaml` is a modelling choice with no
observed data behind it. That includes the whole erosion model in the launch book.

**There is no elasticity coefficient in the allocation solver**, per Jerome's
2026-08-01 finding that elasticity is not measurable at **ISZE→DB** level.
DB→DLR response for **ITUK + UTI** is a labeled **proxy** on ASP / list
pass-through (lasting basis — dealer invoice is not a near-term ask):

- `01_data/00_derived/price_elasticity_db_dlr_ituk_uti.csv`
- method: `01_data/01_Pricing/PRICE_ELASTICITY_DB_DLR_ITUK_UTI.md`
- config: `paths.db_dlr_response` → soft join in `db_dlr_response.py` on `alloc`

Soft signal only: run input hash, diagnostic table, exact (db, PMS cat) flags.
Do **not** multiply allocation deltas by `beta` until `measure_kind=elasticity`
exists with adequate n. The launch book's value is in ranking tactics, not
forecasting a volume response.

**OEM peer street:** fill `oem_peer_scrape_list.csv` → `ingest_oem_peer_street.py`
→ basket → `apply_oem_benchmark`. Runbook: `OEM_STREET_ARRANGE.md`.

```bash
python -m isze_pricing.cli diagnose   # readiness + peer street vs Isuze (PR00×1.785)
python 03_analytics/isze_pricing/scan_eucon_comparable_oem_gap.py
```

internal status brief: `01_data/01_Pricing/PRICING_STATUS_BRIEF_2026-08-10.md`.

## The premium is per category, and it is gated

`allocation.policy_premium` is **not a flat rate**. A single premium across all
categories repeats the class factor's own error — it prices a body panel and a
NOx sensor identically. Each category carries a value *and a basis*:

```yaml
policy_premium:
  by_category:
    brake_pad: {value: 1.40, basis: placeholder}
require_basis: [oem_benchmark, iam_derived]
```

A category whose basis is not in `require_basis` **does not move**. Today every
category is `placeholder`, so a full allocation run holds all 213 cells flat and
reports `n_unbenchmarked_premium: 213`. That is intentional: a premium nobody has
benchmarked is a guess with a decimal point, and the engine must not launder it
into a target.

Two unknowns sit underneath, respected rather than assumed away:

1. **We do not know whether IML has already embedded a premium in BP_JPY**, or
   whether it varies by part type. Layering a flat ISZE premium on top of an
   unknown IML one compounds two errors.
2. **The right reference is a competitor OEM genuine price, not an IAM price.**
   IAM is the floor; the OEM peer is the benchmark. We measure only against IAM
   today, which is why every basis reads `placeholder`.

`launch.erosion.*` is the other judgement-heavy block. `sweep` reports how much
each dimension actually moves the answer — currently mileage 94.5%, IAM entry
2.6%, erosion 1.1%, tactic choice 0.28%.

## Momentum is wired, but only one of its four components

Spec §6 factors θ into `θ_parc × θ_interval × θ_cohort × θ_warranty`. **Only
θ_parc is implemented.** θ_interval is still blocked on the chassis-code →
model-year / SCR mapping; θ_cohort and θ_warranty are Partial. The other three
sit at 1.0 rather than being filled with something plausible.

θ_parc comes from `01_data/00_derived/UIO_carpark_for_GPS_recalc_2026-07-30.csv`
— wallet-weighted CY2026-corrected ÷ CY2025, which reconciles to that file's own
network total (€60,218,250 / €60,785,305, −4.91% vs its stated −4.9%).

The join is distributor-first, then country. That is not cosmetic: the action map
names a country for most cells but a distributor for the two markets that have
more than one, and those four are €3.27M of €5.77M captured. **IUK's LCV parc is
falling 6.0% while ITUK's CV parc rises 4.8%** — a single `U KING` θ would net
them against each other and lose both signals.

Each θ carries a basis, gated by `theta.require_basis` exactly as the premium is:

| Basis | Source | Moves price? |
|---|---|---|
| `uio_locked` | IUK LCV 44,926 — the one exact figure | yes |
| `uio_cohort_model` | ITUK, proper survival model, untouched by the fix | yes |
| `uio_constant_hazard` | corrected by constant-hazard estimate (10.2 / 12.3%) | yes |
| `uio_known_defect` | UTI — missing weight classes, ~23% low | **no** |

**Read the spread before trusting it.** Because no category has a benchmarked
premium, every one of the 213 cells is `NO_EVIDENCE_HOLD` and `d_pos` is zero —
so θ_parc is currently the *only* thing differentiating the allocation. On the
default gate it moves 60 cells: declining takes +1.3%, stable +3.4%, growing
+6.3%, and the 3.00% index still lands exactly. Of the €1.75M in the declining
bucket, €1.17M is the locked IUK figure; the entire €0.59M growing bucket is
constant-hazard estimate, which the car park's own documentation says the full
V20 cohort rebuild will shift by a few per cent. The declining side is anchored,
the growing side is not.

To see the allocation on measured parc only:

```bash
python -m isze_pricing.cli --set theta.require_basis=[uio_locked,uio_cohort_model] alloc
```

That leaves IUK as the sole mover: 12 cells at +1.4% against +3.4% for everyone
else. Gating `uio_known_defect` costs nothing today — UTI's θ is 1.045, already
inside the stable band — so it is a guard against a future car park revision
rather than a live haircut.

θ is a **reallocation** device, not an addition. The index solve absorbs it: the
euro-weighted θ contribution is −0.30pp, so base rises 3.00% → 3.30% and the
declining cells' discount is carried by everyone else.

## Known limits

- **No OEM benchmark exists yet.** Until one does, the allocation engine cannot
  justify differentiating any line, and `alloc` correctly returns a flat run.
- **Body parts are a blind spot.** Not among the 14 PMS categories, absent from
  the action map entirely — yet Israel has raised price complaints there. Marked
  `excluded_blind_spot`; nothing prices it from here.
- Eucon is 44 PNs, n=1–3 per category, within-category spread over 2x.
  `min_n: 3` gates the worst of it but coverage is the binding constraint.
- `p700` costs and volumes remain placeholders; the **spec is now confirmed** —
  new-generation N-Series, engines and SCR carry over, DCT/ADAS/LED are new.
  Rankings are usable, euro amounts are not.
- Realization / pocket-price waterfall is absent — blocked on dated PR00 history.
- 522 PNs / €4.96M billed with no PR00 entry are out of scope of any run here.
- **θ is per distributor/country, not per category.** Categories sell across LD,
  MD and LCV in different proportions and no category → `model_type` mapping
  exists, so every category in a market takes that market's θ. Building that
  mapping is the natural sibling of the chassis-code unblock.
- **θ_interval, θ_cohort and θ_warranty are still 1.0.** Only θ_parc is wired,
  so the D-Max 15,000 km service-interval effect — the largest known momentum
  signal in the spec — is not in any number this engine prints.
- `01_data/00_derived` sits outside the default sparse checkout. If the car park
  file is missing the run does not fail: θ degrades to flat and `summary.md`
  records `theta_source: MISSING::<path>`. Check that line before reading a
  spread. To pull the data in: `git sparse-checkout add 01_data/00_derived`.
