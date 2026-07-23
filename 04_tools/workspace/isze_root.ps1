# ISZE root discovery for PowerShell tools.
# Dot-source from launchers/sync scripts — no callers yet.
#
# Usage (future):
#   . (Join-Path $PSScriptRoot '..\..\04_tools\workspace\isze_root.ps1')
#   $DataRoot = Get-IszePath -Key 'data' -Legacy 'Data'
#   $Derived  = Join-Path $DataRoot 'derived'

function Get-IszeRoot {
    if ($env:ISZE_ROOT -and (Test-Path (Join-Path $env:ISZE_ROOT 'paths.yaml'))) {
        return (Resolve-Path $env:ISZE_ROOT).Path
    }
    $p = $PSScriptRoot
    while ($p) {
        if ((Test-Path (Join-Path $p 'paths.yaml')) -and (Test-Path (Join-Path $p 'FACTS.md'))) {
            return $p
        }
        $parent = Split-Path $p -Parent
        if ($parent -eq $p) { break }
        $p = $parent
    }
    throw "ISZE root not found (set `$env:ISZE_ROOT or run from ISZE tree)"
}

function Get-IszePath {
    param(
        [Parameter(Mandatory)][string]$Key,
        [Parameter(Mandatory)][string]$Legacy
    )
    $root = Get-IszeRoot
    $yaml = Join-Path $root 'paths.yaml'
    if (Test-Path $yaml) {
        $raw = Get-Content $yaml -Raw
        if ($raw -match "(?m)^\s+$Key`: `"([^`"]+)`"") {
            $mapped = Join-Path $root $Matches[1]
            if (Test-Path $mapped) { return $mapped }
        }
    }
    $legacyPath = Join-Path $root $Legacy
    if (Test-Path $legacyPath) { return $legacyPath }
    return (Join-Path $root $Legacy)
}

function Get-DataSubfolderPath {
    param([Parameter(Mandatory)][string]$Key)
    $root = Get-IszeRoot
    $yaml = Join-Path $root 'paths.yaml'
    $numbered = $null
    $legacy = $null
    if (Test-Path $yaml) {
        $inBlock = $false
        $inKey = $false
        foreach ($line in Get-Content $yaml) {
            if ($line -match "^\s+$Key`:") { $inKey = $true; $inBlock = $true; continue }
            if ($inKey -and $line -match '^\s+\w+:') { $inKey = $false }
            if ($inBlock -and -not $inKey -and $line -match '^\s{2}\w+:') { break }
            if ($inKey -and $line -match 'numbered:\s*"([^"]+)"') { $numbered = $Matches[1] }
            if ($inKey -and $line -match 'legacy:\s*"([^"]+)"') { $legacy = $Matches[1] }
        }
    }
    $dataRoot = Get-IszePath -Key 'data' -Legacy 'Data'
    if ($numbered) {
        $p = Join-Path $dataRoot $numbered
        if (Test-Path $p) { return $p }
    }
    if ($legacy) {
        $p = Join-Path $dataRoot $legacy
        if (Test-Path $p) { return $p }
    }
    if ($numbered) { return (Join-Path $dataRoot $numbered) }
    throw "data_subfolders.$Key not found in paths.yaml"
}
