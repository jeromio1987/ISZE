# Cursor stop hook: re-verify derived data if pipeline outputs changed since last report.
$prismRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$derived = Join-Path $prismRoot '..\..\..\Data\derived' | Resolve-Path -ErrorAction SilentlyContinue
if (-not $derived) { exit 0 }

$reportMd = Join-Path $derived '_verification_report.md'
$targets = Get-ChildItem $derived -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -in '.csv', '.parquet' -and $_.Name -notlike '_verification*' }

if (-not $targets) { exit 0 }

$newestData = ($targets | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
$reportTime = if (Test-Path $reportMd) { (Get-Item $reportMd).LastWriteTime } else { [datetime]::MinValue }

if ($newestData -le $reportTime) { exit 0 }

Set-Location $prismRoot
python scripts/verify_derived_pipeline.py
exit $LASTEXITCODE
