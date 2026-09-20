# EQ-Hit session runner — fires 2026-09-19 23:00 local
# Opens pack + EQ URL. Does NOT patch aim_master.
# Requires: PowerShell 5+ ; optional logged-in Snap-on browser for scrape.

$ErrorActionPreference = "Continue"
$ISZE = "C:\Users\jerom\Desktop\claude\ISZE"
$INBOX = Join-Path $ISZE "01_data\90_INBOX"
$BUILD = Join-Path $ISZE "01_data\91_build"
$PRICING = Join-Path $ISZE "01_data\01_Pricing"
$STAMP = "20260919"
$Log = Join-Path $INBOX "_EQ_HIT_SESSION_${STAMP}_log.txt"
$Wake = Join-Path $INBOX "_EQ_HIT_SESSION_${STAMP}_AGENT_WAKE.md"
$Prompt = Join-Path $ISZE "00_docs\agent\EQ_HIT_SESSION_${STAMP}_PROMPT.md"
$Brief = Join-Path $INBOX "_EQ_HIT_SESSION_${STAMP}_BRIEF.md"
$Xlsx = Join-Path $PRICING "EQ_HIT_SESSION_${STAMP}.xlsx"
$Csv = Join-Path $INBOX "_EQ_HIT_SESSION_${STAMP}_queue.csv"
$Json = Join-Path $INBOX "_EQ_HIT_SESSION_${STAMP}_queue.json"
$OpenCmd = Join-Path $INBOX "OPEN_EQ_HIT_SESSION_${STAMP}.cmd"
$EqUrl = "https://isuzu.snaponepc.com/epc/#/"
$Builder = Join-Path $BUILD "build_eq_hit_session_${STAMP}.py"

function Write-Log([string]$msg) {
  $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
  Add-Content -Path $Log -Value $line -Encoding UTF8
  Write-Host $line
}

# --- START stamp ---
$startStamp = Join-Path $INBOX "_EQ_HIT_SESSION_${STAMP}_START.txt"
@"
EQ_HIT_SESSION_${STAMP} START
local_time=$([DateTime]::Now.ToString('o'))
timezone=Europe/Brussels (Windows local)
aim_apply=NO
runner=$PSCommandPath
"@ | Set-Content -Path $startStamp -Encoding UTF8

Write-Log "START stamp written: $startStamp"

# --- Refresh queue from current residual (safe rebuild, no AIM apply) ---
if (Test-Path $Builder) {
  Write-Log "Refreshing queue via $Builder"
  try {
    & python $Builder 2>&1 | Tee-Object -FilePath $Log -Append
    Write-Log "Queue refresh exit=$LASTEXITCODE"
  } catch {
    Write-Log "Queue refresh FAILED: $_"
  }
} else {
  Write-Log "Builder missing — using existing queue files"
}

# --- Open pack ---
Write-Log "Opening brief / Excel / EQ URL"
if (Test-Path $OpenCmd) {
  cmd /c "`"$OpenCmd`""
} else {
  if (Test-Path $Brief) { Start-Process $Brief }
  if (Test-Path $Xlsx) { Start-Process $Xlsx } elseif (Test-Path $Csv) { Start-Process $Csv }
  Start-Process $EqUrl
}

# --- Agent wake note (scrape needs logged-in Snap-on) ---
$wakeBody = @"
# EQ-Hit session — agent wake ($STAMP)

Fired at: $([DateTime]::Now.ToString('o'))

## Status

The scheduled runner opened the brief, the Excel/CSV queue, and the Snap-on EQ URL.
**AIM master was NOT patched.**

EQ scrape **cannot run fully unattended** unless a Snap-on session is already
logged in on this PC. If the browser shows a login page, Jerome (or an agent
with an interactive browser) must sign in first.

## Exact prompt for Cursor overnight agent

Open and follow:

``$Prompt``

Short form of the job:

1. Confirm queue at ``$Csv`` / ``$Json`` (refresh already attempted).
2. If Snap-on is logged in, process queue **top-down by billed euro** using the
   console scraper ``$INBOX\_eq_hit_doubt_console_scraper_20260918.js``
   (or equivalent Playwright/CDP if a live session exists).
3. Write results only to:
   - ``$INBOX\_EQ_HIT_SESSION_${STAMP}_RESULTS.csv``
   - ``$INBOX\_EQ_HIT_SESSION_${STAMP}_RESULTS.json``
4. Append progress to ``$Log``.
5. **Stop** — do not apply AIM. Do not run apply scripts.

## Stop conditions

- Queue exhausted, OR
- Snap-on login required and no interactive session, OR
- Jerome says stop.

When blocked on login, leave this wake file and the START stamp; do not invent classifications.
"@
Set-Content -Path $Wake -Value $wakeBody -Encoding UTF8
Write-Log "Agent wake note: $Wake"

# Copy prompt into log for visibility
if (Test-Path $Prompt) {
  Write-Log "Prompt present: $Prompt"
} else {
  Write-Log "WARNING: prompt missing: $Prompt"
}

Write-Log "DONE runner (open + wake). Unattended EQ scrape depends on logged-in Snap-on."
exit 0
