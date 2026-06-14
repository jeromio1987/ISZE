# delete_phases.ps1 - phases A-D cleanup (2026-06-13)
$ErrorActionPreference = 'Continue'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

function Remove-Target {
    param([string]$Rel)
    $p = Join-Path $root $Rel
    if (-not (Test-Path -LiteralPath $p)) {
        Write-Host "MISSING  $Rel"
        return
    }
    $mb = [math]::Round(((Get-ChildItem -LiteralPath $p -Recurse -File -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum / 1MB), 2)
    try {
        Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction Stop
        Write-Host "OK       $Rel ($mb MB)"
    } catch {
        Write-Host "FAIL     $Rel ($mb MB) - $($_.Exception.Message)"
    }
}

Write-Host "=== Phase A ==="
@(
    'Dashboards', 'Projects', '.netlify',
    '90_archive\Tools_tender_scraper_legacy',
    '90_archive\isze-tools-github',
    '90_archive\prism_mockups',
    '91_legacy\new files',
    '91_legacy\AI_Briefs',
    '03_analytics\Isuzu\AI_Briefs',
    '03_analytics\Isuzu\PMS project',
    '91_legacy\_git_DISABLED_broken_init_20260610',
    '02_dashboards\MASTER_DASHBOARD.html.prefix.tmp'
) | ForEach-Object { Remove-Target $_ }

Write-Host ""
Write-Host "=== Phase B ==="
Remove-Target '07_deploy\publish-site\.netlify'

Write-Host ""
Write-Host "=== Phase C ==="
Remove-Target '90_archive\legacy_data'
$dataDir = Join-Path $root '03_analytics\Isuzu\data'
if (Test-Path $dataDir) {
    Get-ChildItem $dataDir -File -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like 'sales_detailed*' } |
        ForEach-Object { Remove-Target ("03_analytics\Isuzu\data\" + $_.Name) }
}

Write-Host ""
Write-Host "=== Phase D ==="
@('node_modules', '.evidence', 'build', '.svelte-kit') | ForEach-Object {
    Remove-Target ("03_analytics\Isuzu\prism\evidence-app\" + $_)
}

Write-Host ""
Write-Host "Done."
