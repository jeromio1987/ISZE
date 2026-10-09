$ErrorActionPreference = "Stop"
$Deck = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\ISZE_Kickback_Japan_Pack_20261007.pptx"
$OutDir = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\_qa_japan"
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
Get-ChildItem $OutDir -Filter *.png -ErrorAction SilentlyContinue | Remove-Item -Force

$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($Deck, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
$n = $pres.Slides.Count
for ($i = 1; $i -le $n; $i++) {
    $file = Join-Path $OutDir ("s{0:d2}.png" -f $i)
    $pres.Slides.Item($i).Export($file, "PNG", 1920, 1080)
    if (Test-Path $file) { Write-Output ("exported " + $file) } else { Write-Output ("MISSING " + $file) }
}
$pres.Close()
$ppt.Quit()
Write-Output ("SLIDES=" + $n)
