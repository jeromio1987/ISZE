# Aftermarket BI bug audit — 2026-08-19

**internal internal** · Fixes applied same day · Rebuild: `--all` + exec summary

## Critical / fixed

| # | Area | Bug | Fix |
|---|------|-----|-----|
| 1 | `01_data/91_build/build_db_dlr_commercial_stack.py` | `ModuleNotFoundError: build_price_elasticity_db_dlr_ituk_uti` — stack could not finish Phase 3 | Copied canonical module from `02_dashboards/Data/91_build/` → `01_data/91_build/` |
| 2 | `02_dashboards/_build/run_loop_aftermarket_bi.ps1` | `$loopPid` undefined → `InvokeMethodOnNull` on start; PID file never written | Changed to `$PID` (PowerShell automatic variable) |
| 3 | `02_dashboards/_build/verify_tier_a_html_json.py` | Hard-coded hero € `12,553,903` — always failed after data refresh; loop triggered pointless 80s rebuild every tick | Check hero block for `Network € leakage` + `€` pattern instead of stale number |
| 4 | `02_dashboards/_build/build_aftermarket_bi_command_center.py` | Duplicate `.hero-kpis` CSS (TIER_A 5-col + EXTRA 4-col) — conflicting grid rules in shipped HTML | Removed duplicate block from `EXTRA_CSS`; single source in `tier_a_dashboard_common.py` |
| 5 | `02_dashboards/_build/render_ssr_charts.py` | Radar axis labels drawn on polygon edge — clipped/overlapping | Label radius offset (`label=True` → 112% of chart radius) |

## Verified OK (post-fix)

- `verify_aftermarket_bi_command_center.py` — SSR smoke passes (171+ bar/svg elements, 50 network + 500 drill rows)
- `verify_tier_a_html_json.py` — all three Tier A HTML files pass
- `run_loop_aftermarket_bi.ps1 -Once` — verify → rebuild (when needed) → post-verify OK
- Commercial stack — replenishment + elasticity + revision queue completes; GREECE rows in queue (sell-out qty zero → € leakage zero until feed validates)

## Known limits (not bugs — document in UI)

| Item | Notes |
|------|-------|
| GREECE leakage € | Sell-out CY2025 reports 0 qty — register shows overstock/IAM, not positive qty-gap leakage |
| UTI vs UMI | UTI = sold_to 1799 only; never blend with UMI / IDS Israel |
| Vehicle / VIN | Book B bucket + AIM family proxies only unless dealer grain (ITUK) |
| Loop rebuild time | `--all` commercial stack ~60–80s — expected on verify fail |

## New deliverable (2026-08-19 rebuild)

- `02_dashboards/_build/build_leakage_exec_summary.py` → `01_data/01_Pricing/LEAKAGE_EXEC_SUMMARY_20260819.html` (+ `.md`, `OPEN_LEAKAGE_EXEC_SUMMARY.cmd`)

## Fixed this session — charts-first leakage UX

| # | Area | Bug | Fix |
|---|------|-----|-----|
| 6 | `LEAKAGE_EXEC_SUMMARY_20260819.html` | Tables-first; GREECE empty Top 10 with no explanation | Per-DB `chart-grid3` (PN bars + AIM bars + pipeline donut) above tables; GREECE `DATA UNAVAILABLE` banner + overstock/IAM counts + bill-qty fallback table |
| 7 | `render_ssr_charts.py` | Missing network/DB viz helpers; tiny vertical bars invisible | Added `leakage_db_comparison()`, `aim_family_bars()`, `pipeline_donut_svg()`, `data_unavailable_banner()`; min 4px SVG bar height/width |
| 8 | `ISZE_Aftermarket_BI_Command_Center.html` | DB tab charts weak vs network tab; 0-width micro-bars | DB panel: pipeline donut + top-10 PN bars + AIM family bars on load; network tab: side-by-side DB compare strip + donut; verify adds `ssr-donut` / `ssr-db-compare` gates |
| 9 | Replenishment + Book B siblings | Same SSR minimum as Command Center | Replenishment: DB compare strip + pipeline donut. Book B: leakage-by-DB compare + register donut |

## Verified OK (post chart rebuild)

- `verify_aftermarket_bi_command_center.py` — 145 SSR elements, all 12 genius markers incl. donut + db-compare
- `verify_tier_a_html_json.py` — Command Center, Replenishment, Book B pass
- `OPEN_LEAKAGE_EXEC_SUMMARY.cmd` — launched in build turn
