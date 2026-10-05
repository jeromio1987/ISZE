---
name: isze-verify-pipeline
description: >-
  Verify ISZE sales analytics builds (P0-P5) after Codex or Claude changes.
  Run deterministic checks, read the report, and only sign off when green.
---

# ISZE pipeline — build, verify, Claude in the loop

Use this skill whenever you touch:

- `01_data/derived/*` (workspace root: `ISZE/`)
- `prism/scripts/build_*.py`
- `prism/modules/bvp_*.py`, `pms_engine.py`, `data_prep.py`
- BVP / PMS / GPS Streamlit pages

## Roles

| Role | Who | Job |
|------|-----|-----|
| **Builder** | Codex agent (or you) | Edit code, run builds |
| **Verifier** | `verify_derived_pipeline.py` | Deterministic gates (row counts, schema, ITUK UIO anchor, capture bands, GPS/AIM content, UIO consistency cross-check, build manifest) |
| **Reviewer** | Claude (this session) | Read `_verification_report.md`, challenge failures, update fixtures if refresh was intentional |

Codex must **not** claim “build succeeded” or quote ITUK capture % without a green verification report.

## One-shot command

Set `$env:ISZE_ROOT` to your ISZE workspace root if not running from the default tree, then:

```powershell
cd $env:ISZE_ROOT\03_analytics\Isuzu\prism
.\scripts\run_pipeline_and_verify.ps1
```

Or verify only (no rebuild):

```powershell
cd $env:ISZE_ROOT\03_analytics\Isuzu\prism
python scripts/verify_derived_pipeline.py
```

## After every build

1. Open `01_data/derived/_verification_report.md`
2. If any **fail** — fix root cause, re-run builds, re-verify
3. If **warn** only — explain to user (e.g. row count drift after new CY file)
4. If all **pass** — safe to cite numbers in PRISM UI, memory docs, or GPT-safe exports

## Updating golden values

When billing or UIO intentionally changes, edit:

`prism/data/verification_fixtures.yaml`

Then re-run verify. Do not weaken bands without user confirmation.

## ITUK pilot anchors (do not regress silently)

- PRISM-lane UIO denominator: **23,068** bucketed PRISM-lane UIO (cv_std + f_series split; `UIO_OVERRIDES["ITUK"]` in `bvp_analytics.py`). This is the denominator checked against `verification_fixtures.yaml`.
- **The 22,389 figure is a separate lane, not this denominator.** It is the IML v7 external standard (DVLA March 2026) and the basis of the externally published 35.1% oil-filter cover. It is deliberately unchanged — never substitute one for the other, and never quote a PRISM-lane rate against the IML denominator.
- Oil filter total capture bands, PRISM lane (**100% addressable**, registry + BVP-catalog actuals; bands read from `verification_fixtures.yaml`, re-based 2026-09-18 for the N35/N75 interval split):
  - CY2024: **52–61%** uncapped (~56.4% observed)
  - CY2025: **74–84%** uncapped (~78.7% observed)
- These are NOT comparable to legacy dealer-level single-PN rates (~10% / ~17%)
- `verify_derived_pipeline.py` cross-checks `UIO_OVERRIDES` vs `verification_fixtures.yaml` on every run

## GPT / external tools

Never upload `raw/sales/*.XLSX`. After verify passes, aggregates may go to `01_data/gpt_safe/` only.
