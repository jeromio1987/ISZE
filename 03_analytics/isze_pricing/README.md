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

**There is no elasticity coefficient anywhere in this package**, per Jerome's
2026-08-01 finding that elasticity is not measurable at ISZE level. The launch
book's value is in ranking tactics against each other, not in forecasting a number.

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
- `theta_bucket` is hardcoded to `stable` — momentum is specified but not wired
  to UIO, and contributes nothing to current output.
