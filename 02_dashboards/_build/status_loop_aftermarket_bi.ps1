# Is the Aftermarket BI watchdog loop running?
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidPath = Join-Path $root '.loop_aftermarket_bi.pid'
$logPath = Join-Path $root 'loop_aftermarket_bi.log'

Write-Host '=== Aftermarket BI loop status ==='

$running = $false
if (Test-Path $pidPath) {
    $loopPidFromFile = (Get-Content $pidPath -Raw).Trim()
    if ($loopPidFromFile -match '^\d+$') {
        $proc = Get-Process -Id ([int]$loopPidFromFile) -ErrorAction SilentlyContinue
        if ($proc) {
            $running = $true
            Write-Host "RUNNING  pid=$loopPidFromFile  started=$($proc.StartTime)"
        } else {
            Write-Host "STALE    pid file=$loopPidFromFile but process dead - run start_loop_aftermarket_bi.ps1"
        }
    }
} else {
    Write-Host 'STOPPED  no .loop_aftermarket_bi.pid'
}

Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*run_loop_aftermarket_bi.ps1*' -and $_.CommandLine -notlike '*-Once*' } |
    ForEach-Object {
        if (-not $running) {
            Write-Host "ORPHAN   pid=$($_.ProcessId) (no pid file)"
            $running = $true
        }
    }

if (-not $running) {
    Write-Host 'VERDICT  not running'
} else {
    Write-Host 'VERDICT  loop active'
}

if (Test-Path $logPath) {
    Write-Host ''
    Write-Host 'Last 5 log lines:'
    Get-Content $logPath -Tail 5 | ForEach-Object { Write-Host "  $_" }
    $lastTick = Select-String -Path $logPath -Pattern 'TICK OK|REBUILD|LOOP start' | Select-Object -Last 1
    if ($lastTick) {
        Write-Host ''
        Write-Host "Last tick: $($lastTick.Line)"
    }
} else {
    Write-Host 'Log file missing - loop never started.'
}
