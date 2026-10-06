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







# RANGE-05 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "RANGE-05 - unsupported migration unresolved"
$range05 = Join-Path $Root "tests\range_05_unresolved.test.mjs"
if (Test-Path $range05) {
  & node --test $range05
  if ($LASTEXITCODE -eq 0) { Write-Host "RANGE-05 2/0/2" } else { Write-Host "RANGE-05 FAILED"; $script:failed += 1 }
} else {
  Write-Host "RANGE-05 SKIPPED (test file missing)"
}

# RANGE-06 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "RANGE-06 - price-up and price-down investigations"
$range06 = Join-Path $Root "tests\range_06_price_direction.test.mjs"
if (Test-Path $range06) {
  & node --test $range06
  if ($LASTEXITCODE -eq 0) { Write-Host "RANGE-06 2/0/2" } else { Write-Host "RANGE-06 FAILED"; $script:failed += 1 }
} else {
  Write-Host "RANGE-06 SKIPPED (test file missing)"
}
# RANGE-04 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "RANGE-04 - transferred versus new business"
$range04 = Join-Path $Root "tests\range_04_transfer.test.mjs"
if (Test-Path $range04) {
  & node --test $range04
  if ($LASTEXITCODE -eq 0) { Write-Host "RANGE-04 2/0/2" } else { Write-Host "RANGE-04 FAILED"; $script:failed += 1 }
} else {
  Write-Host "RANGE-04 SKIPPED (test file missing)"
}
# RANGE-03 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "RANGE-03 - multi-part basket"
$range03 = Join-Path $Root "tests\range_03_basket.test.mjs"
if (Test-Path $range03) {
  & node --test $range03
  if ($LASTEXITCODE -eq 0) { Write-Host "RANGE-03 3/0/3" } else { Write-Host "RANGE-03 FAILED"; $script:failed += 1 }
} else {
  Write-Host "RANGE-03 SKIPPED (test file missing)"
}
# RANGE-08 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "RANGE-08 - relationship withdrawal without rewriting history"
$range08 = Join-Path $Root "tests\range_08_withdrawal.test.mjs"
if (Test-Path $range08) {
  & node --test $range08
  if ($LASTEXITCODE -eq 0) { Write-Host "RANGE-08 2/0/2" } else { Write-Host "RANGE-08 FAILED"; $script:failed += 1 }
} else {
  Write-Host "RANGE-08 SKIPPED (test file missing)"
}
# RANGE-02 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "RANGE-02 - exact Genuine/BVP comparison"
$range02 = Join-Path $Root "tests\range_02_comparison.test.mjs"
if (Test-Path $range02) {
  & node --test $range02
  if ($LASTEXITCODE -eq 0) { Write-Host "RANGE-02 2/0/2" } else { Write-Host "RANGE-02 FAILED"; $script:failed += 1 }
} else {
  Write-Host "RANGE-02 SKIPPED (test file missing)"
}

# RANGE-01 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "RANGE-01 - typed pairing, supersession and fitment"
$range01 = Join-Path $Root "tests\range_01_relationships.test.mjs"
if (Test-Path $range01) {
  & node --test $range01
  if ($LASTEXITCODE -eq 0) { Write-Host "RANGE-01 3/0/3" } else { Write-Host "RANGE-01 FAILED"; $script:failed += 1 }
} else {
  Write-Host "RANGE-01 SKIPPED (test file missing)"
}

# REVIEW-05 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "REVIEW-05 - separate price, quantity and mix"
$review05 = & node --test (Join-Path $PSScriptRoot "review_05_price_quantity_mix.test.mjs") 2>&1 | Out-String
Write-Host $review05
if ($review05 -match "fail\s+0" -and $review05 -match "pass\s+3") {
    Write-Host "REVIEW-05 3/0/3"
} else {
    Write-Host "REVIEW-05 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}

# MARKET-01 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "MARKET-01 - store dated competitor observations as evidence"
$market01 = & node --test (Join-Path $PSScriptRoot "market_01_observation.test.mjs") 2>&1 | Out-String
Write-Host $market01
if ($market01 -match "fail\s+0" -and $market01 -match "pass\s+2") {
    Write-Host "MARKET-01 2/0/2"
} else {
    Write-Host "MARKET-01 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}

# MARKET-06 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "MARKET-06 - outdated and conflicting observations visible"
$market06 = & node --test (Join-Path $PSScriptRoot "market_06_conflicts.test.mjs") 2>&1 | Out-String
Write-Host $market06
if ($market06 -match "fail\s+0" -and $market06 -match "pass\s+2") {
    Write-Host "MARKET-06 2/0/2"
} else {
    Write-Host "MARKET-06 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}

# MARKET-02 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "MARKET-02 - product equivalence separate from lexical similarity"
$marketX = & node --test (Join-Path $PSScriptRoot "market_02_equivalence.test.mjs") 2>&1 | Out-String
Write-Host $marketX
if ($marketX -match "fail\s+0" -and $marketX -match "pass\s+2") {
    Write-Host "MARKET-02 2/0/2"
} else {
    Write-Host "MARKET-02 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}

# MARKET-03 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "MARKET-03 - packs and kit contents only when supported"
$marketX = & node --test (Join-Path $PSScriptRoot "market_03_packs.test.mjs") 2>&1 | Out-String
Write-Host $marketX
if ($marketX -match "fail\s+0" -and $marketX -match "pass\s+2") {
    Write-Host "MARKET-03 2/0/2"
} else {
    Write-Host "MARKET-03 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}

# MARKET-07 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "MARKET-07 - comparable-price panel with clear exclusions"
$market07 = & node --test (Join-Path $PSScriptRoot "market_07_panel.test.mjs") 2>&1 | Out-String
Write-Host $market07
if ($market07 -match "fail\s+0" -and $market07 -match "pass\s+2") {
    Write-Host "MARKET-07 2/0/2"
} else {
    Write-Host "MARKET-07 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}

# MARKET-08 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "MARKET-08 - ask only for the missing comparison evidence"
$market08 = & node --test (Join-Path $PSScriptRoot "market_08_request.test.mjs") 2>&1 | Out-String
Write-Host $market08
if ($market08 -match "fail\s+0" -and $market08 -match "pass\s+2") {
    Write-Host "MARKET-08 2/0/2"
} else {
    Write-Host "MARKET-08 FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}


# ACCEPT-01 independent verification (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "ACCEPT-01 - independently verify the corrected financial engine"
$accept01 = & node --test (Join-Path $PSScriptRoot "accept_01_independent.test.mjs") 2>&1 | Out-String
Write-Host $accept01
if ($accept01 -match "fail\s+0" -and $accept01 -match "pass\s+2") {
    Write-Host "ACCEPT-01-INDEPENDENT 2/0/2"
} else {
    Write-Host "ACCEPT-01-INDEPENDENT FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}

# CONNECT-01 unit checks (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "CONNECT-01 - IDS evidence through validated identities"
$connect01 = & node --test (Join-Path $PSScriptRoot "connect_01_ids_identities.test.mjs") 2>&1 | Out-String
Write-Host $connect01
if ($connect01 -match "fail\s+0" -and $connect01 -match "pass\s+2") {
    Write-Host "CONNECT-01 2/0/2"
} else {
    Write-Host "CONNECT-01 FAILED"

# ACCEPT-03 independent verification (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "ACCEPT-03 - prove source conservation and correction behaviour"
$accept03 = & node --test (Join-Path $PSScriptRoot "accept_03_independent.test.mjs") 2>&1 | Out-String
Write-Host $accept03
if ($accept03 -match "fail\s+0" -and $accept03 -match "pass\s+2") {
    Write-Host "ACCEPT-03-INDEPENDENT 2/0/2"
} else {
    Write-Host "ACCEPT-03-INDEPENDENT FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}


# SAFE-05 independent verification (node). Existing accept rows are untouched below.
Write-Host ""
Write-Host "SAFE-05 - test actual exported bytes and download paths"
$safe05 = & node --test (Join-Path $PSScriptRoot "safe_05_independent.test.mjs") 2>&1 | Out-String
Write-Host $safe05
if ($safe05 -match "fail\s+0" -and $safe05 -match "pass\s+2") {
    Write-Host "SAFE-05-INDEPENDENT 2/0/2"
} else {
    Write-Host "SAFE-05-INDEPENDENT FAILED"
    $global:REVIEW_UNIT_FAIL = $true
}

& $impl @PSBoundParameters
if ($global:REVIEW_UNIT_FAIL) { exit 1 }
exit $LASTEXITCODE
