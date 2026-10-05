# ISZE OS Hub — headless Chrome QA screenshots
# QA-internal only. Not a user-facing launch.
$ErrorActionPreference = 'Continue'
$chrome = @(
  "C:\Program Files\Google\Chrome\Application\chrome.exe",
  "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
  "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $chrome) { Write-Host "NO_CHROME_FOUND"; exit 1 }
Write-Host "chrome: $chrome"

$root  = "C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub"
$qa    = Join-Path $root "_qa"
New-Item -ItemType Directory -Force -Path $qa | Out-Null
$url   = "file:///" + ((Join-Path $root "ISZE_OS_Hub.html") -replace '\\','/')

$shots = @(
  @{ name = "01_top_1440";        w = 1440; h = 1100 },
  @{ name = "02_stack_1440";      w = 1440; h = 1500 },
  @{ name = "03_joins_market_1440"; w = 1440; h = 1700 },
  @{ name = "04_bars_gaps_1440";  w = 1440; h = 1700 },
  @{ name = "05_links_carry_1440"; w = 1440; h = 1900 },
  @{ name = "06_narrow_760";      w = 760;  h = 1500 }
)

foreach ($s in $shots) {
  $out = Join-Path $qa ($s.name + ".png")
  if (Test-Path $out) { Remove-Item $out -Force }
  & $chrome --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 `
            --virtual-time-budget=6000 --window-size="$($s.w),$($s.h)" `
            --screenshot="$out" $url 2>$null | Out-Null
  if (Test-Path $out) {
    $len = (Get-Item $out).Length
    Write-Host ("OK   {0}  {1} bytes" -f $s.name, $len)
  } else {
    Write-Host ("FAIL {0}  no file written" -f $s.name)
  }
}

# print-to-PDF render as a second modality (page-count / blank-page check)
$pdf = Join-Path $qa "ISZE_OS_Hub.pdf"
if (Test-Path $pdf) { Remove-Item $pdf -Force }
& $chrome --headless=new --disable-gpu --no-pdf-header-footer `
          --virtual-time-budget=8000 --print-to-pdf="$pdf" $url 2>$null | Out-Null
if (Test-Path $pdf) { Write-Host ("OK   pdf  {0} bytes" -f (Get-Item $pdf).Length) }
else { Write-Host "FAIL pdf" }
