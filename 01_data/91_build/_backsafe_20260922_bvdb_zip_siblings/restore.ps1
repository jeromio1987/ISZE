# restore.ps1 — put back the originals changed by the BVDB zip / sibling-file pass
#
# Backup taken 2026-09-22 evening, folder:
#   C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_bvdb_zip_siblings\
#
# Usage
#   ...\restore.ps1                       # put every backed-up file back
#   ...\restore.ps1 -File "01_data/00_derived/gps_spu_by_family.csv"
#   ...\restore.ps1 -WhatIf               # list what would change, write nothing
#   ...\restore.ps1 -Verify               # write nothing; exit 1 if any file differs
#
# Every copy in .\original\ is byte-for-byte, and _before.json records the sha256 of
# each one. After a restore the hash is recomputed and compared; a mismatch is an
# error, not a warning.

[CmdletBinding()]
param(
    [string]$File,
    [switch]$WhatIf,
    [switch]$Verify
)

$ErrorActionPreference = 'Stop'
$Here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Orig    = Join-Path $Here 'original'
$Root    = 'C:\Users\jerom\Desktop\claude\ISZE'
$BeforeJ = Join-Path $Here '_before.json'

if (-not (Test-Path $BeforeJ)) { throw "missing $BeforeJ" }
$Before = Get-Content $BeforeJ -Raw | ConvertFrom-Json

function Get-Sha256([string]$p) {
    (Get-FileHash -Algorithm SHA256 -Path $p).Hash.ToLower()
}

$targets = @()
foreach ($prop in $Before.PSObject.Properties) {
    if ($File -and ($prop.Name -ne ($File -replace '\\', '/'))) { continue }
    $targets += $prop.Name
}
if ($File -and $targets.Count -eq 0) { throw "no backed-up file matches '$File'" }

$changed = 0; $matching = 0; $failed = 0
foreach ($rel in $targets) {
    $src = Join-Path $Orig ($rel -replace '/', '\')
    $dst = Join-Path $Root ($rel -replace '/', '\')
    $want = $Before.$rel.sha256_before

    if (-not (Test-Path $src)) { Write-Host "MISSING BACKUP  $rel"; $failed++; continue }

    $srcHash = Get-Sha256 $src
    if ($srcHash -ne $want) {
        Write-Host "BACKUP HASH MISMATCH  $rel  (expected $($want.Substring(0,16))…, got $($srcHash.Substring(0,16))…)"
        $failed++
        continue
    }

    $dstHash = if (Test-Path $dst) { Get-Sha256 $dst } else { '' }
    $same = ($dstHash -eq $want)

    if ($Verify) {
        if ($same) { Write-Host "matches original   $rel"; $matching++ }
        else       { Write-Host "DIFFERS            $rel";  $changed++ }
        continue
    }

    if ($WhatIf) {
        if ($same) { Write-Host "would keep         $rel" }
        else       { Write-Host "would restore      $rel" }
        continue
    }

    if ($same) {
        Write-Host "already original   $rel"
        $matching++
        continue
    }

    # temp + replace: truncating writes fail on some files in this workspace
    $tmp = "$dst.restoretmp"
    Copy-Item -LiteralPath $src -Destination $tmp -Force
    Move-Item -LiteralPath $tmp -Destination $dst -Force
    $newHash = Get-Sha256 $dst
    if ($newHash -eq $want) { Write-Host "restored           $rel"; $changed++ }
    else { Write-Host "RESTORE FAILED     $rel"; $failed++ }
}

Write-Host ""
if ($Verify) {
    Write-Host "Verify: $changed changed, $matching matching, $failed failed"
    if ($failed -gt 0 -or $changed -gt 0) { exit 1 }
} elseif ($WhatIf) {
    Write-Host "WhatIf: nothing written."
} else {
    Write-Host "Restore: $changed restored, $matching already original, $failed failed"
    if ($failed -gt 0) { exit 1 }
}
