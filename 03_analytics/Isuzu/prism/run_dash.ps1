# PRISM Dash launcher — Plotly Dash (Offset Insights)
# Double-click or:  powershell -ExecutionPolicy Bypass -File run_dash.ps1

$ErrorActionPreference = "Stop"
$PrismRoot = $PSScriptRoot
$IszeRootPs1 = Join-Path (Split-Path (Split-Path (Split-Path $PrismRoot -Parent) -Parent) -Parent) '04_tools\workspace\isze_root.ps1'
. $IszeRootPs1
$DataRoot = Get-IszePath -Key 'data' -Legacy 'Data'

if (-not $env:ISZE_DERIVED) {
    $derived = Join-Path $DataRoot "derived"
    if (Test-Path $derived) { $env:ISZE_DERIVED = $derived }
}

$Python = "C:\Python314\python.exe"
if (-not (Test-Path $Python)) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $Python) {
    Write-Host "ERROR: Python not found." -ForegroundColor Red
    pause
    exit 1
}

Set-Location $PrismRoot
Write-Host "Dash server -> http://127.0.0.1:8050" -ForegroundColor Green
& $Python dash_app/app.py
