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
