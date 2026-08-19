# Internal PRISM launcher — extra tabs (dealer leakage, attach, elasticity,
# demand-flow, aftermarket scrape). Close the usual PRISM window first if it
# is already open (same address: http://localhost:8503).
#
# Double-click or:
#   powershell -ExecutionPolicy Bypass -File run_prism_internal.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "PRISM internal — extra tabs on." -ForegroundColor Yellow
Write-Host "Close the usual PRISM window first if it is already open." -ForegroundColor Yellow
Write-Host ""

& (Join-Path $PSScriptRoot "run_prism.ps1") -Internal
