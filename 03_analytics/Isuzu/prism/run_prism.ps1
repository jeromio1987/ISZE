# PRISM launcher — use this instead of "streamlit" from an unknown Python.
# Double-click or:  powershell -ExecutionPolicy Bypass -File run_prism.ps1

$ErrorActionPreference = "Stop"
$PrismRoot = $PSScriptRoot
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
$parquet = Join-Path $dataRoot 'derived\sales_fact.parquet'
if (-not (Test-Path $parquet)) {
    Write-Host "WARNING: Missing $parquet" -ForegroundColor Yellow
    Write-Host "Run: python scripts\build_sales_fact_from_cy.py" -ForegroundColor Yellow
}

& $Python -m pip install -q -r requirements.txt 2>$null

Write-Host ""
Write-Host "Starting PRISM on http://localhost:$Port" -ForegroundColor Green
Write-Host "(Not Jarvis — Jarvis often uses port 8501)" -ForegroundColor DarkGray
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

& $Python -m streamlit run app.py --server.port $Port --browser.gatherUsageStats false
