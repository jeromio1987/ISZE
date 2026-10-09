param(
    [string]$Deck = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\_build\_ring_probe.pptx",
    [string]$OutDir = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\_build\_render",
    [int]$W = 1920,
    [int]$H = 1080
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }
Get-ChildItem $OutDir -Filter *.png -ErrorAction SilentlyContinue | Remove-Item -Force

$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($Deck, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
$n = $pres.Slides.Count
Write-Output ("SLIDES=" + $n)
for ($i = 1; $i -le $n; $i++) {
    $file = Join-Path $OutDir ("s{0:d2}.png" -f $i)
    $pres.Slides.Item($i).Export($file, "PNG", $W, $H)
    if (Test-Path $file) { Write-Output ("exported " + $file) } else { Write-Output ("MISSING " + $file) }
}
$pres.Close()
$ppt.Quit()
Write-Output "DONE"
