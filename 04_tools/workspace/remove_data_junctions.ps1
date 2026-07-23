# remove_data_junctions.ps1 — delete 01_data legacy junction stubs (blue-arrow folders)
# Safe: only removes reparse-point junctions, never numbered real folders.
# Run: powershell -ExecutionPolicy Bypass -File "04_tools\workspace\remove_data_junctions.ps1"

$ErrorActionPreference = 'Continue'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$dataRoot = Join-Path $root '01_data'

$legacyNames = @(
    'derived', 'Pricing', 'PMS', 'sales data', 'Dealer_sellout', 'Warranty',
    'UIO', 'Distributor', 'Tender', 'planning', 'raw', 'models', 'dashboards',
    'gpt_safe', 'exports', '_INBOX', '_build', '_archive'
)

Write-Host "Removing 01_data legacy junctions under $dataRoot" -ForegroundColor Cyan

foreach ($name in $legacyNames) {
    $path = Join-Path $dataRoot $name
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Host "MISSING  $name"
        continue
    }
    $item = Get-Item -LiteralPath $path -Force
    if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        Write-Host "SKIP (real folder, not junction): $name"
        continue
    }
    try {
        cmd /c "rmdir `"$path`"" 2>&1 | Out-Null
        if (-not (Test-Path -LiteralPath $path)) {
            Write-Host "OK removed junction: $name"
        } else {
            Write-Warning "Failed to remove $name"
        }
    } catch {
        Write-Warning "Failed to remove $name : $_"
    }
}

Write-Host ''
Write-Host 'Done. Numbered folders (00_derived, 12_raw, ...) are unchanged.'
