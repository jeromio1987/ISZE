<#
    The one entry point for the AIM Universe verification suite.

    The checks live in tests\accept\ because that folder holds everything the
    independent reviewer owns. This file is the single command to run them all;
    it forwards its switches, so it behaves exactly like running the suite
    directly.

        powershell -ExecutionPolicy Bypass -File tests\run_all.ps1
        powershell -ExecutionPolicy Bypass -File tests\run_all.ps1 -SkipBrowser
        powershell -ExecutionPolicy Bypass -File tests\run_all.ps1 -SkipBaseline
        powershell -ExecutionPolicy Bypass -File tests\run_all.ps1 -BaselineFileUrl

    Every *.test.mjs and *.test.cjs file in this folder is run, found by
    listing the folder, so a new test file cannot be left out by forgetting to
    add a block here. A file passes only when node --test exits 0.

    Exit code: 1 when any unit file or acceptance check fails; 3 when nothing
    failed but a known finding is open or a step did not run; 0 only when
    every file and every check ran and passed. None of these is an acceptance
    - see the summary it prints.

    -BaselineFileUrl makes the baseline browser step open the frozen v03 file
    through a real file address instead of in memory. The default is in-memory;
    the reasoning and what each mode does and does not accept is in the note
    above the BASE-BROWSER step in accept\run_all.ps1.
#>
[CmdletBinding()]
param(
    [switch]$SkipBaseline,
    [switch]$SkipBrowser,
    [string]$Chrome = "",
    [switch]$KeepProfile,
    [switch]$BaselineFileUrl
)

$impl = Join-Path $PSScriptRoot "accept\run_all.ps1"
if (-not (Test-Path $impl)) {
    Write-Error "The acceptance suite is missing: $impl"
    exit 2
}


& $impl @PSBoundParameters
$acceptExit = $LASTEXITCODE

# Unit test files (node --test). Each file is listed from disk, run on its
# own, and judged on its exit code - never on matching a pass count in the text.
# They run after the acceptance suite because ux_07_keyboard_small reads the
# result the UX-07 browser step writes in this same run.
# Before U27 each file had its own block here; 24 files had no block, and the
# RANGE blocks read a root variable that was never set, so seven more never ran.
$unitFiles = Get-ChildItem -Path $PSScriptRoot -File |
    Where-Object { $_.Name -match '\.test\.(mjs|cjs)$' } |
    Sort-Object Name
$unitFailed = @()
Write-Host ""
Write-Host ("UNIT - {0} test files found in {1}" -f $unitFiles.Count, $PSScriptRoot)
foreach ($f in $unitFiles) {
    $out = & node --test $f.FullName 2>&1 | Out-String
    $code = $LASTEXITCODE
    $pass = if ($out -match '(?m)\bpass (\d+)\s*$') { [int]$Matches[1] } else { $null }
    $fail = if ($out -match '(?m)\bfail (\d+)\s*$') { [int]$Matches[1] } else { $null }
    if ($code -eq 0 -and $pass -gt 0) {
        Write-Host ("  PASS {0}  {1} pass / {2} fail" -f $f.Name, $pass, $fail)
    } else {
        $unitFailed += $f.Name
        Write-Host ("  FAIL {0}  exit {1}, {2} pass / {3} fail" -f $f.Name, $code, $pass, $fail) -ForegroundColor Yellow
        Write-Host $out
    }
}
Write-Host ("UNIT - {0} of {1} files passed" -f ($unitFiles.Count - $unitFailed.Count), $unitFiles.Count)
foreach ($n in $unitFailed) { Write-Host "  UNIT FAILED: $n" -ForegroundColor Yellow }

if ($unitFailed.Count -gt 0) {
    Write-Host ""
    Write-Host ("  Result: {0} unit test file(s) failed: {1}" -f $unitFailed.Count, ($unitFailed -join ", ")) -ForegroundColor Yellow
    exit 1
}
exit $acceptExit
