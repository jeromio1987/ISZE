# Start Aftermarket BI loop in background — kills stale instances first
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$loopScript = Join-Path $root 'run_loop_aftermarket_bi.ps1'
$pidPath = Join-Path $root '.loop_aftermarket_bi.pid'
$logPath = Join-Path $root 'loop_aftermarket_bi.log'

function Stop-StaleLoop {
    if (Test-Path $pidPath) {
        $oldPid = (Get-Content $pidPath -Raw).Trim()
        if ($oldPid -match '^\d+$') {
            $proc = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "Stopping stale loop PID $oldPid"
                Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 1
            }
        }
        Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
    }
    Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*run_loop_aftermarket_bi.ps1*' } |
        ForEach-Object {
            Write-Host "Stopping orphan loop PID $($_.ProcessId)"
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
}

Stop-StaleLoop
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Add-Content -Path $logPath -Value "[$ts] [INFO] start_loop - launching background watchdog" -Encoding utf8

$job = Start-Process -FilePath 'powershell.exe' `
    -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', $loopScript) `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 3
$loopPid = $null
if (Test-Path $pidPath) {
    $loopPid = (Get-Content $pidPath -Raw).Trim()
}
$alive = $false
if ($loopPid -match '^\d+$') {
    $proc = Get-Process -Id ([int]$loopPid) -ErrorAction SilentlyContinue
    $alive = [bool]$proc
}

if ($alive) {
    Write-Host "Aftermarket BI loop RUNNING pid=$loopPid (launcher=$($job.Id))"
} else {
    Write-Host "WARN: loop may have failed - check tail of $logPath"
    if (Test-Path $logPath) { Get-Content $logPath -Tail 5 }
}

$statusScript = Join-Path $root 'status_loop_aftermarket_bi.ps1'
$stopScript = Join-Path $root 'stop_loop_aftermarket_bi.ps1'
Write-Host "Log: $logPath"
Write-Host "Status: powershell -NoProfile -File $statusScript"
Write-Host "Stop: powershell -NoProfile -File $stopScript"
