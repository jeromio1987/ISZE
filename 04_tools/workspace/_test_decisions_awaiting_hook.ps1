# =============================================================================
# Standalone test for .cursor/hooks/decisions-awaiting-on-stop.mjs
#
# Run it after editing the hook or the register:
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\_test_decisions_awaiting_hook.ps1
#
# Case 1 runs against a purpose-built fixture register, so the assertions on the
# blocking block, the count line and the safe tier do not depend on what happens
# to be open in the live register today. Case 2 runs against the live register and
# asserts only properties that must hold whatever the content is.
#
# Read-only apart from the hook's own state file, which the test removes first and
# leaves as it found it. Exits 0 when every case passes, 1 otherwise.
# ASCII only: Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI.
# =============================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$root   = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$hook   = Join-Path $root '.cursor\hooks\decisions-awaiting-on-stop.mjs'
$twin   = Join-Path $root '.codex\hooks\decisions-awaiting-on-stop.mjs'
$state  = Join-Path $root '.cursor\hooks\.decisions-awaiting-announced.json'
$inbox  = Join-Path $root '01_data\90_INBOX'

$failures = [System.Collections.Generic.List[string]]::new()
$passes   = 0

function Invoke-Hook {
    param([string]$StdinJson, [string]$Register)
    $old = $env:ISZE_DECISIONS_REGISTER
    try {
        if ($Register) { $env:ISZE_DECISIONS_REGISTER = $Register }
        else { Remove-Item Env:\ISZE_DECISIONS_REGISTER -ErrorAction SilentlyContinue }
        $out = $StdinJson | node $hook 2>&1
        return ($out | Where-Object { $_ -is [string] } | Out-String).Trim()
    } finally {
        if ($old) { $env:ISZE_DECISIONS_REGISTER = $old }
        else { Remove-Item Env:\ISZE_DECISIONS_REGISTER -ErrorAction SilentlyContinue }
    }
}

function Assert-True {
    param([string]$Name, [bool]$Ok, [string]$Detail)
    if ($Ok) {
        $script:passes++
        Write-Host ('  PASS  ' + $Name) -ForegroundColor Green
    } else {
        $script:failures.Add($Name + ' - ' + $Detail)
        Write-Host ('  FAIL  ' + $Name + ' - ' + $Detail) -ForegroundColor Red
    }
}

function Reset-State { if (Test-Path $state) { Remove-Item $state -Force } }

function Remove-State { if (Test-Path $state) { Remove-Item $state -Force } }

function New-Fixture {
    param([string]$Path, [string]$Body)
    # UTF8Encoding($false) = no byte-order mark. A BOM would make the fixture
    # invalid JSON for a strict parser, which is not what these cases test.
    [System.IO.File]::WriteAllText($Path, $Body, (New-Object System.Text.UTF8Encoding($false)))
    return $Path
}

Write-Host ''
Write-Host 'decisions-awaiting-on-stop.mjs - standalone test' -ForegroundColor Cyan
Write-Host ('hook : ' + $hook)
Write-Host ''

if (-not (Test-Path $hook)) { Write-Host ('Hook not found: ' + $hook) -ForegroundColor Red; exit 1 }

$fixture = Join-Path $env:TEMP 'isze_decisions_fixture_test.json'
$empty   = Join-Path $env:TEMP 'isze_decisions_empty_test.json'
$broken  = Join-Path $env:TEMP 'isze_decisions_broken_test.json'
$missing = Join-Path $env:TEMP 'isze_decisions_does_not_exist_test.json'

# ---------------------------------------------------------------------------
# Case 1 - fixture: 2 blocking, 1 high, 2 normal, 1 already decided
# ---------------------------------------------------------------------------
Write-Host 'Case 1 - fixture register: 2 blocking, 1 high, 2 normal, 1 decided' -ForegroundColor Yellow
Reset-State
New-Fixture -Path $fixture -Body @'
{
  "register": "decisions_awaiting_jerome",
  "generated": "2026-09-19T00:00:00+02:00",
  "source": "fixture",
  "decisions": [
    { "id": "D01", "title": "First blocking item", "question": "Approve the first blocking thing?",
      "recommendation": "Yes.", "urgency": "blocking", "blocks": "Workstream A", "status": "open" },
    { "id": "D07", "title": "Second blocking item", "question": "Approve the second blocking thing?",
      "recommendation": "Yes.", "urgency": "blocking", "blocks": "Workstream B", "status": "open" },
    { "id": "D03", "title": "A high item", "question": "A high question?",
      "recommendation": "Yes.", "urgency": "high", "blocks": "Workstream C", "status": "open" },
    { "id": "D04", "title": "A normal item", "question": "A normal question?",
      "recommendation": "Yes.", "urgency": "normal", "blocks": "Nothing", "status": "open" },
    { "id": "D05", "title": "Another normal item", "question": "Another normal question?",
      "recommendation": "Yes.", "urgency": "normal", "blocks": "Nothing", "status": "open" },
    { "id": "D99", "title": "Already decided", "question": "Decided question?",
      "recommendation": "n/a", "urgency": "blocking", "blocks": "Nothing", "status": "decided" }
  ],
  "safe_tier": [
    { "id": "S1", "title": "safe one" },
    { "id": "S2", "title": "safe two" },
    { "id": "S3", "title": "safe three" }
  ]
}
'@
$out1 = Invoke-Hook -StdinJson '{"status":"completed","loop_count":0}' -Register $fixture
Write-Host '--- hook output ---------------------------------------------------------'
Write-Host $out1
Write-Host '-------------------------------------------------------------------------'

Assert-True -Name 'says something' -Ok ($out1 -ne '{}' -and $out1.Length -gt 0) -Detail 'hook returned {} for a register with open items'
Assert-True -Name 'is JSON with followup_message' -Ok ($out1 -match 'followup_message') -Detail 'no followup_message field'
Assert-True -Name 'counts only the 5 open items, not the decided one' -Ok ($out1 -match '5 decisions are waiting') -Detail 'expected "5 decisions are waiting"'
Assert-True -Name 'does not count the decided item' -Ok ($out1 -notmatch 'D99') -Detail 'D99 (status decided) leaked into the output'
Assert-True -Name 'carries the blocking count' -Ok ($out1 -match 'BLOCKING \(2\)') -Detail 'expected BLOCKING (2)'
Assert-True -Name 'prints blocking items in full' -Ok (($out1 -match 'D01') -and ($out1 -match 'D07')) -Detail 'a blocking id is missing'
Assert-True -Name 'prints the blocking question' -Ok ($out1 -match 'Approve the first blocking thing') -Detail 'the blocking question text is missing'
Assert-True -Name 'prints what the blocking items block' -Ok ($out1 -match 'Workstream A') -Detail 'Blocks field not printed for blocking items'
Assert-True -Name 'counts the rest instead of listing it' -Ok ($out1 -match '1 high \(D03\)') -Detail 'expected a "1 high (D03)" count line'
Assert-True -Name 'counts the normal items too' -Ok ($out1 -match '2 normal') -Detail 'expected "2 normal"'
Assert-True -Name 'mentions the safe tier as a count' -Ok ($out1 -match '3 safe-tier repairs') -Detail 'expected "3 safe-tier repairs"'
Assert-True -Name 'points at the register it read' -Ok ($out1 -match 'isze_decisions_fixture_test\.json') -Detail 'register path not named'
Assert-True -Name 'quotes no em dash or smart quote' -Ok ($out1 -notmatch '[^\x00-\x7F]') -Detail 'non-ASCII character in the message'
Assert-True -Name 'writes the once-per-chat state file' -Ok (Test-Path $state) -Detail 'state file not written'

# ---------------------------------------------------------------------------
# Case 2 - same chat, second turn: quiet
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host 'Case 2 - second turn of the same chat, nothing answered' -ForegroundColor Yellow
$out2 = Invoke-Hook -StdinJson '{"status":"completed","loop_count":0}' -Register $fixture
Write-Host ('  output: ' + $out2)
Assert-True -Name 'stays silent' -Ok ($out2 -eq '{}') -Detail ('expected {}, got: ' + $out2)

# ---------------------------------------------------------------------------
# Case 3 - a changed register re-announces
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host 'Case 3 - one blocking item is answered, so the register revision changes' -ForegroundColor Yellow
New-Fixture -Path $fixture -Body @'
{
  "register": "decisions_awaiting_jerome",
  "generated": "2026-09-19T00:00:00+02:00",
  "decisions": [
    { "id": "D01", "status": "decided", "urgency": "blocking", "title": "First blocking item", "question": "q", "blocks": "b" },
    { "id": "D07", "status": "open", "urgency": "blocking", "title": "Second blocking item", "question": "Approve the second blocking thing?", "blocks": "Workstream B" },
    { "id": "D03", "status": "open", "urgency": "high", "title": "A high item", "question": "q", "blocks": "c" },
    { "id": "D04", "status": "open", "urgency": "normal", "title": "A normal item", "question": "q", "blocks": "n" },
    { "id": "D05", "status": "open", "urgency": "normal", "title": "Another normal item", "question": "q", "blocks": "n" }
  ],
  "safe_tier": []
}
'@
$out3 = Invoke-Hook -StdinJson '{"status":"completed","loop_count":0}' -Register $fixture
Write-Host ('  firing again: ' + ($out3 -ne '{}'))
Assert-True -Name 'fires again because the answer set changed' -Ok ($out3 -match 'BLOCKING \(1\)') -Detail 'expected BLOCKING (1) after D01 was decided'
Assert-True -Name 'names only the remaining blocking item' -Ok (($out3 -match 'D07') -and ($out3 -notmatch '"D01"')) -Detail 'D01 still reported after being decided'

# ---------------------------------------------------------------------------
# Case 4 - quiet when this turn is a follow-up the hook caused
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host 'Case 4 - the turn is a hook follow-up (loop_count 1, then stop_hook_active)' -ForegroundColor Yellow
Reset-State
$out4 = Invoke-Hook -StdinJson '{"status":"completed","loop_count":1}' -Register $fixture
Write-Host ('  loop_count 1 output: ' + $out4)
Assert-True -Name 'stays silent on loop_count 1' -Ok ($out4 -eq '{}') -Detail ('expected {}, got: ' + $out4)
$out4b = Invoke-Hook -StdinJson '{"status":"completed","stop_hook_active":true}' -Register $fixture
Write-Host ('  stop_hook_active output: ' + $out4b)
Assert-True -Name 'stays silent on stop_hook_active' -Ok ($out4b -eq '{}') -Detail ('expected {}, got: ' + $out4b)

# ---------------------------------------------------------------------------
# Case 5 - quiet on an aborted or failed turn
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host 'Case 5 - aborted and error turns' -ForegroundColor Yellow
Reset-State
$out5a = Invoke-Hook -StdinJson '{"status":"aborted","loop_count":0}' -Register $fixture
$out5b = Invoke-Hook -StdinJson '{"status":"error","loop_count":0}' -Register $fixture
Write-Host ('  aborted: ' + $out5a + '   error: ' + $out5b)
Assert-True -Name 'stays silent on aborted' -Ok ($out5a -eq '{}') -Detail ('expected {}, got: ' + $out5a)
Assert-True -Name 'stays silent on error' -Ok ($out5b -eq '{}') -Detail ('expected {}, got: ' + $out5b)

# ---------------------------------------------------------------------------
# Case 6 - quiet when nothing is open
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host 'Case 6 - register exists but nothing is open' -ForegroundColor Yellow
Reset-State
New-Fixture -Path $empty -Body @'
{
  "register": "decisions_awaiting_jerome",
  "generated": "2026-09-19T00:00:00+02:00",
  "decisions": [
    { "id": "D01", "status": "decided", "urgency": "blocking", "title": "closed", "question": "closed?" }
  ],
  "safe_tier": []
}
'@
$out6 = Invoke-Hook -StdinJson '{"status":"completed","loop_count":0}' -Register $empty
Write-Host ('  output: ' + $out6)
Assert-True -Name 'stays silent with zero open items' -Ok ($out6 -eq '{}') -Detail ('expected {}, got: ' + $out6)
Assert-True -Name 'writes no state file when silent' -Ok (-not (Test-Path $state)) -Detail 'state file written on a silent run'

# ---------------------------------------------------------------------------
# Case 7 - quiet when the register cannot be read
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host 'Case 7 - register unreadable or absent' -ForegroundColor Yellow
Reset-State
New-Fixture -Path $broken -Body 'not json at all {{{'
$out7a = Invoke-Hook -StdinJson '{"status":"completed","loop_count":0}' -Register $broken
$out7b = Invoke-Hook -StdinJson '{"status":"completed","loop_count":0}' -Register $missing
Write-Host ('  broken: ' + $out7a + '   missing: ' + $out7b)
Assert-True -Name 'stays silent on a broken register' -Ok ($out7a -eq '{}') -Detail ('expected {}, got: ' + $out7a)
Assert-True -Name 'stays silent on a missing register' -Ok ($out7b -eq '{}') -Detail ('expected {}, got: ' + $out7b)

# ---------------------------------------------------------------------------
# Case 8 - the live register, content-independent properties only
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host 'Case 8 - the live register (properties that hold whatever is open)' -ForegroundColor Yellow
Reset-State
$out8 = Invoke-Hook -StdinJson '{"status":"completed","loop_count":0}' -Register $null
$liveCount = 0
$livePath = Join-Path $inbox 'DECISIONS_AWAITING_JEROME_2026-09-19.json'
if (Test-Path $livePath) {
    $live = Get-Content $livePath -Raw | ConvertFrom-Json
    $liveCount = @($live.decisions | Where-Object { $_.status -eq 'open' }).Count
}
Write-Host ('  open items in the live register: ' + $liveCount)
if ($liveCount -eq 0) {
    Assert-True -Name 'silent, because the live register has nothing open' -Ok ($out8 -eq '{}') -Detail ('expected {}, got: ' + $out8)
} else {
    Assert-True -Name 'fires against the real register' -Ok ($out8 -match 'followup_message') -Detail 'no followup_message from the live register'
    Assert-True -Name 'reports the live open count' -Ok ($out8 -match ("$liveCount decisions are waiting")) -Detail ('expected "' + $liveCount + ' decisions are waiting"')
    Assert-True -Name 'names the real register file' -Ok ($out8 -match 'DECISIONS_AWAITING_JEROME') -Detail 'register filename not named'
    Assert-True -Name 'parses as JSON with a string message' -Ok (
        (Test-Path variable:out8) -and
        ((($out8 | ConvertFrom-Json).followup_message) -is [string])
    ) -Detail 'followup_message is not a string'
}
Remove-State

# ---------------------------------------------------------------------------
# Case 9 - the .cursor and .codex hooks stay in step
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host 'Case 9 - the .cursor and .codex copies are byte-identical' -ForegroundColor Yellow
if (-not (Test-Path $twin)) {
    Assert-True -Name 'twin exists' -Ok $false -Detail ('not found: ' + $twin)
} else {
    $a = (Get-FileHash $hook -Algorithm SHA256).Hash
    $b = (Get-FileHash $twin -Algorithm SHA256).Hash
    Write-Host ('  .cursor ' + $a)
    Write-Host ('  .codex  ' + $b)
    Assert-True -Name 'byte-identical twins' -Ok ($a -eq $b) -Detail 'the twins differ'
}

# --- clean up fixtures ------------------------------------------------------
foreach ($f in @($fixture, $empty, $broken)) { Remove-Item $f -Force -ErrorAction SilentlyContinue }
Remove-State

# --- result ----------------------------------------------------------------
Write-Host ''
if ($failures.Count -eq 0) {
    Write-Host ('DECISIONS_HOOK_TEST_OK - ' + $passes + ' assertions passed') -ForegroundColor Green
    exit 0
}
Write-Host ('DECISIONS_HOOK_TEST_FAIL - ' + $failures.Count + ' failed, ' + $passes + ' passed') -ForegroundColor Red
foreach ($f in $failures) { Write-Host ('  - ' + $f) -ForegroundColor Red }
exit 1
