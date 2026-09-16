# Stop Aftermarket BI background loop
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidPath = Join-Path $root '.loop_aftermarket_bi.pid'
$logPath = Join-Path $root 'loop_aftermarket_bi.log'

$stopped = $false
if (Test-Path $pidPath) {
    $pid = (Get-Content $pidPath -Raw).Trim()
    if ($pid -match '^\d+$') {
        Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue
        $stopped = $true
        Write-Host "Stopped loop PID $pid"
    }
    Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
}

Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*run_loop_aftermarket_bi.ps1*' } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        $stopped = $true
        Write-Host "Stopped orphan loop PID $($_.ProcessId)"
    }

if (-not $stopped) { Write-Host 'No running loop found.' }
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Add-Content -Path $logPath -Value "[$ts] [INFO] stop_loop - watchdog stopped" -Encoding utf8
