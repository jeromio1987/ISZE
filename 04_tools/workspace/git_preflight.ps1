# git_preflight.ps1 - ISZE root commit safety gate
# Usage:
#   .\04_tools\workspace\git_preflight.ps1 [-Root $env:ISZE_ROOT] [-PreInit] [-DryRun] [-Strict]
#
# -PreInit  Skip git-status checks (use before first git init)
# -DryRun    Report issues but always exit 0
# -Strict    Treat large on-disk files (>500 KB) as failures (default: warn only)

param(
    [string]$Root = $env:ISZE_ROOT,
    [switch]$PreInit,
    [switch]$DryRun,
    [switch]$Strict
)

$ErrorActionPreference = 'Stop'

if (-not $Root) {
    $here = $PSScriptRoot
    while ($here) {
        if ((Test-Path (Join-Path $here 'paths.yaml')) -and (Test-Path (Join-Path $here 'FACTS.md'))) {
            $Root = $here
            break
        }
        $parent = Split-Path $here -Parent
        if ($parent -eq $here) { break }
        $here = $parent
    }
}
if (-not $Root -or -not (Test-Path (Join-Path $Root 'paths.yaml'))) {
    Write-Host 'FAIL: ISZE root not found (set $env:ISZE_ROOT)' -ForegroundColor Red
    exit 1
}

Set-Location $Root
$fail = 0
$warn = 0

function Fail($msg) {
    Write-Host "FAIL: $msg" -ForegroundColor Red
    $script:fail++
}
function Warn($msg) {
    Write-Host "WARN: $msg" -ForegroundColor Yellow
    $script:warn++
}
function Pass($msg) { Write-Host "PASS: $msg" -ForegroundColor Green }

Write-Host "ISZE git preflight - $Root" -ForegroundColor Cyan
if ($PreInit) { Write-Host '(PreInit mode - git status checks skipped)' -ForegroundColor DarkGray }
if ($DryRun) { Write-Host '(DryRun mode - exit 0 even if issues found)' -ForegroundColor DarkGray }

# 1. Raw billing
$billing = Get-ChildItem -Recurse -File -EA SilentlyContinue |
    Where-Object {
        $_.FullName -match '\\01_data\\(12_raw|raw)\\sales\\' -or
        ($_.DirectoryName -eq (Join-Path $Root '01_data') -and $_.Extension -match '\.xlsx?$')
    }
if ($billing) {
    $billing | ForEach-Object { Warn "billing/workbook on disk (must stay gitignored): $($_.FullName)" }
} else {
    Pass 'no raw billing at 01_data root or raw/sales'
}

# 2. Secrets filenames (content not read)
$secretNames = Get-ChildItem -Recurse -File -Force -EA SilentlyContinue |
    Where-Object {
        ($_.Name -eq '.env') -or
        ($_.Name -like '.env.*' -and $_.Name -ne '.env.example') -or
        $_.Name -match 'credentials|secrets\.toml|isze_config\.json'
    } |
    Where-Object { $_.FullName -notmatch '\\90_archive\\|\\91_legacy\\|\.env\.example$' }
if ($secretNames) {
    $secretNames | ForEach-Object { Fail "secret file present: $($_.FullName)" }
} else {
    Pass 'no live secret filenames outside archive/legacy'
}

# 3. PAT / token pattern scan (skip archive, legacy, deploy)
$codeFiles = Get-ChildItem -Recurse -File -EA SilentlyContinue -Include *.py, *.ps1, *.js, *.html, *.md, *.json |
    Where-Object { $_.FullName -notmatch '\\90_archive\\|\\91_legacy\\|\\07_deploy\\|node_modules|\.git\\' }
$patPattern = 'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}'
$tokenHits = @()
foreach ($f in $codeFiles) {
    if (Select-String -Path $f.FullName -Pattern $patPattern -Quiet -EA SilentlyContinue) {
        $tokenHits += $f.FullName
    }
}
if ($tokenHits) {
    $tokenHits | ForEach-Object { Fail "token pattern in $_" }
} else {
    Pass 'no PAT/token patterns in non-archive paths'
}

# 4. Large files (>500 KB) outside archive/legacy/deploy
$large = Get-ChildItem -Recurse -File -EA SilentlyContinue |
    Where-Object { $_.Length -gt 500KB } |
    Where-Object { $_.FullName -notmatch '\\90_archive\\|\\91_legacy\\|\\07_deploy\\|\\.git\\' }
foreach ($f in $large) {
    $rel = $f.FullName.Substring($Root.Length + 1)
    if ($rel -match '^01_data\\(00_derived|derived)\\_(verification|metrics_snapshot)') { continue }
    $sizeMb = [math]::Round($f.Length / 1MB, 1)
    $msg = "large file (>500KB): $rel (${sizeMb} MB)"
    if ($Strict) { Fail $msg } else { Warn $msg }
}

# 5-6. Git status checks (post-init only)
if (-not $PreInit -and (Test-Path (Join-Path $Root '.git'))) {
    $porcelain = git -C $Root status --porcelain 2>$null
    if ($porcelain | Select-String '07_deploy') { Fail '07_deploy paths appear in git status' }
    else { Pass '07_deploy not staged' }

    if ($porcelain | Select-String '90_archive|91_legacy') { Fail 'archive/legacy paths in git status' }
    else { Pass '90_archive / 91_legacy not staged' }

    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $dryAdd = git -C $Root add -n . 2>&1 | Out-String
    $addExit = $LASTEXITCODE
    $ErrorActionPreference = $prevEap
    if ($addExit -ne 0) { Fail "git add -n exited $addExit" }
    $forbidden = @(
        '01_data/12_raw/', '01_data/raw/', '01_data/90_INBOX/', '01_data/_INBOX/',
        '01_data/13_models/', '01_data/models/',
        '07_deploy/', '90_archive/', '91_legacy/', '.env', 'secrets.toml',
        'gps_dashboard/data/', '_results.csv'
    )
    foreach ($pat in $forbidden) {
        $winPat = $pat.Replace('/', '\')
        $haystack = if ($pat -eq '.env') { $dryAdd -replace '\.env\.example', '' } else { $dryAdd }
        if ($haystack -match [regex]::Escape($winPat)) {
            Fail "git add -n would track forbidden path pattern: $pat"
        }
    }
    Pass 'git add -n dry-run checked'
} elseif ($PreInit) {
    Pass 'git status checks deferred (PreInit)'
}

Write-Host ''
if ($fail -gt 0) {
    Write-Host "PREFLIGHT: $fail failure(s), $warn warning(s)." -ForegroundColor Red
    if ($DryRun) { exit 0 }
    exit 1
}
Write-Host "PREFLIGHT PASSED ($warn warning(s))." -ForegroundColor Green
exit 0
