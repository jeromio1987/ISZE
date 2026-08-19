# Aftermarket BI Command Center — 10-minute SSR loop

## What it does

Every **10 minutes** the background loop prints an `AGENT_LOOP_TICK_aftermarket_bi` line so the agent can re-run SSR smoke checks (hero KPIs, network chart cards, top-50 table) and rebuild if charts are empty.

The **immediate** verify/build on loop start is separate; the first tick fires **600s after** the loop starts (no tick at T=0).

## Rebuild (full stack)

```powershell
Set-Location C:\Users\jerom\Desktop\claude\ISZE
python 02_dashboards/_build/build_aftermarket_bi_command_center.py --all
```

Verify only:

```powershell
python 02_dashboards/_build/verify_aftermarket_bi_command_center.py
python 02_dashboards/_build/verify_tier_a_html_json.py
```

Open dashboard:

```powershell
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\OPEN_Aftermarket_BI_Command_Center.cmd
```

## Start loop

```powershell
powershell -NoProfile -File C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\run_loop_aftermarket_bi.ps1
```

PID is written to `02_dashboards/_build/.loop_aftermarket_bi.pid`.

## Stop loop

```powershell
$pid = Get-Content C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\.loop_aftermarket_bi.pid
Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
Remove-Item C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\.loop_aftermarket_bi.pid -ErrorAction SilentlyContinue
```

If the PID file is stale, find the process:

```powershell
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*run_loop_aftermarket_bi.ps1*' }
```
