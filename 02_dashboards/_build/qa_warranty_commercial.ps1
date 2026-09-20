# Warranty commercial review — render QA
# QA-internal only. Not a user-facing launch.
#
# Cache discipline: Chrome caches file:// pages on disk, so a repeat run can silently re-shoot the
# previous build. Each shot therefore gets a cache-busting query and the profile is fresh per run.
$ErrorActionPreference = 'Continue'
$chrome = @(
  "C:\Program Files\Google\Chrome\Application\chrome.exe",
  "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
  "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $chrome) { Write-Host "NO_CHROME_FOUND"; exit 1 }

$root = "C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales"
$file = Join-Path $root "Warranty_Commercial_Review.html"
$qa   = Join-Path $root "_qa_warranty"
New-Item -ItemType Directory -Force -Path $qa | Out-Null
$profile = Join-Path $env:TEMP ("qa_warranty_" + [guid]::NewGuid().ToString("N").Substring(0,8))
$stamp = [guid]::NewGuid().ToString("N").Substring(0,8)
$url  = "file:///" + ($file -replace '\\','/') + "?v=$stamp"

Write-Host ("html built: " + (Get-Item $file).LastWriteTime.ToString("HH:mm:ss") + "  size " + (Get-Item $file).Length)
Write-Host ("cache-buster: " + $stamp)

$shots = @(
  @{ name = "01_top";              w = 1440; h = 1150 },
  @{ name = "02_two_bills";        w = 1440; h = 1250 },
  @{ name = "03_concentration";    w = 1440; h = 1000 },
  @{ name = "04_limits";           w = 1440; h = 1100 },
  @{ name = "05_truck_books";      w = 1440; h = 1200 },
  @{ name = "06_vs_the_business";  w = 1440; h = 1150 },
  @{ name = "07_who_pays";         w = 1440; h = 1150 },
  @{ name = "08_anomalies";        w = 1440; h = 1100 },
  @{ name = "09_narrow_780";       w = 780;  h = 1500 }
)
foreach ($s in $shots) {
  $out = Join-Path $qa ($s.name + ".png")
  if (Test-Path $out) { Remove-Item $out -Force }
  & $chrome --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 `
            --user-data-dir="$profile" --disk-cache-dir="$profile\cache" `
            --virtual-time-budget=9000 --window-size="$($s.w),$($s.h)" `
            --screenshot="$out" $url 2>$null | Out-Null
  if (Test-Path $out) { Write-Host ("OK   {0}  {1} bytes" -f $s.name, (Get-Item $out).Length) }
  else { Write-Host ("FAIL {0}" -f $s.name) }
}
Remove-Item $profile -Recurse -Force -ErrorAction SilentlyContinue
