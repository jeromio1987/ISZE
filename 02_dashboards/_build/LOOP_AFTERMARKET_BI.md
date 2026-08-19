# Aftermarket BI — 10-minute verify loop

**Purpose:** Re-check SSR command center every 10 minutes; rebuild if hero/charts/table regress.

**Loop tick prompt:** verify hero KPIs, bar-rows in network cards, top-50 table; `python 02_dashboards/_build/build_aftermarket_bi_command_center.py --all` if broken.

## Commands

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE
python 02_dashboards\_build\verify_aftermarket_bi_command_center.py
python 02_dashboards\_build\verify_tier_a_html_json.py
python 02_dashboards\_build\build_aftermarket_bi_command_center.py --all
```

**Open:** `02_dashboards\sales\OPEN_Aftermarket_BI_Command_Center.cmd` · hard refresh **Ctrl+F5** if cached.

## Stop loop

Read PID: `02_dashboards/_build/.loop_aftermarket_bi.pid`  
Kill: `Stop-Process -Id (Get-Content ...\.loop_aftermarket_bi.pid)` or tell agent **stop loop**.

## Root cause (2026-08-19 SSR fix)

Duplicate `let sortKey` / `let sortDir` in one script block → SyntaxError → entire JS dead → empty UI. Fix: build-time SSR (no JSON payload on command center).
