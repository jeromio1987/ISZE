# =============================================================================
# ISZE live-state auditor
#
# Compares three sources that are supposed to agree and never do:
#
#   1. 00_docs\AUTOMATION_REGISTER.md   what we say runs
#   2. Windows Task Scheduler           what actually runs
#   3. FACTS.md vs pipeline             what the numbers say
#
# Output is a numbered "waiting on Jerome" list, newest first, written to
# 05_memory\briefs\automation_drift_<date>.md and echoed to the console.
#
# This is a report, not a gate. It never changes a task, a register row or a
# FACTS value - drift always needs a human decision about which side is right.
#
# Exit 0 = no findings, exit 2 = at least one HIGH finding, exit 1 = crash.
#
# ASCII only: Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI, so any
# non-ASCII character here becomes a parse error.
#
#   .\isze_live_state_audit.ps1                     # write brief + console
#   .\isze_live_state_audit.ps1 -Quiet              # write brief only
#   .\isze_live_state_audit.ps1 -IncludeOutOfScope  # audit personal tasks too
#   .\isze_live_state_audit.ps1 -MaxAuditAgeDays 14
# =============================================================================

[CmdletBinding()]
param(
  [switch]$Quiet,
  [switch]$IncludeOutOfScope,
  [int]$MaxAuditAgeDays = 30,
  [string]$IszeRoot
)

$ErrorActionPreference = 'Stop'

if (-not $IszeRoot) {
  $IszeRoot = if ($env:ISZE_ROOT) { $env:ISZE_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
}

$RegisterPath = Join-Path $IszeRoot '00_docs\AUTOMATION_REGISTER.md'
$SkillRoot    = 'C:\Users\jerom\Documents\Claude\Scheduled'
$BriefDir     = Join-Path $IszeRoot '05_memory\briefs'

if (-not (Test-Path $RegisterPath)) {
  Write-Error "AUTOMATION_REGISTER.md not found at $RegisterPath"
  exit 1
}

$Findings = [System.Collections.Generic.List[object]]::new()

<#
  Severity drives ordering in the brief, not just colour:
    HIGH   something runs twice, does not run at all, or fails
    MEDIUM the register and reality disagree but nothing is broken today
    LOW    cosmetic or bookkeeping
#>
function Add-Finding([string]$Severity, [string]$Area, [string]$What, [string]$Ask) {
  $needsJerome = ($Severity -eq 'HIGH')
  $Findings.Add([pscustomobject]@{
    severity = $Severity
    area = $Area
    what = $What
    ask = $Ask
    needsJerome = $needsJerome
  })
}

<#
  The discount scanner is a personal supermarket-promo scraper (Lidl, Delhaize,
  Colruyt, AH, Carrefour). It carries the ISZE task prefix but it is not work
  automation, so its drift is noise in a report about the ISZE data chain.
  Excluded from the checks, still listed in the inventory table so it is not
  invisible, and -IncludeOutOfScope brings it back.
#>
$OutOfScopePattern = 'Discount[ _]?Scanner|discount_scraper'

function Test-InScope([string]$Name) {
  if ($IncludeOutOfScope) { return $true }
  return ($Name -notmatch $OutOfScopePattern)
}

# -Encoding UTF8 is not the default in PowerShell 5.1; without it the register's
# em-dashes come back as mojibake and end up in the brief.
$RegisterText = Get-Content $RegisterPath -Raw -Encoding UTF8

# --- Source 2: live Task Scheduler state -------------------------------------
# /V gives Task To Run and Last Result, which is what makes duplicate detection
# possible - two tasks with different names running the same batch file.
$liveTasks = @()
try {
  $liveTasks = @(
    schtasks /Query /FO CSV /V 2>$null |
      ConvertFrom-Csv |
      Where-Object { $_.TaskName -match 'ISZE' -and $_.TaskName -ne 'TaskName' } |
      ForEach-Object {
        [pscustomobject]@{
          Name       = ($_.TaskName -replace '^\\', '').Trim()
          Action     = ($_.'Task To Run').Trim()
          LastResult = ($_.'Last Result').Trim()
          NextRun    = ($_.'Next Run Time').Trim()
        }
      }
  )
} catch {
  Add-Finding 'HIGH' 'scheduler' ("Could not query Task Scheduler: " + $_.Exception.Message) 'Run this script again from an account that can read the task store.'
}

# --- Check 1: two tasks, one script -----------------------------------------
# The expensive kind of drift. Both copies fire, the second one overwrites or
# collides with the first, and nothing in the output says it happened twice.
$liveTasks |
  Where-Object { $_.Action -and (Test-InScope $_.Name) } |
  Group-Object { $_.Action.ToLowerInvariant() } |
  Where-Object { $_.Count -gt 1 } |
  ForEach-Object {
    $names = ($_.Group | ForEach-Object { $_.Name }) -join ' and '
    $script = Split-Path $_.Group[0].Action -Leaf
    Add-Finding 'HIGH' 'scheduler' `
      ("{0} both run {1}" -f $names, $script) `
      ("Decide which task name is canonical and delete the other: schtasks /delete /tn ""<name>"" /f")
  }

# --- Check 2: live but undocumented ----------------------------------------
# A task nobody wrote down is a task nobody maintains.
foreach ($t in $liveTasks) {
  if (-not (Test-InScope $t.Name)) { continue }
  if ($RegisterText -notmatch [regex]::Escape($t.Name)) {
    Add-Finding 'MEDIUM' 'register' `
      ("Task {0} is live but appears nowhere in AUTOMATION_REGISTER.md" -f $t.Name) `
      ("Add a row to the live-state table, or delete the task if it was a one-off.")
  }
}

# --- Check 3: documented but not live --------------------------------------
# Pull the backticked names out of the live-state table and see which of them
# the scheduler has never heard of.
#
# Task names drift too, so identity is matched two ways: by name, and by the
# script the row mentions. Without the second one a renamed task reads as both
# "gone" and "undocumented" while it is really just the same job under a new name.
$liveStateSection = ''
$m = [regex]::Match($RegisterText, '(?s)##\s*Windows Task Scheduler.*?(?=\r?\n---)')
if ($m.Success) { $liveStateSection = $m.Value }

foreach ($row in ($liveStateSection -split "`n")) {
  if ($row -notmatch '^\|') { continue }
  $nameMatch = [regex]::Match($row, '`([^`]+)`')
  if (-not $nameMatch.Success) { continue }
  $claimed = $nameMatch.Groups[1].Value.Trim()
  if ($claimed -notmatch 'ISZE') { continue }
  if (-not (Test-InScope $claimed)) { continue }

  $byName = @($liveTasks | Where-Object { $_.Name -eq $claimed })

  $rowScripts = @([regex]::Matches($row, '([A-Za-z0-9_\-\.]+\.(?:bat|cmd|ps1))') |
    ForEach-Object { $_.Groups[1].Value.ToLowerInvariant() } | Sort-Object -Unique)
  $byScript = @($liveTasks | Where-Object {
    $_.Action -and $rowScripts -contains (Split-Path $_.Action -Leaf).ToLowerInvariant()
  })

  $claimsRegistered = $row -notmatch 'not registered'

  if ($claimsRegistered -and $byName.Count -eq 0) {
    if ($byScript.Count -gt 0) {
      Add-Finding 'MEDIUM' 'register' `
        ("Register calls it {0}, but the live task running that script is {1}" -f $claimed, ($byScript.Name -join ', ')) `
        ("Rename the register row to the live task name so the two can be matched.")
    } else {
      Add-Finding 'HIGH' 'scheduler' `
        ("Register says {0} is registered, but no task runs it" -f $claimed) `
        ("Either re-import the XML, or correct the register row.")
    }
  } elseif (-not $claimsRegistered -and ($byName.Count -gt 0 -or $byScript.Count -gt 0)) {
    $live = if ($byName.Count -gt 0) { $byName.Name -join ', ' } else { $byScript.Name -join ', ' }
    Add-Finding 'MEDIUM' 'register' `
      ("Register says {0} is not registered, but {1} is live" -f $claimed, $live) `
      ("Update the register row - the gap it describes is already closed.")
  }
}

# --- Check 4: last run outcome ---------------------------------------------
# Task Scheduler result codes (hex -> decimal) that are states, not failures:
#   267009 = 0x41301 SCHED_S_TASK_RUNNING      still running at query time
#   267010 = 0x41302 SCHED_S_TASK_DISABLED     disabled by user/policy
#   267011 = 0x41303 SCHED_S_TASK_HAS_NOT_RUN  never fired yet
# A long job (the 07:00 refresh runs ~1h43m) legitimately shows RUNNING when the
# 08:00 audit queries it - mislabelling that as a crash floods the brief with
# false HIGH alarms and hides real failures. States are LOW/informational.
foreach ($t in $liveTasks) {
  if (-not (Test-InScope $t.Name)) { continue }
  $code = $t.LastResult
  if ($code -eq '0' -or -not $code) { continue }
  if ($code -eq '267009') {
    Add-Finding 'LOW' 'scheduler' `
      ("{0} was still running when the audit queried it" -f $t.Name) `
      ("Usually a long job (the PMS/IAM refresh runs ~1h43m) overlapping the 08:00 audit - check its log to confirm it finished, not that it hung.")
  } elseif ($code -eq '267010') {
    Add-Finding 'LOW' 'scheduler' `
      ("{0} is disabled" -f $t.Name) `
      ("Re-enable it if it should run, or move the register row to Retired.")
  } elseif ($code -eq '267011') {
    Add-Finding 'LOW' 'scheduler' `
      ("{0} has never run yet" -f $t.Name) `
      ("Fine if it was just imported; otherwise check the trigger.")
  } else {
    Add-Finding 'HIGH' 'scheduler' `
      ("{0} last exited with code {1}" -f $t.Name, $code) `
      ("Open the task history and fix the underlying script before trusting its output.")
  }
}

# --- Check 5: active skills without an implementation ----------------------
# The register indexes jobs that live outside the repo, so the folder can vanish
# without a single test going red.
$registeredSkills = @{}
foreach ($row in ($RegisterText -split "`n")) {
  if ($row -notmatch '^\|\s*`') { continue }
  $mm = [regex]::Match($row, '^\|\s*`([^`]+)`\s*\|\s*(Active|Superseded|Retired)\b')
  if (-not $mm.Success) { continue }
  $registeredSkills[$mm.Groups[1].Value.Trim()] = $mm.Groups[2].Value.Trim()
}

if (Test-Path $SkillRoot) {
  $skillDirs = @(Get-ChildItem $SkillRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })

  foreach ($skill in $registeredSkills.Keys) {
    if ($registeredSkills[$skill] -ne 'Active') { continue }
    $skillFile = Join-Path (Join-Path $SkillRoot $skill) 'SKILL.md'
    if (-not (Test-Path $skillFile)) {
      Add-Finding 'HIGH' 'skills' `
        ("Register lists {0} as Active but {1}\SKILL.md is missing" -f $skill, $skill) `
        ("Restore the job folder, or move the row to Retired.")
    }
  }

  foreach ($dir in $skillDirs) {
    if (-not $registeredSkills.ContainsKey($dir)) {
      Add-Finding 'LOW' 'skills' `
        ("Job folder {0} exists but is not in the register" -f $dir) `
        ("Add a row, or delete the folder.")
    } elseif ($registeredSkills[$dir] -ne 'Active') {
      Add-Finding 'LOW' 'skills' `
        ("Job folder {0} still on disk while the register marks it {1}" -f $dir, $registeredSkills[$dir]) `
        ("Delete the folder so it cannot be scheduled by accident.")
    }
  }
} else {
  Add-Finding 'MEDIUM' 'skills' `
    ("Job implementation root {0} does not exist" -f $SkillRoot) `
    ("Fix the path in the register, or restore the folder.")
}

# --- Source 3: FACTS vs pipeline -------------------------------------------
# The runbook already produces these two reports; the auditor only reads them,
# so a green run here means the same thing it means in the monthly refresh.
function Resolve-DerivedFile([string]$Name) {
  foreach ($dir in @('01_data\00_derived', '01_data\derived')) {
    $candidate = Join-Path $IszeRoot (Join-Path $dir $Name)
    if (Test-Path $candidate) { return $candidate }
  }
  return $null
}

$factsReport = Resolve-DerivedFile '_facts_drift_report.md'
if (-not $factsReport) {
  Add-Finding 'MEDIUM' 'facts' 'No _facts_drift_report.md found' 'Run 04_tools\verify_facts_drift.py so FACTS.md can be trusted.'
} else {
  $factsText = Get-Content $factsReport -Raw -Encoding UTF8
  $resultMatch = [regex]::Match($factsText, '\*\*Result:\s*([A-Z]+)\*\*(.*)')
  $ageDays = [math]::Round(((Get-Date) - (Get-Item $factsReport).LastWriteTime).TotalDays, 1)

  if (-not $resultMatch.Success) {
    Add-Finding 'MEDIUM' 'facts' '_facts_drift_report.md has no Result line' 'Re-run verify_facts_drift.py.'
  } elseif ($resultMatch.Groups[1].Value -ne 'ALIGNED') {
    $detail = ($resultMatch.Groups[2].Value -replace '[^\x20-\x7E]', ' ').Trim(' -')
    Add-Finding 'HIGH' 'facts' `
      ("FACTS drift: {0} {1}" -f $resultMatch.Groups[1].Value, $detail) `
      ("Decide which side is right, then update FACTS.md and facts_anchor.yaml together.")
  } elseif ($ageDays -gt $MaxAuditAgeDays) {
    Add-Finding 'LOW' 'facts' `
      ("FACTS drift report is aligned but {0} days old" -f $ageDays) `
      ("Re-run verify_facts_drift.py to confirm it still holds.")
  }
}

$verifyJson = Resolve-DerivedFile '_verification_report.json'
if (-not $verifyJson) {
  Add-Finding 'MEDIUM' 'pipeline' 'No _verification_report.json found' 'Run the monthly refresh orchestrator.'
} else {
  $verify = Get-Content $verifyJson -Raw | ConvertFrom-Json
  $s = $verify.summary
  $ageDays = [math]::Round(((Get-Date) - (Get-Item $verifyJson).LastWriteTime).TotalDays, 1)
  if ($s -and (-not $s.ok -or $s.fail -gt 0)) {
    Add-Finding 'HIGH' 'pipeline' `
      ("Pipeline verification not green: {0} pass / {1} warn / {2} fail" -f $s.pass, $s.warn, $s.fail) `
      ("Read _verification_report.md and fix before publishing anything.")
  } elseif ($ageDays -gt $MaxAuditAgeDays) {
    Add-Finding 'LOW' 'pipeline' `
      ("Pipeline verification is green but {0} days old" -f $ageDays) `
      ("Re-run isze_monthly_refresh.ps1.")
  }
}

$gpsReport = Resolve-DerivedFile 'gps_reconciliation_report.json'
if ($gpsReport) {
  $gps = Get-Content $gpsReport -Raw | ConvertFrom-Json
  if ($gps.result -ne 'PASS' -or $gps.hard_failures -gt 0) {
    $failed = @()
    if ($gps.checks) {
      $failed = @($gps.checks | Where-Object { $_.severity -eq 'hard' -and $_.status -eq 'FAIL' } | ForEach-Object { $_.id })
    }
    $which = if ($failed.Count -gt 0) { ": " + ($failed -join ', ') } else { '' }
    Add-Finding 'HIGH' 'pipeline' `
      ("GPS reconciliation {0} with {1} hard failure(s){2}" -f $gps.result, $gps.hard_failures, $which) `
      ("Fix the failing check - the monthly refresh will not pass its gate until this is PASS.")
  }
}

# --- Check 6: is the register itself being maintained? ---------------------
$auditMatch = [regex]::Match($RegisterText, '\*\*Last audited:\*\*\s*(\d{4}-\d{2}-\d{2})')
if ($auditMatch.Success) {
  $auditAge = [math]::Round(((Get-Date) - [datetime]::ParseExact($auditMatch.Groups[1].Value, 'yyyy-MM-dd', $null)).TotalDays, 0)
  if ($auditAge -gt $MaxAuditAgeDays) {
    Add-Finding 'MEDIUM' 'register' `
      ("Register was last audited {0} days ago ({1})" -f $auditAge, $auditMatch.Groups[1].Value) `
      ("Walk this list, then bump the Last audited date.")
  }
} else {
  Add-Finding 'LOW' 'register' 'Register has no Last audited date' 'Add one so staleness is measurable.'
}

# --- Check 7: the register's own open items --------------------------------
# Closed / archived / resolved rows are NOT waiting on Jerome (same class as
# Nordics keys). Path-map tables of old XLSX/HTML must not land on his list.
$openMatch = [regex]::Match($RegisterText, '(?s)##\s*Open items \(Jerome\).*?(?=\r?\n---)')
if ($openMatch.Success) {
  $closedPat = 'CLOSED|RESOLVED|ARCHIVED|DONE|SKIP'
  $archivePat = '_archive|90_archive|_ARCHIVE'
  foreach ($row in ($openMatch.Value -split "`n")) {
    if ($row -notmatch '^\|\s*`') { continue }
    if ($row -match 'Watched file|Live path') { continue }
    $cells = ($row.Trim('|', ' ') -split '\s*\|\s*')
    if ($cells.Count -lt 2) { continue }
    $status = if ($cells.Count -ge 3) { $cells[-1] } else { '' }
    if ($status -match $closedPat) { continue }
    if ($row -match $archivePat) { continue }
    $name = $cells[0].Trim('`', ' ')
    if ($name -match '\.(xlsx|html|txt)$') { continue }
    $Findings.Add([pscustomobject]@{
      severity = 'MEDIUM'
      area = 'open-item'
      what = ("{0}: {1}" -f $cells[0].Trim('`', ' '), $cells[1].Trim())
      ask = 'Still an open human gate in the register — not an archive leftover.'
      needsJerome = $true
    })
  }
}

# --- Render ----------------------------------------------------------------
$order = @{ 'HIGH' = 0; 'MEDIUM' = 1; 'LOW' = 2 }
$sorted = @($Findings | Sort-Object { $order[$_.severity] }, area)
$high = @($sorted | Where-Object { $_.severity -eq 'HIGH' }).Count

$today = Get-Date -Format 'yyyy-MM-dd'
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("# ISZE live-state audit - $today")
$lines.Add('')
$lines.Add("Compares AUTOMATION_REGISTER.md against Windows Task Scheduler and the")
$lines.Add("FACTS/pipeline reports. Nothing here has been changed automatically.")
$lines.Add('')
$lines.Add(("**{0} finding(s): {1} high, {2} medium, {3} low.**" -f `
  $sorted.Count, $high, `
  @($sorted | Where-Object { $_.severity -eq 'MEDIUM' }).Count, `
  @($sorted | Where-Object { $_.severity -eq 'LOW' }).Count))
$lines.Add('')

if ($sorted.Count -eq 0) {
  $lines.Add('No drift found. Register, scheduler and FACTS agree.')
} else {
  $lines.Add('## Findings')
  $lines.Add('')
  $i = 1
  foreach ($f in $sorted) {
    $lines.Add(("{0}. **[{1}]** ({2}) {3}" -f $i, $f.severity, $f.area, $f.what))
    $lines.Add((' ' * ("$i. ").Length) + ("- {0}" -f $f.ask))
    $i++
  }
  $human = @($sorted | Where-Object { $_.needsJerome })
  $lines.Add('')
  $lines.Add('## Waiting on Jerome')
  $lines.Add('')
  if ($human.Count -eq 0) {
    $lines.Add('None. Archive paths, superseded skill folders, and overlapping long jobs are not a human gate.')
  } else {
    $j = 1
    foreach ($f in $human) {
      $lines.Add(("{0}. **[{1}]** ({2}) {3}" -f $j, $f.severity, $f.area, $f.what))
      $lines.Add((' ' * ("$j. ").Length) + ("- {0}" -f $f.ask))
      $j++
    }
  }
}

$lines.Add('')
$lines.Add('---')
$lines.Add('')
$lines.Add("Live ISZE tasks at audit time ($($liveTasks.Count)):")
$lines.Add('')
if ($liveTasks.Count -gt 0) {
  $lines.Add('| Task | Runs | Last result | Next run | Audited |')
  $lines.Add('|---|---|---|---|---|')
  foreach ($t in ($liveTasks | Sort-Object Name)) {
    $scope = if (Test-InScope $t.Name) { 'yes' } else { 'no - personal, not ISZE' }
    $lines.Add(("| {0} | {1} | {2} | {3} | {4} |" -f $t.Name, (Split-Path $t.Action -Leaf), $t.LastResult, $t.NextRun, $scope))
  }
}
$lines.Add('')
$lines.Add("Generated by ``04_tools\workspace\isze_live_state_audit.ps1``.")

if (-not (Test-Path $BriefDir)) { New-Item -ItemType Directory -Path $BriefDir -Force | Out-Null }
$outPath = Join-Path $BriefDir "automation_drift_$today.md"
$lines -join "`r`n" | Set-Content -Path $outPath -Encoding UTF8

if (-not $Quiet) {
  Write-Host ''
  Write-Host "=== ISZE live-state audit ===" -ForegroundColor Cyan
  Write-Host ("Root: {0}" -f $IszeRoot)
  Write-Host ''
  if ($sorted.Count -eq 0) {
    Write-Host 'No drift found.' -ForegroundColor Green
  } else {
    $i = 1
    foreach ($f in $sorted) {
      $colour = switch ($f.severity) { 'HIGH' { 'Red' } 'MEDIUM' { 'Yellow' } default { 'DarkGray' } }
      Write-Host ("{0,2}. [{1}] ({2}) {3}" -f $i, $f.severity, $f.area, $f.what) -ForegroundColor $colour
      Write-Host ("     -> {0}" -f $f.ask) -ForegroundColor DarkGray
      $i++
    }
  }
  Write-Host ''
  Write-Host ("Brief: {0}" -f $outPath) -ForegroundColor DarkGray
}

if ($high -gt 0) { exit 2 }
exit 0
