while ($true) {
  Start-Sleep -Seconds 300
  $state = "C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_overnight_state.json"
  $status = "UNKNOWN"
  if (Test-Path $state) {
    try { $status = (Get-Content $state -Raw | ConvertFrom-Json).status } catch {}
  }
  if ($status -eq "COMPLETE") {
    Write-Output "AGENT_LOOP_TICK_eq_hit {`"prompt`":`"EQ overnight COMPLETE — summarise RESULTS for Jerome. AIM apply still OFF.`"}"
    break
  }
  Write-Output "AGENT_LOOP_TICK_eq_hit {`"prompt`":`"EQ overnight harvest: poll 3 Glass EQ tabs (0e130666, e0d4a8d2, b9f05f9e). Harvest window.__eqDoubtResults via browser_cdp, pipe to harvest_eq_hit_session_20260919.py, update log/state. If a session finished and shard_2 not started, inject scraper + start_shard_2. Do NOT patch aim_master. Keep going until queue exhausted or login wall.`"}"
}
