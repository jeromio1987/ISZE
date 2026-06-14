# sync_context_to_github.ps1 - mirror ISZE agent markdown to GitHub (isze-dashboard/context/)
#
# Canonical source : C:\Users\jerom\Desktop\claude\ISZE\
# Whitelist         : docs\context_sync_whitelist.txt  (not all *.md)
# Target            : Master Dashboard\context\  ->  git push  ->  github.com/jeromio1987/isze-dashboard
#
# Usage:
#   .\sync_context_to_github.ps1              # copy, commit if changed, push
#   .\sync_context_to_github.ps1 -CopyOnly    # copy only (no git)
#   .\sync_context_to_github.ps1 -Message "Update PRISM docs"

param(
    [switch]$CopyOnly,
    [string]$Message = "Sync ISZE context markdown for other machines."
)

$ErrorActionPreference = 'Stop'
$env:GIT_REDIRECT_STDERR = '2>&1'

$IszeRootPs1 = Join-Path $PSScriptRoot '..\04_tools\workspace\isze_root.ps1'
. $IszeRootPs1
$IszeRoot       = Get-IszeRoot

$DocsDir        = Get-IszePath -Key 'docs' -Legacy 'docs'
$DeployRoot     = Join-Path (Get-IszePath -Key 'deploy' -Legacy '07_deploy') 'Master Dashboard'
if (-not (Test-Path $DeployRoot)) {
    $DeployRoot = Join-Path $IszeRoot 'Master Dashboard'
}
$DestRoot       = Join-Path $DeployRoot 'context'
$WhitelistPath  = Join-Path $DocsDir 'context_sync_whitelist.txt'

function Get-WhitelistedFiles {
    param(
        [string]$Root,
        [string]$ListPath
    )

    if (-not (Test-Path $ListPath)) {
        throw "Whitelist not found: $ListPath"
    }

    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    $files = @()

    foreach ($raw in Get-Content $ListPath) {
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith('#')) { continue }

        $line = $line -replace '/', '\'

        if ($line -match '\\$') {
            $dir = Join-Path $Root ($line.TrimEnd('\'))
            if (-not (Test-Path $dir)) {
                Write-Warning "Whitelist dir missing: $line"
                continue
            }
            Get-ChildItem $dir -Recurse -Filter '*.md' -File -ErrorAction SilentlyContinue | ForEach-Object {
                if ($seen.Add($_.FullName)) { $files += $_ }
            }
            continue
        }

        if ($line -match '\*') {
            $parentRel = Split-Path $line -Parent
            $pattern   = Split-Path $line -Leaf
            $parent    = if ($parentRel) { Join-Path $Root $parentRel } else { $Root }
            if (-not (Test-Path $parent)) {
                Write-Warning "Whitelist glob parent missing: $line"
                continue
            }
            Get-ChildItem $parent -Filter $pattern -File -ErrorAction SilentlyContinue | ForEach-Object {
                if ($seen.Add($_.FullName)) { $files += $_ }
            }
            continue
        }

        $full = Join-Path $Root $line
        if (-not (Test-Path $full)) {
            Write-Warning "Whitelist path missing: $line"
            continue
        }
        $item = Get-Item $full
        if ($item.PSIsContainer) {
            Get-ChildItem $full -Recurse -Filter '*.md' -File -ErrorAction SilentlyContinue | ForEach-Object {
                if ($seen.Add($_.FullName)) { $files += $_ }
            }
        }
        elseif ($seen.Add($item.FullName)) {
            $files += $item
        }
    }

    return $files | Sort-Object FullName
}

Write-Host "ISZE context sync - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Source: $IszeRoot"
Write-Host "Whitelist: $WhitelistPath"
Write-Host "Target: $DestRoot"
Write-Host ""

if (Test-Path $DestRoot) {
    Remove-Item $DestRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $DestRoot -Force | Out-Null

$sourceFiles = Get-WhitelistedFiles -Root $IszeRoot -ListPath $WhitelistPath
$count = 0

foreach ($src in $sourceFiles) {
    $rel = $src.FullName.Substring($IszeRoot.Length + 1)
    $target = Join-Path $DestRoot $rel
    $targetDir = Split-Path $target -Parent
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Copy-Item $src.FullName $target -Force
    $count++
}

Write-Host "Copied $count whitelisted files."
Write-Host ""

if ($CopyOnly) {
    Write-Host "CopyOnly - skipping git commit/push."
    return
}

if (-not (Test-Path (Join-Path $DeployRoot '.git'))) {
    throw "No git repo at $DeployRoot"
}

Push-Location $DeployRoot
git add context/
$status = git status --porcelain context/
if (-not $status) {
    Write-Host "No context changes - nothing to commit."
    Pop-Location
    return
}

git commit -m $Message
git push origin main
Write-Host ""
Write-Host "Pushed to https://github.com/jeromio1987/isze-dashboard/tree/main/context"
Pop-Location
