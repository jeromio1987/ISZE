# Single watchdog tick — verify + rebuild if needed (for manual / CI smoke)
powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\run_loop_aftermarket_bi.ps1" -Once
