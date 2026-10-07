<#
=============================================================================
 run_all.ps1 - the one entry point for the AIM Universe verification suite.

 Every check that this reviewer owns is run from here, in one place, and the
 summary states:

   * each check, its exact command, and what it actually returned
   * the SHA-256 of every file that was examined, so a later run can say
     whether it tested the same revision
   * what is independent verification and what is only a developer test
   * that a non-zero exit is expected while defects remain, and that exit 0
     would not mean the product is accepted
   * every step that did not run, by name; exit 3 means known findings are
     open or a step did not run, and is never reported as "every check
     returned zero"

 Nothing here writes to src\, build\ or dist\. It reads them and reports.

   powershell -ExecutionPolicy Bypass -File tests\accept\run_all.ps1
   powershell -ExecutionPolicy Bypass -File tests\accept\run_all.ps1 -SkipBrowser
   powershell -ExecutionPolicy Bypass -File tests\accept\run_all.ps1 -SkipBaseline
   powershell -ExecutionPolicy Bypass -File tests\accept\run_all.ps1 -BaselineFileUrl

The baseline browser step has two load modes and the default is chosen
deliberately - see the note above the BASE-BROWSER invocation below.
=============================================================================
#>
[CmdletBinding()]
param(
    [switch]$SkipBaseline,
    [switch]$SkipBrowser,
    [string]$Chrome = "",
    [switch]$KeepProfile,
    # The supplied review's browser check can load the frozen file either as an
    # in-memory document (default here) or through a real file:// URL. The
    # default is in-memory; this switch selects the file URL instead so the two
    # can be compared on the same machine.
    [switch]$BaselineFileUrl
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$Accept  = $PSScriptRoot
$Root    = (Resolve-Path (Join-Path $Accept "..\..")).Path
$Out     = Join-Path $Accept "_out"
$Summary = Join-Path $Out "run_all_summary.json"
$Handoff = Join-Path (Split-Path $Root -Parent) "06_Working\AIM_v03_HANDOFF_20260922"

New-Item -ItemType Directory -Force -Path $Out | Out-Null

$script:Checks  = @()
$script:Failed  = 0
$script:Skipped = 0
# Steps that did not run, with the reason. A skipped step is never a pass.
$script:NotRun  = @()
# Steps that exited 3: no ordinary fail, but known findings are still open.
$script:KnownOpen = @()

# Exit codes the checks use (testsccept\lib\harness.cjs and accept_02_journey.py).
$EXIT_KNOWN_FINDINGS = 3
$EXIT_NOT_RUN = 4

function Add-NotRun($id, $reason) {
    $script:Skipped++
    $script:NotRun += [pscustomobject]@{ Id = $id; Reason = $reason }
}

function Write-Head($text) {
    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor DarkCyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor DarkCyan
}

function Write-Note($text, $colour) {
    if (-not $colour) { $colour = "Gray" }
    Write-Host "  $text" -ForegroundColor $colour
}

function Invoke-Step {
    param(
        [string]$Id,
        [string]$Title,
        [string]$Command,
        [string[]]$Arguments,
        [string]$WorkDir,
        [string]$RawFile
    )
    Write-Host ""
    Write-Host "-- $Id  $Title" -ForegroundColor White
    Write-Host "   $Command $($Arguments -join ' ')" -ForegroundColor DarkGray

    # Read the raw result BEFORE the run, so a step that writes nothing cannot be
    # mistaken for a step that passed on a stale file from an earlier run.
    $before = $null
    if ($RawFile -and (Test-Path $RawFile)) { $before = (Get-Item $RawFile).LastWriteTimeUtc }
    if ($RawFile -and (Test-Path $RawFile)) { Remove-Item -Force $RawFile }

    $log = $null
    if ($RawFile) { $log = [System.IO.Path]::ChangeExtension($RawFile, ".log") }
    elseif ($WorkDir) { $log = Join-Path $Out ("step_" + ($Id -replace "[^A-Za-z0-9]", "_") + ".log") }
    else { $log = Join-Path $Out ("step_" + ($Id -replace "[^A-Za-z0-9]", "_") + ".log") }

    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    if ($WorkDir) { Push-Location $WorkDir }
    try {
        & $Command @Arguments 2>&1 | Tee-Object -FilePath $log
    } finally {
        if ($WorkDir) { Pop-Location }
    }
    $code = $LASTEXITCODE
    $timer.Stop()

    $summary = $null
    $tested = $null
    $wrote = $false
    if ($RawFile -and (Test-Path $RawFile)) {
        $wrote = $true
        try {
            $json = Get-Content -Raw -Path $RawFile | ConvertFrom-Json
            if ($json.summary) { $summary = $json.summary }
            if ($json.tested_files) { $tested = $json.tested_files }
            if ($json.artifact_sha256 -and -not $tested) {
                $tested = @{ "dist artifact" = $json.artifact_sha256 }
            }
        } catch { }
    }

    $record = [ordered]@{
        id             = $Id
        title          = $Title
        command        = "$Command " + ($Arguments -join " ")
        exit_code      = $code
        seconds        = [math]::Round($timer.Elapsed.TotalSeconds, 1)
        summary        = $summary
        tested_files   = $tested
        result_file    = $RawFile
        result_written = $wrote
        console_log    = $log
    }
    $script:Checks += $record

    if ($code -eq $EXIT_KNOWN_FINDINGS) {
        $script:KnownOpen += $Id
    } elseif ($code -eq $EXIT_NOT_RUN) {
        Add-NotRun $Id "the step started but reported that it could not run (exit $EXIT_NOT_RUN)"
    } elseif ($code -ne 0) {
        $script:Failed++
    }
    $colour = "Green"; if ($code -ne 0) { $colour = "Yellow" }
    Write-Host ("   -> exit $code in $($record.seconds)s" + $(if ($RawFile -and -not $wrote) { "  (NO RESULT FILE WRITTEN)" } else { "" })) -ForegroundColor $colour
    return $code
}

# ---------------------------------------------------------------- environment
Write-Head "Environment"

$nodeVersion = (& node --version 2>&1) -join ""
$pyVersion   = (& python --version 2>&1) -join ""
if (-not $Chrome) {
    $candidates = @(
        "C:\Program Files\Google\Chrome\Application\chrome.exe",
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $Chrome = $c; break } }
}
if (-not $env:PLAYWRIGHT_BROWSERS_PATH) {
    $pw = Join-Path $env:LOCALAPPDATA "ms-playwright"
    if (Test-Path $pw) { $env:PLAYWRIGHT_BROWSERS_PATH = $pw }
}

Write-Note "root            : $Root"
Write-Note "node            : $nodeVersion"
Write-Note "python          : $pyVersion"
Write-Note "chrome          : $(if ($Chrome) { $Chrome } else { 'NOT FOUND' })"
Write-Note "playwright path : $env:PLAYWRIGHT_BROWSERS_PATH"

Write-Head "Tested revision (SHA-256 of each file this suite reads)"
$examined = @(
    "src\data\contracts.js",
    "src\engine\engine.js",
    "src\data\export.js",
    "src\data\scenario.js",
    "src\data\cases.js",
    "src\data\candidates.js",
    "src\data\evidence.js",
    "src\data\manifest.js",
    "src\data\costbasis.js",
    "src\output\recipients.js",
    "src\case\schema.js",
    "src\case\store.js",
    "src\ui\app.js",
    "tools\build.py",
    "reference\ISZE_AIM_Pricing_Decisions_v03_FROZEN.html",
    "dist\ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html",
    "dist\_build_report.json",
    "tests\fixtures\synthetic_payload.json"
)
$revision = [ordered]@{}
foreach ($rel in $examined) {
    $full = Join-Path $Root $rel
    if (Test-Path $full) {
        $hash = (Get-FileHash -Algorithm SHA256 -Path $full).Hash.ToLower()
        $size = (Get-Item $full).Length
        $revision[$rel] = @{ sha256 = $hash; bytes = $size; mtime = (Get-Item $full).LastWriteTime.ToString("s") }
        Write-Note ("{0}  {1}" -f $hash.Substring(0,16), $rel)
    } else {
        $revision[$rel] = @{ sha256 = $null; bytes = $null; missing = $true }
        Write-Note ("MISSING           {0}" -f $rel) "Red"
    }
}

$frozenExpect = "7494cea1955be820d0082eef15473610945663fbefc7a06d7969c15822423e14"
$frozenActual = $revision["reference\ISZE_AIM_Pricing_Decisions_v03_FROZEN.html"].sha256
Write-Host ""
if ($frozenActual -eq $frozenExpect) {
    Write-Note "The frozen v03 reference matches the checksum named in the brief." "Green"
} else {
    Write-Note "The frozen v03 reference does NOT match the checksum named in the brief." "Red"
    Write-Note "  expected $frozenExpect" "Red"
    Write-Note "  observed $frozenActual" "Red"
}

# ----------------------------------------------------------------- suite scope
# GUARD-01. The modules this suite loads are recorded here BEFORE any check runs,
# so a reviewer can see which revision answered each question. GUARD-09 (a step
# below) asserts the property this list makes visible: an acceptance check must
# not load a module the build does not assemble without saying so in its own file.
Write-Head "Suite scope - which source modules this run loads, and whether the build ships them"
$shippedByBuild = @()
$retiredByBuild = @()
try {
    $buildText = Get-Content -Raw -Path (Join-Path $Root "tools\build.py")
    $unwiredAt = $buildText.IndexOf("UNWIRED_MODULES")
    $bannedAt = $buildText.IndexOf("BANNED_IN_OUTPUT")
    if ($unwiredAt -lt 0) { throw "tools/build.py has no UNWIRED_MODULES block" }
    $beforeBlock = $buildText.Substring(0, $unwiredAt)
    $retiredBlock = if ($bannedAt -gt $unwiredAt) { $buildText.Substring($unwiredAt, $bannedAt - $unwiredAt) }
                    else { $buildText.Substring($unwiredAt) }
    $shippedByBuild = [regex]::Matches($beforeBlock, '\("(src/[^"]+)",\s*"[^"]+"\)') |
        ForEach-Object { $_.Groups[1].Value }
    $retiredByBuild = [regex]::Matches($retiredBlock, '\("(src/[^"]+)",\s*"[^"]+"\)') |
        ForEach-Object { $_.Groups[1].Value }
    Write-Note ("build.py assembles {0} module(s), retires {1}" -f $shippedByBuild.Count, $retiredByBuild.Count)
} catch {
    Write-Note "The build's module lists could not be read: $_" "Red"
}
$acceptSrcPaths = @(
    "src\data\contracts.js", "src\engine\engine.js", "src\data\export.js",
    "src\data\scenario.js", "src\data\cases.js", "src\data\candidates.js",
    "src\data\evidence.js", "src\data\manifest.js", "src\data\costbasis.js",
    "src\output\recipients.js", "src\case\schema.js", "src\case\store.js",
    "src\ui\app.js")
$suiteScope = @()
foreach ($rel in $acceptSrcPaths) {
    $posix = $rel.Replace("\", "/")
    $status = if ($shippedByBuild -contains $posix) { "assembled" }
              elseif ($retiredByBuild -contains $posix) { "RETIRED (unwired)" }
              else { "NEITHER LIST (orphan)" }
    $suiteScope += [pscustomobject]@{ Module = $posix; Build = $status }
    $colour = if ($status -eq "assembled") { "Gray" } else { "Yellow" }
    Write-Note ("  {0,-24} {1}" -f $status, $posix) $colour
}
Write-Note "A load of a RETIRED module is allowed only with a declaration in the check file - see GUARD-09."


# ------------------------------------------------------------------ baseline
if (-not $SkipBaseline) {
    Write-Head "BASELINE - the supplied independent review against the untouched frozen v03"
    Write-Note "This is the reproduction of the review that established the baseline." "Gray"
    Write-Note "A non-zero exit here is EXPECTED and CORRECT: it means the v03 defects reproduce." "Gray"
    $engineCheck = Join-Path $Handoff "tests\review_engine.cjs"
    $browserCheck = Join-Path $Handoff "tests\review_browser.py"
    if (-not (Test-Path $engineCheck)) {
        Write-Note "The supplied review pack is not present at $Handoff" "Red"
        Write-Note "The baseline cannot be reproduced in this environment. Steps skipped." "Red"
        Add-NotRun "BASE-ENGINE" "the supplied review pack is not present at $Handoff"
        Add-NotRun "BASE-BROWSER" "the supplied review pack is not present at $Handoff"
    } else {
        Invoke-Step -Id "BASE-ENGINE" -Title "Supplied 30 engine checks against frozen v03 (expect 11 pass / 19 fail)" `
            -Command "node" `
            -Arguments @(
                $engineCheck,
                (Join-Path $Root "reference\ISZE_AIM_Pricing_Decisions_v03_FROZEN.html"),
                (Join-Path $Out "baseline_engine_frozen.json")
            ) -RawFile (Join-Path $Out "baseline_engine_frozen.json") | Out-Null

        # --- BASE-BROWSER: which load mode, and why -------------------------
        #
        # The supplied review notes two load modes and says what each one is
        # for. Measured on this machine, 2026-09-22:
        #
        #   in-memory (`--memory`)  29 pass / 1 fail, exit 1
        #   file URL (no `--memory`) 29 pass / 1 fail, exit 1
        #
        # Both modes reproduce the review's baseline identically, so the mode is
        # not what decides the result. In-memory is the DEFAULT here, for two
        # reasons: it is the mode the review published its baseline in, and it is
        # the only one that still runs when a real file:// navigation is blocked.
        #
        # What in-memory does and does not accept, stated plainly because the
        # number above depends on it:
        #   * It DOES accept: the exact bytes of the frozen file, rendered in a
        #     real Chromium; every case and every tab; script errors; the
        #     structural observations the review records.
        #   * It does NOT accept: file-origin behaviour of any kind. Storage
        #     origin, `file://` navigation, the Windows launcher, hosting, and
        #     cross-user permissions are outside what this mode exercises. A
        #     result from this mode is evidence about the document, not about how
        #     a person would open it.
        #   * -BaselineFileUrl switches to the real file URL. On this machine that
        #     mode also works; on a machine where it is blocked the step would
        #     fail for an environment reason rather than a product one.
        #
        # Two defects made this step write nothing, and both were in this file,
        # not in the product:
        #   1. The step passed `--chrome <path>`. review_browser.py's actual flags
        #      are `--memory`, `--browser-path` and `--output`; there is no
        #      `--chrome` flag, so argparse aborted before the browser started.
        #   2. With no browser flag at all, Playwright resolves through
        #      PLAYWRIGHT_BROWSERS_PATH. In this environment that variable points
        #      at a sandbox cache holding no browser, so the launch died with
        #      "Executable doesn't exist ... chrome-headless-shell.exe".
        #   3. (Third cause, added after re-measuring.) ACCEPT-02 above sets
        #      PLAYWRIGHT_BROWSERS_PATH to the machine's real install; the
        #      supplied review's script then resolves from that variable rather
        #      than from the default install. The path is restored to the value
        #      that was in effect before ACCEPT-02 ran.
        # The step therefore passes `--browser-path` explicitly whenever Chrome
        # is present, and reports a missing browser as an error instead of
        # letting argparse or the launch fail silently.
        $baselineBrowserArgs = @(
            $browserCheck,
            (Join-Path $Root "reference\ISZE_AIM_Pricing_Decisions_v03_FROZEN.html")
        )
        if (-not $BaselineFileUrl) { $baselineBrowserArgs += "--memory" }
        if ($Chrome) { $baselineBrowserArgs += @("--browser-path", $Chrome) }
        $baselineBrowserArgs += @("--output", (Join-Path $Out "baseline_browser_frozen.json"))

        $baselineMode = if ($BaselineFileUrl) { "file URL" } else { "in-memory exact HTML" }
        Write-Note "load mode : $baselineMode" "Gray"
        Write-Note "browser   : $(if ($Chrome) { $Chrome } else { 'NOT FOUND - the launch will fail' })" `
            $(if ($Chrome) { "Gray" } else { "Red" })

        # The variable the supplied script resolves against. Set it for this step
        # so the browser is found even when ACCEPT-02 has not run in this session.
        $pwBefore = $env:PLAYWRIGHT_BROWSERS_PATH
        if ($Chrome) { $env:PLAYWRIGHT_BROWSERS_PATH = $null }

        Invoke-Step -Id "BASE-BROWSER" -Title "Supplied browser navigation against frozen v03 (expect 29 pass / 1 fail)" `
            -Command "python" `
            -Arguments $baselineBrowserArgs `
            -RawFile (Join-Path $Out "baseline_browser_frozen.json") | Out-Null

        $env:PLAYWRIGHT_BROWSERS_PATH = $pwBefore
    }
} else {
    Add-NotRun "BASE-ENGINE" "skipped by -SkipBaseline"
    Add-NotRun "BASE-BROWSER" "skipped by -SkipBaseline"
    Write-Head "BASELINE - skipped by -SkipBaseline"
}

# ------------------------------------------------------------- acceptance set
Write-Head "ACCEPT-01 - corrected engine"
Invoke-Step -Id "ACCEPT-01" -Title "30 supplied expectations carried to src/engine/engine.js, plus 16 added" `
    -Command "node" -Arguments @((Join-Path $Accept "accept_01_engine.cjs")) `
    -RawFile (Join-Path $Out "accept_01_engine.json") | Out-Null

Write-Head "ACCEPT-02 - complete browser journey (real file URL, restart, reopen)"
if ($SkipBrowser) {
    Add-NotRun "ACCEPT-02" "skipped by -SkipBrowser"
    Write-Note "skipped by -SkipBrowser" "Yellow"
} elseif (-not (Test-Path (Join-Path $Root "dist\ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html"))) {
    Add-NotRun "ACCEPT-02" "the built artifact does not exist yet"
    Write-Note "skipped: the built artifact does not exist yet" "Yellow"
} else {
    $browserArgs = @((Join-Path $Accept "accept_02_journey.py"))
    if ($Chrome) { $browserArgs += @("--chrome", $Chrome) }
    if ($KeepProfile) { $browserArgs += "--keep-profile" }
    Invoke-Step -Id "ACCEPT-02" -Title "all five cases, six tabs, both objectives, save, export, restart, reopen" `
        -Command "python" -Arguments $browserArgs `
        -RawFile (Join-Path $Out "accept_02_journey.json") | Out-Null
}

Write-Head "UX-07 - the agreed small-screen layout, measured on the painted page"
if ($SkipBrowser) {
    Add-NotRun "UX-07" "skipped by -SkipBrowser"
    Write-Note "skipped by -SkipBrowser" "Yellow"
} elseif (-not (Test-Path (Join-Path $Root "dist\ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html"))) {
    Add-NotRun "UX-07" "the built artifact does not exist yet"
    Write-Note "skipped: the built artifact does not exist yet" "Yellow"
} else {
    $narrowArgs = @((Join-Path $Accept "ux_07_narrow.py"))
    if ($Chrome) { $narrowArgs += @("--chrome", $Chrome) }
    Invoke-Step -Id "UX-07" -Title "prices, units, scope and limitations stay readable at 390 and 768" `
        -Command "python" -Arguments $narrowArgs `
        -RawFile (Join-Path $Out "ux_07_narrow.json") | Out-Null
}

Write-Head "U28-CONNECT-MATRIX - every feed paints, or states what is missing"`r`nif ($SkipBrowser) {`r`n    Add-NotRun "U28-CONNECT-MATRIX" "skipped by -SkipBrowser"`r`n    Write-Note "skipped by -SkipBrowser" "Yellow"`r`n} elseif (-not (Test-Path (Join-Path $Root "dist\ISZE_AIM_Pricing_Decisions_v04_SYNTHETIC.html"))) {`r`n    Add-NotRun "U28-CONNECT-MATRIX" "the synthetic artifact the matrix drives has not been built"`r`n    Write-Note "skipped: the synthetic artifact the matrix drives has not been built (run python tools/build.py)" "Yellow"`r`n} else {`r`n    $matrixArgs = @((Join-Path $Accept "connect_matrix_journey.py"))`r`n    if ($Chrome) { $matrixArgs += @("--chrome", $Chrome) }`r`n    Invoke-Step -Id "U28-CONNECT-MATRIX" -Title "nine feeds, one browser run: painted with its source, or honestly not available" `r`n        -Command "python" -Arguments $matrixArgs `r`n        -RawFile (Join-Path $Out "connect_matrix_journey.json") | Out-Null`r`n}`r`n`r`nWrite-Head "ACCEPT-03 - source conservation and correction behaviour"
Invoke-Step -Id "ACCEPT-03" -Title "repeat import, correction, set-aside, visible remainder" `
    -Command "node" -Arguments @((Join-Path $Accept "accept_03_conservation.cjs")) `
    -RawFile (Join-Path $Out "accept_03_conservation.json") | Out-Null

Write-Head "GUARD-09 - the suite may only load modules the build assembles"
Invoke-Step -Id "GUARD-09" -Title "no acceptance check loads an unshipped module without declaring it" `
    -Command "node" -Arguments @((Join-Path $Accept "guard_09_module_scope.cjs")) `
    -RawFile (Join-Path $Out "guard_09_module_scope.json") | Out-Null

Write-Head "ACCEPT-04 - participant-facing output, judged on bytes"
Invoke-Step -Id "ACCEPT-04" -Title "no restricted field survives, in nested data or in free text" `
    -Command "node" -Arguments @((Join-Path $Accept "accept_04_participant.cjs")) `
    -RawFile (Join-Path $Out "accept_04_participant.json") | Out-Null

Write-Head "SAFE-05 / SAFE-08 - exported bytes, hostile content, unauthorised recipient"
Invoke-Step -Id "SAFE-05/08" -Title "download routes, crafted markup, permission table" `
    -Command "node" -Arguments @((Join-Path $Accept "accept_05_08_safety.cjs")) `
    -RawFile (Join-Path $Out "accept_05_08_safety.json") | Out-Null

# ------------------------------------------------------------------- summary
Write-Head "SUMMARY"

$rows = @()
foreach ($c in $script:Checks) {
    $p = "-"; $f = "-"; $t = "-"
    if ($c.summary) {
        if ($null -ne $c.summary.pass)    { $p = $c.summary.pass }
        if ($null -ne $c.summary.fail)    { $f = $c.summary.fail }
        if ($null -ne $c.summary.total)   { $t = $c.summary.total }
    }
    $rows += [pscustomobject]@{
        Check   = $c.id
        Pass    = $p
        Fail    = $f
        Total   = $t
        Exit    = $c.exit_code
        Seconds = $c.seconds
    }
}
$rows | Format-Table -AutoSize | Out-String -Width 200 | Write-Host

foreach ($c in $script:Checks) {
    if ($c.exit_code -eq $EXIT_KNOWN_FINDINGS) {
        Write-Host "  KNOWN FINDINGS OPEN: $($c.id) - no ordinary fail, but $($c.summary.known_findings) known finding(s) open; see $($c.console_log)" -ForegroundColor Yellow
    } elseif ($c.exit_code -eq $EXIT_NOT_RUN) {
        Write-Host "  NOT RUN: $($c.id) - the step could not run; see $($c.console_log)" -ForegroundColor Red
    } elseif ($c.exit_code -ne 0) {
        Write-Host "  NON-ZERO: $($c.id) - see $($c.console_log)" -ForegroundColor Yellow
        if ($c.summary -and $c.summary.fail -gt 0) {
            Write-Host "            $($c.summary.fail) of $($c.summary.total) assertions failed" -ForegroundColor Yellow
        }
        if (-not $c.result_written) {
            Write-Host "            NO RESULT FILE WAS WRITTEN by this step" -ForegroundColor Red
        }
    } elseif (-not $c.result_written) {
        Write-Host "  NO RESULT FILE: $($c.id) exited 0 but wrote no result - treat as unverified" -ForegroundColor Red
    }
}

$engineBaseline = $script:Checks | Where-Object { $_.id -eq "BASE-ENGINE" }
if ($engineBaseline -and $engineBaseline.summary) {
    Write-Host ""
    Write-Host ("  Baseline engine checks : {0} pass / {1} fail / {2} total" -f `
        $engineBaseline.summary.pass, $engineBaseline.summary.fail, $engineBaseline.summary.total) -ForegroundColor White
}

Write-Host ""
Write-Host "  What this summary does and does not mean" -ForegroundColor Cyan
Write-Note "These are independent verification checks written by the reviewer, not the author's suite."
Write-Note "A green arithmetic check does not prove the export uses the same calculation path; the"
Write-Note "browser journey in ACCEPT-02 is what tests that, and it is the check that matters most."
Write-Note "Every failing check identifies a defect in the implementation. None of them has been fixed"
Write-Note "here: the reviewer writes failing tests and reports them."
Write-Note "No check in this suite confers business, technical, privacy or spending approval, and none"
Write-Note "substitutes for production identity, server-side access control or an independent audit."

Write-Host ""
foreach ($n in $script:NotRun) {
    Write-Host ("  NOT RUN: {0} - {1}" -f $n.Id, $n.Reason) -ForegroundColor Red
}
if ($script:Failed -gt 0) {
    Write-Host "  Result: $script:Failed check(s) failed. That is expected while defects remain." -ForegroundColor Yellow
    Write-Host "  Exit code 0 here would mean every assertion passed, which is NOT the same as accepted." -ForegroundColor Yellow
}
if ($script:KnownOpen.Count -gt 0) {
    Write-Host ("  Result: known findings still open in {0}. Not passed." -f ($script:KnownOpen -join ", ")) -ForegroundColor Yellow
}
if ($script:NotRun.Count -gt 0) {
    Write-Host ("  Result: {0} step(s) not run ({1}). This run is incomplete and is not a pass." -f `
        $script:NotRun.Count, (($script:NotRun | ForEach-Object { $_.Id }) -join ", ")) -ForegroundColor Red
}
if ($script:Failed -eq 0 -and $script:KnownOpen.Count -eq 0 -and $script:NotRun.Count -eq 0) {
    Write-Host "  Result: every check ran and returned zero." -ForegroundColor Green
    Write-Host "  That is not an acceptance. Human, technical, commercial and independent review are separate." -ForegroundColor Green
}

$report = [ordered]@{
    generated_at   = (Get-Date).ToString("s")
    machine        = $env:COMPUTERNAME
    node           = $nodeVersion
    python         = $pyVersion
    chrome         = $Chrome
    root           = $Root
    frozen_checksum_expected = $frozenExpect
    frozen_checksum_observed = $frozenActual
    frozen_checksum_matches  = ($frozenActual -eq $frozenExpect)
    baseline_browser_load_mode = if ($SkipBaseline) { "skipped" }
                                 elseif ($BaselineFileUrl) { "file URL" } else { "in-memory exact HTML" }
    suite_module_scope = $suiteScope
    build_module_lists = @{
        assembled = $shippedByBuild
        retired   = $retiredByBuild
        source    = "tools/build.py"
    }
    revision       = $revision
    checks         = $script:Checks
    failed_checks  = $script:Failed
    skipped_steps  = $script:Skipped
    not_run        = $script:NotRun
    known_findings_open_in = $script:KnownOpen
    interpretation = @(
        "Independent verification, written by the reviewer, run against the maintained source and the built artifact.",
        "A non-zero exit is expected while the reported defects remain unfixed.",
        "Exit 0 is not an acceptance: business, technical, privacy and spending authority are separate.",
        "Developer tests (tests/run_tests.cjs) are the author's; they are not run or endorsed here.",
        "GUARD-09 checks which source modules the acceptance suite loads, against the module lists in tools/build.py."
    )
}
$report | ConvertTo-Json -Depth 8 | Set-Content -Path $Summary -Encoding UTF8

Write-Host ""
Write-Host "  Combined report : $Summary" -ForegroundColor White
Write-Host "  Raw outputs     : $Out" -ForegroundColor White
Write-Host ""

# 1 = a check failed; 3 = nothing failed but findings are open or steps did not run; 0 = all ran clean.
if ($script:Failed -gt 0) { exit 1 }
if ($script:KnownOpen.Count -gt 0 -or $script:NotRun.Count -gt 0) { exit $EXIT_KNOWN_FINDINGS }
exit 0
