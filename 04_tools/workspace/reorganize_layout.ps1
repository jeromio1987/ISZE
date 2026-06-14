# reorganize_layout.ps1 — apply numbered ISZE layout (paths.yaml)
# Idempotent. Continues on individual failures (e.g. locked Data folder).
# Run: powershell -ExecutionPolicy Bypass -File reorganize_layout.ps1

$ErrorActionPreference = 'Continue'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root

function Write-Step($msg) { Write-Host "`n== $msg ==" -ForegroundColor Cyan }

function Rename-Safe {
    param([string]$From, [string]$To)
    $fromPath = Join-Path $root $From
    $toPath   = Join-Path $root $To
    if (-not (Test-Path $fromPath)) { return $true }
    if ((Test-Path $toPath) -and ((Get-ChildItem $toPath -Force -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)) {
        Write-Host "SKIP (target not empty): $To"
        return $false
    }
    if (Test-Path $toPath) { Remove-Item $toPath -Force -Recurse -ErrorAction SilentlyContinue }
    try {
        Rename-Item -Path $fromPath -NewName (Split-Path $To -Leaf) -ErrorAction Stop
        Write-Host "OK rename $From -> $To"
        return $true
    } catch {
        Write-Warning "Rename failed $From : $_"
        return $false
    }
}

function Merge-Into {
    param([string]$From, [string]$ToDir)
    $fromPath = Join-Path $root $From
    $toPath   = Join-Path $root $ToDir
    if (-not (Test-Path $fromPath)) { return $true }
    New-Item -ItemType Directory -Force -Path $toPath | Out-Null
    Get-ChildItem $fromPath -Force | ForEach-Object {
        $dest = Join-Path $toPath $_.Name
        if (Test-Path $dest) { Write-Host "SKIP exists: $ToDir\$($_.Name)"; return }
        Move-Item $_.FullName $dest -Force
        Write-Host "OK $From\$($_.Name) -> $ToDir\"
    }
    if ((Get-ChildItem $fromPath -Force -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0) {
        Remove-Item $fromPath -Force -Recurse -ErrorAction SilentlyContinue
        Write-Host "removed empty $From"
    }
    return $true
}

function Move-Tree {
    param([string]$From, [string]$ToDir)
    $fromPath = Join-Path $root $From
    $toDirPath = Join-Path $root $ToDir
    if (-not (Test-Path $fromPath)) { return $true }
    New-Item -ItemType Directory -Force -Path $toDirPath | Out-Null
    $dest = Join-Path $toDirPath (Split-Path $From -Leaf)
    if (Test-Path $dest) { Write-Host "SKIP exists: $dest"; return $false }
    try {
        Move-Item -Path $fromPath -Destination $toDirPath -Force -ErrorAction Stop
        Write-Host "OK $From -> $ToDir\"
        return $true
    } catch {
        Write-Warning "Move failed $From : $_"
        return $false
    }
}

function Copy-Tree-Robocopy {
    param([string]$From, [string]$To, [switch]$DeleteSource)
    $fromPath = Join-Path $root $From
    $toPath   = Join-Path $root $To
    if (-not (Test-Path $fromPath)) { return $true }
    if (Test-Path $toPath) { Write-Host "SKIP robocopy (target exists): $To"; return $false }
    New-Item -ItemType Directory -Force -Path $toPath | Out-Null
    $args = @($fromPath, $toPath, '/E', '/R:2', '/W:2', '/NFL', '/NDL', '/NJH', '/NJS')
    if ($DeleteSource) { $args += '/MOVE' }
    & robocopy @args | Out-Null
    $code = $LASTEXITCODE
    if ($code -ge 8) {
        Write-Warning "robocopy $From -> $To failed (exit $code)"
        return $false
    }
    Write-Host "OK robocopy $From -> $To"
    return $true
}

Write-Step 'Create numbered folders'
@('00_docs','01_data','02_dashboards','03_analytics','04_tools','05_memory','06_uio',
  '07_deploy','08_gpt','09_meetings','90_archive','91_legacy') | ForEach-Object {
    New-Item -ItemType Directory -Force -Path (Join-Path $root $_) | Out-Null
}

Write-Step 'docs -> 00_docs'
if (Test-Path (Join-Path $root 'docs')) {
    if (-not (Rename-Safe 'docs' '00_docs')) {
        Merge-Into 'docs' '00_docs' | Out-Null
    }
}

Write-Step 'Top-level renames'
foreach ($pair in @(
    @('Dashboards','02_dashboards'), @('Tools','04_tools'), @('memory','05_memory'),
    @('UIO','06_uio'), @('GPT_Enterprise','08_gpt'), @('_archive','90_archive')
)) {
    if (-not (Rename-Safe $pair[0] $pair[1])) {
        Copy-Tree-Robocopy -From $pair[0] -To $pair[1] -DeleteSource | Out-Null
    }
}

Write-Step 'Data -> 01_data'
if (Test-Path (Join-Path $root 'Data')) {
    if (-not (Rename-Safe 'Data' '01_data')) {
        Copy-Tree-Robocopy -From 'Data' -To '01_data' -DeleteSource | Out-Null
    }
}

Write-Step 'Projects/Isuzu -> 03_analytics/Isuzu'
Move-Tree 'Projects\Isuzu' '03_analytics' | Out-Null
if (Test-Path (Join-Path $root 'Projects')) {
    Remove-Item (Join-Path $root 'Projects') -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Step 'Deploy -> 07_deploy'
Move-Tree 'Master Dashboard' '07_deploy' | Out-Null
Move-Tree 'publish-site' '07_deploy' | Out-Null

Write-Step 'Meetings -> 09_meetings'
@('Preparation Meetings', 'evaluaties', 'Financial_business plan') | ForEach-Object {
    Move-Tree $_ '09_meetings' | Out-Null
}

Write-Step 'Legacy -> 91_legacy'
@(
    'Isuzu', 'ISZE_Dashboard', 'isuzu pricing engine', 'tender scraper',
    'outputs', 'new files', '_build', '_git_DISABLED_broken_init_20260610', 'AI_Briefs'
) | ForEach-Object { Move-Tree $_ '91_legacy' | Out-Null }

Write-Step 'Archive root clutter'
$keep = @(
    'INDEX.md', 'AGENTS.md', 'CLAUDE.md', 'FACTS.md', 'README.md',
    'paths.yaml', '.cursorignore', '.gitignore'
)
$rf = Join-Path $root '90_archive\root_files'
New-Item -ItemType Directory -Force -Path $rf | Out-Null
Get-ChildItem $root -File | Where-Object { $keep -notcontains $_.Name } | ForEach-Object {
    try {
        Move-Item $_.FullName $rf -Force -ErrorAction Stop
        Write-Host "archived $($_.Name)"
    } catch { Write-Warning "Could not archive $($_.Name): $_" }
}

Write-Step 'Dashboard subfolders (02_dashboards)'
$dash = Join-Path $root '02_dashboards'
if (-not (Test-Path $dash)) { $dash = Join-Path $root 'Dashboards' }
if (Test-Path $dash) {
    @('hub', 'sales', 'fleet', 'gps', 'ops', 'side', '_archive') | ForEach-Object {
        New-Item -ItemType Directory -Force -Path (Join-Path $dash $_) | Out-Null
    }
    $map = @{
        hub   = @('PROJECT_HUB.html','MASTER_DASHBOARD.html','index.html','AI_Operations_Explorer.html')
        sales = @('AIM_Dashboard_CY2025.html','ISZE_Competitiveness_Dashboard.html','Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html','Dealer_Sellout_UTI_vs_ITUK.html','ISZE_Monthly_Sales_Tracker.html','ISZE_SPA_RunRate_UTI.html')
        fleet = @('ISUZU_UIO_Dashboard_2026_v18.html','ITUK_ZEV_Golden_Window_Dashboard.html','ISZE_Plan_Tracker_2030.html','ISZE_FY2026_YearEnd_Review.html')
        gps   = @('ISZE_GPS_Dashboard_v9.html','ISZE_GPS_TargetStudy_Reconciliation_Dashboard.html','ISZE_GPS_Network_SPU_Dashboard.html')
        ops   = @('ISZE_Tender_Monitor_v2.html','ISZE_Tools_Legal_Map.html','ISZE_AI_Tools_Overview.html')
        side  = @('PROPERTIQ.html')
    }
    foreach ($folder in $map.Keys) {
        foreach ($file in $map[$folder]) {
            $src = Join-Path $dash $file
            $dst = Join-Path (Join-Path $dash $folder) $file
            if ((Test-Path $src) -and -not (Test-Path $dst)) {
                Move-Item $src $dst -Force -ErrorAction SilentlyContinue
                Write-Host "  $folder\$file"
            }
        }
    }
    $v17 = Join-Path $dash 'ISUZU_UIO_Dashboard_2026_v17.html'
    if (Test-Path $v17) {
        Move-Item $v17 (Join-Path $dash '_archive\') -Force -ErrorAction SilentlyContinue
        Write-Host '  _archive\v17'
    }
}

Write-Host ''
Write-Host 'Layout applied. Run 04_tools\workspace\delete_phases.ps1 for cleanup if needed.'
