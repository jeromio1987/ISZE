<#
ISZE delegator watch — AIM change detector.

What it does
------------
Ticks on a schedule (registered task: every 20 minutes). On each tick it fingerprints
a small set of AIM and pricing-base files and compares that fingerprint to the last
one it stored. Nothing else happens on a quiet tick: no agent is woken, no rebuild is
run, no file is written except the state file.

When a fingerprint actually MOVES, it writes a row to the shared board
(00_docs/agent/DELEGATOR_BOARD.md) so the next agent that starts in this workspace can
see that AIM moved and what depends on it.

Why a fingerprint and not an agent on every tick
------------------------------------------------
20 minutes is 72 ticks a day. The real trigger is an AIM file change, which is monthly
work. An agent on every tick would burn tokens on 71 no-ops. So the tick is a free
comparison and the agent only runs on a real change.

SCOPE — read this before extending the script
---------------------------------------------
This watcher is DETECT-ONLY by default. It never publishes, never mails, and never
changes a price. Setting -RefreshDerived runs a rebuild, and that rebuild is limited to
the artifacts this workstream owns. It refuses to write any file on the protected list
below, because Jerome locked those existing pricing deliverables as read-only on
2026-09-17. If a protected file needs rebuilding, the watcher records the command and
leaves it to a human.

Usage
-----
  powershell -NoProfile -ExecutionPolicy Bypass -File isze_delegator_watch.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File isze_delegator_watch.ps1 -RefreshDerived
  powershell -NoProfile -ExecutionPolicy Bypass -File isze_delegator_watch.ps1 -Status
  powershell -NoProfile -ExecutionPolicy Bypass -File isze_delegator_watch.ps1 -AcceptBaseline

Exit codes
----------
  0  clean run (baseline established, no change, or a change was handled)
  1  crash / preflight failure — the scheduled task will show this as a failure

-Note. The watcher deliberately does NOT exit non-zero on "change detected". A detected
change is the job working, not the job failing, and a task that reports failure every
time it does its job gets ignored within a week.
#>
[CmdletBinding()]
param(
    [switch]$RefreshDerived,
    [switch]$Status,
    [switch]$AcceptBaseline,
    [switch]$Quiet,
    # Override used by the test harness so a smoke test does not write into the live log.
    [string]$LogPath
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------- paths
. (Join-Path $PSScriptRoot 'isze_root.ps1')
$Root       = Get-IszeRoot
$AgentDir   = Join-Path $Root '00_docs\agent'
$StatePath  = Join-Path $AgentDir 'DELEGATOR_STATE.json'
$BoardPath  = Join-Path $AgentDir 'DELEGATOR_BOARD.md'
if (-not $LogPath) { $LogPath = Join-Path $PSScriptRoot 'delegator_watch.log' }

# ---------------------------------------------------------------- watched set
# The fingerprint set. Keep it small: every file here is hashed on every tick.
$Watched = @(
    @{ Rel = '01_data/00_derived/aim_master_v2.csv';                Role = 'corrected AIM master' },
    @{ Rel = '01_data/00_derived/aim_pn_classification_v2.csv';     Role = 'PN classification v2' },
    @{ Rel = '01_data/00_derived/aim_classification_gate.json';     Role = 'classification safety gate' },
    @{ Rel = '01_data/00_derived/aim_master_v2.meta.json';          Role = 'AIM coverage + fix log' },
    @{ Rel = '01_data/00_derived/price_bp_weighted_compare_pn.csv'; Role = 'price-revision base (in-scope L12M)' }
)

# ---------------------------------------------------------------- protected set
# Jerome, 2026-09-17: these are LOCKED read-only. The watcher must never write them,
# not even with -RefreshDerived. Matched on a normalised relative path; a directory
# entry ending in '/' matches everything under it.
$Protected = @(
    '01_data/01_Pricing/Pricing_Revision_AIM_Source_Analysis.xlsx',
    '01_data/01_Pricing/Pricing_Revision_AIM_Source_Analysis.SHIP_RECEIPT.json',
    '01_data/01_Pricing/OPEN_Pricing_Revision_AIM_Source_Analysis.cmd',
    '01_data/Pricing/',
    '02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html',
    '02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.SHIP_RECEIPT.json',
    '02_dashboards/pricing/OPEN_Pricing_Revision_AIM_Source.cmd',
    '02_dashboards/pricing/_build/pricing_dashboard_data.json',
    '02_dashboards/pricing/AIM_PRIORITY_LIST.csv',
    '02_dashboards/pricing/AIM_PRIORITY_LIST.xlsx',
    '01_data/00_derived/aim_master_v2.csv',
    '01_data/00_derived/',
    '03_analytics/isze_pricing/config.yaml'
)

# The rebuild this workstream owns. Only these are ever written by -RefreshDerived.
$OwnedStamp   = '2026-09-17'
$OwnedBuilder = '02_dashboards/pricing/_build/price_5pct_review_2026-09-17/build_price_increase_5pct_review.py'

# ---------------------------------------------------------------- helpers
function Write-Log {
    param([string]$Message)
    $line = '[{0}] {1}' -f (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'), $Message
    # Logging must never be able to fail the run. The launcher redirects its own console
    # output to a separate file, so this sink is ours alone; the try/catch covers the case
    # where someone else holds the file open.
    try { Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8 -ErrorAction Stop }
    catch { }
    if (-not $Quiet) { Write-Output $line }
}

function Assert-Preflight {
    # Policy is abort, not repair: no folders are created, nothing is auto-fixed.
    $missing = @()
    foreach ($w in $Watched) {
        $p = Join-Path $Root ($w.Rel -replace '/', '\')
        if (-not (Test-Path -LiteralPath $p)) { $missing += $w.Rel }
    }
    if (-not (Test-Path -LiteralPath $AgentDir)) { $missing += '00_docs/agent/' }
    if ($missing.Count -gt 0) {
        Write-Log "delegator-watch ABORTED - missing input: $($missing -join '; ')"
        exit 1
    }
}

function Get-FileFingerprint {
    param([string]$FullPath)
    $fi = Get-Item -LiteralPath $FullPath
    $sha = (Get-FileHash -LiteralPath $FullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $rows = $null
    if ($fi.Extension -ieq '.csv') {
        # Streamed count so a 165k-row file does not land in memory.
        $n = 0
        $sr = [System.IO.StreamReader]::new($FullPath)
        try   { while ($null -ne $sr.ReadLine()) { $n++ } }
        finally { $sr.Dispose() }
        $rows = [int]$n
    }
    [pscustomobject]@{
        sha256   = $sha
        bytes    = [int64]$fi.Length
        mtime    = $fi.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')
        rows     = $rows
    }
}

function Is-ProtectedPath {
    param([string]$Rel)
    $norm = $Rel -replace '\\', '/'
    foreach ($p in $Protected) {
        if ($p.EndsWith('/')) { if ($norm.StartsWith($p)) { return $true } }
        elseif ($norm -ieq $p) { return $true }
    }
    return $false
}

function Read-State {
    if (-not (Test-Path -LiteralPath $StatePath)) { return $null }
    try { return (Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json) }
    catch { Write-Log "state file unreadable, treating as first run: $($_.Exception.Message)"; return $null }
}

function Write-State {
    param($Files)
    $obj = [ordered]@{
        schema_version = 1
        updated_utc    = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        note           = 'Fingerprints of the AIM watch set. Written by isze_delegator_watch.ps1.'
        files          = $Files
    }
    $obj | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $StatePath -Encoding UTF8
}

function Add-BoardRow {
    param(
        [string]$Change,
        [string]$Files,
        [string]$NextStep
    )
    $stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm')
    $row = "| $stamp | delegator-watch | $Change | $Files | $NextStep |"
    Add-Content -LiteralPath $BoardPath -Value $row -Encoding UTF8
}

# ---------------------------------------------------------------- main
Assert-Preflight
$state = Read-State

# ------- -Status: print the current fingerprint without writing anything
if ($Status) {
    $live = [ordered]@{}
    foreach ($w in $Watched) {
        $fp = Get-FileFingerprint (Join-Path $Root ($w.Rel -replace '/', '\'))
        $live[$w.Rel] = $fp
        $was = if ($state -and $state.files.PSObject.Properties.Name -contains $w.Rel) { $state.files.$($w.Rel).sha256 } else { $null }
        $flag = if ($null -eq $was) { 'no-baseline' } elseif ($was -ne $fp.sha256) { 'CHANGED' } else { 'same' }
        '{0,-52} {1,-12} rows={2}' -f $w.Rel, $flag, $fp.rows
    }
    exit 0
}

# ------- first run (or forced rebaseline): record the fingerprint, do not alarm
$haveBaseline = $state -and $state.files -and ($state.files.PSObject.Properties.Name.Count -gt 0)
if (-not $haveBaseline -or $AcceptBaseline) {
    $fresh = [ordered]@{}
    foreach ($w in $Watched) {
        $fresh[$w.Rel] = Get-FileFingerprint (Join-Path $Root ($w.Rel -replace '/', '\'))
    }
    Write-State $fresh
    $verb = if ($AcceptBaseline -and $haveBaseline) { 'baseline re-accepted' } else { 'baseline established' }
    Write-Log "delegator-watch $verb over $($Watched.Count) files"
    if (-not $Quiet) { $Watched | ForEach-Object { '  {0,-52} {1}' -f $_.Rel, $_.Role } }
    exit 0
}

# ------- compare
$changed = @()
$live    = [ordered]@{}
foreach ($w in $Watched) {
    $fp  = Get-FileFingerprint (Join-Path $Root ($w.Rel -replace '/', '\'))
    $live[$w.Rel] = $fp
    $prev = $state.files.$($w.Rel)
    if ($null -eq $prev) {
        $changed += [pscustomobject]@{ Rel = $w.Rel; Kind = 'new to watch set'; Before = $null; After = $fp }
        continue
    }
    if ($prev.sha256 -ne $fp.sha256) {
        $kind = 'content changed'
        if ($null -ne $prev.rows -and $null -ne $fp.rows) {
            $d = $fp.rows - $prev.rows
            if ($d -gt 0) { $kind = "content changed, +$d rows" }
            elseif ($d -lt 0) { $kind = "content changed, $d rows" }
        }
        $changed += [pscustomobject]@{ Rel = $w.Rel; Kind = $kind; Before = $prev; After = $fp }
    }
}

if ($changed.Count -eq 0) {
    Write-State $live
    Write-Log 'delegator-watch: no change'
    exit 0
}

# ------- something moved
Write-Log "delegator-watch: $($changed.Count) file(s) changed"
$changed | ForEach-Object { Write-Log ("  {0} - {1}" -f $_.Rel, $_.Kind) }

# Anything AIM-side means the AIM-derived packs are stale.
# @() is required: a one-item pipeline result is a bare object with no .Count, so
# without it a single changed file would silently take the else branch below.
$aimSide = @($changed | Where-Object { $_.Rel -notlike '*price_bp_weighted_compare_pn.csv' })

$fileList = ($changed | ForEach-Object { $_.Rel }) -join ', '
if ($aimSide.Count -gt 0) {
    Add-BoardRow -Change "AIM moved ($($aimSide.Count) file(s))" -Files $fileList `
        -NextStep 'AIM-derived packs are stale. Detect-only run: no rebuild performed. Manual refresh command is in DELEGATOR_REFRESH_HOWTO.md. A price change is never delegated.'
} else {
    Add-BoardRow -Change 'Price-revision base moved' -Files $fileList `
        -NextStep 'The in-scope revision base changed. The 5% review pack is stale against it; rebuild on request only.'
}

Write-State $live

# ------- optional rebuild — our own new artifacts only
if ($RefreshDerived) {
    Write-Log '-RefreshDerived on: considering rebuild'
    $builderAbs = Join-Path $Root ($OwnedBuilder -replace '/', '\')
    if (Is-ProtectedPath $OwnedBuilder) {
        Write-Log "refusing: $OwnedBuilder is on the protected list"
    }
    elseif (-not (Test-Path -LiteralPath $builderAbs)) {
        Write-Log "no rebuild performed: builder not found at $OwnedBuilder"
    }
    else {
        Write-Log "running owned builder: $OwnedBuilder"
        $py = Get-Command python -ErrorAction SilentlyContinue
        if (-not $py) { Write-Log 'no rebuild performed: python not on PATH' }
        else {
            & $py.Source $builderAbs 2>&1 | ForEach-Object { Write-Log "  $_" }
            Write-Log "owned builder exit=$LASTEXITCODE"
        }
    }
    Write-Log 'note: AIM-derived packs (AIM master, priority list, revision pack) are on the protected list and were NOT rebuilt.'
}

exit 0
