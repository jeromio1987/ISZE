# Test run: Belgium dealer ranking from Box folder export.
# 1. In Box (logged in): open IBX > BE, click Download, unzip to Data\_INBOX\IDS_2026\BE
# 2. Run: .\Tools\ids_dealer_ranking\run_be_test.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
# Box zip often unpacks as BE\BE\ — use nested path if present
$inputDir = Join-Path $root "Data\_INBOX\IDS_2026\BE\BE"
if (-not (Test-Path $inputDir)) {
    $inputDir = Join-Path $root "Data\_INBOX\IDS_2026\BE"
}
$output = Join-Path $root "Data\_INBOX\IDS_2026\rankings\BE_dealer_ranking_TEST.xlsx"

if (-not (Test-Path $inputDir)) {
    New-Item -ItemType Directory -Path $inputDir -Force | Out-Null
    Write-Host "Created $inputDir"
    Write-Host "Download the BE folder from Box into this path, then re-run."
    exit 1
}

$xlsx = @(Get-ChildItem $inputDir -Filter "*.xlsx" | Where-Object { $_.Name -notlike '~$*' })
if ($xlsx.Count -eq 0) {
    Write-Host "No .xlsx files in $inputDir"
    Write-Host "Download/unzip the BE folder from Box, then re-run."
    exit 1
}

python (Join-Path $PSScriptRoot "build_country_ranking.py") `
    --input-dir $inputDir `
    --country BE `
    --output $output `
    --limit 5

Write-Host "Open: $output"
