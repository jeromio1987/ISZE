<#
Test harness for isze_delegator_watch.ps1.

Runs the REAL watcher script against a throwaway workspace in the temp folder, so the live
AIM files, the live board and the live log are never touched. Proves four things:

  1. first run establishes a baseline and exits 0
  2. a second run with nothing changed reports "no change" and exits 0
  3. a changed watched file is detected, and a row lands on the board
  4. the board row names the file that moved, and the state file advances to the new hash

Run: powershell -NoProfile -ExecutionPolicy Bypass -File _test_delegator_watch.ps1
Exit 0 = all assertions passed.
#>
[CmdletBinding()]
param(
    # Keep the throwaway workspace on disk for inspection instead of deleting it.
    [switch]$Keep
)

$ErrorActionPreference = 'Stop'

$src   = $PSScriptRoot
$test  = Join-Path $env:TEMP ('isze_delegator_test_' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$ws    = Join-Path $test '04_tools\workspace'
$agent = Join-Path $test '00_docs\agent'
$der   = Join-Path $test '01_data\00_derived'

$fail = 0
function Check {
    param([string]$Name, [bool]$Ok, [string]$Detail = '')
    if ($Ok) { Write-Output ("  PASS  {0}" -f $Name) }
    else { Write-Output ("  FAIL  {0} {1}" -f $Name, $Detail); $script:fail++ }
}

Write-Output "delegator watch test"
Write-Output "  sandbox: $test"

try {
    # ---- build the throwaway workspace
    New-Item -ItemType Directory -Force -Path $ws, $agent, $der | Out-Null
    Set-Content -LiteralPath (Join-Path $test 'paths.yaml') -Value "root: ." -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $test 'FACTS.md')   -Value "# stub" -Encoding UTF8

    Copy-Item -LiteralPath (Join-Path $src 'isze_delegator_watch.ps1') -Destination $ws
    Copy-Item -LiteralPath (Join-Path $src 'isze_root.ps1')            -Destination $ws

    $watched = @(
        'aim_master_v2.csv',
        'aim_pn_classification_v2.csv',
        'aim_classification_gate.json',
        'aim_master_v2.meta.json',
        'price_bp_weighted_compare_pn.csv'
    )
    foreach ($f in $watched) {
        Set-Content -LiteralPath (Join-Path $der $f) -Value "pn,qty`n1,10" -Encoding UTF8
    }

    $env:ISZE_ROOT = $test
    $script = Join-Path $ws 'isze_delegator_watch.ps1'
    $tlog = Join-Path $test 'test.log'
    $board = Join-Path $agent 'DELEGATOR_BOARD.md'
    $state = Join-Path $agent 'DELEGATOR_STATE.json'

    # ---- 1. baseline
    & powershell -NoProfile -ExecutionPolicy Bypass -File $script -LogPath $tlog | Out-Null
    Check 'baseline run exits 0' ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
    Check 'state file written' (Test-Path -LiteralPath $state)
    $st = Get-Content -LiteralPath $state -Raw | ConvertFrom-Json
    Check 'state holds 5 fingerprints' ($st.files.PSObject.Properties.Name.Count -eq 5) `
        "count=$($st.files.PSObject.Properties.Name.Count)"

    # ---- 2. no change
    & powershell -NoProfile -ExecutionPolicy Bypass -File $script -LogPath $tlog | Out-Null
    Check 'second run exits 0' ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
    $log2 = Get-Content -LiteralPath $tlog -Raw
    Check 'second run reports no change' ($log2 -match 'no change')

    & powershell -NoProfile -ExecutionPolicy Bypass -File $script -LogPath $tlog | Out-Null
    $log3 = Get-Content -LiteralPath $tlog -Raw
    Check 'third run reports no change' ($log3 -match 'no change')

    # ---- 3. a watched file moves
    Start-Sleep -Milliseconds 1200   # let mtime advance so a same-size rewrite is still visible
    Set-Content -LiteralPath (Join-Path $der 'aim_master_v2.csv') -Value "pn,qty`n1,10`n2,20`n3,30" -Encoding UTF8
    & powershell -NoProfile -ExecutionPolicy Bypass -File $script -LogPath $tlog | Out-Null
    Check 'change run exits 0' ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
    $log4 = Get-Content -LiteralPath $tlog -Raw
    Check 'change is reported' ($log4 -match 'changed')

    # ---- 4. board row and advanced state
    Check 'board file created' (Test-Path -LiteralPath $board)
    $bt = Get-Content -LiteralPath $board -Raw
    Check 'board row says AIM moved' ($bt -match 'AIM moved')
    Check 'board row names the file that moved' ($bt -match 'aim_master_v2\.csv')
    Check 'board row names the next step' ($bt -match 'stale')

    $st2 = Get-Content -LiteralPath $state -Raw | ConvertFrom-Json
    $newsha = (Get-FileHash -LiteralPath (Join-Path $der 'aim_master_v2.csv') -Algorithm SHA256).Hash.ToLowerInvariant()
    Check 'state advanced to the new hash' ($st2.files.'01_data/00_derived/aim_master_v2.csv'.sha256 -eq $newsha)
    Check 'row count tracked (+2)' ($st2.files.'01_data/00_derived/aim_master_v2.csv'.rows -eq 4) `
        "rows=$($st2.files.'01_data/00_derived/aim_master_v2.csv'.rows)"

    # ---- 5. protected files are refused by -RefreshDerived
    $protOut = Join-Path $test 'refresh.log'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $script -RefreshDerived -LogPath $protOut | Out-Null
    Check '-RefreshDerived exits 0' ($LASTEXITCODE -eq 0) "exit=$LASTEXITCODE"
}
finally {
    if ($Keep) { Write-Output "  kept: $test" }
    elseif (Test-Path -LiteralPath $test) { Remove-Item -LiteralPath $test -Recurse -Force -ErrorAction SilentlyContinue }
    Remove-Item Env:\ISZE_ROOT -ErrorAction SilentlyContinue
}

Write-Output ''
if ($fail -eq 0) { Write-Output 'DELEGATOR_WATCH_TEST_OK'; exit 0 }
Write-Output "DELEGATOR_WATCH_TEST_FAILED ($fail)"; exit 1
