# reorganize_data_layout.ps1 — numbered 01_data subfolders (paths.yaml data_subfolders)
# Idempotent: renames legacy -> numbered, then junctions legacy -> numbered for compat.
# Run: powershell -ExecutionPolicy Bypass -File "04_tools\workspace\reorganize_data_layout.ps1"
# Optional: -CreateJunctions for legacy blue-arrow stubs (not recommended)

param(
    [switch]$CreateJunctions
)

$ErrorActionPreference = 'Continue'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root

function Write-Step($msg) { Write-Host "`n== $msg ==" -ForegroundColor Cyan }

# Keep in sync with paths.yaml -> data_subfolders (legacy -> numbered)
$legacyToNumbered = [ordered]@{
    'derived'        = '00_derived'
    'Pricing'        = '01_Pricing'
    'PMS'            = '03_PMS'
    'sales data'     = '04_sales'
    'Dealer_sellout' = '05_Dealer_sellout'
    'Warranty'       = '06_Warranty'
    'UIO'            = '07_UIO'
    'Distributor'    = '08_Distributor'
    'Tender'         = '10_Tender'
    'planning'       = '11_planning'
    'raw'            = '12_raw'
    'models'         = '13_models'
    'dashboards'     = '14_dashboards'
    'gpt_safe'       = '15_gpt_safe'
    'exports'        = '16_exports'
    '_INBOX'         = '90_INBOX'
    '_build'         = '91_build'
    '_archive'       = '92_archive'
}

$dataRoot = Join-Path $root '01_data'
if (-not (Test-Path $dataRoot)) {
    Write-Warning "01_data not found at $dataRoot"
    exit 1
}

function New-LegacyJunction {
    param([string]$LegacyName, [string]$NumberedName)
    $legacyPath = Join-Path $dataRoot $LegacyName
    $numberedPath = Join-Path $dataRoot $NumberedName
    if (-not (Test-Path $numberedPath)) {
        Write-Host "SKIP junction (numbered missing): $NumberedName"
        return
    }
    if (Test-Path $legacyPath) {
        $item = Get-Item -LiteralPath $legacyPath -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            Write-Host "OK junction exists: $LegacyName -> $NumberedName"
            return
        }
        Write-Host "SKIP junction (legacy path is real folder): $LegacyName"
        return
    }
    $target = (Resolve-Path -LiteralPath $numberedPath).Path
    $cmd = "mklink /J `"$legacyPath`" `"$target`""
    cmd /c $cmd 2>&1 | ForEach-Object { Write-Host $_ }
    if (Test-Path -LiteralPath $legacyPath) {
        Write-Host "OK junction $LegacyName -> $NumberedName"
    } else {
        Write-Warning "Junction failed: $LegacyName (run as admin if needed)"
    }
}

Write-Step 'Rename legacy 01_data subfolders -> numbered'
foreach ($entry in $legacyToNumbered.GetEnumerator()) {
    $legacy = $entry.Key
    $numbered = $entry.Value
    $legacyPath = Join-Path $dataRoot $legacy
    $numberedPath = Join-Path $dataRoot $numbered
    if (-not (Test-Path -LiteralPath $legacyPath)) {
        if (Test-Path -LiteralPath $numberedPath) {
            Write-Host "OK already numbered: $numbered"
        }
        continue
    }
    if (Test-Path -LiteralPath $numberedPath) {
        Write-Host "SKIP rename (numbered exists): $legacy -> $numbered"
        continue
    }
    try {
        Rename-Item -LiteralPath $legacyPath -NewName $numbered -ErrorAction Stop
        Write-Host "OK rename $legacy -> $numbered"
    } catch {
        Write-Warning "Rename failed $legacy -> $numbered : $_"
    }
}

Write-Step 'Create legacy junctions (backward-compatible paths)'
if ($CreateJunctions) {
    foreach ($entry in $legacyToNumbered.GetEnumerator()) {
        New-LegacyJunction -LegacyName $entry.Key -NumberedName $entry.Value
    }
} else {
    Write-Host 'Skipped (use -CreateJunctions to add blue-arrow compat stubs)'
}

Write-Step 'Optional placeholder: 02_GPS (topic folder deferred in DATA_MANIFEST)'
$gpsPath = Join-Path $dataRoot '02_GPS'
if (-not (Test-Path $gpsPath)) {
    New-Item -ItemType Directory -Force -Path $gpsPath | Out-Null
    Write-Host 'OK created empty 02_GPS/'
}

Write-Host ''
Write-Host '01_data subfolder layout applied. Resolver: paths.yaml + _shared/paths.py + prism/config.py'
