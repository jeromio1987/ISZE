<#
    The one entry point for the AIM Universe verification suite.

    The checks live in tests\accept\ because that folder holds everything the
    independent reviewer owns. This file is the single command to run them all;
    it forwards its switches, so it behaves exactly like running the suite
    directly.

        powershell -ExecutionPolicy Bypass -File tests\run_all.ps1
        powershell -ExecutionPolicy Bypass -File tests\run_all.ps1 -SkipBrowser
        powershell -ExecutionPolicy Bypass -File tests\run_all.ps1 -SkipBaseline
        powershell -ExecutionPolicy Bypass -File tests\run_all.ps1 -BaselineFileUrl

    Exit code: 1 when any check fails, 0 when every check passes. Neither is an
    acceptance - see the summary it prints.

    -BaselineFileUrl makes the baseline browser step open the frozen v03 file
    through a real file address instead of in memory. The default is in-memory;
    the reasoning and what each mode does and does not accept is in the note
    above the BASE-BROWSER step in accept\run_all.ps1.
#>
[CmdletBinding()]
param(
    [switch]$SkipBaseline,
    [switch]$SkipBrowser,
    [string]$Chrome = "",
    [switch]$KeepProfile,
    [switch]$BaselineFileUrl
)

$impl = Join-Path $PSScriptRoot "accept\run_all.ps1"
if (-not (Test-Path $impl)) {
    Write-Error "The acceptance suite is missing: $impl"
    exit 2
}


# REVIEW-03 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "REVIEW-03 - selectable comparison visible everywhere"
$review03 = & node --test (Join-Path $PSScriptRoot "review_03_comparison.test.mjs") 2>&1 | Out-String
Write-Host $review03
if ($review03 -match "fail\s+0" -and $review03 -match "pass\s+2") {
    Write-Host "REVIEW-03 2/0/2"
} else {
    Write-Host "REVIEW-03 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}

# REVIEW-04 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "REVIEW-04 - parts behind a purchasing movement"
$review04 = & node --test (Join-Path $PSScriptRoot "review_04_contributors.test.mjs") 2>&1 | Out-String
Write-Host $review04
if ($review04 -match "fail\s+0" -and $review04 -match "pass\s+2") {
    Write-Host "REVIEW-04 2/0/2"
} else {
    Write-Host "REVIEW-04 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}



# REVIEW-06 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "REVIEW-06 - recurrence, interruption and new purchasing"
$review06 = & node --test (Join-Path $PSScriptRoot "review_06_recurrence.test.mjs") 2>&1 | Out-String
Write-Host $review06
if ($review06 -match "fail\s+0" -and $review06 -match "pass\s+2") {
    Write-Host "REVIEW-06 2/0/2"
} else {
    Write-Host "REVIEW-06 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}


# REVIEW-07 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "REVIEW-07 - turn each question into the appropriate next action"
$review07 = & node --test (Join-Path $PSScriptRoot "review_07_next_action.test.mjs") 2>&1 | Out-String
Write-Host $review07
if ($review07 -match "fail\s+0" -and $review07 -match "pass\s+2") {
    Write-Host "REVIEW-07 2/0/2"
} else {
    Write-Host "REVIEW-07 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}


# REVIEW-08 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "REVIEW-08 - supported new reviews beyond the five examples"
$review08 = & node --test (Join-Path $PSScriptRoot "review_08_new_review.test.mjs") 2>&1 | Out-String
Write-Host $review08
if ($review08 -match "fail\s+0" -and $review08 -match "pass\s+2") {
    Write-Host "REVIEW-08 2/0/2"
} else {
    Write-Host "REVIEW-08 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}

& $impl @PSBoundParameters
if ($global:REVIEW_UNIT_FAIL) { exit 1 }
exit $LASTEXITCODE
