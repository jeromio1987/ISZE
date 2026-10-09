param(
    [string]$Deck = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\ISZE_Kickback_Japan_Pack_20261007.pptx",
    [string]$Tmp = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\_build\_reopen_probe.pptx"
)
$ErrorActionPreference = "Stop"
$ppt = New-Object -ComObject PowerPoint.Application

# 1  open the deliverable read-only and report what PowerPoint sees
$p1 = $ppt.Presentations.Open($Deck, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
Write-Output ("OPEN_OK slides=" + $p1.Slides.Count + " width=" + $p1.PageSetup.SlideWidth + " height=" + $p1.PageSetup.SlideHeight)
$p1.Close()

# 2  round trip: copy, open, save-as, reopen, count
if (Test-Path $Tmp) { Remove-Item $Tmp -Force }
Copy-Item $Deck $Tmp -Force
$p2 = $ppt.Presentations.Open($Tmp, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
$p2.Save()
$p2.Close()
$p3 = $ppt.Presentations.Open($Tmp, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
Write-Output ("ROUNDTRIP_OK slides=" + $p3.Slides.Count)
$p3.Close()
$ppt.Quit()
Remove-Item $Tmp -Force
Write-Output "OPEN_TEST_DONE"
