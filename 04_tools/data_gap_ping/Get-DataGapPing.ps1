#requires -Version 5.1
<#
.SYNOPSIS
    Data gap ping - tells Jerome which source-data gaps he personally still owes.

.DESCRIPTION
    READ-ONLY command line tool. It parses the markdown table(s) in
    01_data\00_derived\_data_integrity_open_issues.md and reports every open gap
    grouped by action owner, with Jerome's own items listed first.

    The source markdown file is the single source of truth: rows added there
    show up here automatically, rows removed there disappear. Nothing is
    hardcoded and this script never writes to disk - no cache, no log, no state
    file, no scheduled task.

    A table counts as an "open gaps" table when its header row has an ID column
    AND an Action owner column. Other tables in the same file (closed issues,
    out-of-scope markets, feed staleness) are ignored by design.

    It fails loudly instead of reporting nothing: exit 2 if the table format
    changed (missing ID / Action owner column, row cell count mismatch, escaped
    pipe), exit 3 if no gap row could be found at all.

.USAGE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\Get-DataGapPing.ps1               # all gaps, grouped by owner
    powershell -NoProfile -ExecutionPolicy Bypass -File .\Get-DataGapPing.ps1 -WhatIOwe     # only what Jerome owes
    powershell -NoProfile -ExecutionPolicy Bypass -File .\Get-DataGapPing.ps1 -Quiet        # scheduled run: silent when nothing owed
    powershell -NoProfile -ExecutionPolicy Bypass -File .\Get-DataGapPing.ps1 -Json         # machine-readable for a dashboard
    Or just double-click RUN_Data_Gap_Ping.cmd

.PARAMETER WhatIOwe
    List only the gaps whose Action owner column mentions Jerome (case-insensitive).

.PARAMETER Quiet
    Scheduled-task mode. Prints one short reminder line when Jerome owes
    something, prints nothing at all and still exits 0 when he does not.

.PARAMETER Json
    Emit a single JSON object (counts + parsed gaps) on stdout and nothing else.

.PARAMETER Path
    Override the source markdown file. Default is the open-issues file above.

.PARAMETER Help
    Print usage and exit.

.OUTPUTS
    Plain text, or JSON with -Json.

.NOTES
    Exit codes: 0 ok / 1 source file missing or unreadable / 2 source format
    changed / 3 no gap rows found / 4 bad command line.
#>
[CmdletBinding()]
param(
    [switch]$WhatIOwe,
    [switch]$Quiet,
    [switch]$Json,
    [string]$Path = '',
    [switch]$Help
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

$script:AsciiMap = New-Object 'System.Collections.Generic.Dictionary[int,string]'
$script:AsciiMap.Add(0x2013, '-')     # en dash
$script:AsciiMap.Add(0x2014, '-')     # em dash
$script:AsciiMap.Add(0x2018, "'")
$script:AsciiMap.Add(0x2019, "'")
$script:AsciiMap.Add(0x201C, '"')
$script:AsciiMap.Add(0x201D, '"')
$script:AsciiMap.Add(0x2026, '...')
$script:AsciiMap.Add(0x20AC, 'EUR ')  # euro
$script:AsciiMap.Add(0x00A3, 'GBP ')  # pound
$script:AsciiMap.Add(0x2192, '->')
$script:AsciiMap.Add(0x2248, '~')
$script:AsciiMap.Add(0x00A0, ' ')     # non-breaking space

function ConvertTo-AsciiText {
    param([string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return '' }
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in $Text.ToCharArray()) {
        $code = [int]$ch
        if ($code -lt 128) {
            [void]$sb.Append($ch)
        } elseif ($script:AsciiMap.ContainsKey($code)) {
            [void]$sb.Append($script:AsciiMap[$code])
        } else {
            [void]$sb.Append('?')
        }
    }
    return $sb.ToString()
}

function ConvertFrom-MarkdownInline {
    param([string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return '' }
    $t = $Text
    $t = $t -replace '!\[([^\]]*)\]\(([^)]+)\)', '$1 ($2)'
    $t = $t -replace '\[([^\]]+)\]\(([^)]+)\)', '$1 ($2)'
    $t = $t -replace '\*\*', ''
    $t = $t -replace '`', ''
    $t = $t -replace '\s+', ' '
    return $t.Trim()
}

function Get-ShortText {
    param([string]$Text, [int]$Max = 170)
    $t = ($Text -replace '\s+', ' ').Trim()
    if ($t.Length -le $Max) { return $t }
    $cut = $t.Substring(0, $Max)
    $sp = $cut.LastIndexOf(' ')
    if ($sp -gt 40) { $cut = $cut.Substring(0, $sp) }
    return ($cut.TrimEnd(' ', '.', ',', ';', ':') + ' ...')
}

function Stop-WithError {
    param([string]$Message, [int]$Code)
    [Console]::Error.WriteLine('DATA GAP PING ERROR: ' + $Message)
    exit $Code
}

function Get-UsageText {
    return @(
        'Data gap ping - read-only. Lists the open source-data gaps from:',
        '  01_data\00_derived\_data_integrity_open_issues.md',
        '',
        '  Get-DataGapPing.ps1                 all open gaps, grouped by action owner',
        '  Get-DataGapPing.ps1 -WhatIOwe       only the gaps waiting on Jerome',
        '  Get-DataGapPing.ps1 -Quiet          scheduled mode: silent when nothing is owed',
        '  Get-DataGapPing.ps1 -Json           JSON output for a dashboard or task',
        '  Get-DataGapPing.ps1 -Path <file>    use a different source markdown file',
        '',
        'Preview only (-WhatIf) is not supported: the tool never changes anything.',
        'Exit codes: 0 ok / 1 source missing / 2 format changed / 3 no gap rows / 4 bad arguments.'
    )
}

function Split-MarkdownRow {
    param([string]$Line)
    $t = $Line.Trim()
    if ($t.StartsWith('|')) { $t = $t.Substring(1) }
    if ($t.EndsWith('|')) { $t = $t.Substring(0, $t.Length - 1) }
    return ($t -split '\|')
}

function Test-MarkdownSeparator {
    param([string[]]$Cells)
    if ($Cells.Count -eq 0) { return $false }
    foreach ($c in $Cells) {
        if ($c.Trim() -notmatch '^:?-{2,}:?$') { return $false }
    }
    return $true
}

function Get-SourceFiles {
    param([string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return @() }
    $rx = [regex]'[A-Za-z0-9_][A-Za-z0-9_\\/.\-]*\.(csv|xlsx|parquet|json|py|ps1|md|html)'
    $hits = @()
    foreach ($m in $rx.Matches($Text)) {
        $v = $m.Value
        if ($hits -notcontains $v) { $hits += $v }
    }
    # Prefer real paths (contain a folder separator) over bare file names.
    $paths = @($hits | Where-Object { $_ -match '[\\/]' })
    $bare = @($hits | Where-Object { $_ -notmatch '[\\/]' })
    $all = @($paths + $bare)
    if ($all.Count -gt 3) { $all = $all[0..2] }
    return $all
}

function Get-OwnerGroupKey {
    param([string]$Owner)
    $o = ($Owner -replace '\s+', ' ').Trim()
    if ($o -match '(?i)jerome') { return 'Jerome (you)' }
    # "UIO model owner - V20 rebuild per ..." groups under the owner, not the task.
    $seg = ($o -split ' - ')[0].Trim()
    if ($seg -eq '') { $seg = $o }
    if ($seg.Length -gt 70) { $seg = $seg.Substring(0, 67).TrimEnd() + '...' }
    return $seg
}

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

if ($Help) {
    Get-UsageText | ForEach-Object { [Console]::Out.WriteLine($_) }
    exit 0
}
if ($Quiet -and $Json) {
    Stop-WithError '-Quiet and -Json cannot be combined (a scheduled JSON run should just be -Json).' 4
}
if ($Quiet -and $WhatIOwe) {
    # Harmless: quiet mode already reports only what Jerome owes.
    $WhatIOwe = $false
}

# ---------------------------------------------------------------------------
# Resolve and read the source file (read-only)
# ---------------------------------------------------------------------------

$scriptDir = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptDir)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
}
if ([string]::IsNullOrWhiteSpace($Path)) {
    $Path = Join-Path $scriptDir '..\..\01_data\00_derived\_data_integrity_open_issues.md'
}

$resolved = $null
try {
    $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
} catch {
    Stop-WithError ('Source file not found: ' + $Path) 1
}
if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
    Stop-WithError ('Source is not a file: ' + $resolved) 1
}

$lines = $null
try {
    $lines = [System.IO.File]::ReadAllLines($resolved, [System.Text.Encoding]::UTF8)
} catch {
    Stop-WithError ('Could not read ' + $resolved + ' - ' + $_.Exception.Message) 1
}

$sourceHash = ''
$sourceWrite = ''
try {
    $sourceHash = (Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash
    $sourceWrite = (Get-Item -LiteralPath $resolved).LastWriteTime.ToString('s')
} catch {
    # Hash is metadata only; never fail the ping because of it.
    $sourceHash = ''
    $sourceWrite = ''
}

# ---------------------------------------------------------------------------
# Parse the markdown pipe tables
# ---------------------------------------------------------------------------

$parseErrors = New-Object System.Collections.Generic.List[string]
$gaps = New-Object System.Collections.Generic.List[object]

$section = ''
$inTable = $false
$isGapTable = $false
$headerCells = @()
$colId = -1
$colIssue = -1
$colPeriod = -1
$colImpact = -1
$colOwner = -1
$gapTableCount = 0
$nonGapTableCount = 0
$skippedOtherRows = 0
$rowNumber = 0

foreach ($line in $lines) {
    $rowNumber++
    $trimmed = $line.Trim()

    if ($trimmed -eq '') { $inTable = $false; $isGapTable = $false; continue }

    if ($trimmed.StartsWith('#')) {
        $section = $trimmed.TrimStart('#').Trim()
        $inTable = $false
        $isGapTable = $false
        continue
    }

    if (-not $trimmed.StartsWith('|')) {
        $inTable = $false
        $isGapTable = $false
        continue
    }

    if ($trimmed.Contains('\|')) {
        $parseErrors.Add(('Line ' + $rowNumber + ": escaped pipe ('\|') inside a table cell - cannot split safely."))
        continue
    }

    $cells = @(Split-MarkdownRow -Line $trimmed)

    if (-not $inTable) {
        # First pipe row of a table is its header row.
        $inTable = $true
        $headerCells = $cells
        $colId = -1; $colIssue = -1; $colPeriod = -1; $colImpact = -1; $colOwner = -1
        for ($c = 0; $c -lt $cells.Count; $c++) {
            $name = (ConvertFrom-MarkdownInline -Text $cells[$c])
            if ($name -match '^(?i)id$') { $colId = $c }
            elseif ($name -match '(?i)action\s*owner') { $colOwner = $c }
            elseif ($name -match '^(?i)issue$') { $colIssue = $c }
            elseif ($name -match '^(?i)period$') { $colPeriod = $c }
            elseif ($name -match '(?i)^impact$') { $colImpact = $c }
        }
        if ($colOwner -ge 0 -and $colId -lt 0) {
            $parseErrors.Add(('Line ' + $rowNumber + ': table has an Action owner column but no ID column.'))
        }
        $isGapTable = ($colOwner -ge 0 -and $colId -ge 0 -and $colIssue -ge 0)
        if ($isGapTable) { $gapTableCount++ } else { $nonGapTableCount++ }
        continue
    }

    if (Test-MarkdownSeparator -Cells $cells) { continue }

    if (-not $isGapTable) {
        $skippedOtherRows++
        continue
    }

    if ($cells.Count -ne $headerCells.Count) {
        $parseErrors.Add(('Line ' + $rowNumber + ': row has ' + $cells.Count + ' cells but the header has ' + $headerCells.Count + '.'))
        continue
    }

    $id = ConvertFrom-MarkdownInline -Text $cells[$colId]
    if ([string]::IsNullOrWhiteSpace($id)) {
        $parseErrors.Add(('Line ' + $rowNumber + ': empty gap ID.'))
        continue
    }

    $issue = ConvertTo-AsciiText (ConvertFrom-MarkdownInline -Text $cells[$colIssue])
    $period = ''
    if ($colPeriod -ge 0) { $period = ConvertTo-AsciiText (ConvertFrom-MarkdownInline -Text $cells[$colPeriod]) }
    $impact = ''
    if ($colImpact -ge 0) { $impact = ConvertTo-AsciiText (ConvertFrom-MarkdownInline -Text $cells[$colImpact]) }
    $owner = ConvertTo-AsciiText (ConvertFrom-MarkdownInline -Text $cells[$colOwner])
    if ([string]::IsNullOrWhiteSpace($owner)) {
        $parseErrors.Add(('Line ' + $rowNumber + ': gap ' + $id + ' has an empty Action owner.'))
        continue
    }

    $owed = ($owner -match '(?i)jerome')
    $gaps.Add([pscustomobject]@{
        Id             = $id
        Section        = $section
        Summary        = Get-ShortText -Text $issue -Max 300
        Period         = Get-ShortText -Text $period -Max 120
        Blocked        = Get-ShortText -Text $impact -Max 300
        ActionOwner    = $owner
        OwnerGroup     = Get-OwnerGroupKey -Owner $owner
        OwedByJerome   = $owed
        MentionsJerome = ($owed -or ($issue -match '(?i)jerome'))
        SourceFiles    = @(Get-SourceFiles -Text ($issue + ' ' + $owner))
        LineNumber     = $rowNumber
    })
}

if ($parseErrors.Count -gt 0) {
    [Console]::Error.WriteLine('DATA GAP PING ERROR: source table format changed - refusing to report a partial list.')
    [Console]::Error.WriteLine('File: ' + $resolved)
    foreach ($e in $parseErrors) { [Console]::Error.WriteLine('  - ' + $e) }
    [Console]::Error.WriteLine('Fix the markdown table (or point -Path at the right file) and run again.')
    exit 2
}

if ($gaps.Count -eq 0) {
    if ($Quiet -and $gapTableCount -gt 0) {
        # Valid gap table, no open rows: genuinely nothing owed, stay silent.
        exit 0
    }
    Stop-WithError ('No open gap rows found in ' + $resolved + ' (' + $gapTableCount + ' gap table(s) matched). Check that the file still has an ID + Action owner table.') 3
}

$sorted = @($gaps | Sort-Object -Property @{ Expression = { if ($_.OwedByJerome) { 0 } else { 1 } } }, OwnerGroup, Id)
$owed = @($gaps | Where-Object { $_.OwedByJerome } | Sort-Object Id)
$stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm')

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

if ($Json) {
    $byOwner = [ordered]@{}
    foreach ($g in $sorted) {
        if ($byOwner.Contains($g.OwnerGroup)) { $byOwner[$g.OwnerGroup] = [int]$byOwner[$g.OwnerGroup] + 1 }
        else { $byOwner[$g.OwnerGroup] = 1 }
    }
    $gapJson = @()
    foreach ($g in $sorted) {
        $gapJson += [ordered]@{
            id               = $g.Id
            section          = $g.Section
            summary          = $g.Summary
            period           = $g.Period
            blocked          = $g.Blocked
            action_owner     = $g.ActionOwner
            owner_group      = $g.OwnerGroup
            owed_by_jerome   = [bool]$g.OwedByJerome
            mentions_jerome  = [bool]$g.MentionsJerome
            source_files     = @($g.SourceFiles)
            source_line      = [int]$g.LineNumber
        }
    }
    $doc = [ordered]@{
        tool             = 'data_gap_ping'
        generated_at     = (Get-Date).ToString('o')
        source_file      = $resolved
        source_sha256    = $sourceHash
        source_last_write= $sourceWrite
        gap_tables       = $gapTableCount
        non_gap_tables   = $nonGapTableCount
        ignored_rows     = $skippedOtherRows
        counts           = [ordered]@{
            total           = $gaps.Count
            owed_by_jerome  = $owed.Count
            by_owner        = $byOwner
        }
        gaps             = $gapJson
        glossary         = [ordered]@{
            UIO = 'vehicles in service'
            GPS = 'spend per unit'
            UTI = 'Israel'
            ITUK = 'United Kingdom'
            ISZE = 'Isuzu Motors Europe'
        }
    }
    $jsonText = $doc | ConvertTo-Json -Depth 8
    [Console]::Out.WriteLine($jsonText)
    exit 0
}

if ($Quiet) {
    if ($owed.Count -eq 0) { exit 0 }
    $ids = ($owed | ForEach-Object { $_.Id }) -join ', '
    [Console]::Out.WriteLine('[' + $stamp + '] Data gap ping: ' + $owed.Count + ' open data gap(s) need you - ' + $ids + '. Run RUN_Data_Gap_Ping.cmd -WhatIOwe for detail.')
    exit 0
}

function Write-Row {
    param($Gap, [bool]$IsOwed)
    $label = 'Action  : '
    if ($IsOwed) { $label = 'You owe : ' }
    [Console]::Out.WriteLine('  [' + $Gap.Id + '] ' + (Get-ShortText -Text $Gap.Summary -Max 170))
    if ($Gap.Period -ne '')    { [Console]::Out.WriteLine('      Period  : ' + $Gap.Period) }
    if ($Gap.Blocked -ne '')   { [Console]::Out.WriteLine('      Blocked : ' + (Get-ShortText -Text $Gap.Blocked -Max 170)) }
    [Console]::Out.WriteLine('      ' + $label + $Gap.ActionOwner)
    foreach ($f in $Gap.SourceFiles) { [Console]::Out.WriteLine('      File    : ' + $f) }
    [Console]::Out.WriteLine('')
}

if ($WhatIOwe) {
    [Console]::Out.WriteLine('ISZE DATA GAP PING - WHAT YOU OWE        ' + $stamp)
    [Console]::Out.WriteLine('Source (read-only): ' + $resolved)
    [Console]::Out.WriteLine('')
    if ($owed.Count -eq 0) {
        [Console]::Out.WriteLine('Nothing owed right now - no open gap row names you as Action owner.')
        [Console]::Out.WriteLine('')
        exit 0
    }
    [Console]::Out.WriteLine($owed.Count.ToString() + ' open gap(s) are waiting on you:')
    [Console]::Out.WriteLine('')
    $n = 0
    foreach ($g in $owed) {
        $n++
        [Console]::Out.WriteLine(' ' + $n + ') [' + $g.Id + '] ' + (Get-ShortText -Text $g.Summary -Max 170))
        [Console]::Out.WriteLine('    You owe : ' + $g.ActionOwner)
        if ($g.Blocked -ne '') { [Console]::Out.WriteLine('    Blocked : ' + (Get-ShortText -Text $g.Blocked -Max 170)) }
        if ($g.Period -ne '')  { [Console]::Out.WriteLine('    Period  : ' + $g.Period) }
        foreach ($f in $g.SourceFiles) { [Console]::Out.WriteLine('    File    : ' + $f) }
        [Console]::Out.WriteLine('')
    }
    [Console]::Out.WriteLine('Nothing else in the source file is owned by you.')
    exit 0
}

[Console]::Out.WriteLine('================================================================================')
[Console]::Out.WriteLine(' ISZE DATA GAP PING                       ' + $stamp)
[Console]::Out.WriteLine(' Source (read-only) : ' + $resolved)
[Console]::Out.WriteLine(' Open gaps parsed   : ' + $gaps.Count + '   |   Owed by Jerome: ' + $owed.Count)
[Console]::Out.WriteLine(' Other tables in the same file, not open gaps: ' + $nonGapTableCount +
    '  (' + $skippedOtherRows + ' row(s) ignored: closed issues, out-of-scope markets, feed staleness)')
[Console]::Out.WriteLine('================================================================================')
[Console]::Out.WriteLine('')

foreach ($grp in ($sorted | Group-Object -Property OwnerGroup)) {
    $isOwedGroup = [bool]($grp.Group[0].OwedByJerome)
    $banner = ' OWNER: ' + $grp.Name + '  --  ' + $grp.Count + ' gap(s)'
    if ($isOwedGroup) { $banner += '   *** YOUR ACTION ***' }
    [Console]::Out.WriteLine('--------------------------------------------------------------------------------')
    [Console]::Out.WriteLine($banner)
    [Console]::Out.WriteLine('--------------------------------------------------------------------------------')
    [Console]::Out.WriteLine('')
    foreach ($g in ($grp.Group | Sort-Object Id)) { Write-Row -Gap $g -IsOwed $isOwedGroup }
}

[Console]::Out.WriteLine('Glossary: UIO = vehicles in service; GPS = spend per unit; UTI = Israel; ITUK = UK.')
[Console]::Out.WriteLine('Only the open-gap table named above is listed (' + $gapTableCount + ' table(s)); ' + $nonGapTableCount + ' other table(s) in the file are not open gaps.')
[Console]::Out.WriteLine('Read-only tool: it writes nothing. Exit code 0 = list produced.')
exit 0
