# PRISM Evidence launcher — SQL + Markdown BI (Evidence.dev)
# Double-click or:  powershell -ExecutionPolicy Bypass -File run_evidence.ps1

$ErrorActionPreference = "Stop"
$PrismRoot = $PSScriptRoot
$IszeRootPs1 = Join-Path (Split-Path (Split-Path (Split-Path $PrismRoot -Parent) -Parent) -Parent) '04_tools\workspace\isze_root.ps1'
. $IszeRootPs1
$DataRoot = Get-IszePath -Key 'data' -Legacy 'Data'

if (-not $env:ISZE_DERIVED) {
    $derived = Join-Path $DataRoot "derived"
    if (Test-Path $derived) { $env:ISZE_DERIVED = $derived }
}

Write-Host "Syncing derived CSVs for portable Evidence paths..." -ForegroundColor Cyan
python (Join-Path $PrismRoot "scripts\sync_evidence_derived.py")

Set-Location (Join-Path $PrismRoot "evidence-app")
if (-not (Test-Path node_modules)) {
    Write-Host "Installing npm dependencies..." -ForegroundColor Cyan
    npm install
}
Write-Host "Evidence dev server -> http://127.0.0.1:3000" -ForegroundColor Green
npm run sources
npm run dev
