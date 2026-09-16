# Ship gate — run tier-A dashboard verify scripts; exit 1 on any failure.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ISZE = Split-Path -Parent (Split-Path -Parent $root)

$scripts = @(
    (Join-Path $root 'verify_aftermarket_bi_command_center.py'),
    (Join-Path $root 'verify_tier_a_html_json.py'),
    (Join-Path $root 'verify_action_ledger.py')
)

$fail = $false
foreach ($script in $scripts) {
    if (-not (Test-Path $script)) {
        Write-Host "SHIP_GATE_FAIL missing $script"
        exit 1
    }
    Write-Host "Running $(Split-Path -Leaf $script) ..."
    & python $script
    if ($LASTEXITCODE -ne 0) {
        Write-Host "SHIP_GATE_FAIL $(Split-Path -Leaf $script) exit $LASTEXITCODE"
        $fail = $true
    }
}

if ($fail) {
    exit 1
}

Write-Host 'SHIP_GATE_OK'
exit 0
