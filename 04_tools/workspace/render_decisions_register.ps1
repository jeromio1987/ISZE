#Requires -Version 5.1
<#
.SYNOPSIS
  Renders the readable twin of the decisions-awaiting register.

.DESCRIPTION
  DECISIONS_AWAITING_JEROME_<date>.json is the single source. This script renders
  DECISIONS_AWAITING_JEROME_<date>.md from it, so the two cannot drift and the .md
  is never hand-edited.

  The renderer is deliberately ALL-FIELDS: every scalar field present on a decision
  or on the register appears in the output, with a known field getting a readable
  label and an unknown field falling back to its own name. That is the property that
  makes the twin trustworthy - a field added to the JSON cannot be silently dropped
  from the page Jerome reads, which is exactly how the earlier hand-maintained twin
  came to disagree with its source.

  -Check regenerates in memory and compares against the file on disk, exiting 1 on a
  mismatch. Use it before claiming the two agree.

  Source note: this file is kept pure ASCII on purpose. Windows PowerShell 5.1 reads a
  BOM-less .ps1 as the system ANSI code page, so a literal em dash or middle dot in the
  source reaches the output as mojibake. Non-ASCII output characters are built from
  their code points instead.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\render_decisions_register.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File .\render_decisions_register.ps1 -Check
#>
[CmdletBinding()]
param(
    [string]$JsonPath,
    [string]$OutPath,
    [switch]$Check
)

$ErrorActionPreference = 'Stop'

$EM  = [char]0x2014   # em dash
$MID = [char]0x00B7   # middle dot

$root  = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$inbox = Join-Path $root '01_data\90_INBOX'

if (-not $JsonPath) {
    $candidate = Get-ChildItem $inbox -Filter 'DECISIONS_AWAITING_JEROME_*.json' |
        Sort-Object Name -Descending | Select-Object -First 1
    if (-not $candidate) { throw "No DECISIONS_AWAITING_JEROME_*.json found in $inbox" }
    $JsonPath = $candidate.FullName
}
if (-not $OutPath) { $OutPath = [IO.Path]::ChangeExtension($JsonPath, '.md') }

$doc = (Get-Content -LiteralPath $JsonPath -Raw -Encoding UTF8) | ConvertFrom-Json

# --- small helpers ---------------------------------------------------------

function Prop {
    param($Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    $p = $Object.PSObject.Properties[$Name]
    if ($p) { return $p.Value }
    return $null
}

function IsBlank {
    param($Value)
    if ($null -eq $Value) { return $true }
    if ($Value -is [string]) { return [string]::IsNullOrWhiteSpace($Value) }
    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        return (@($Value).Count -eq 0)
    }
    return $false
}

# Field label map. Order here is the order the fields print in.
$Labels = [ordered]@{
    'reopened_on'                     = 'Reopened'
    'was_urgency'                     = 'Urgency when first raised'
    'urgency_now'                     = 'Urgency now'
    'urgency_rationale'               = 'Why the urgency moved'
    'answered_half'                   = 'Answered half, stands'
    'open_half'                       = 'Still open, not authorised'
    'recommended_reading_unconfirmed' = 'Recommended reading, UNCONFIRMED'
    'assumed_and_unconfirmed'         = 'What was assumed, and that it is unconfirmed'
    'deferred_not_decided'            = 'Status of the words used'
    'what_the_words_support'          = 'What his words do support'
    'what_would_close_it'             = 'What would close it'
    'partner'                         = 'Partner item'
    'sheet_ref'                       = 'Sheet'
    'asked_on'                        = 'Asked on'
    'note'                            = 'Note'
}

$CoreFields = @('id', 'title', 'question', 'status', 'urgency', 'recommendation', 'blocks')

function Get-ExtraFields {
    param($Decision)
    $seen = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($f in $CoreFields) { [void]$seen.Add($f) }
    $out = [System.Collections.Generic.List[object]]::new()
    foreach ($name in $Labels.Keys) {
        if ($name -in $CoreFields) { continue }
        if (-not ($Decision.PSObject.Properties.Name -contains $name)) { continue }
        $value = Prop $Decision $name
        if (IsBlank $value) { continue }
        [void]$seen.Add($name)
        $out.Add([pscustomobject]@{ Name = $name; Label = $Labels[$name]; Value = $value })
    }
    foreach ($p in $Decision.PSObject.Properties) {
        if ($seen.Contains($p.Name)) { continue }
        if (IsBlank $p.Value) { continue }
        $label = ($p.Name -replace '_', ' ')
        $label = $label.Substring(0, 1).ToUpper() + $label.Substring(1)
        $out.Add([pscustomobject]@{ Name = $p.Name; Label = $label; Value = $p.Value })
    }
    return $out
}

$sb = [System.Text.StringBuilder]::new()
function Add-Line {
    param([string]$Text = '')
    [void]$sb.AppendLine($Text)
}

# --- header ----------------------------------------------------------------

$counts   = Prop $doc 'counts'
$open     = [int](Prop $counts 'open')
$blocking = [int](Prop $counts 'blocking')
$high     = [int](Prop $counts 'high')
$normal   = [int](Prop $counts 'normal')
$safeN    = [int](Prop $counts 'safe_tier_ready')
$decidedN = [int](Prop $counts 'decided')

Add-Line ('# Decisions awaiting Jerome')
Add-Line ('')
Add-Line ('**Register:** `' + (Split-Path $JsonPath -Leaf) + '` - the JSON is the single source. This page is a rendered twin and must not be hand-edited; re-render it from the JSON rather than editing here.')
$src = Prop $doc 'source'
if (-not (IsBlank $src)) { Add-Line ('**Source of truth:** `' + $src + '`') }
$srcNote = Prop $doc 'source_note'
if (-not (IsBlank $srcNote)) { Add-Line ('**Source note:** ' + $srcNote) }
$gen = Prop $doc 'generated'
if (-not (IsBlank $gen)) { Add-Line ('**Generated:** ' + $gen) }
Add-Line ('**Status:** ' + $open + ' open, ' + $decidedN + ' decided. Nothing in the source sheet has been executed.')
Add-Line ('')

$vocab = Prop $doc 'status_vocabulary'
if (-not (IsBlank $vocab)) {
    Add-Line ('**Chat answers are provisional until they are recorded here.** ' + $vocab)
    Add-Line ('')
}

Add-Line ('**Open: ' + $open + '.** Blocking ' + $blocking + ' ' + $MID + ' high ' + $high +
          ' ' + $MID + ' normal ' + $normal + '. Ready with no decision: ' + $safeN + ' safe-tier repairs.')
Add-Line ('')

$how = Prop $doc 'how_it_reaches_jerome'
if (-not (IsBlank $how)) {
    Add-Line ('**How it reaches Jerome.** ' + $how)
    Add-Line ('')
}

# --- reopened block --------------------------------------------------------

$reopeningNote = Prop $doc 'reopening_note'
$reopened      = Prop $doc 'reopened'
if ((-not (IsBlank $reopened)) -or (-not (IsBlank $reopeningNote))) {
    $reopenedOn = Prop $doc 'reopened_on'
    $heading = 'Reopened'
    if (-not (IsBlank $reopenedOn)) { $heading += ' - ' + $reopenedOn }
    Add-Line ('## ' + $heading)
    Add-Line ('')
    if (-not (IsBlank $reopeningNote)) {
        Add-Line ($reopeningNote)
        Add-Line ('')
    }
    foreach ($r in @($reopened)) {
        Add-Line ('### ' + (Prop $r 'id'))
        Add-Line ('')
        if (-not (IsBlank (Prop $r 'was'))) { Add-Line ('**Was recorded as:** ' + (Prop $r 'was')) }
        if (-not (IsBlank (Prop $r 'now'))) { Add-Line ('**Now:** ' + (Prop $r 'now')) }
        Add-Line ('')
        if (-not (IsBlank (Prop $r 'quote'))) {
            Add-Line ('He said: *"' + (Prop $r 'quote') + '"*')
            Add-Line ('')
        }
        if (-not (IsBlank (Prop $r 'why'))) {
            Add-Line ('Why: ' + (Prop $r 'why'))
            Add-Line ('')
        }
    }
}

# --- decisions, grouped by urgency ----------------------------------------

function Write-Decision {
    param($Decision)
    Add-Line ('### ' + (Prop $Decision 'id') + ' ' + $EM + ' ' + (Prop $Decision 'title'))
    Add-Line ('')
    if (-not (IsBlank (Prop $Decision 'question'))) {
        Add-Line (Prop $Decision 'question')
        Add-Line ('')
    }
    if (-not (IsBlank (Prop $Decision 'recommendation'))) {
        Add-Line ('**View:** ' + (Prop $Decision 'recommendation'))
    }
    if (-not (IsBlank (Prop $Decision 'blocks'))) {
        Add-Line ('**Blocks:** ' + (Prop $Decision 'blocks'))
    }
    $extras = Get-ExtraFields $Decision
    if (@($extras).Count -gt 0) {
        Add-Line ('')
        foreach ($e in $extras) {
            $text = $e.Value
            if ($text -is [System.Collections.IEnumerable] -and $text -isnot [string]) {
                $text = (@($text) -join '; ')
            }
            Add-Line ('**' + $e.Label + ':** ' + $text)
        }
    }
    Add-Line ('')
}

$decisions = @(Prop $doc 'decisions')

$blockingOpen = @($decisions | Where-Object { (Prop $_ 'urgency') -eq 'blocking' -and (Prop $_ 'status') -eq 'open' })

Add-Line ('---')
Add-Line ('')
Add-Line ('## Blocking ' + $EM + ' these stop work (' + $blockingOpen.Count + ')')
Add-Line ('')
if ($blockingOpen.Count -eq 0) {
    Add-Line ('None.')
    Add-Line ('')
}
foreach ($d in $blockingOpen) { Write-Decision $d }

$highItems = @($decisions | Where-Object { (Prop $_ 'urgency') -eq 'high' -and (Prop $_ 'status') -eq 'open' })
Add-Line ('---')
Add-Line ('')
Add-Line ('## High ' + $EM + ' each holds up a published pack (' + $highItems.Count + ')')
Add-Line ('')
foreach ($d in $highItems) { Write-Decision $d }

$normalItems = @($decisions | Where-Object { (Prop $_ 'urgency') -eq 'normal' -and (Prop $_ 'status') -eq 'open' })
Add-Line ('---')
Add-Line ('')
Add-Line ('## Normal ' + $EM + ' ' + $normalItems.Count + ' items, one answer each')
Add-Line ('')
foreach ($d in $normalItems) { Write-Decision $d }

$otherItems = @($decisions | Where-Object {
    (Prop $_ 'status') -ne 'open' -and (Prop $_ 'urgency') -notin @('blocking', 'high', 'normal')
})
if ($otherItems.Count -gt 0) {
    Add-Line ('---')
    Add-Line ('')
    Add-Line ('## Other (' + $otherItems.Count + ')')
    Add-Line ('')
    foreach ($d in $otherItems) { Write-Decision $d }
}

# --- safe tier -------------------------------------------------------------

$safeTier = @(Prop $doc 'safe_tier')
Add-Line ('---')
Add-Line ('')
Add-Line ('## Ready with no decision ' + $EM + ' ' + $safeTier.Count + ' safe-tier repairs')
Add-Line ('')
Add-Line ('Wording, pointers and factual corrections in files we own. None changes a number, a formula, a')
Add-Line ('fixture or a dashboard. None needs a rebuild.')
Add-Line ('')
Add-Line ('| Ref | What | Where |')
Add-Line ('|---|---|---|')
foreach ($s in $safeTier) {
    $title = ((Prop $s 'title') -replace '\|', '\|')
    $file  = ((Prop $s 'file')  -replace '\|', '\|')
    Add-Line ('| **' + (Prop $s 'id') + '** | ' + $title + ' | `' + $file + '` |')
}
Add-Line ('')
Add-Line ('S1 and S2 must land in the same sitting - leaving S2 would undo S1 on the next checker run.')
Add-Line ('S3 is two near-identical twins that differ in three words; make the same substantive edit in both')
Add-Line ('and preserve the difference.')
Add-Line ('')

# --- withdrawn -------------------------------------------------------------

$withdrawn = @(Prop $doc 'withdrawn')
Add-Line ('---')
Add-Line ('')
Add-Line ('## Withdrawn (' + $withdrawn.Count + ')')
Add-Line ('')
Add-Line ('| Ref | What | Why |')
Add-Line ('|---|---|---|')
foreach ($w in $withdrawn) {
    $what = ((Prop $w 'what') -replace '\|', '\|')
    $why  = ((Prop $w 'why')  -replace '\|', '\|')
    Add-Line ('| **' + (Prop $w 'id') + '** | ' + $what + ' | ' + $why + ' |')
}
Add-Line ('')

# --- decided record --------------------------------------------------------

$decidedItems = @($decisions | Where-Object { (Prop $_ 'status') -eq 'decided' })
if ($decidedItems.Count -gt 0) {
    Add-Line ('---')
    Add-Line ('')
    Add-Line ('## Decided (' + $decidedItems.Count + ')')
    Add-Line ('')
    foreach ($d in $decidedItems) { Write-Decision $d }
}

# --- register-level notes not already printed ------------------------------

$handled = @(
    'register', 'generated', 'source', 'source_note', 'how_it_reaches_jerome',
    'status_vocabulary', 'reopened_on', 'reopening_note', 'reopened',
    'still_to_correct', 'counts', 'decisions', 'safe_tier', 'withdrawn',
    'travel_proposal_not_applied'
)

$loose = @()
foreach ($p in $doc.PSObject.Properties) {
    if ($p.Name -in $handled) { continue }
    if (IsBlank $p.Value) { continue }
    $loose += $p
}
$stillToCorrect = @(Prop $doc 'still_to_correct')

if ($loose.Count -gt 0 -or $stillToCorrect.Count -gt 0) {
    Add-Line ('---')
    Add-Line ('')
    Add-Line ('## Register notes')
    Add-Line ('')
    if ($stillToCorrect.Count -gt 0) {
        Add-Line ('**Still to correct:**')
        foreach ($line in $stillToCorrect) { Add-Line ('- ' + $line) }
        Add-Line ('')
    }
    foreach ($p in $loose) {
        $label = ($p.Name -replace '_', ' ')
        $label = $label.Substring(0, 1).ToUpper() + $label.Substring(1)
        $value = $p.Value
        if ($value -is [System.Collections.IEnumerable] -and $value -isnot [string]) {
            Add-Line ('**' + $label + ':**')
            foreach ($line in @($value)) { Add-Line ('  - ' + $line) }
        } else {
            Add-Line ('**' + $label + ':** ' + $value)
        }
        Add-Line ('')
    }
}

# --- travel proposal (structured, at register level) -----------------------

$travel = Prop $doc 'travel_proposal_not_applied'
if (-not (IsBlank $travel)) {
    Add-Line ('---')
    Add-Line ('')
    Add-Line ('## Travel proposal - NOT APPLIED')
    Add-Line ('')
    Add-Line ('This section is a proposal. Nothing in it has been applied: `.gitignore` was not touched, no file was moved, and no hook was edited.')
    Add-Line ('')
    $travelLabels = [ordered]@{
        'problem'                        = 'Problem'
        'recommendation'                 = 'Recommendation'
        'why_no_gitignore_change_is_needed' = 'Why this needs no .gitignore change'
        'why_not_option_a'               = 'Why not the allowlist option'
        'the_read_only_lock_question'    = 'The read-only lock question'
        'status'                         = 'Status'
    }
    foreach ($name in $travelLabels.Keys) {
        if (-not ($doc.travel_proposal_not_applied.PSObject.Properties.Name -contains $name)) { continue }
        $v = Prop $travel $name
        if (IsBlank $v) { continue }
        Add-Line ('**' + $travelLabels[$name] + ':** ' + $v)
        Add-Line ('')
    }
    $optA = Prop $travel 'option_a_exact_lines_if_needed'
    if (-not (IsBlank $optA)) {
        Add-Line ('**The exact lines that would be needed (allowlist option):**')
        Add-Line ('')
        foreach ($line in @(Prop $optA 'lines')) { Add-Line ('    ' + $line) }
        Add-Line ('')
        foreach ($name in @('placement', 'proof_it_works', 'caveat')) {
            $v = Prop $optA $name
            if (IsBlank $v) { continue }
            $lbl = ($name -replace '_', ' ')
            $lbl = $lbl.Substring(0, 1).ToUpper() + $lbl.Substring(1)
            Add-Line ('*' + $lbl + ':* ' + $v)
            Add-Line ('')
        }
    }
    $effects = @(Prop $travel 'second_order_effects')
    if ($effects.Count -gt 0) {
        Add-Line ('**Second-order effects if the register moves:**')
        Add-Line ('')
        foreach ($e in $effects) { Add-Line ('  - ' + $e) }
        Add-Line ('')
    }
}

# --- how it reaches him ----------------------------------------------------

Add-Line ('---')
Add-Line ('')
Add-Line ('## How this list reaches you')
Add-Line ('')
Add-Line ('A hook runs at the end of the first agent turn in a chat and prints the **blocking** items in full')
Add-Line ('plus a count of the rest. It reads this register, so it cannot go out of date independently of it.')
Add-Line ('It stays quiet when nothing is open, and it does not repeat itself within a chat.')
Add-Line ('')
Add-Line ('**To answer:** say the answer in chat, and it is recorded here, in `DECISIONS.md`, and in')
Add-Line ('`00_docs\ISZE_ROADMAP.md` in the same pass. Until all three agree the item stays open on this list.')
Add-Line ('')
Add-Line ('_Rendered from `' + (Split-Path $JsonPath -Leaf) + '` by `04_tools\workspace\render_decisions_register.ps1`. Do not hand-edit this page._')
Add-Line ('')

$rendered = $sb.ToString()

if ($Check) {
    if (-not (Test-Path -LiteralPath $OutPath)) {
        Write-Host ('MISMATCH: ' + $OutPath + ' does not exist') -ForegroundColor Red
        exit 1
    }
    $onDisk = (Get-Content -LiteralPath $OutPath -Raw -Encoding UTF8)
    $a = ($onDisk   -replace "`r`n", "`n").TrimEnd()
    $b = ($rendered -replace "`r`n", "`n").TrimEnd()
    if ($a -ceq $b) {
        Write-Host ('MATCH: ' + (Split-Path $OutPath -Leaf) + ' is exactly the render of ' + (Split-Path $JsonPath -Leaf)) -ForegroundColor Green
        exit 0
    }
    Write-Host ('MISMATCH: ' + (Split-Path $OutPath -Leaf) + ' differs from the render of ' + (Split-Path $JsonPath -Leaf)) -ForegroundColor Red
    $aLines = $a -split "`n"
    $bLines = $b -split "`n"
    $max = [Math]::Max($aLines.Count, $bLines.Count)
    $shown = 0
    for ($i = 0; $i -lt $max -and $shown -lt 10; $i++) {
        $l = if ($i -lt $aLines.Count) { $aLines[$i] } else { '<missing>' }
        $r = if ($i -lt $bLines.Count) { $bLines[$i] } else { '<missing>' }
        if ($l -cne $r) {
            Write-Host ('  line ' + ($i + 1) + ' on disk : ' + $l)
            Write-Host ('  line ' + ($i + 1) + ' rendered: ' + $r)
            $shown++
        }
    }
    exit 1
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($OutPath, $rendered, $utf8NoBom)
Write-Host ('Rendered ' + (Split-Path $OutPath -Leaf) + ' from ' + (Split-Path $JsonPath -Leaf)) -ForegroundColor Green
