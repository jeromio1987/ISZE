# Publish tender v3 xlsx -> 01_data/dashboards/tender_data.json (canonical live feed)
$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
# ISZE root = two levels up from 04_tools\ISZE_Tender_Monitor_Install
$IszeRoot = Split-Path (Split-Path $Here -Parent) -Parent
# Canonical live dashboards folder (01_data/dashboards is a junction -> 01_data/14_dashboards)
$DashDir = Join-Path $IszeRoot '01_data\dashboards'
if (-not (Test-Path $DashDir)) { $DashDir = Join-Path $IszeRoot '01_data\14_dashboards' }
$LiveJson = Join-Path $DashDir 'tender_data.json'
$BackupDir = Split-Path $LiveJson -Parent

if (Test-Path $LiveJson) {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmm'
    Copy-Item $LiveJson (Join-Path $BackupDir "tender_data.backup_$stamp.json") -Force
}

Push-Location $Here
try {
    python build_dashboard_v2.py --json-output $LiveJson
    if ($LASTEXITCODE -ne 0) { throw "build_dashboard_v2.py failed" }
    Write-Host "Published: $LiveJson"
    $meta = Get-Item $LiveJson
    Write-Host "  Size: $([math]::Round($meta.Length/1MB, 2)) MB  Modified: $($meta.LastWriteTime)"
}
finally {
    Pop-Location
}
