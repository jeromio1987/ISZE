# run_globe_server.ps1
#
# Starts the local web server the globe page needs, then reports the port.
#
# Why a server at all: MapLibre GL JS runs its data processing in a Web Worker.
# Browsers refuse to start a Worker from a file:// origin, so double-clicking
# index.html directly cannot work. The page also reads its numbers with
# fetch(), which file:// blocks for the same reason. Served over http://
# localhost both work.
#
# Behaviour
#   - If something is already answering on the start port with our page, reuse it.
#   - Otherwise walk up from the start port until a free port is found.
#   - Start `python -m http.server` bound to 127.0.0.1, detached, minimised.
#   - Wait until the page actually answers over HTTP before reporting success.
#   - Write the chosen port to -PortFile so the .cmd launcher can open the URL.
#
# Usage
#   powershell -NoProfile -ExecutionPolicy Bypass -File run_globe_server.ps1
#   powershell ... -File run_globe_server.ps1 -PortFile "$env:TEMP\p.txt"
#
# Exit codes: 0 = a server is answering, 1 = could not get one up.

[CmdletBinding()]
param(
    [int]$StartPort = 8511,
    [int]$MaxTries = 20,
    [string]$PortFile = "",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Page = "index.html"

function Write-Info($msg) {
    if (-not $Quiet) { Write-Host $msg }
}

# --- does a port already answer with our page? --------------------------------
function Test-GlobeServer([int]$port) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/$Page" `
            -TimeoutSec 3 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            # Make sure it is our page and not some other app on this port.
            return ($response.Content -match "ISZE Globe")
        }
    } catch { }
    return $false
}

# --- is a port free to bind? -------------------------------------------------
function Test-PortFree([int]$port) {
    try {
        $listener = New-Object System.Net.Sockets.TcpListener(
            [System.Net.IPAddress]::Loopback, $port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

function Find-Python {
    foreach ($name in @("python", "python3", "py")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

# --- 1. reuse an existing globe server ---------------------------------------
$port = $StartPort
while ($port -lt ($StartPort + $MaxTries)) {
    if (Test-GlobeServer $port) {
        Write-Info "Globe server already running on port $port - reusing it."
        if ($PortFile) { Set-Content -Path $PortFile -Value $port -NoNewline -Encoding ascii }
        Write-Info "http://localhost:$port/$Page"
        exit 0
    }
    if (-not (Test-PortFree $port)) {
        Write-Info "Port $port is busy with something else - trying the next one."
        $port++
        continue
    }
    break
}

if ($port -ge ($StartPort + $MaxTries)) {
    Write-Error "No free port found between $StartPort and $($StartPort + $MaxTries)."
    exit 1
}

# --- 2. start the server -----------------------------------------------------
$python = Find-Python
if (-not $python) {
    Write-Error "Python was not found on PATH. The globe needs it for the local web server."
    exit 1
}

Write-Info "Starting local web server on port $port from $Root"
Start-Process -FilePath $python `
    -ArgumentList "-m", "http.server", $port, "--bind", "127.0.0.1" `
    -WorkingDirectory $Root `
    -WindowStyle Minimized | Out-Null

# --- 3. wait until it actually answers ---------------------------------------
$ok = $false
for ($i = 1; $i -le 40; $i++) {
    Start-Sleep -Milliseconds 250
    if (Test-GlobeServer $port) { $ok = $true; break }
}

if (-not $ok) {
    Write-Error "Server was started on port $port but $Page did not answer within 10 seconds."
    exit 1
}

if ($PortFile) { Set-Content -Path $PortFile -Value $port -NoNewline -Encoding ascii }
Write-Info "Globe server ready."
Write-Info "http://localhost:$port/$Page"
exit 0
