# Aftermarket BI SSR watchdog - 10 minute tick
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$loopPid = $PID
$loopPid | Out-File -FilePath (Join-Path $root ".loop_aftermarket_bi.pid") -Encoding ascii -NoNewline
while ($true) {
  Start-Sleep -Seconds 600
  Write-Output 'AGENT_LOOP_TICK_aftermarket_bi {"prompt":"Loop tick: verify Aftermarket BI Command Center SSR paints (hero KPIs, bar-rows in all 4 network chart cards, top-50 table). Rebuild --all if empty. Note regressions. No alloc."}'
}
