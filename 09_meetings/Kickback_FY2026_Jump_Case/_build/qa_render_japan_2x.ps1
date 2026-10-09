param(
    [string]$Deck = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\ISZE_Kickback_Japan_Pack_20261007.pptx",
    [string]$OutDir = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\_qa_japan_2x",
    [int[]]$Slides = @(4,5,6,7,8,9),
    [int]$W = 3840,
    [int]$H = 2160
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }
Get-ChildItem $OutDir -Filter *.png -ErrorAction SilentlyContinue | Remove-Item -Force

$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($Deck, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
Write-Output ("SLIDES=" + $pres.Slides.Count)
foreach ($i in $Slides) {
    $file = Join-Path $OutDir ("x{0:d2}.png" -f $i)
    $pres.Slides.Item($i).Export($file, "PNG", $W, $H)
    if (Test-Path $file) { Write-Output ("exported " + $file) } else { Write-Output ("MISSING " + $file) }
}
$pres.Close()
$ppt.Quit()
Write-Output "DONE"
