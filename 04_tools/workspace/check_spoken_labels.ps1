<#
=============================================================================
 check_spoken_labels.ps1
=============================================================================

 WHAT THIS DOES
   Scans text content in .html, .md, .csv and .json files and reports wording
   that the ISZE language rules forbid in anything a human reads, plus two
   stale-figure phrases that have been corrected more than once by hand.

   For every hit it prints: the file, the line number, the offending word,
   and the exact suggested replacement taken from the rule files.

 WHY IT EXISTS
   The same corrections came back repeatedly because a written rule is only
   obeyed if the agent happens to load it. A rule file that is never opened
   cannot object; a checker can. The point is to make one whole class of
   correction mechanical instead of a matter of memory or attention.

 WHERE THE RULES COME FROM (nothing here is invented)
   ISZE\.cursor\rules\isze-spoken-labels.mdc      - forbidden labels -> say instead
   ISZE\.cursor\rules\isze-pricing-no-street-ui.mdc - pricing "street" wording
   ISZE\.cursor\rules\isze-exec-aftersales-paper.mdc - hard failure 2 (stale count/share)

 USAGE
   .\check_spoken_labels.ps1 -Path <file-or-folder> [-Glob <pattern>] [-AllowFileNames]

   -Path    A file, a folder (scanned recursively), or a wildcard such as
            'ISZE\02_dashboards\*.html'.
            An explicit path to ONE file is always scanned, wherever that file
            sits - including a builder under a `_build` folder. Naming a file is
            a deliberate request, so it overrules the allowlist below; the run
            says so in its output instead of skipping it quietly.
   -Glob    Optional additional filter, e.g. -Glob 'Sales_*' or '*.md'.
   -AllowFileNames
            The language rule permits quoting a filename that contains a
            forbidden word, once, in a footnote. With this switch, a hit that
            sits inside a backticked path or a path-like token is reported as
            OK-FILENAME instead of a violation. Default is to report it, so
            nothing is hidden by accident.

 BEHAVIOUR
   - Read-only. This script never writes, moves, renames or deletes anything.
     It only reads file contents and prints to the console.
   - Fail-soft. A missing path, an unreadable file or a bad regex is reported
     and the scan continues. The script never throws and never exits non-zero
     because of a scan problem.
   - Exit code is always 0 unless a violation-free run is not what you want to
     gate on; see the caller for how to react to the summary line.

 NOTE ON THE PATTERNS
   The forbidden strings appear below only as detection patterns, in the same
   way JSON field names may stay in pipeline code (see the two rule files).
   They must never be used as labels in chat, HTML or a pack.

=============================================================================
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Path = '',

    [string]$Glob = '',

    [switch]$AllowFileNames,

    # Report only files whose last write is within this many days. 0 = no filter.
    # This is how a build gate checks the artifact that was just built instead of
    # the whole legacy tree: -ChangedWithinDays 2 after a ship, 0 for a sweep.
    [int]$ChangedWithinDays = 0,

    # Extra folder names to skip, at any depth. Added to the built-in allowlist.
    [string[]]$SkipDirs = @(),

    # Extra file names to skip. Added to the built-in allowlist.
    [string[]]$SkipFiles = @(),

    # Ignore the built-in allowlist and scan every matched file.
    [switch]$NoSkipList,

    # Exit 1 when a violation is found. Default is report-only: exit 0 always, so
    # the weekly audit can add a finding without failing. A build gate passes this.
    [switch]$FailOnViolation
)

# Never let an unexpected failure turn into a non-zero exit; this is a reader.
$ErrorActionPreference = 'Continue'

$script:FilesScanned = 0
$script:Violations = 0
$script:Advisories = 0
$script:FileNamePasses = 0
$script:RuleCounts = @{}
$script:Errors = New-Object System.Collections.ArrayList
$script:Skipped = 0
$script:ExplicitCount = 0

$AllowedExtensions = @('.html', '.htm', '.md', '.mdc', '.csv', '.json', '.txt', '.ps1', '.py', '.mjs')

# ---------------------------------------------------------------------------
# Allowlist - files that must name the banned words because their whole job is
# to police them, or because they are inputs rather than anything a human reads.
#
# Why this exists: the 18 Sep register records that the checker fires on the rule
# files themselves, on this script, and on QA scratch copies. A gate that blocks
# on a legitimate file is worse than no gate, because it cannot be satisfied.
#
# Kept in step with LANG_SKIP_FILES in 04_tools\workspace\_overnight_angles.py,
# which already carried this idea. Added here: the rule and memory folders that
# quote a banned word while defining it, scratch/QA folders, and old backups.
#
# 19 Sep - `_build` is deliberately NOT skipped any more. Builders and
# generators are the code that writes the pages, so a checker that skips them
# reports a page clean while the banned wording sits in the thing that will put
# it back on the next rebuild. That is exactly how two sales builders showed
# zero while their pages carried 85 labels. A builder under `_build` is scanned
# like any other .py.
# ---------------------------------------------------------------------------
$DefaultSkipDirNames = @(
    '.cursor',          # the rule files themselves
    '.claude',          # agent worktrees - parallel checkouts of this same tree
    '.git',
    '__pycache__',
    '.venv', 'venv', 'node_modules',
    '_archive',         # retired dashboards and retired builders, not shipped
    '90_archive',
    '_working',
    '05_memory',        # internal notes and briefs, not read by Jerome as a pack
    'context'           # generated deploy copy of the memory folder
)

$DefaultSkipFileNames = @(
    'check_spoken_labels.ps1',        # this script names the words to detect them
    '_overnight_angles.py',           # carries the same ban list
    'isze_delegator_watch.ps1',
    'isze_overnight_orchestrator.ps1',
    'DELEGATOR_BOARD.md',
    'DELEGATOR_REFRESH_HOWTO.md',
    'isze-spoken-labels.mdc',
    'isze-pricing-no-street-ui.mdc',
    'PRICING_POLICY_PAPER_2026-09-17.md'
)

# Scratch and backup copies are not deliverables: an HTML written by a QA probe,
# a browser DOM dump, or a .bak from an earlier edit. They repeat the page's own
# wording, so flagging them doubles every real hit and cannot be acted on.
$SkipFilePatterns = @(
    '^_.*\.html$',        # _probe.html, _dom.html, _interaction.html
    '^_.*\.mjs$',
    '\.bak.*$',
    '\.min\.js$'
)

# Namespace prefixes that really are generated or scratch, as opposed to a
# hand-written builder. `_build` used to be in this list and must not come back:
# the two sales builders live in `_build` folders, so skipping the folder meant
# skipping the code that writes the pages.
$SkipDirPatterns = @(
    '^_qa',
    '^_audit$',
    '^_design$',
    '^_composable$',
    '^_tmp',
    '^_probe',
    '^_scratch',
    '^_extracted$',
    '^__pycache__$'
)

# Two different questions, which must not be conflated:
#
#   Test-IsBannedByJob  Does this file's whole job require it to name the banned
#                       words (the rules, this script, its companion ban-lists),
#                       or is it a non-deliverable (archive, scratch, backup)?
#                       This applies even to an explicit path. Scanning the
#                       checker against its own pattern table would produce a
#                       fixed batch of false violations that no rebuild can
#                       clear, which is exactly the unsatisfiable gate the
#                       allowlist exists to prevent.
#
#   Test-IsSkipped      Does its folder normally get skipped when we sweep a
#                       spread of files (QA output, scratch, generated caches)?
#                       An explicit path overrides THIS list only, so a builder
#                       under `_build` or `sales\_build` is scanned - the hole
#                       fixed on 19 Sep.
function Test-IsBannedByJob {
    param([System.IO.FileInfo]$File)

    foreach ($name in $DefaultSkipFileNames) {
        if ($File.Name -ieq $name) { return $true }
    }
    foreach ($name in $SkipFiles) {
        if (-not [string]::IsNullOrWhiteSpace($name) -and $File.Name -ieq $name) { return $true }
    }
    foreach ($pat in $SkipFilePatterns) {
        if ($File.Name -match $pat) { return $true }
    }
    if ($NoSkipList) { return $false }
    foreach ($name in $DefaultSkipDirNames) {
        if ($File.DirectoryName -and ($File.DirectoryName -split '[\\/]') -contains $name) { return $true }
    }
    foreach ($name in $SkipDirs) {
        if (-not [string]::IsNullOrWhiteSpace($name) -and
            $File.DirectoryName -and ($File.DirectoryName -split '[\\/]') -contains $name) { return $true }
    }
    return $false
}

# Names a build gate should only apply to the artifact it just built.
#
# -Explicit is set when -Path named this exact file rather than a folder or a
# wildcard. It overrides the folder-level skip only; see the comment above.
function Test-IsSkipped {
    param(
        [System.IO.FileInfo]$File,
        [switch]$Explicit
    )

    # Files whose job is to name the words, backups and archives are out either
    # way - an explicit path does not override that.
    if (Test-IsBannedByJob -File $File) { return $true }

    # An explicit path overrides the folder-level skip: this is the case that was
    # broken, where naming one builder under `_build` scanned nothing at all.
    if ($Explicit) { return $false }

    if (-not $NoSkipList) {
        # Folder-pattern skips (QA output, scratch, extracted fragments).
        foreach ($pat in $SkipDirPatterns) {
            $dirs = if ($File.DirectoryName) { $File.DirectoryName -split '[\\/]' } else { @() }
            foreach ($d in $dirs) { if ($d -match $pat) { return $true } }
        }
    }
    return $false
}

# ---------------------------------------------------------------------------
# Rule table.
#   Id            short handle used in output
#   Pattern       regex to find the offending wording
#   Replacement   the exact wording the rule files tell us to use instead
#   Source        the rule file the replacement comes from
#   Kind          'Violation' or 'Advisory'
#   SkipIdentifier  $true = ignore hits that are part of a snake_case / dotted
#                   identifier or file name (allowed in pipeline code by the rule)
#   Context       optional regex; the line must also match this to count
# ---------------------------------------------------------------------------
$Rules = @(
    @{
        Id             = 'sellout-to-dealer'
        Pattern        = 'sell[\s\-]?out'
        Replacement    = 'sales to dealer'
        Source         = 'isze-spoken-labels.mdc'
        Kind           = 'Violation'
        SkipIdentifier = $true
        Context        = ''
    },
    @{
        Id             = 'sellout-compound'
        Pattern        = '(?i)\b(dealer|reference|peer)\s+sell[\s\-]?out'
        Replacement    = 'dealer sales (or rewrite as sales to dealer)'
        Source         = 'the two rule files disagree - see RECURRING_CORRECTIONS_20260916.md'
        Kind           = 'Advisory'
        SkipIdentifier = $true
        Context        = ''
    },
    @{
        Id             = 'price-list-nickname'
        Pattern        = 'book[\s\-_]?b\b'
        Replacement    = 'the price list / a price revision'
        Source         = 'isze-spoken-labels.mdc'
        Kind           = 'Violation'
        SkipIdentifier = $true
        Context        = ''
    },
    @{
        Id             = 'theoretical-spend'
        Pattern        = '\bwallet\b'
        Replacement    = 'parts billed (vs) target spend per truck'
        Source         = 'isze-spoken-labels.mdc'
        Kind           = 'Violation'
        SkipIdentifier = $true
        Context        = ''
    },
    @{
        Id             = 'street-index'
        Pattern        = 'street[\s\-_]?index'
        Replacement    = 'price index'
        Source         = 'isze-pricing-no-street-ui.mdc'
        Kind           = 'Violation'
        SkipIdentifier = $true
        Context        = ''
    },
    @{
        Id             = 'competitor-retail'
        Pattern        = '\bstreet\b'
        Replacement    = 'OEM peer retail / reference dealer price'
        Source         = 'isze-pricing-no-street-ui.mdc'
        Kind           = 'Violation'
        SkipIdentifier = $true
        Context        = ''
    },
    @{
        Id             = 'stale-count-nine-flat'
        Pattern        = 'nine\s+near[\s\-]?flat'
        Replacement    = 'eight near-flat markets'
        Source         = 'isze-exec-aftersales-paper.mdc (hard failure 2)'
        Kind           = 'Violation'
        SkipIdentifier = $false
        Context        = ''
    },
    @{
        Id             = 'stale-count-nine-placeholder'
        Pattern        = 'nine\s+placeholder'
        Replacement    = 'eight placeholder markets'
        Source         = 'isze-exec-aftersales-paper.mdc (hard failure 2)'
        Kind           = 'Violation'
        SkipIdentifier = $false
        Context        = ''
    },
    @{
        Id             = 'stale-share-37-3'
        Pattern        = '37\.3'
        Replacement    = '40.3%'
        Source         = 'isze-exec-aftersales-paper.mdc (hard failure 2)'
        Kind           = 'Violation'
        SkipIdentifier = $false
        Context        = 'ceiling|placeholder|flat|near[\s\-]?flat|%'
    },
    @{
        Id             = 'conversion-needs-english'
        Pattern        = '1\.785'
        Replacement    = 'first add one plain English sentence, then the factor may sit in a footnote'
        Source         = 'isze-spoken-labels.mdc'
        Kind           = 'Advisory'
        SkipIdentifier = $false
        Context        = ''
    }
)

function Add-RuleCount {
    param([string]$Id, [string]$Kind)
    $key = "$Kind|$Id"
    if ($script:RuleCounts.ContainsKey($key)) {
        $script:RuleCounts[$key] = [int]$script:RuleCounts[$key] + 1
    }
    else {
        $script:RuleCounts[$key] = 1
    }
}

# A hit sits inside a backticked span when an odd number of backticks precedes it.
# The language rule permits quoting a file name that contains a forbidden word,
# once, in a footnote - and a backticked span is exactly how that is written.
function Test-InBackticks {
    param([string]$Line, [int]$Start)
    if ($Start -le 0 -or [string]::IsNullOrEmpty($Line)) { return $false }
    $before = $Line.Substring(0, [Math]::Min($Start, $Line.Length))
    $ticks = 0
    foreach ($ch in $before.ToCharArray()) { if ($ch -eq '`') { $ticks++ } }
    return (($ticks % 2) -eq 1)
}

# A hit is treated as part of a file name or path when it is glued to path
# punctuation or carries a file extension on the same whitespace-delimited token.
# Important: this must look at the ONE token containing the hit, not at a fixed
# character window. A window is useless in HTML, where closing tags are full of
# slashes and would mark almost every hit as a "file name".
function Test-IsFileNameQuoted {
    param([string]$Line, [int]$Start, [int]$Length)

    if ($Start -lt 0 -or $Line.Length -eq 0) { return $false }
    $end = $Start + $Length
    if ($end -gt $Line.Length) { $end = $Line.Length }

    $before = if ($Start -gt 0) { $Line.Substring(0, $Start) } else { '' }
    $after = if ($end -lt $Line.Length) { $Line.Substring($end) } else { '' }

    # The whitespace-delimited token surrounding the hit.
    $tokenStart = $before.Length
    while ($tokenStart -gt 0 -and -not [char]::IsWhiteSpace($before[$tokenStart - 1])) { $tokenStart-- }
    $tokenBefore = $before.Substring($tokenStart)
    $tokenEnd = 0
    while ($tokenEnd -lt $after.Length -and -not [char]::IsWhiteSpace($after[$tokenEnd])) { $tokenEnd++ }
    $tokenAfter = $after.Substring(0, $tokenEnd)
    $token = $tokenBefore + $tokenAfter

    # A path separator inside that single token => a path, not prose.
    if ($token -match '[\\/]') { return $true }

    # A file extension sits on the same token => file name or field name.
    if ($token -match '\.(html|htm|md|mdc|csv|json|txt|ps1|py|mjs|yml|yaml|xlsx|pptx|pdf|cmd|parquet)\b') { return $true }

    return $false
}

# A hit inside a long snake_case / dotted token is allowed as pipeline code.
function Test-IsIdentifier {
    param([string]$Line, [int]$Start, [int]$Length)

    $end = $Start + $Length
    $before = if ($Start -gt 0) { $Line[$Start - 1] } else { [char]0 }
    $after = if ($end -lt $Line.Length) { $Line[$end] } else { [char]0 }

    $isWord = { param($c) ([char]::IsLetterOrDigit($c)) -or $c -eq '_' -or $c -eq '-' -or $c -eq '.' }
    return ((& $isWord $before) -or (& $isWord $after))
}

function Get-ScannedFiles {
    param([string]$Target, [string]$GlobFilter)

    $files = New-Object System.Collections.ArrayList
    $hasWildcard = $Target -match '[\*\?]'
    # -Path named one exact file rather than a folder or a wildcard. That file is
    # scanned even if the allowlist would otherwise skip its folder.
    $explicitFile = $false

    try {
        if ($hasWildcard) {
            $dir = Split-Path $Target -Parent
            if ([string]::IsNullOrWhiteSpace($dir)) { $dir = '.' }
            $leaf = Split-Path $Target -Leaf
            if (Test-Path -LiteralPath $dir) {
                Get-ChildItem -Path (Join-Path $dir $leaf) -File -Recurse -ErrorAction SilentlyContinue |
                    ForEach-Object { [void]$files.Add($_) }
            }
            else {
                [void]$script:Errors.Add("Wildcard parent folder not found: $dir")
            }
        }
        elseif (Test-Path -LiteralPath $Target) {
            $item = Get-Item -LiteralPath $Target -ErrorAction Stop
            if ($item.PSIsContainer) {
                Get-ChildItem -LiteralPath $item.FullName -File -Recurse -ErrorAction SilentlyContinue |
                    ForEach-Object { [void]$files.Add($_) }
            }
            else {
                [void]$files.Add($item)
                $explicitFile = $true
                $script:ExplicitCount++
            }
        }
        else {
            [void]$script:Errors.Add("Path not found: $Target")
            return @()
        }
    }
    catch {
        [void]$script:Errors.Add("Could not enumerate '$Target': $($_.Exception.Message)")
        return @()
    }

    $out = New-Object System.Collections.ArrayList
    $cutoff = if ($ChangedWithinDays -gt 0) { (Get-Date).AddDays(-1 * $ChangedWithinDays) } else { $null }
    foreach ($f in $files) {
        if ($AllowedExtensions -notcontains $f.Extension.ToLower()) { continue }
        if (-not [string]::IsNullOrWhiteSpace($GlobFilter)) {
            if (-not ($f.Name -like $GlobFilter)) { continue }
        }
        if (Test-IsSkipped -File $f -Explicit:$explicitFile) { $script:Skipped++; continue }
        if ($cutoff -and $f.LastWriteTime -lt $cutoff) { continue }
        [void]$out.Add($f)
    }
    return $out.ToArray()
}

function Invoke-Scan {
    param([string]$Target, [string]$GlobFilter)

    Write-Host ''
    Write-Host ('check_spoken_labels - scanning: ' + $Target) -ForegroundColor Cyan
    if (-not [string]::IsNullOrWhiteSpace($GlobFilter)) {
        Write-Host ('  extra glob filter: ' + $GlobFilter) -ForegroundColor DarkGray
    }
    if ($script:ExplicitCount -gt 0) {
        Write-Host '  explicit single-file path - allowlist bypassed, this file is scanned wherever it sits' -ForegroundColor DarkGray
    }
    Write-Host ('  file-name quoting: ' + $(if ($AllowFileNames) { 'allowed (OK-FILENAME)' } else { 'reported as a violation (default)' })) -ForegroundColor DarkGray
    Write-Host ''

    $targets = Get-ScannedFiles -Target $Target -GlobFilter $GlobFilter
    if ($targets.Count -eq 0) {
        Write-Host '  No matching files to scan.' -ForegroundColor Yellow
    }

    foreach ($file in $targets) {
        $script:FilesScanned++
        $lines = @()
        try {
            $lines = Get-Content -LiteralPath $file.FullName -ErrorAction Stop
        }
        catch {
            [void]$script:Errors.Add("Could not read '$($file.FullName)': $($_.Exception.Message)")
            continue
        }
        if ($null -eq $lines) { continue }
        if ($lines -is [string]) { $lines = @($lines) }

        $lineNo = 0
        foreach ($line in $lines) {
            $lineNo++
            if ($null -eq $line) { continue }
            $text = [string]$line
            if ($text.Length -eq 0) { continue }
            if ($text.Length -gt 4000) { $text = $text.Substring(0, 4000) }

            foreach ($rule in $Rules) {
                $hits = @()
                try {
                    $hits = [regex]::Matches($text, $rule.Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
                }
                catch {
                    [void]$script:Errors.Add("Bad regex for rule '$($rule.Id)': $($_.Exception.Message)")
                    continue
                }

                foreach ($m in $hits) {
                    if ($m.Length -eq 0) { continue }

                    if (-not [string]::IsNullOrWhiteSpace($rule.Context)) {
                        if (-not ($text -match $rule.Context)) { continue }
                    }

                    $inBackticks = Test-InBackticks -Line $text -Start $m.Index
                    $isFileName = Test-IsFileNameQuoted -Line $text -Start $m.Index -Length $m.Length
                    $isQuotedName = ($inBackticks -or $isFileName)

                    # Order matters. Field names and paths get pass/fail reporting
                    # before the identifier skip, otherwise a backticked file name
                    # would be silently dropped instead of shown.
                    if ($isQuotedName) {
                        if ($AllowFileNames) {
                            $script:FileNamePasses++
                            Write-Host ("OK-FILENAME  {0}:{1}  [{2}]  <{3}>" -f $file.Name, $lineNo, $rule.Id, $m.Value) -ForegroundColor DarkGray
                            continue
                        }
                    }
                    elseif ($rule.SkipIdentifier) {
                        if (Test-IsIdentifier -Line $text -Start $m.Index -Length $m.Length) { continue }
                    }
                    $snippet = $text.Trim()
                    if ($snippet.Length -gt 200) { $snippet = $snippet.Substring(0, 200) + ' ...' }

                    $isAdvisory = ($rule.Kind -eq 'Advisory')

                    $tag = if ($isAdvisory -and $isQuotedName) { 'ADVISORY (inside a path or file name)' }
                    elseif ($isAdvisory) { 'ADVISORY' }
                    elseif ($isQuotedName) { 'VIOLATION (quoted file name - rule allows this once in a footnote)' }
                    else { 'VIOLATION' }

                    if ($isAdvisory) { $script:Advisories++ }
                    else { $script:Violations++ }
                    Add-RuleCount -Id $rule.Id -Kind $(if ($isAdvisory) { 'Advisory' } else { 'Violation' })

                    $colour = if ($isAdvisory) { 'Yellow' } else { 'Red' }
                    Write-Host ("{0}  {1}:{2}" -f $tag, $file.FullName, $lineNo) -ForegroundColor $colour
                    Write-Host ("    found      : <{0}>" -f $m.Value) -ForegroundColor $colour
                    Write-Host ("    replace    : {0}" -f $rule.Replacement) -ForegroundColor Green
                    Write-Host ("    rule source: {0}" -f $rule.Source) -ForegroundColor DarkGray
                    Write-Host ("    line       : {0}" -f $snippet) -ForegroundColor DarkGray
                    Write-Host ''
                }
            }
        }
    }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
try {
    Write-Host 'check_spoken_labels.ps1 - read-only language and stale-figure check' -ForegroundColor White
    Write-Host 'It never writes to any file. It reports and continues.' -ForegroundColor DarkGray

    if ([string]::IsNullOrWhiteSpace($Path)) {
        Write-Host ''
        Write-Host 'No -Path given. Nothing scanned.' -ForegroundColor Yellow
        Write-Host 'Usage: .\check_spoken_labels.ps1 -Path <file-or-folder> [-Glob <pattern>] [-AllowFileNames]' -ForegroundColor Yellow
    }
    else {
        Invoke-Scan -Target $Path -GlobFilter $Glob
    }
}
catch {
    # Fail-soft: report, then fall through to the summary. Never a hard failure.
    [void]$script:Errors.Add("Unhandled: $($_.Exception.Message)")
}

Write-Host ''
Write-Host '-------------------------- summary --------------------------' -ForegroundColor Cyan
Write-Host ("Files scanned          : {0}" -f $script:FilesScanned)
Write-Host ("Files skipped (allowlist): {0}" -f $script:Skipped) -ForegroundColor DarkGray
if ($script:ExplicitCount -gt 0) {
    Write-Host ("Explicit path scans     : {0} (allowlist bypassed)" -f $script:ExplicitCount) -ForegroundColor DarkGray
}
Write-Host ("Violations             : {0}" -f $script:Violations) -ForegroundColor $(if ($script:Violations -gt 0) { 'Red' } else { 'Green' })
Write-Host ("Advisories             : {0}" -f $script:Advisories) -ForegroundColor $(if ($script:Advisories -gt 0) { 'Yellow' } else { 'Green' })
Write-Host ("File-name quotes passed: {0}" -f $script:FileNamePasses) -ForegroundColor DarkGray

if ($script:RuleCounts.Count -gt 0) {
    Write-Host 'By rule:' -ForegroundColor Cyan
    foreach ($key in ($script:RuleCounts.Keys | Sort-Object)) {
        $parts = $key.Split('|')
        Write-Host ("  {0,-12} {1,-30} {2}" -f $parts[0], $parts[1], $script:RuleCounts[$key])
    }
}

if ($script:Errors.Count -gt 0) {
    Write-Host 'Notes (not failures):' -ForegroundColor Yellow
    foreach ($e in $script:Errors) { Write-Host ("  " + $e) -ForegroundColor Yellow }
}

if ($script:Violations -eq 0) {
    Write-Host 'SPOKEN_LABELS_CHECK: CLEAN (no violations found)' -ForegroundColor Green
}
else {
    Write-Host ("SPOKEN_LABELS_CHECK: {0} violation(s) found" -f $script:Violations) -ForegroundColor Red
}
Write-Host 'No files were modified.' -ForegroundColor DarkGray
Write-Host '-------------------------------------------------------------' -ForegroundColor Cyan

# Report-only by default so the weekly audit can add a finding without failing.
# A build gate passes -FailOnViolation to turn the count into an exit code.
if ($FailOnViolation -and $script:Violations -gt 0) { exit 1 }
exit 0

