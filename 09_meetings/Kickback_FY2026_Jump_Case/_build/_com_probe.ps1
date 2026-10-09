$ErrorActionPreference = "Stop"
$Deck = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\ISZE_Kickback_Japan_Pack_20261007.pptx"
$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($Deck, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
Write-Output ("type=" + $pres.GetType().FullName)
Write-Output ("slides=" + $pres.Slides.Count)
$pres.Close()
$ppt.Quit()
