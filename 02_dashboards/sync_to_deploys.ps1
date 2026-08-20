# sync_to_deploys.ps1 - ISZE dashboard sync
#
# Source : 02_dashboards\  (grouped: hub/, sales/, fleet/, gps/, ops/, side/)
# Deploy : flat *.html at 07_deploy\Master Dashboard\ + publish-site\ (URLs unchanged)
#
# Also copies _ui/, propertiq-assets/, 01_data\dashboards\*.json

$ErrorActionPreference = 'Stop'

$IszeRootPs1 = Join-Path $PSScriptRoot '..\04_tools\workspace\isze_root.ps1'
. $IszeRootPs1
$IszeRoot = Get-IszeRoot

$Dashboards = Get-IszePath -Key 'dashboards' -Legacy 'Dashboards'
$dataRoot = Get-IszePath -Key 'data' -Legacy 'Data'
$DataJson = Join-Path $dataRoot '14_dashboards'
if (-not (Test-Path $DataJson)) {
    $DataJson = Join-Path $dataRoot 'dashboards'
}
$DeployRoot = Get-IszePath -Key 'deploy' -Legacy '07_deploy'
$Targets    = @(
    (Join-Path $DeployRoot 'Master Dashboard'),
    (Join-Path $DeployRoot 'publish-site'),
    (Join-Path $IszeRoot 'Master Dashboard'),
    (Join-Path $IszeRoot 'publish-site')
) | Select-Object -Unique | Where-Object { Test-Path $_ }

# Reduced copy set (consolidation 2026-08-20): skip scratch, internal SPA, and
# the mirrored Data folder (JSON feeds are copied separately below). _composable
# stays in the deploy set (PRISM map + master desk are still shipped).
$SkipDirs = @('_archive', '_build', '_working', 'spa_internal', 'Data')

function Convert-ToDeployHtml {
    param([string]$Content)
    $c = $Content
    $c = $c -replace '\.\./hub/', ''
    $c = $c -replace '\.\./sales/', ''
    $c = $c -replace '\.\./fleet/', ''
    $c = $c -replace '\.\./gps/', ''
    $c = $c -replace '\.\./ops/', ''
    $c = $c -replace '\.\./side/', ''
    $c = $c -replace '\.\./_ui/', '_ui/'
    $c = $c -replace '\.\./propertiq-assets/', 'propertiq-assets/'
    $c = $c -replace '\.\./\.\./01_data/', '../Data/'
    $c = $c -replace '\.\./\.\./Data/', '../Data/'
    $c = $c -replace '\.\./\.\./03_analytics/', '../Projects/'
    $c = $c -replace '\.\./\.\./Projects/', '../Projects/'
    $c = $c -replace '\.\./\.\./91_legacy/Isuzu/', '../Isuzu/'
    $c = $c -replace '\.\./\.\./Isuzu/', '../Isuzu/'
    $c = $c -replace 'href="\.\./[^/"]+/([^"]+\.html)"', 'href="$1"'
    $c = $c -replace "href='\.\./[^/']+/([^']+\.html)'", "href='`$1'"
    $c = $c -replace 'content="0;url=\.\./[^/"]+/([^"]+\.html)"', 'content="0;url=$1"'
    return $c
}

function Get-SourceHtmlFiles {
    param([string]$Root)
    $files = @()
    Get-ChildItem -Path $Root -Filter '*.html' -File -ErrorAction SilentlyContinue | ForEach-Object { $files += $_ }
    Get-ChildItem -Path $Root -Directory | Where-Object { $SkipDirs -notcontains $_.Name } | ForEach-Object {
        Get-ChildItem -Path $_.FullName -Filter '*.html' -File -ErrorAction SilentlyContinue | ForEach-Object { $files += $_ }
    }
    $files | Sort-Object Name -Unique
}

Write-Host "ISZE dashboard sync - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Source: $Dashboards (flatten on deploy)"
Write-Host ""

$sourceHtml = Get-SourceHtmlFiles -Root $Dashboards
if (-not $sourceHtml) {
    throw "No HTML files found under $Dashboards"
}

foreach ($target in $Targets) {
    Write-Host "-> $target"
    $count = 0
    foreach ($src in $sourceHtml) {
        $dest = Join-Path $target $src.Name
        $raw = Get-Content -Path $src.FullName -Raw -Encoding UTF8
        $flat = Convert-ToDeployHtml -Content $raw
        Set-Content -Path $dest -Value $flat -Encoding UTF8 -NoNewline
        Write-Host "    $($src.Name)"
        $count++
    }
    $uiSrc = Join-Path $Dashboards '_ui'
    if (Test-Path $uiSrc) {
        $uiDest = Join-Path $target '_ui'
        New-Item -ItemType Directory -Path $uiDest -Force | Out-Null
        Get-ChildItem -Path $uiSrc -File | ForEach-Object {
            Copy-Item $_.FullName (Join-Path $uiDest $_.Name) -Force
            Write-Host "    _ui\$($_.Name)"
            $count++
        }
    }
    $pqSrc = Join-Path $Dashboards 'propertiq-assets'
    if (Test-Path $pqSrc) {
        $pqDest = Join-Path $target 'propertiq-assets'
        New-Item -ItemType Directory -Path $pqDest -Force | Out-Null
        Get-ChildItem -Path $pqSrc -File | ForEach-Object {
            Copy-Item $_.FullName (Join-Path $pqDest $_.Name) -Force
            Write-Host "    propertiq-assets\$($_.Name)"
            $count++
        }
    }
    if (Test-Path $DataJson) {
        $destJsonDir = Join-Path $target 'Data\dashboards'
        New-Item -ItemType Directory -Path $destJsonDir -Force | Out-Null
        Get-ChildItem -Path $DataJson -Filter '*.json' -File |
            Where-Object { $_.Name -notlike '*.backup_*' } |
            ForEach-Object {
            $dest = Join-Path $destJsonDir $_.Name
            if ($_.FullName -ne $dest) {
                Copy-Item $_.FullName $dest -Force
            }
            Write-Host "    Data\dashboards\$($_.Name)"
            $count++
        }
        $vizSrc = Join-Path $DataJson 'viz'
        if (Test-Path $vizSrc) {
            $vizDest = Join-Path $destJsonDir 'viz'
            New-Item -ItemType Directory -Path $vizDest -Force | Out-Null
            Get-ChildItem -Path $vizSrc -Filter '*.json' -File | ForEach-Object {
                Copy-Item $_.FullName (Join-Path $vizDest $_.Name) -Force
                Write-Host "    Data\dashboards\viz\$($_.Name)"
                $count++
            }
        }
    }
    $dataJs = Join-Path (Join-Path $Dashboards 'sales') 'risk_cockpit.data.js'
    if (Test-Path $dataJs) {
        foreach ($target in $Targets) {
            Copy-Item $dataJs (Join-Path $target 'risk_cockpit.data.js') -Force
            Write-Host "    risk_cockpit.data.js -> $target"
        }
    }
    Write-Host "  $count files copied"
}

Write-Host ""
Write-Host "Done."
Write-Host "  GitHub Pages : cd '07_deploy\Master Dashboard' ; bash deploy.sh"
Write-Host "  Netlify      : drag '07_deploy\publish-site' folder to app.netlify.com/drop"
