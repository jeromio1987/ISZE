---
name: scraper-triage
description: >-
  Weekly triage of ISZE scraper health output under 04_tools/. Read
  scraper_health_report.md and proposed_patch.diff; apply allowlisted patches
  or escalate manual_review items. Use when Jerome asks to review scraper
  health, weekly scraper check, or proposed_patch.diff.
---

# ISZE scraper triage (weekly)

**Model tier: CHEAP**

Policy `ISZE/DECISIONS.md` § 2026-07-24: healthcheck **auto-applies** allowlisted competitive scrapers; Tender stays propose-only. This skill is for Jerome's manual Monday triage of leftovers.

## Preflight

```powershell
if (-not $env:ISZE_ROOT) { $env:ISZE_ROOT = 'C:\Users\jerom\Desktop\claude\ISZE' }
$tools = Join-Path $env:ISZE_ROOT '04_tools'
Test-Path (Join-Path $tools 'scraper_health_report.md')
```

## Read (in order)

1. `$env:ISZE_ROOT\04_tools\scraper_health_report.md`
2. `$env:ISZE_ROOT\04_tools\applied_patches_log.md` — what the job already applied
3. `$env:ISZE_ROOT\04_tools\proposed_patch.diff` — leftovers
4. `$env:ISZE_ROOT\04_tools\manual_review_required.md`

## Verifier

| Check | PASS | FAIL → escalate |
|-------|------|-----------------|
| Tender JSON fresh | `tender_data.json` meta ≤ 14 days | Stale tender |
| KS CSV fresh | `ks_results.csv` ≤ 14 days | Stale pricing |
| Allowlist scope | applied log only names allowlisted `*_scraper.py` | Off-list edit → revert + report |

## Allowlist (auto-apply OK for job; you may also apply these by hand)

`ks_scraper.py`, `tranzparts_scraper.py`, `tmc_scraper.py`, `mekonomen_scraper.py`, `auto365_scraper.py` under `04_tools/autodoc_scraper/` — URL/selector string fixes only.

**Escalate (never silent-apply):** Tender Install tree, `refresh_and_check_drift.py`, Autodoc/Oscaro/Mister Auto, bats/ps1/yaml.

## Apply leftover allowlisted patch (if job left it in proposed_patch.diff)

```powershell
cd $env:ISZE_ROOT\04_tools
# Prefer applying only hunks that touch allowlisted *_scraper.py files
git apply --check proposed_patch.diff
git apply proposed_patch.diff
python -m py_compile autodoc_scraper\ks_scraper.py  # and any other touched allowlisted files
```

Append to `applied_patches_log.md`. Revert with `git checkout -- <file>` if compile/smoke fails.

## Escalate

Summarize for Jerome:

- Open manual-review item numbers + one-line root cause
- Whether diff is empty vs actionable
- Suggested next step (live browser test, Task Scheduler check, etc.)

Do not apply Tender / wrapper / credential hunks.

## Out of scope

- Do not load `01_data\raw\sales\*.XLSX`
- Do not edit `07_deploy/` (generated mirror only)
