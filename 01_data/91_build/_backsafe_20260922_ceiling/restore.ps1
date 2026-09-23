# restore.ps1 - put every file in this backup set back, byte-for-byte.
#
#   One file:      .\restore.ps1 -File 01_data/00_derived/wallet_waterfall.csv
#   Everything:    .\restore.ps1
#   Check only:    .\restore.ps1 -WhatIf
#   Verify only:   .\restore.ps1 -Verify
#
# The backup copies live in .\original\ mirroring the workspace layout.
# Each file's original sha256 is in .\_before.json.
#
# This script only ever writes to the paths listed in _before.json. It never
# deletes anything.

[CmdletBinding()]
param(
    [string]$File,
    [switch]$WhatIf,
    [switch]$Verify
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = 'C:\Users\jerom\Desktop\claude\ISZE'
$Before = Get-Content (Join-Path $Here '_before.json') -Raw | ConvertFrom-Json
$scope = @($Before.files)

if ($File) {
    $want = $File.Replace('\', '/').TrimStart('/')
    $scope = @($scope | Where-Object { $_.rel -eq $want })
    if ($scope.Count -eq 0) { throw "not in this backup set: $File" }
}

function Get-Sha256([string]$Path) {
    (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLower()
}

if ($Verify) {
    $bad = 0
    foreach ($f in $scope) {
        if ($f.revertible -eq $false) {
            Write-Host "NOT-REVERTIBLE  $($f.rel)"
            Write-Host "               the pre-change bytes were lost inside this folder; this file can"
            Write-Host "               only be reproduced by re-running its builder after wallet_waterfall.csv"
            $bad++
            continue
        }
        $target = Join-Path $Root ($f.rel.Replace('/', '\'))
        if (-not (Test-Path $target)) { Write-Host "ABSENT   $($f.rel)"; $bad++; continue }
        $now = Get-Sha256 $target
        if ($now -eq $f.sha256_before) {
            Write-Host "matches  $($f.rel)"
        } else {
            Write-Host "CHANGED  $($f.rel)"
            Write-Host "           now  $now"
            Write-Host "           was  $($f.sha256_before)"
            $bad++
        }
    }
    exit $bad
}

foreach ($f in $scope) {
    if ($f.revertible -eq $false) {
        Write-Host "SKIPPED (not revertible) $($f.rel)"
        continue
    }
    $src = Join-Path $Here ('original\' + $f.rel.Replace('/', '\'))
    $dst = Join-Path $Root ($f.rel.Replace('/', '\'))
    if (-not (Test-Path $src)) { throw "backup copy missing: $src" }
    $fromSha = Get-Sha256 $src
    if ($fromSha -ne $f.sha256_before) {
        throw "backup copy is not the recorded original for $($f.rel): $fromSha vs $($f.sha256_before)"
    }
    if ($WhatIf) {
        Write-Host "would restore $($f.rel)  ($fromSha)"
        continue
    }
    $dstDir = Split-Path -Parent $dst
    if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $now = Get-Sha256 $dst
    if ($now -ne $f.sha256_before) { throw "restore did not verify for $($f.rel)" }
    Write-Host "restored $($f.rel)"
}

if (-not $WhatIf) { Write-Host "`nDone. Re-run with -Verify to confirm." }
