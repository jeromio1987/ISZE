# =============================================================================
# ISZE monthly refresh orchestrator
#
# Runs the automatable half of 00_docs\RUNBOOK_MONTHLY_REFRESH.md as one
# command and stops the moment a verification gate is not green.
#
#   Step 4  PRISM build + verify       run_pipeline_and_verify.ps1
#   gate    _verification_report.json  summary.ok and 0 fail, freshly written
#   Step 4b GPS reconciliation         04_tools\gps_reconcile.py
#   gate    gps_reconciliation_report.json  result PASS, 0 hard failures
#   Step 6  Dashboard JSON             rebuilt only when the pipeline skipped it
#
# Steps 1-3 (SAP ingest, Excel Phase 1/2/3), Step 5 (FACTS.md), Step 7
# (publish) and Step 8 (GPT-safe slice) stay manual and are listed at the end.
#
# Fail-closed on purpose: a gate that cannot be proven green is treated as red,
# and nothing downstream runs. A stale report counts as not proven, so each gate
# also checks that the report was written during this run.
#
# ASCII only: Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI, so any
# non-ASCII character here becomes a parse error.
#
#   .\isze_monthly_refresh.ps1              # full run
#   .\isze_monthly_refresh.ps1 -DryRun      # preconditions + gates, no builds
#   .\isze_monthly_refresh.ps1 -SkipGps     # when no GPS upload happened
# =============================================================================

[CmdletBinding()]
param(
  [switch]$DryRun,
  [switch]$SkipGps,
  [string]$IszeRoot
)

$ErrorActionPreference = 'Stop'

if (-not $IszeRoot) {
  $IszeRoot = if ($env:ISZE_ROOT) { $env:ISZE_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
}

$RunStart = Get-Date
$Stages = [System.Collections.Generic.List[object]]::new()

function Add-Stage([string]$Name, [string]$Status, [string]$Detail) {
  $Stages.Add([pscustomobject]@{ stage = $Name; status = $Status; detail = $Detail })
  $colour = switch ($Status) { 'ok' { 'Green' } 'skipped' { 'DarkGray' } default { 'Red' } }
  Write-Host ("  [{0,-7}] {1}: {2}" -f $Status, $Name, $Detail) -ForegroundColor $colour
}

function Write-RunReport([string]$Outcome) {
  $path = Join-Path $IszeRoot '01_data\00_derived\_monthly_refresh_run.json'
  $report = [pscustomobject]@{
    started_at  = $RunStart.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    finished_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    outcome     = $Outcome
    dry_run     = [bool]$DryRun
    skip_gps    = [bool]$SkipGps
    isze_root   = $IszeRoot
    stages      = $Stages
  }
  try {
    $dir = Split-Path $path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $report | ConvertTo-Json -Depth 6 | Set-Content -Path $path -Encoding UTF8
    Write-Host ("Run report: {0}" -f $path) -ForegroundColor DarkGray
  } catch {
    Write-Warning ("Could not write run report: " + $_.Exception.Message)
  }
}

function Stop-FailClosed([string]$Name, [string]$Reason) {
  Add-Stage $Name 'FAILED' $Reason
  Write-Host ''
  Write-Host '=== MONTHLY REFRESH STOPPED (fail-closed) ===' -ForegroundColor Red
  Write-Host $Reason -ForegroundColor Red
  Write-Host 'Do not update FACTS.md and do not publish while this is red.' -ForegroundColor Red
  Write-RunReport 'failed'
  exit 1
}

<#
  The runbook still points at 01_data\derived; the pipeline actually writes to
  01_data\00_derived. Resolve both so a runbook fix does not break this script.
#>
function Resolve-DerivedFile([string]$Name) {
  foreach ($dir in @('01_data\00_derived', '01_data\derived')) {
    $candidate = Join-Path $IszeRoot (Join-Path $dir $Name)
    if (Test-Path $candidate) { return $candidate }
  }
  return $null
}

Write-Host '=== ISZE monthly refresh ===' -ForegroundColor Cyan
Write-Host ("Root: {0}" -f $IszeRoot)
if ($DryRun) { Write-Host 'Dry run: gates are evaluated against existing reports, nothing is rebuilt.' -ForegroundColor Yellow }
Write-Host ''

# --- Preconditions ----------------------------------------------------------
Write-Host 'Preconditions' -ForegroundColor Cyan

$prismDir = Join-Path $IszeRoot '03_analytics\Isuzu\prism'
$pipelineScript = Join-Path $prismDir 'scripts\run_pipeline_and_verify.ps1'
$gpsScript = Join-Path $IszeRoot '04_tools\gps_reconcile.py'
$dashboardScript = Join-Path $prismDir 'scripts\build_isze_dashboard_json.py'
$dashboardJson = Join-Path $IszeRoot '01_data\dashboards\isze_data.json'

$missing = @()
foreach ($p in @($pipelineScript, $dashboardScript)) { if (-not (Test-Path $p)) { $missing += $p } }
if (-not $SkipGps -and -not (Test-Path $gpsScript)) { $missing += $gpsScript }
if ($missing.Count -gt 0) {
  Stop-FailClosed 'preconditions' ("Missing required script(s): " + ($missing -join '; '))
}

$pythonVersion = $null
try {
  $pythonVersion = (& python --version 2>&1) -join ' '
} catch {
  $pythonVersion = $null
}
if (-not $pythonVersion) { Stop-FailClosed 'preconditions' 'python is not on PATH' }
Add-Stage 'preconditions' 'ok' ("scripts present, {0}" -f $pythonVersion.Trim())

$inbox = Join-Path $IszeRoot '01_data\_INBOX'
if (Test-Path $inbox) {
  $pending = @(Get-ChildItem $inbox -File -ErrorAction SilentlyContinue)
  if ($pending.Count -gt 0) {
    Write-Host ("  note: {0} file(s) still in 01_data\_INBOX, Step 1 ingest is manual" -f $pending.Count) -ForegroundColor Yellow
  }
}

# --- Step 4: PRISM build + verify -------------------------------------------
Write-Host ''
Write-Host 'Step 4: PRISM build + verify' -ForegroundColor Cyan

if ($DryRun) {
  Add-Stage 'pipeline' 'skipped' 'dry run'
} else {
  $env:ISZE_ROOT = $IszeRoot
  & $pipelineScript
  $pipelineExit = $LASTEXITCODE
  if ($pipelineExit -ne 0) {
    Stop-FailClosed 'pipeline' ("run_pipeline_and_verify.ps1 exited {0}; read _verification_report.md" -f $pipelineExit)
  }
  Add-Stage 'pipeline' 'ok' 'build and verify completed'
}

# --- Gate: verification report ----------------------------------------------
$verifyJson = Resolve-DerivedFile '_verification_report.json'
if (-not $verifyJson) { Stop-FailClosed 'verify-gate' 'no _verification_report.json found under 01_data' }

try {
  $verify = Get-Content $verifyJson -Raw | ConvertFrom-Json
} catch {
  Stop-FailClosed 'verify-gate' ("could not parse {0}: {1}" -f $verifyJson, $_.Exception.Message)
}

if (-not $DryRun) {
  $written = (Get-Item $verifyJson).LastWriteTime
  if ($written -lt $RunStart) {
    Stop-FailClosed 'verify-gate' ("report is stale (written {0}, run started {1}), treating as not proven" -f $written, $RunStart)
  }
}

$s = $verify.summary
if (-not $s) { Stop-FailClosed 'verify-gate' 'report has no summary block' }
if ($s.fail -gt 0 -or -not $s.ok) {
  Stop-FailClosed 'verify-gate' ("verification not green: {0} pass / {1} warn / {2} fail" -f $s.pass, $s.warn, $s.fail)
}
Add-Stage 'verify-gate' 'ok' ("{0} pass / {1} warn / 0 fail" -f $s.pass, $s.warn)
if ($s.warn -gt 0) {
  Write-Host '  warns are allowed but must be documented in CHANGELOG.md (runbook Step 4.3)' -ForegroundColor Yellow
}

# --- Step 4b: GPS reconciliation --------------------------------------------
Write-Host ''
Write-Host 'Step 4b: GPS reconciliation' -ForegroundColor Cyan

if ($SkipGps) {
  Add-Stage 'gps' 'skipped' '-SkipGps'
} elseif ($DryRun) {
  Add-Stage 'gps' 'skipped' 'dry run'
} else {
  Push-Location (Join-Path $IszeRoot '04_tools')
  try {
    & python gps_reconcile.py
    $gpsExit = $LASTEXITCODE
  } finally {
    Pop-Location
  }
  if ($gpsExit -ne 0) {
    Stop-FailClosed 'gps' ("gps_reconcile.py exited {0}" -f $gpsExit)
  }
  Add-Stage 'gps' 'ok' 'reconcile completed'
}

if (-not $SkipGps) {
  $gpsReport = Resolve-DerivedFile 'gps_reconciliation_report.json'
  if (-not $gpsReport) {
    Stop-FailClosed 'gps-gate' 'no gps_reconciliation_report.json found'
  }
  $gps = Get-Content $gpsReport -Raw | ConvertFrom-Json
  if (-not $DryRun -and (Get-Item $gpsReport).LastWriteTime -lt $RunStart) {
    Stop-FailClosed 'gps-gate' 'GPS report is stale, treating as not proven'
  }
  if ($gps.result -ne 'PASS' -or $gps.hard_failures -gt 0) {
    Stop-FailClosed 'gps-gate' ("GPS reconciliation {0} with {1} hard failure(s), see {2}" -f $gps.result, $gps.hard_failures, $gpsReport)
  }
  Add-Stage 'gps-gate' 'ok' '0 hard failures'
}

# --- Step 6: dashboard JSON --------------------------------------------------
Write-Host ''
Write-Host 'Step 6: Dashboard JSON' -ForegroundColor Cyan

if ($DryRun) {
  Add-Stage 'dashboard' 'skipped' 'dry run'
} else {
  $fresh = (Test-Path $dashboardJson) -and ((Get-Item $dashboardJson).LastWriteTime -ge $RunStart)
  if ($fresh) {
    Add-Stage 'dashboard' 'ok' 'rebuilt by the pipeline post-verify stage'
  } else {
    Push-Location $prismDir
    try {
      & python scripts\build_isze_dashboard_json.py
      $dashExit = $LASTEXITCODE
    } finally {
      Pop-Location
    }
    if ($dashExit -ne 0) { Stop-FailClosed 'dashboard' ("build_isze_dashboard_json.py exited {0}" -f $dashExit) }
    if (-not (Test-Path $dashboardJson) -or (Get-Item $dashboardJson).LastWriteTime -lt $RunStart) {
      Stop-FailClosed 'dashboard' 'isze_data.json mtime did not move'
    }
    Add-Stage 'dashboard' 'ok' 'rebuilt'
  }
}

# --- Done --------------------------------------------------------------------
Write-Host ''
Write-Host '=== MONTHLY REFRESH GREEN ===' -ForegroundColor Green
Write-RunReport 'green'

Write-Host ''
Write-Host 'Still manual (runbook):' -ForegroundColor Cyan
Write-Host '  1. Step 1-2  Move the SAP export into 01_data\raw\sales and update DATA_MANIFEST.md'
Write-Host '  2. Step 3    Refresh Phase 2/3 workbooks and export their CSVs, if a meeting needs them'
Write-Host '  3. Step 5    Update FACTS.md and prism\data\facts_anchor.yaml together, only for intentional changes'
Write-Host '  4. Step 7    Publish via 02_dashboards\sync_to_deploys.ps1 (never edit 07_deploy directly)'
Write-Host '  5. Step 8    Rebuild 01_data\gpt_safe and update 08_gpt\UPLOAD_STATUS.md'
