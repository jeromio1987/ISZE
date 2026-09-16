# PRISM launcher — use this instead of "streamlit" from an unknown Python.
# Double-click or:  powershell -ExecutionPolicy Bypass -File run_prism.ps1
# Internal tabs (attach / leakage / elasticity / Sankey / scrape):
#   .\run_prism_internal.ps1   (same port; close this window first)

param(
    [switch]$Internal
)

$ErrorActionPreference = "Stop"
$PrismRoot = $PSScriptRoot
if ($Internal) {
    $env:PRISM_INTERNAL = "true"
} else {
    $env:PRISM_INTERNAL = "false"
}
$IszeRootPs1 = Join-Path (Split-Path (Split-Path (Split-Path $PrismRoot -Parent) -Parent) -Parent) '04_tools\workspace\isze_root.ps1'
. $IszeRootPs1
$Port = 8503

# Prefer real Python 3.14 install (avoid Windows Store shim)
$Python = "C:\Python314\python.exe"
if (-not (Test-Path $Python)) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $Python) {
    Write-Host "ERROR: Python not found. Install from python.org or fix PATH." -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Using: $Python" -ForegroundColor Cyan
Set-Location $PrismRoot

$dataRoot = Get-IszePath -Key 'data' -Legacy 'Data'
$parquet = Join-Path $dataRoot '00_derived\sales_fact.parquet'
if (-not (Test-Path $parquet)) {
    Write-Host "WARNING: Missing $parquet" -ForegroundColor Yellow
    Write-Host "Run: python scripts\build_sales_fact_from_cy.py" -ForegroundColor Yellow
}

# Deps are installed already; a pip failure must never abort the launch.
try {
    & $Python -m pip install -q -r requirements.txt 2>$null
} catch {
    Write-Host "pip install skipped (deps already present)." -ForegroundColor DarkGray
}

Write-Host ""
if ($Internal) {
    Write-Host "Starting PRISM INTERNAL on http://localhost:$Port" -ForegroundColor Yellow
    Write-Host "Extra tabs on: attach, ITUK leakage, elasticity, demand-flow, scrape." -ForegroundColor Yellow
} else {
    Write-Host "Starting the usual PRISM window (http://localhost:$Port)" -ForegroundColor Green
    Write-Host "MD-safe default. Extra tabs: double-click run_prism_internal.ps1" -ForegroundColor DarkGray
}
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

& $Python -m streamlit run app.py --server.port $Port --browser.gatherUsageStats false
