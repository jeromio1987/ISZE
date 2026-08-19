# Start PRISM Streamlit (opens browser on Windows).
# Legacy port 8501. Canonical daily launcher is ..\run_prism.ps1 (8503).
$ErrorActionPreference = "Stop"
$env:PRISM_INTERNAL = "false"
$PrismRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $PrismRoot

Write-Host "PRISM root: $PrismRoot" -ForegroundColor Cyan

function Test-PythonModule($name) {
    python -c "import $name" 2>$null
    return $LASTEXITCODE -eq 0
}

if (-not (Test-PythonModule "streamlit")) {
    Write-Host "Installing dependencies from requirements.txt ..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
}

$port = 8501
$url = "http://localhost:$port"

# If something is already listening, open browser only.
$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    Write-Host "Port $port already in use — opening browser (PRISM may already be running)." -ForegroundColor Green
    Start-Process $url
    exit 0
}

Write-Host "Starting PRISM → $url" -ForegroundColor Green
Write-Host "Leave this window open. Press Ctrl+C to stop." -ForegroundColor DarkGray

$openJob = Start-Job -ScriptBlock {
    param($u)
    Start-Sleep -Seconds 3
    Start-Process $u
} -ArgumentList $url

try {
    python -m streamlit run app.py --server.port $port
} finally {
    Stop-Job $openJob -ErrorAction SilentlyContinue
    Remove-Job $openJob -Force -ErrorAction SilentlyContinue
}
