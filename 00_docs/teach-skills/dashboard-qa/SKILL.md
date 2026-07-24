---
name: dashboard-qa
description: >-
  Visual QA for ISZE/GPS HTML dashboards under 02_dashboards/. Run harness
  checks, open dashboards in a browser, confirm charts render with vendored
  ECharts (no CDN), console clean. Use after dashboard rebuilds or before
  sharing GPS/fleet HTML.
---

# ISZE dashboard visual QA

**Model tier: CHEAP**

Local HTML: `$env:ISZE_ROOT\02_dashboards\`. JSON feeds: `$env:ISZE_ROOT\01_data\dashboards\`. Never edit `07_deploy/`.

## Preflight

```powershell
if (-not $env:ISZE_ROOT) { . "$PWD\ISZE\04_tools\workspace\isze_root.ps1"; $env:ISZE_ROOT = Get-IszeRoot }
```

## Step 1 — Harness (deterministic gate)

No “looks fine” without a green gate (same habit as `isze-verify-pipeline`).

```powershell
cd $env:ISZE_ROOT\04_tools
python gps_reconcile.py --skip-raw --skip-kosha
```

Read `$env:ISZE_ROOT\01_data\derived\gps_reconciliation_report.json`. **FAIL** if `dashboard_selfcontained` reports external CDN `<script src>` or nested-script ECharts breakage.

GPS dashboards must inline `$env:ISZE_ROOT\02_dashboards\_ui\echarts.min.js` (see `02_dashboards\_build\build_gps_dashboards.py`). CDN → blank chart divs offline.

IDS dealer compare: `build_ids_dashboard.py` runs `ids_dashboard_qa.py` — no `--skip-qa` unless explicit.

## Step 2 — Open targets

Priority files (task may name others):

- `$env:ISZE_ROOT\02_dashboards\fleet\ISZE_GPS_Dashboard.html`
- `$env:ISZE_ROOT\02_dashboards\gps\ISZE_GPS_Network_SPU_Dashboard.html`
- `$env:ISZE_ROOT\02_dashboards\gps\ISZE_GPS_TargetStudy_Reconciliation_Dashboard.html`
- `$env:ISZE_ROOT\02_dashboards\hub\MASTER_DASHBOARD.html`

Use `file:///` or a local static server — not GitHub Pages.

## Step 3 — Visual + console

Each file:

1. Loads without stuck “Loading…”
2. Chart canvases non-empty (not grey boxes)
3. One tab/filter redraws a chart
4. DevTools Console: no errors (`echarts is not defined`, failed JSON fetch = **FAIL**)

## Step 4 — Report

```
Harness: PASS/FAIL | Visual: PASS/FAIL | Console: PASS/FAIL
```

Fix in `02_dashboards\_build\` or `04_tools\build_gps_*.py`, rebuild, re-run harness, re-open.

Related: `isze-verify-pipeline` (derived sales), `isze-gps-auditor` (full GPS lineage when raw billing changed).
