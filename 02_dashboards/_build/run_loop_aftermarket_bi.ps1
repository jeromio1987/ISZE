# Aftermarket BI watchdog — 10-minute tick with verify + rebuild + log
# Writes every action to loop_aftermarket_bi.log (timestamps). Safe to run foreground or via start script.
param(
    [switch]$Once
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ISZE = Split-Path -Parent (Split-Path -Parent $root)
$logPath = Join-Path $root 'loop_aftermarket_bi.log'
$pidPath = Join-Path $root '.loop_aftermarket_bi.pid'
$buildPy = Join-Path $root 'build_aftermarket_bi_command_center.py'
$verifyPy = Join-Path $root 'verify_aftermarket_bi_command_center.py'
$verifyTierPy = Join-Path $root 'verify_tier_a_html_json.py'
$intervalSec = 600

function Write-LoopLog {
    param([string]$Message, [string]$Level = 'INFO')
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$ts] [$Level] $Message"
    Add-Content -Path $logPath -Value $line -Encoding utf8
    # Do not Write-Output — pollutes Invoke-AftermarketBiTick return value
}

function Invoke-AftermarketBiTick {
    Write-LoopLog 'TICK start — verify Aftermarket BI Command Center SSR'
    $fail = $false
    $reason = @()

    if (-not (Test-Path $verifyPy)) {
        Write-LoopLog "MISSING verify script: $verifyPy" 'ERROR'
        return $false
    }

    Push-Location $ISZE
    try {
        $v1 = & python $verifyPy 2>&1 | Out-String
        Write-LoopLog ("verify_aftermarket_bi: " + ($v1 -replace '\s+', ' ').Trim())
        if ($LASTEXITCODE -ne 0) {
            $fail = $true
            $reason += 'verify_aftermarket_bi failed'
        }

        if (Test-Path $verifyTierPy) {
            $v2 = & python $verifyTierPy 2>&1 | Out-String
            Write-LoopLog ("verify_tier_a: " + ($v2 -replace '\s+', ' ').Trim())
            if ($LASTEXITCODE -ne 0) {
                $fail = $true
                $reason += 'verify_tier_a failed'
            }
        }
    }
    finally {
        Pop-Location
    }

    if ($fail) {
        Write-LoopLog ("REBUILD --all triggered: " + ($reason -join '; ')) 'WARN'
        Push-Location $ISZE
        try {
            $rb = & python $buildPy --all 2>&1 | Out-String
            Write-LoopLog ("rebuild output: " + ($rb -replace '\s+', ' ').Trim().Substring(0, [Math]::Min(800, ($rb -replace '\s+', ' ').Trim().Length)))
            if ($LASTEXITCODE -ne 0) {
                Write-LoopLog 'REBUILD failed' 'ERROR'
                return $false
            }
            $v3 = & python $verifyPy 2>&1 | Out-String
            Write-LoopLog ("post-rebuild verify: " + ($v3 -replace '\s+', ' ').Trim())
            if ($LASTEXITCODE -ne 0) {
                Write-LoopLog 'post-rebuild verify still failing' 'ERROR'
                return $false
            }
            Write-LoopLog 'TICK OK — rebuilt and verified' 'OK'
            return $true
        }
        finally {
            Pop-Location
        }
    }

    Write-LoopLog 'TICK OK — verify passed, no rebuild needed' 'OK'
    return $true
}

# Record this loop instance
$PID | Out-File -FilePath $pidPath -Encoding ascii -NoNewline
Write-LoopLog "LOOP start pid=$PID once=$Once interval=${intervalSec}s"

if ($Once) {
    $ok = Invoke-AftermarketBiTick
    Write-LoopLog "LOOP once exit ok=$ok"
    if (-not $ok) { exit 1 }
    exit 0
}

# First tick immediately, then every 10 minutes
while ($true) {
    $null = Invoke-AftermarketBiTick
    Write-LoopLog "AGENT_LOOP_TICK_aftermarket_bi sleep ${intervalSec}s — check $logPath for last result"
    Start-Sleep -Seconds $intervalSec
}
