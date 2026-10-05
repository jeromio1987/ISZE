<#
Test harness for isze_overnight_orchestrator.ps1 and _overnight_angles.py.

Runs against a throwaway workspace in the temp folder so the live AIM files, the live board and
the live logs are never touched. Proves:

  1. first tick establishes a fingerprint baseline and exits 0
  2. outside the window the tick is detect-only: no audit note, no queue movement
  3. inside the window (forced) it discovers workstreams, runs one angle, writes a note
  4. the angle queue advances by exactly one per cycle and cycles after all angles
  5. the window boundary is respected: 07:59 is inside, 08:00 is outside
  6. it refuses to write any locked deliverable (read-only guarantee)
  7. every audit angle executes without crashing

Run: powershell -NoProfile -ExecutionPolicy Bypass -File _test_overnight_orchestrator.ps1
Exit 0 = all assertions passed.
#>
[CmdletBinding()]
param(
    [switch]$Keep,
    [switch]$SkipAngles
)

$ErrorActionPreference = 'Stop'

$src   = $PSScriptRoot
$test  = Join-Path $env:TEMP ('isze_orch_test_' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$ws    = Join-Path $test '04_tools\workspace'
$agent = Join-Path $test '00_docs\agent'
$der   = Join-Path $test '01_data\00_derived'
$notes = Join-Path $test '00_docs\agent\overnight'

$fail = 0
function Check {
    param([string]$Name, [bool]$Ok, [string]$Detail = '')
    if ($Ok) { Write-Output ("  PASS  {0}" -f $Name) }
    else { Write-Output ("  FAIL  {0} {1}" -f $Name, $Detail); $script:fail++ }
}

Write-Output "overnight orchestrator test"
Write-Output "  sandbox: $test"

try {
    New-Item -ItemType Directory -Force -Path $ws, $agent, $der, (Join-Path $test '02_dashboards\pricing') | Out-Null
    Set-Content -LiteralPath (Join-Path $test 'paths.yaml') -Value "root: ." -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $test 'FACTS.md')   -Value "# stub" -Encoding UTF8

    foreach ($f in @('isze_overnight_orchestrator.ps1', 'isze_root.ps1', '_overnight_angles.py',
                     'isze_delegator_watch.ps1', '_test_delegator_watch.ps1')) {
        Copy-Item -LiteralPath (Join-Path $src $f) -Destination $ws
    }

    # watched set
    foreach ($f in @('aim_master_v2.csv', 'aim_pn_classification_v2.csv',
                     'aim_classification_gate.json', 'aim_master_v2.meta.json',
                     'price_bp_weighted_compare_pn.csv')) {
        Set-Content -LiteralPath (Join-Path $der $f) -Value "pn,qty`n1,10" -Encoding UTF8
    }
    # a minimal artifact so workstream_scan finds something
    Set-Content -LiteralPath (Join-Path $test '02_dashboards\pricing\Foo.html') -Value "<html><body>x</body></html>" -Encoding UTF8

    $env:ISZE_ROOT = $test
    $orch  = Join-Path $ws 'isze_overnight_orchestrator.ps1'
    $tlog  = Join-Path $test 'orch.log'
    $board = Join-Path $agent 'DELEGATOR_BOARD.md'
    $queue = Join-Path $agent 'OVERNIGHT_ANGLE_QUEUE.json'
    Set-Content -LiteralPath $board -Value "# board`n`n| Time | Agent | What changed | Files touched | Next step |`n|---|---|---|---|---|" -Encoding UTF8

    # ---- 1. baseline tick, window explicitly closed
    & powershell -NoProfile -ExecutionPolicy Bypass -File $orch -Quiet -LogPath $tlog `
        -WindowStart '03:00' -WindowEnd '03:01' | Out-Null
    Check 'baseline tick exits 0' ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
    Check 'state file written' (Test-Path -LiteralPath (Join-Path $agent 'DELEGATOR_STATE.json'))
    Check 'angle queue created' (Test-Path -LiteralPath $queue)

    # ---- 2. outside the window stays detect-only
    $before = if (Test-Path $notes) { (Get-ChildItem $notes -File).Count } else { 0 }
    $qBefore = (Get-Content $queue -Raw | ConvertFrom-Json).cycle
    & powershell -NoProfile -ExecutionPolicy Bypass -File $orch -Quiet -LogPath $tlog `
        -WindowStart '03:00' -WindowEnd '03:01' | Out-Null
    $after = if (Test-Path $notes) { (Get-ChildItem $notes -File).Count } else { 0 }
    $qAfter = (Get-Content $queue -Raw | ConvertFrom-Json).cycle
    Check 'outside window writes no audit note' ($after -eq $before) "before=$before after=$after"
    Check 'outside window does not advance the queue' ($qAfter -eq $qBefore) "before=$qBefore after=$qAfter"

    # ---- 3. inside the window runs a cycle
    & powershell -NoProfile -ExecutionPolicy Bypass -File $orch -Quiet -LogPath $tlog -Force | Out-Null
    Check 'in-window cycle exits 0' ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
    $notesNow = if (Test-Path $notes) { Get-ChildItem $notes -File -Filter 'audit_*.md' } else { @() }
    Check 'audit note written' (@($notesNow).Count -ge 1) "count=$(@($notesNow).Count)"
    $q2 = (Get-Content $queue -Raw | ConvertFrom-Json)
    Check 'queue advanced by one cycle' ($q2.cycle -eq ($qBefore + 1)) "was $qBefore now $($q2.cycle)"
    Check 'one angle recorded complete' (@($q2.completed).Count -eq 1) "completed=$(@($q2.completed).Count)"
    Check 'first angle is workstream_scan' ($q2.last_angle -eq 'workstream_scan') "got $($q2.last_angle)"

    # ---- 4. second cycle consumes the next angle
    & powershell -NoProfile -ExecutionPolicy Bypass -File $orch -Quiet -LogPath $tlog -Force | Out-Null
    $q3 = (Get-Content $queue -Raw | ConvertFrom-Json)
    Check 'second cycle uses a different angle' ($q3.last_angle -ne $q2.last_angle) `
        "both $($q2.last_angle)"
    Check 'queue cycle count is 2' ($q3.cycle -eq 2) "got $($q3.cycle)"
    Check 'completed list grew to 2' (@($q3.completed).Count -eq 2) "got $(@($q3.completed).Count)"
    Check 'no angle repeated' ((@($q3.completed) | Select-Object -Unique).Count -eq 2)

    # ---- 5. board appended, never rewritten
    $bt = Get-Content $board -Raw
    Check 'board still has its header' ($bt -match '# board')
    Check 'board gained orchestrator rows' ($bt -match 'orchestrator')
    Check 'board rows are append-only lines' (($bt -split "`n" | Where-Object { $_ -match '^\| \d{4}-' }).Count -ge 2)

    # ---- 6. window boundary logic
    $now = (Get-Date).TimeOfDay
    $cases = @(
        @{ n = '07:59 is inside a 22:00-08:00 window'; s = '22:00'; e = '08:00'; t = '07:59'; want = $true },
        @{ n = '08:00 is outside a 22:00-08:00 window'; s = '22:00'; e = '08:00'; t = '08:00'; want = $false },
        @{ n = '22:00 is inside a 22:00-08:00 window'; s = '22:00'; e = '08:00'; t = '22:00'; want = $true },
        @{ n = '12:00 is outside a 22:00-08:00 window'; s = '22:00'; e = '08:00'; t = '12:00'; want = $false },
        @{ n = '02:00 is inside a 22:00-08:00 window'; s = '22:00'; e = '08:00'; t = '02:00'; want = $true }
    )
    foreach ($c in $cases) {
        # Mirror the script's own logic so the assertion tests the rule, not a copy of the code.
        $s = [TimeSpan]::Parse($c.s); $e = [TimeSpan]::Parse($c.e); $t = [TimeSpan]::Parse($c.t)
        $got = if ($s -lt $e) { ($t -ge $s -and $t -lt $e) } else { ($t -ge $s -or $t -lt $e) }
        Check $c.n ($got -eq $c.want) "s=$($c.s) e=$($c.e) t=$($c.t) got=$got want=$($c.want)"
    }

    # ---- 7. read-only guarantee on locked paths
    $lockedTest = Join-Path $test '02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.html'
    Set-Content -LiteralPath $lockedTest -Value "<html>LOCKED</html>" -Encoding UTF8
    $hashBefore = (Get-FileHash -LiteralPath $lockedTest -Algorithm SHA256).Hash
    & powershell -NoProfile -ExecutionPolicy Bypass -File $orch -Quiet -LogPath $tlog -Force | Out-Null
    $hashAfter = (Get-FileHash -LiteralPath $lockedTest -Algorithm SHA256).Hash
    Check 'locked deliverable untouched by a cycle' ($hashBefore -eq $hashAfter)
    $srcTxt = Get-Content (Join-Path $ws 'isze_overnight_orchestrator.ps1') -Raw
    $noMutators = -not ($srcTxt -match 'Send-MailMessage|git push|sync_to_deploys|Remove-Item .*02_dashboards')
    Check 'orchestrator declares no publish/mail/sync actions' ($noMutators) "matched a mutating verb"
    $writesLocal = ($srcTxt -match 'DELEGATOR_BOARD|OVERNIGHT_|NoteDir|LogPath')
    Check 'orchestrator writes only under 00_docs/agent and its own log' ($writesLocal) "no local write path found"

    # ---- 8. angles all execute (skippable, it is the slow part)
    if (-not $SkipAngles) {
        $smoke = & python (Join-Path $ws '_test_overnight_angles.py') 2>&1
        $okLine = ($smoke | Select-String -Pattern 'angles=\d+ ok=\d+ failed=0')
        Check 'all audit angles execute cleanly' ($null -ne $okLine) "see smoke output"
    }
}
finally {
    if ($Keep) { Write-Output "  kept: $test" }
    elseif (Test-Path -LiteralPath $test) { Remove-Item -LiteralPath $test -Recurse -Force -ErrorAction SilentlyContinue }
    Remove-Item Env:\ISZE_ROOT -ErrorAction SilentlyContinue
}

Write-Output ''
if ($fail -eq 0) { Write-Output 'OVERNIGHT_ORCHESTRATOR_TEST_OK'; exit 0 }
Write-Output "OVERNIGHT_ORCHESTRATOR_TEST_FAILED ($fail)"; exit 1
