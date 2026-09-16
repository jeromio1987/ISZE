# =============================================================================
# ISZE decision-drift check (read-only)
#
# Companion to isze_live_state_audit.ps1. It answers one question the audit does
# not: does a row in ISZE_ROADMAP.md section 2 "Waiting on Jerome" still read as
# waiting, while DECISIONS.md already carries a dated entry on the same subject?
#
# That combination is the failure this check exists for. A decision was taken,
# the decision log recorded it, and the queue was never updated - so the item
# keeps coming back as an open question and every reader spends time on it
# again.
#
# Contract:
#   - Read-only. Never writes to ISZE_ROADMAP.md or DECISIONS.md.
#   - Fail-soft. Any parse failure is reported as a note. Always exits 0.
#   - Additive. Called from run_live_state_audit.cmd after the audit. It cannot
#     change the audit's findings list, its order, or its exit code.
#
# How a row is matched:
#   1. Read the roadmap's "Last updated" date and the rows of section 2.
#   2. Keep only DECISIONS.md entries dated after that date.
#   3. For each section 2 row, take the meaningful words of its Decision cell
#      and count how many appear in a kept entry (trailing "s" ignored).
#      A row is reported when at least 2 words match, or 1 when the row yields
#      only one meaningful word.
#   The matched words are printed, so a weak match is visible and cheap to
#   dismiss.
#
# Usage:
#   .\check_decision_drift.ps1                    # print to console
#   .\check_decision_drift.ps1 -AppendToBrief     # also append to today's brief
#
# ASCII only: Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI, so any
# non-ASCII character here becomes a parse error.
# =============================================================================

[CmdletBinding()]
param(
  [string]$IszeRoot,
  [switch]$AppendToBrief
)

$ErrorActionPreference = 'Stop'

$notes = [System.Collections.Generic.List[string]]::new()
$drift = [System.Collections.Generic.List[object]]::new()
$cutoffText = ''

# Words that carry no subject meaning in a waiting-list row. Nothing here is
# specific to any one project.
$SkipWords = @(
  'about', 'after', 'again', 'also', 'auto', 'before', 'being', 'book',
  'both', 'been', 'could', 'does', 'done', 'down', 'each', 'first', 'for',
  'from', 'given', 'had', 'has', 'have', 'into', 'keep', 'last', 'less',
  'level', 'may', 'means', 'might', 'more', 'most', 'much', 'must', 'need',
  'needs', 'never', 'next', 'only', 'open', 'order', 'other', 'others',
  'out', 'over', 'per', 'point', 'same', 'should', 'sign', 'some', 'step',
  'still', 'such', 'table', 'takes', 'than', 'that', 'the', 'their', 'them',
  'then', 'there', 'these', 'they', 'this', 'those', 'under', 'using',
  'very', 'via', 'wait', 'was', 'were', 'what', 'when', 'where', 'which',
  'while', 'who', 'with', 'would'
)

function Get-SubjectWords([string]$Text) {
  $clean = $Text -replace '[`*_\[\]\(\)]', ' '
  $words = [System.Collections.Generic.List[string]]::new()
  foreach ($m in [regex]::Matches($clean.ToLowerInvariant(), '[a-z0-9][a-z0-9.%\/-]*')) {
    $w = $m.Value.Trim('.', '-', '/', '%')
    if ($w.Length -lt 2) { continue }
    if ($SkipWords -contains $w) { continue }
    if (-not $words.Contains($w)) { $words.Add($w) }
  }
  return $words
}

try {
  if (-not $IszeRoot) {
    $IszeRoot = if ($env:ISZE_ROOT) { $env:ISZE_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
  }

  $RoadmapPath = Join-Path $IszeRoot '00_docs\ISZE_ROADMAP.md'
  $DecisionsPath = Join-Path $IszeRoot 'DECISIONS.md'

  if (-not (Test-Path $RoadmapPath)) {
    $notes.Add('ISZE_ROADMAP.md not found - decision drift not checked.')
  } elseif (-not (Test-Path $DecisionsPath)) {
    $notes.Add('DECISIONS.md not found - decision drift not checked.')
  } else {

    # --- Source 1: the roadmap's own last-update date ----------------------
    $RoadmapText = Get-Content $RoadmapPath -Raw -Encoding UTF8
    $cutoffMatch = [regex]::Match($RoadmapText, '\*\*Last updated:\*\*\s*(\d{4}-\d{2}-\d{2})')
    $cutoff = $null
    if ($cutoffMatch.Success) {
      $cutoffText = $cutoffMatch.Groups[1].Value
      $cutoff = [datetime]::ParseExact($cutoffText, 'yyyy-MM-dd', $null)
    } else {
      $notes.Add('ISZE_ROADMAP.md has no "Last updated" date - decision drift not checked.')
    }

    # --- Source 2: the section 2 rows --------------------------------------
    $sectionText = ''
    $sectionMatch = [regex]::Match($RoadmapText, '(?s)##\s*2\.\s*Waiting on Jerome.*?(?=\r?\n---)')
    if ($sectionMatch.Success) { $sectionText = $sectionMatch.Value }

    $rows = [System.Collections.Generic.List[object]]::new()
    if (-not $sectionText) {
      $notes.Add('ISZE_ROADMAP.md section 2 "Waiting on Jerome" not found - decision drift not checked.')
    } else {
      foreach ($line in ($sectionText -split "`n")) {
        if ($line -notmatch '^\s*\|') { continue }
        $cells = @($line.Trim().Trim('|') -split '\|' | ForEach-Object { $_.Trim() })
        if ($cells.Count -lt 2) { continue }
        $ref = $cells[0].Trim('`', ' ')
        $subject = $cells[1]
        if ($ref -eq '' -or $ref -match '^-+$' -or $ref -eq 'Ref') { continue }
        if ($subject -eq '') { continue }
        $rows.Add([pscustomobject]@{ ref = $ref; subject = $subject })
      }
      if ($rows.Count -eq 0) {
        $notes.Add('No rows parsed out of ISZE_ROADMAP.md section 2 - decision drift not checked.')
      }
    }

    # --- Source 3: DECISIONS.md entries dated after the roadmap update ------
    if ($cutoff -ne $null -and $rows.Count -gt 0) {
      $DecisionsText = Get-Content $DecisionsPath -Raw -Encoding UTF8
      $heads = @([regex]::Matches($DecisionsText, '(?m)^##\s+(\d{4}-\d{2}-\d{2})([^\r\n]*)'))
      $entries = [System.Collections.Generic.List[object]]::new()

      for ($i = 0; $i -lt $heads.Count; $i++) {
        $dateText = $heads[$i].Groups[1].Value
        $titleRaw = $heads[$i].Groups[2].Value.Trim(' ', '-', [char]0x2014, [char]0x2013)
        try { $entryDate = [datetime]::ParseExact($dateText, 'yyyy-MM-dd', $null) } catch { continue }
        if ($entryDate -le $cutoff) { continue }

        $start = $heads[$i].Index
        $end = if ($i + 1 -lt $heads.Count) { $heads[$i + 1].Index } else { $DecisionsText.Length }
        $body = $DecisionsText.Substring($start, $end - $start).ToLowerInvariant()
        $entries.Add([pscustomobject]@{ date = $dateText; title = $titleRaw; body = $body })
      }

      if ($entries.Count -eq 0) {
        $notes.Add('No DECISIONS.md entry is dated after the roadmap last update (' + $cutoffText + ') - nothing to compare.')
      }

      foreach ($row in $rows) {
        $words = Get-SubjectWords $row.subject
        if ($words.Count -eq 0) { continue }
        $needed = [math]::Min(2, $words.Count)

        foreach ($entry in $entries) {
          $hits = [System.Collections.Generic.List[string]]::new()
          foreach ($w in $words) {
            $probe = if ($w.Length -gt 4 -and $w.EndsWith('s')) { $w.Substring(0, $w.Length - 1) } else { $w }
            if ($entry.body.Contains($probe)) { $hits.Add($w) }
          }
          if ($hits.Count -ge $needed) {
            $drift.Add([pscustomobject]@{
              ref     = $row.ref
              subject = $row.subject
              date    = $entry.date
              title   = $entry.title
              words   = ($hits -join ', ')
            })
          }
        }
      }
    }
  }
} catch {
  $notes.Add('decision-drift check failed: ' + $_.Exception.Message)
}

# --- Render ----------------------------------------------------------------
$today = Get-Date -Format 'yyyy-MM-dd'
$section = [System.Collections.Generic.List[string]]::new()
$section.Add('')
$section.Add('---')
$section.Add('')
$section.Add('## Decision drift (read-only)')
$section.Add('')
$section.Add('Compares this roadmap''s section 2 "Waiting on Jerome" against')
$section.Add('DECISIONS.md entries dated after the roadmap''s own last-update line.')
$section.Add('A hit means the item may already be decided but still reads as waiting.')
$section.Add('It is a prompt to check the three-place rule, not a decision.')
$section.Add('')

if ($cutoffText) { $section.Add('Roadmap last update: ' + $cutoffText + '.') }
if ($drift.Count -gt 0) {
  foreach ($d in $drift) {
    $title = $d.title
    if ($title.Length -gt 90) { $title = $title.Substring(0, 87) + '...' }
    $line = '- **' + $d.ref + '** ' + $d.subject + ' - may already be decided: DECISIONS.md ' + $d.date
    if ($title) { $line = $line + ' ("' + $title + '")' }
    $line = $line + ' mentions ' + $d.words + '. It still reads as waiting - check before answering it again.'
    $section.Add($line)
  }
}
foreach ($n in $notes) { $section.Add('- ' + $n) }
if ($drift.Count -eq 0 -and $notes.Count -eq 0) {
  $section.Add('- No drift found. No section 2 item shares a subject with a newer decision entry.')
}
$section.Add('')
$section.Add('Generated by ``04_tools\workspace\check_decision_drift.ps1``.')

foreach ($line in $section) { Write-Host $line }

if ($AppendToBrief) {
  try {
    $brief = Join-Path (Join-Path $IszeRoot '05_memory\briefs') ('automation_drift_' + $today + '.md')
    if (-not (Test-Path $brief)) {
      Write-Host ('Brief not found, nothing appended: ' + $brief) -ForegroundColor DarkGray
    } elseif ((Get-Content $brief -Raw -Encoding UTF8).Contains('## Decision drift')) {
      Write-Host ('Decision-drift section already present, not appended twice: ' + $brief) -ForegroundColor DarkGray
    } else {
      Add-Content -Path $brief -Value ($section -join "`r`n") -Encoding UTF8
      Write-Host ('Appended to: ' + $brief) -ForegroundColor DarkGray
    }
  } catch {
    Write-Host ('Could not append to the brief: ' + $_.Exception.Message) -ForegroundColor DarkGray
  }
}

exit 0
