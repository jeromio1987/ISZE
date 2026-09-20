# Ship gate — run tier-A dashboard verify scripts; exit 1 on any failure.
#
#   .\ship_gate_check.ps1                     # normal run; banned wording BLOCKS
#   .\ship_gate_check.ps1 -LanguageReportOnly  # emergency override: report only
#   .\ship_gate_check.ps1 -SkipLanguageCheck   # omit the language check entirely
#
# The language check became blocking by default on 19 Sep, once the three
# certified pages and the leakage executive summary had been cleaned by editing
# their builders and were measured at zero banned labels.
#
[CmdletBinding()]
param(
    # Accepted for backwards compatibility and now redundant: blocking is the
    # default, so this only re-asserts it (and wins if combined with
    # -LanguageReportOnly). Kept so existing callers and docs do not break.
    [switch]$LanguageGateBlocks,

    # Emergency override. Banned wording is reported but does not fail the gate.
    # Only use this to unblock an urgent build on a page you will fix next; the
    # normal run fails on any hit, with no switch needed.
    [switch]$LanguageReportOnly,

    # Skip the language check entirely (verify scripts only).
    [switch]$SkipLanguageCheck,

    # Pages the language check reads. Default is the certified gate pages; pass
    # explicit paths to check one artifact, e.g. the page just built.
    [string[]]$LanguagePages = @()
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ISZE = Split-Path -Parent (Split-Path -Parent $root)

$scripts = @(
    (Join-Path $root 'verify_aftermarket_bi_command_center.py'),
    (Join-Path $root 'verify_tier_a_html_json.py'),
    (Join-Path $root 'verify_action_ledger.py'),
    (Join-Path $root 'verify_os_hub.py')
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

# Language and stale-figure check (04_tools\workspace\check_spoken_labels.ps1).
#
# CM17 in the 18 Sep error register: the checker was written on 16 Sep and never
# called from anywhere, which is why the same wording corrections came back on the
# 18th and 19th. This is the build-gate call.
#
# BLOCKING BY DEFAULT since 19 Sep. It used to report only, because on 19 Sep the
# three pages this gate certifies carried 85 banned labels between them
# (44 + 30 + 11). Those pages have since been cleaned by editing their builders
# and measure zero, after the checker was fixed to scan the builders. So the check
# now bites on a normal run: a build with banned wording fails without a switch.
# Emergency override: -LanguageReportOnly. To omit the check: -SkipLanguageCheck.
$languageScript = Join-Path $ISZE '04_tools\workspace\check_spoken_labels.ps1'
$languageGateBlocks = (-not [bool]$LanguageReportOnly) -or [bool]$LanguageGateBlocks
if ($LanguagePages.Count -gt 0) {
    $languagePages = $LanguagePages
}
else {
    $languagePages = @(
        (Join-Path $ISZE '02_dashboards\sales\ISZE_Aftermarket_BI_Command_Center.html'),
        (Join-Path $ISZE '02_dashboards\sales\ISZE_DB_DLR_Replenishment_CY2025.html'),
        (Join-Path $ISZE '01_data\01_Pricing\BOOK_B_REVISION_REVIEW_20260819.html')
    )
}
$languageViolations = 0

if (-not $SkipLanguageCheck) {

if (-not (Test-Path $languageScript)) {
    Write-Host "SHIP_GATE_FAIL missing $languageScript"
    exit 1
}

foreach ($page in $languagePages) {
    if (-not (Test-Path $page)) {
        Write-Host "SHIP_GATE_LANGUAGE skipped (not on disk): $page"
        continue
    }
    Write-Host "Running check_spoken_labels.ps1 on $(Split-Path -Leaf $page) ..."
    # A native command's stderr would become a terminating error under the
    # 'Stop' preference set at the top of this script, so relax it for the call.
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $languageOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $languageScript -Path $page -FailOnViolation
    $languageExit = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference

    $countLine = @($languageOut | Where-Object { $_ -match '^\s*Violations\s+:\s+(\d+)' } | Select-Object -Last 1)
    if ($countLine.Count -gt 0 -and $countLine[0] -match '(\d+)') {
        $languageViolations += [int]$Matches[1]
    }
    if ($languageExit -ne 0) {
        Write-Host "SHIP_GATE_LANGUAGE $(Split-Path -Leaf $page) has banned labels"
    }
}

if ($languageViolations -gt 0) {
    Write-Host "SHIP_GATE_LANGUAGE $languageViolations banned label(s) in the gate pages"
    if ($languageGateBlocks) {
        Write-Host 'SHIP_GATE_FAIL check_spoken_labels.ps1'
        $fail = $true
    }
    else {
        Write-Host '  (report only - emergency override -LanguageReportOnly is set)'
    }
}
else {
    Write-Host 'SHIP_GATE_LANGUAGE clean'
}

}  # end: not $SkipLanguageCheck

if ($fail) {
    exit 1
}

Write-Host 'SHIP_GATE_OK'
exit 0
