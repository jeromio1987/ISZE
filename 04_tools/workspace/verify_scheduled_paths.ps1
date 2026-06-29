# verify_scheduled_paths.ps1 - fail loud if Scheduled skills reference stale ISZE paths
# Usage: .\04_tools\workspace\verify_scheduled_paths.ps1 [-ScheduledRoot $path]

param(
    [string]$ScheduledRoot = (Join-Path $env:USERPROFILE 'Documents\Claude\Scheduled'),
    [string]$IszeRoot = $env:ISZE_ROOT
)

$ErrorActionPreference = 'Stop'

if (-not $IszeRoot) {
    $here = $PSScriptRoot
    while ($here) {
        if ((Test-Path (Join-Path $here 'paths.yaml')) -and (Test-Path (Join-Path $here 'FACTS.md'))) {
            $IszeRoot = $here
            break
        }
        $parent = Split-Path $here -Parent
        if ($parent -eq $here) { break }
        $here = $parent
    }
}

if (-not $IszeRoot -or -not (Test-Path (Join-Path $IszeRoot 'paths.yaml'))) {
    Write-Host 'FAIL: ISZE root not found' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ScheduledRoot)) {
    Write-Host ('FAIL: Scheduled root missing: ' + $ScheduledRoot) -ForegroundColor Red
    exit 1
}

$stalePatterns = @(
    'ISZE\Tools\',
    'ISZE\Data\',
    'ISZE\Isuzu\',
    'ISZE\memory\',
    'ISZE\Dashboards\',
    'ISZE\Projects\',
    'ISZE/Tools/',
    'ISZE/Data/',
    'ISZE/Isuzu/',
    'ISZE/memory/'
)

$skills = Get-ChildItem -Path $ScheduledRoot -Directory -ErrorAction SilentlyContinue
$fail = 0
$checked = 0

foreach ($dir in $skills) {
    $skill = Join-Path $dir.FullName 'SKILL.md'
    if (-not (Test-Path $skill)) { continue }
    $checked++
    $text = Get-Content -Raw -LiteralPath $skill
    foreach ($pat in $stalePatterns) {
        if ($text -like ('*' + $pat + '*')) {
            Write-Host ('FAIL: ' + $dir.Name + ' stale path: ' + $pat) -ForegroundColor Red
            $fail++
        }
    }
}

$anchors = @(
    (Join-Path $IszeRoot '04_tools\ISZE_Tender_Monitor_Install\tender_scraper_v3.py'),
    (Join-Path $IszeRoot '04_tools\autodoc_scraper\autodoc_scraper.py'),
    (Join-Path $IszeRoot '01_data'),
    (Join-Path $IszeRoot '05_memory')
)
foreach ($p in $anchors) {
    if (-not (Test-Path -LiteralPath $p)) {
        Write-Host ('FAIL: ISZE anchor missing: ' + $p) -ForegroundColor Red
        $fail++
    }
}

Write-Host ('Checked ' + $checked + ' SKILL files under ' + $ScheduledRoot) -ForegroundColor Cyan
if ($fail -gt 0) {
    Write-Host ('SCHEDULED_PATH_CHECK: ' + $fail + ' failures') -ForegroundColor Red
    exit 1
}
Write-Host 'SCHEDULED_PATH_CHECK: PASS' -ForegroundColor Green
exit 0
