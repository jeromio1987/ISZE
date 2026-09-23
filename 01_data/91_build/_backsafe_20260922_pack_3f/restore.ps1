<#
    restore.ps1 - undo path for the section 3f reconciliation of 2026-09-22.

    Restores one or all of the four documents edited in that pass, from the copies held in
    this folder, and prints the sha256 of each restored file.

    Usage:
        restore.ps1                          # restore all four
        restore.ps1 -File 00_READ_ME_FIRST.md   # restore one

    To put the correction back afterwards, run _apply_3f.py then _apply_3f_b.py in this folder.
#>
[CmdletBinding()]
param(
    [string[]]$File
)

$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Pack = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920'

$All = @(
    '00_READ_ME_FIRST.md',
    '01_BRIEF_FOR_THE_MODEL.md',
    '02_CORRECTION_LOG.md',
    '04_FILE_CATALOG.csv'
)

if (-not $File -or $File.Count -eq 0) { $File = $All }

foreach ($name in $File) {
    if ($All -notcontains $name) {
        throw "Unknown file '$name'. Valid names: $($All -join ', ')"
    }

    $src = Join-Path $Here $name
    $dst = Join-Path $Pack $name

    if (-not (Test-Path -LiteralPath $src)) {
        throw "Backup copy not found: $src"
    }

    Copy-Item -LiteralPath $src -Destination $dst -Force

    $hash = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash.ToLower()
    $size = (Get-Item -LiteralPath $dst).Length
    Write-Host ("restored {0,-28} {1}  {2} bytes" -f $name, $hash.Substring(0, 16), $size)
}

Write-Host ''
Write-Host 'Done. To re-apply the correction: python _apply_3f.py ; python _apply_3f_b.py'
