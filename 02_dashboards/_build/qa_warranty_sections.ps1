# Warranty commercial review — render QA, per-section.
# QA-internal only.
#
# Why this exists: a full-page screenshot at a fixed window height always shows the TOP of the page.
# Reading "section 6" from a 1150px shot of a 6000px page shows sections 1-2, not section 6. This
# script scrolls to each section id, waits, and captures the viewport at that position.
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
$profile = Join-Path $env:TEMP ("qa_wsec_" + [guid]::NewGuid().ToString("N").Substring(0,8))
$stamp = [guid]::NewGuid().ToString("N").Substring(0,8)
$url  = "file:///" + ($file -replace '\\','/') + "?v=$stamp"
Write-Host ("html: " + (Get-Item $file).LastWriteTime.ToString("HH:mm:ss") + " " + (Get-Item $file).Length + " bytes")

# The page carries static anchors h2#sec1..sec8, so each capture opens straight onto its section
# with a native fragment link. Chrome screenshots the fragment target without any scroll script.
$sections = 1..8
foreach ($i in $sections) {
  $out = Join-Path $qa ("sec{0}.png" -f $i)
  if (Test-Path $out) { Remove-Item $out -Force }
  $u = $url + "#sec$i"
  & $chrome --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 `
            --user-data-dir="$profile" --disk-cache-dir="$profile\cache" `
            --virtual-time-budget=9000 --window-size="1440,1250" `
            --screenshot="$out" $u 2>$null | Out-Null
  if (Test-Path $out) { Write-Host ("OK   sec{0}  {1} bytes" -f $i, (Get-Item $out).Length) }
  else { Write-Host ("FAIL sec{0}" -f $i) }
}
Remove-Item $profile -Recurse -Force -ErrorAction SilentlyContinue
