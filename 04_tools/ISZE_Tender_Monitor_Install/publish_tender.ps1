# publish_tender.ps1 - rebuild live tender JSON from isuzu_tenders_v3.xlsx
# Run after tender_scraper_v3.py. Output: 01_data\dashboards\tender_data.json

$ErrorActionPreference = 'Stop'
$Here = $PSScriptRoot
$IszeRootPs1 = Join-Path (Split-Path $Here -Parent) '..\workspace\isze_root.ps1'
. $IszeRootPs1
$DataRoot = Get-IszePath -Key 'data' -Legacy 'Data'
$LiveJson = Join-Path $DataRoot 'dashboards\tender_data.json'
$DataDash = Split-Path $LiveJson -Parent

if (-not (Test-Path $DataDash)) {
    New-Item -ItemType Directory -Path $DataDash -Force | Out-Null
}

if (Test-Path $LiveJson) {
    $backup = Join-Path $DataDash ("tender_data.backup_{0:yyyyMMdd_HHmm}.json" -f (Get-Date))
    Copy-Item $LiveJson $backup -Force
    Write-Host "Backup: $backup"
}

$xlsx = Join-Path $Here 'isuzu_tenders_v3.xlsx'
if (-not (Test-Path $xlsx)) {
    Write-Error "Missing isuzu_tenders_v3.xlsx - run tender_scraper_v3.py first."
}

python (Join-Path $Here 'build_dashboard_v2.py') --json-output $LiveJson
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Published: $LiveJson"
python (Join-Path $Here '_print_tender_summary.py') $LiveJson
