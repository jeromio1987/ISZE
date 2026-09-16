# Aftermarket BI Command Center — watchdog loop

## What it does

Every **10 minutes** (and **immediately on start**) the loop:

1. Runs `verify_aftermarket_bi_command_center.py` (+ tier-a verify if present)
2. On failure → `build_aftermarket_bi_command_center.py --all`
3. Re-verifies and appends timestamped lines to `loop_aftermarket_bi.log`

No reliance on Cursor `AGENT_LOOP_TICK` stdout — check the **log file** for truth.

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

## Is it running? (30-second check)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\status_loop_aftermarket_bi.ps1
```

| Signal | Meaning |
|--------|---------|
| `RUNNING pid=…` | Watchdog alive — expect `TICK OK` or `REBUILD` in log every ≤10 min |
| `STALE pid file=… but process dead` | Hidden shell exited — run **Start loop** again |
| `STOPPED no .loop_aftermarket_bi.pid` | Never started or stopped cleanly |
| Log ends with `once=True` only | You ran manual tick (`run_loop_tick_once.ps1`), **not** the continuous loop |

**Truth source:** `loop_aftermarket_bi.log` — not Cursor stdout, not `.pid` alone.

After start, within **60 seconds** you should see:

```
[…] [INFO] LOOP start pid=… once=False interval=600s
[…] [INFO] TICK start — verify Aftermarket BI Command Center SSR
[…] [OK] TICK OK — …
[…] [INFO] AGENT_LOOP_TICK_aftermarket_bi sleep 600s …
```

## Start loop (kills stale first)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\start_loop_aftermarket_bi.ps1
```

PID written to `02_dashboards/_build/.loop_aftermarket_bi.pid`.  
Log: `02_dashboards/_build/loop_aftermarket_bi.log`

## Stop loop

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\stop_loop_aftermarket_bi.ps1
```

Or manually:

```powershell
$pid = Get-Content C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\.loop_aftermarket_bi.pid
Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
Remove-Item C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\.loop_aftermarket_bi.pid -ErrorAction SilentlyContinue
```

## One manual tick (CI / smoke)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\run_loop_tick_once.ps1
```

## Why the old loop failed

| Issue | Old behaviour | Fix |
|-------|---------------|-----|
| No work on tick | Only `Write-Output AGENT_LOOP_TICK…` after 600s sleep | Runs verify + rebuild |
| First tick delayed | Sleep **before** first action | Tick runs immediately, then sleep |
| Cursor wake | Assumed stdout triggers agent | Log file + optional manual tick |
| Stale PID | `.loop_aftermarket_bi.pid` pointed at dead shell | `start_loop_*` kills stale + orphans |
| No audit trail | No log | Every action → `loop_aftermarket_bi.log` |
