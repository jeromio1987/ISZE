<#
ISZE overnight orchestrator — the delegator cycle.

WHAT IT IS HONESTLY ABLE TO DO — READ THIS FIRST
------------------------------------------------
Agents cannot message each other. Cursor exposes no tool for one agent to wake, command or read
another chat's context. The shared board is the only channel between them.

So "keep the agents working" means exactly this: wake, look at the evidence every workstream
left on disk, and write corrective work as a QUEUED TASK for Jerome to approve. It does not mean
commanding another agent's session, and it cannot restart a chat that has stopped.

WHAT IT DOES PER 20-MINUTE TICK
-------------------------------
  1. fingerprints the watched AIM / pricing set (as the detect-only watch always did)
  2. checks the evidence of every active workstream discovered on disk
  3. inside the overnight window, runs ONE audit angle from a rotating queue
  4. appends results to the board and writes an audit note under 00_docs/agent/overnight/
  5. appends any corrective work to the queue file for Jerome

Outside the window it stays cheap and detect-only: fingerprint, compare, exit.

HARD LIMITS — NON-NEGOTIABLE
----------------------------
READ-ONLY on all deliverables. It may not rebuild, publish, sync, mail, bump a version or move a
price. It writes only to its own state and log, the board, and internal notes under
00_docs/agent/. A fix it believes is needed becomes a queued task, never an applied change.
Authority: 00_docs/RUNBOOK_ROUTINE_HANDOVER.md section 5 and .cursor/rules/isze-no-ship-without-ok.mdc.

Usage
-----
  powershell -File isze_overnight_orchestrator.ps1                     # normal tick
  powershell -File isze_overnight_orchestrator.ps1 -Status             # what cycle/angle is next
  powershell -File isze_overnight_orchestrator.ps1 -Force              # ignore the window
  powershell -File isze_overnight_orchestrator.ps1 -RunAngle <name>    # run one angle now
  powershell -File isze_overnight_orchestrator.ps1 -ResetQueue         # restart the angle queue

Window: 22:00 local to 08:00 local. Each run is one cycle. The orchestrator does not sleep.
#>
[CmdletBinding()]
param(
    [switch]$Status,
    [switch]$Force,
    [switch]$ResetQueue,
    [string]$RunAngle,
    [switch]$Quiet,
    [string]$LogPath,
    [string]$WindowStart = '22:00',
    [string]$WindowEnd = '08:00',
    [double]$ReportHours = 48
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'isze_root.ps1')
$Root      = Get-IszeRoot
$AgentDir  = Join-Path $Root '00_docs\agent'
$BoardPath = Join-Path $AgentDir 'DELEGATOR_BOARD.md'
$StatePath = Join-Path $AgentDir 'DELEGATOR_STATE.json'
$CyclePath = Join-Path $AgentDir 'OVERNIGHT_CYCLE.json'
$QueuePath = Join-Path $AgentDir 'OVERNIGHT_ANGLE_QUEUE.json'
$TaskQueue = Join-Path $AgentDir 'OVERNIGHT_TASKS_QUEUE.md'
$NoteDir   = Join-Path $AgentDir 'overnight'
$AnglesPy  = Join-Path $PSScriptRoot '_overnight_angles.py'
if (-not $LogPath) { $LogPath = Join-Path $PSScriptRoot 'overnight_orchestrator.log' }

$Watched = @(
    @{ Rel = '01_data/00_derived/aim_master_v2.csv';                Role = 'corrected AIM master' },
    @{ Rel = '01_data/00_derived/aim_pn_classification_v2.csv';     Role = 'PN classification v2' },
    @{ Rel = '01_data/00_derived/aim_classification_gate.json';     Role = 'classification safety gate' },
    @{ Rel = '01_data/00_derived/aim_master_v2.meta.json';          Role = 'AIM coverage + fix log' },
    @{ Rel = '01_data/00_derived/price_bp_weighted_compare_pn.csv'; Role = 'price-revision base (in-scope L12M)' }
)

# The rotating queue. One angle per cycle; it cycles back only after every angle has run.
$AngleQueue = @(
    'workstream_scan',
    'numbers_tie_out',
    'receipt_mtime_drift',
    'language_sweep',
    'locked_file_integrity',
    'html_first_paint',
    'coverage_honesty',
    'entity_separation',
    'excel_formula_errors',
    'gaps_need_context',
    'cross_artifact_consistency',
    'chart_form_quality',
    'blank_pages',
    'orphan_artifact',
    'memory_markdown_drift',
    'receipt_quality'
)

function Write-Log {
    param([string]$Message)
    $line = '[{0}] {1}' -f (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'), $Message
    try { Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8 -ErrorAction Stop } catch { }
    if (-not $Quiet) { Write-Output $line }
}

function Read-Json {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try { return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) } catch { return $null }
}

function Write-Json {
    param([string]$Path, $Object)
    $Object | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Add-BoardRow {
    param([string]$Agent, [string]$Change, [string]$Files, [string]$NextStep)
    $stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm')
    # Append one line only. Never rewrite the board wholesale: two agents share it and a
    # read-modify-write would silently drop the other's row.
    try {
        Add-Content -LiteralPath $BoardPath -Value "| $stamp | $Agent | $Change | $Files | $NextStep |" `
            -Encoding UTF8 -ErrorAction Stop
    }
    catch {
        Write-Log "board append failed (lock contention?): $($_.Exception.Message)"
    }
}

function In-OvernightWindow {
    $now = (Get-Date).TimeOfDay
    $s = [TimeSpan]::Parse($WindowStart)
    $e = [TimeSpan]::Parse($WindowEnd)
    if ($s -lt $e) { return ($now -ge $s -and $now -lt $e) }
    # A window that crosses midnight, which is the normal case here.
    return ($now -ge $s -or $now -lt $e)
}

function Get-Fingerprint {
    param([string]$FullPath)
    $fi = Get-Item -LiteralPath $FullPath
    [pscustomobject]@{
        sha256 = (Get-FileHash -LiteralPath $FullPath -Algorithm SHA256).Hash.ToLowerInvariant()
        bytes  = [int64]$fi.Length
        mtime  = $fi.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')
    }
}

# ---------------------------------------------------------------- preflight
# Policy is abort, not repair.
$missing = @()
foreach ($w in $Watched) {
    $p = Join-Path $Root ($w.Rel -replace '/', '\')
    if (-not (Test-Path -LiteralPath $p)) { $missing += $w.Rel }
}
if (-not (Test-Path -LiteralPath $AnglesPy)) { $missing += '_overnight_angles.py' }
if (-not (Test-Path -LiteralPath $AgentDir)) { $missing += '00_docs/agent/' }
if ($missing.Count -gt 0) {
    Write-Log "orchestrator ABORTED - missing input: $($missing -join '; ')"
    exit 1
}

foreach ($d in @($NoteDir)) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}

# ---------------------------------------------------------------- queue state
function Reset-Queue {
    Write-Json -Path $QueuePath -Object ([ordered]@{
        created_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        queue       = $AngleQueue
        completed   = @()
        cycle       = 0
    })
}

if ($ResetQueue) {
    Reset-Queue
    Write-Log "angle queue reset: $($AngleQueue.Count) angles"
    exit 0
}
$queueState = Read-Json -Path $QueuePath
if (-not $queueState) { Reset-Queue; $queueState = Read-Json -Path $QueuePath }

function Get-NextAngle {
    $done = @($queueState.completed)
    $remaining = @($AngleQueue | Where-Object { $done -notcontains $_ })
    if ($remaining.Count -eq 0) {
        # Every angle has run once. Start the next pass over the same queue.
        $queueState.completed = @()
        $remaining = $AngleQueue
    }
    return $remaining[0]
}

function Complete-Angle {
    param([string]$Angle)
    # Rebuild the object rather than mutating it. A PSCustomObject from ConvertFrom-Json has a
    # fixed property set, so assigning a property it does not already have throws.
    # Assign to $script: so the caller sees the updated cycle count.
    $done = @($script:queueState.completed)
    if ($done -notcontains $Angle) { $done += $Angle }
    $cycle = [int]$script:queueState.cycle + 1
    $script:queueState = [pscustomobject]@{
        created_utc   = $script:queueState.created_utc
        queue         = $script:queueState.queue
        completed     = $done
        cycle         = $cycle
        last_angle    = $Angle
        last_run_utc  = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    }
    Write-Json -Path $QueuePath -Object $script:queueState
}

# ---------------------------------------------------------------- -Status
if ($Status) {
    $st = Read-Json -Path $StatePath
    $qs = Read-Json -Path $QueuePath
    $inWin = In-OvernightWindow
    Write-Output "orchestrator status"
    Write-Output "  now (local)        : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Output "  window             : $WindowStart -> $WindowEnd"
    Write-Output "  inside window      : $inWin"
    Write-Output "  cycles completed   : $($qs.cycle)"
    Write-Output "  angles done        : $(@($qs.completed).Count) of $($AngleQueue.Count)"
    Write-Output "  next angle         : $(Get-NextAngle)"
    if ($inWin) { Write-Output "  next tick will     : check workstreams and run that angle"
    } else { Write-Output "  next tick will     : fingerprint and exit (detect-only)" }
    if ($st) { Write-Output "  last fingerprint   : $($st.updated_utc)" }
    exit 0
}

# ---------------------------------------------------------------- -RunAngle
if ($RunAngle) {
    if ($AngleQueue -notcontains $RunAngle) {
        Write-Log "unknown angle '$RunAngle'. Known: $($AngleQueue -join ', ')"
        exit 2
    }
    Write-Log "running one angle on demand: $RunAngle"
    & python $AnglesPy --angle $RunAngle --hours $ReportHours | Out-Null
    Complete-Angle -Angle $RunAngle
    Write-Log "angle $RunAngle done, exit=$LASTEXITCODE"
    exit $LASTEXITCODE
}

# ---------------------------------------------------------------- 1. fingerprint
foreach ($w in $Watched) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root ($w.Rel -replace '/', '\')))) {
        Write-Log "watched file vanished: $($w.Rel)"
    }
}
$live = [ordered]@{}
foreach ($w in $Watched) {
    $live[$w.Rel] = Get-Fingerprint (Join-Path $Root ($w.Rel -replace '/', '\'))
}

$state = Read-Json -Path $StatePath
$changed = @()
if (-not $state -or -not $state.files) {
    $obj = [ordered]@{ schema_version = 1
        updated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        note = 'Fingerprints of the AIM watch set. Written by isze_overnight_orchestrator.ps1.'
        files = $live }
    Write-Json -Path $StatePath -Object $obj
    Write-Log 'fingerprint baseline established'
} else {
    $stateFiles = $state.files
    foreach ($k in $live.Keys) {
        $prev = $stateFiles.$k
        if ($null -eq $prev -or $prev.sha256 -ne $live[$k].sha256) { $changed += $k }
    }
    $obj = [ordered]@{ schema_version = 1
        updated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        note = 'Fingerprints of the AIM watch set. Written by isze_overnight_orchestrator.ps1.'
        files = $live }
    Write-Json -Path $StatePath -Object $obj
    if ($changed.Count -gt 0) {
        Write-Log "fingerprint change: $($changed -join ', ')"
        Add-BoardRow -Agent 'orchestrator' -Change "watched set moved ($($changed.Count) file(s))" `
            -Files ($changed -join ', ') `
            -NextStep 'AIM or pricing base changed. Detect-only: no rebuild performed. See DELEGATOR_REFRESH_HOWTO.md.'
    }
}

$inWindow = In-OvernightWindow
if (-not $inWindow -and -not $Force) {
    Write-Log "outside the overnight window ($WindowStart-$WindowEnd): fingerprint only, exiting"
    exit 0
}

# ---------------------------------------------------------------- 2. workstream evidence
$cycleStart = Get-Date
Write-Log "=== cycle $([int]$queueState.cycle + 1) start (window open) ==="

$scanPath = Join-Path $NoteDir 'evidence_scan.json'
& python $AnglesPy --angle workstream_scan --hours $ReportHours --out $scanPath | Out-Null
$scanExit = $LASTEXITCODE
$scan = Read-Json -Path $scanPath

$wsSummary = 'no workstreams found'
$wsFindings = 0
$driftCount = 0
$wsTableRows = @()
if ($scan) {
    $wsFindings = @($scan.findings).Count
    $driftCount = @($scan.findings | Where-Object { $_.severity -eq 'high' }).Count
    $wsSummary = "$($scan.n_workstreams) workstreams, $wsFindings findings ($driftCount high)"
    $wsTableRows = @($scan.workstreams | ForEach-Object {
        $newest = $_.newest
        $cov = 'no receipt'
        foreach ($a in $_.artifacts) {
            if ($a.name -eq $newest) {
                if ($a.receipt) { $cov = if ($a.receipt_covers_file) { 'receipt covers' } else { 'RECEIPT DRIFTED' } }
            }
        }
        [pscustomobject]@{ dir = $_.dir; newest = $newest; mtime = $_.newest_mtime_utc; cover = $cov }
    })
}
Write-Log "workstream evidence: $wsSummary (scan exit=$scanExit)"

# ---------------------------------------------------------------- 3. one audit angle
$angle = Get-NextAngle
Write-Log "audit angle this cycle: $angle"
$anglePath = Join-Path $NoteDir ("angle_{0}_{1}.json" -f $angle, (Get-Date -Format 'yyyyMMdd_HHmm'))
& python $AnglesPy --angle $angle --hours $ReportHours --out $anglePath | Out-Null
$angleExit = $LASTEXITCODE
$aj = Read-Json -Path $anglePath

$angleFindings = 0
$angleHigh = 0
$angleRecent = 0
$angleBacklog = 0
$angleRows = @()
if ($aj) {
    $angleFindings = @($aj.findings).Count
    $angleHigh = @($aj.findings | Where-Object { $_.severity -eq 'high' }).Count
    $angleRecent = [int]$aj.recent_count
    $angleBacklog = [int]$aj.backlog_count
    $angleRows = @($aj.findings | Select-Object -First 12)
}
Write-Log "angle ${angle}: $angleFindings findings, $angleHigh high, $angleRecent on recent artifacts, $angleBacklog pre-existing backlog (exit=$angleExit)"

# ---------------------------------------------------------------- 4. audit note
$stamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$noteFile = Join-Path $NoteDir ("audit_{0}_{1}.md" -f $stamp, $angle)
$note = @()
$note += "# Overnight audit - $angle"
$note += ""
$note += "**Cycle:** $([int]$queueState.cycle + 1) - **Run:** $(Get-Date -Format 'yyyy-MM-dd HH:mm') local"
$note += "**Angle:** ``$angle`` - $($aj.description)"
$note += ""
$note += "Read-only pass. Nothing was rebuilt, published or fixed. Any corrective work is queued in"
$note += "``OVERNIGHT_TASKS_QUEUE.md`` for Jerome to approve."
$note += ""
$note += "## Workstream evidence"
$note += ""
$note += "| Workstream | Newest artifact | Modified (UTC) | Receipt |"
$note += "|---|---|---|---|"
foreach ($r in $wsTableRows) { $note += "| ``$($r.dir)`` | $($r.newest) | $($r.mtime) | $($r.cover) |" }
$note += ""
$note += "Findings: **$wsFindings** in total, **$driftCount** high severity."
$note += ""
$note += "## This cycle's angle"
$note += ""
$note += "**$angleFindings findings** - $angleHigh high, $angleRecent on recent artifacts,"
$note += "$angleBacklog pre-existing backlog. Attribution is by artifact age only: two agents write"
$note += "in this workspace, so 'recent' does not mean this workstream did it."
$note += ""
if ($angleFindings -eq 0) {
    $note += "Clean on this angle."
} else {
    $note += "| Severity | Workstream | Finding |"
    $note += "|---|---|---|"
    foreach ($f in $angleRows) {
        $txt = ($f.what -replace '\|', '/').Substring(0, [Math]::Min(150, $f.what.Length))
        $note += "| $($f.severity) | $($f.workstream) | $txt |"
    }
    $note += ""
    $note += "Full detail: ``$([System.IO.Path]::GetFileName($anglePath))``"
}
$note += ""
$note += "## Honest limits"
$note += ""
$note += "Agents cannot message each other; the board is the only channel. This orchestrator can"
$note += "observe evidence on disk and queue corrective work. It cannot command another agent's"
$note += "session or restart a chat that has stopped."
$note | Set-Content -LiteralPath $noteFile -Encoding UTF8
Write-Log "wrote audit note $([System.IO.Path]::GetFileName($noteFile))"

# ---------------------------------------------------------------- 5. queue corrective work
$newTasks = @()
if ($driftCount -gt 0) {
    foreach ($f in @($scan.findings | Where-Object { $_.severity -eq 'high' })) {
        $newTasks += [pscustomobject]@{ sev = 'high'; ws = $f.workstream; what = $f.what
            action = $f.action; evidence = $f.evidence }
    }
}
foreach ($f in @($aj.findings | Where-Object { $_.severity -eq 'high' })) {
    $newTasks += [pscustomobject]@{ sev = 'high'; ws = $f.workstream; what = $f.what
        action = $f.action; evidence = $f.evidence }
}
if ($newTasks.Count -gt 0) {
    $q = @()
    $q += ""
    $q += "### $(Get-Date -Format 'yyyy-MM-dd HH:mm') - cycle $([int]$queueState.cycle + 1), angle ``$angle``"
    $q += ""
    foreach ($t in ($newTasks | Select-Object -First 10)) {
        $q += "- **[$($t.sev)] $($t.ws)** - $($t.what)"
        if ($t.action)    { $q += "  - Suggested action: $($t.action)" }
        if ($t.evidence)  { $q += "  - Evidence: ``$($t.evidence)``" }
    }
    if (-not (Test-Path -LiteralPath $TaskQueue)) {
        @('# Overnight corrective work queue',
          '',
          'Written by the overnight orchestrator. **This file is a queue, not a change log.**',
          'Every item here needs Jerome to approve it. The orchestrator never applies a fix: it is',
          'read-only on all deliverables by design (00_docs/RUNBOOK_ROUTINE_HANDOVER.md section 5).',
          '') | Set-Content -LiteralPath $TaskQueue -Encoding UTF8
    }
    Add-Content -LiteralPath $TaskQueue -Value $q -Encoding UTF8
    Write-Log "queued $([Math]::Min(10, $newTasks.Count)) corrective task(s) for approval"
}

# ---------------------------------------------------------------- 6. board + cycle state
Complete-Angle -Angle $angle
$elapsed = [int]((Get-Date) - $cycleStart).TotalSeconds
Write-Json -Path $CyclePath -Object ([ordered]@{
    updated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    cycle = [int]$queueState.cycle
    last_angle = $angle
    elapsed_seconds = $elapsed
    workstreams = if ($scan) { [int]$scan.n_workstreams } else { 0 }
    workstream_findings = $wsFindings
    recent_count = if ($aj) { [int]$aj.recent_count } else { 0 }
    backlog_count = if ($aj) { [int]$aj.backlog_count } else { 0 }
    angle_findings = $angleFindings
    angle_high = $angleHigh
    queued_tasks = [Math]::Min(10, $newTasks.Count)
})

Add-BoardRow -Agent "orchestrator (cycle $([int]$queueState.cycle))" `
    -Change "audit angle '$angle': $angleFindings findings ($angleHigh high); $wsSummary" `
    -Files "00_docs/agent/overnight/$([System.IO.Path]::GetFileName($noteFile))" `
    -NextStep "Next angle: $(Get-NextAngle). Read-only pass; $([Math]::Min(10, $newTasks.Count)) corrective items queued in OVERNIGHT_TASKS_QUEUE.md for approval."

Write-Log "=== cycle done in ${elapsed}s ==="
exit 0
