$path = "C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\Pricing_Revision_AIM_Source_Analysis.xlsx"
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$xl.AskToUpdateLinks = $false
$wb = $xl.Workbooks.Open($path)
foreach ($name in @("Read me","DB summary","DB x AIM L1","DB x AIM L2","DB x AIM L3","TH-JP source","Source x AIM L1","Customer","Top movers","PN data","Checks")) {
  $ws = $wb.Worksheets.Item($name)
  if ($ws.Columns.Item(2).ColumnWidth -lt 28) { $ws.Columns.Item(2).ColumnWidth = 28 }
}
$xl.CalculateFullRebuild()
$wb.Save()
$ws = $wb.Worksheets.Item("DB x AIM L1")
Write-Host ("D5=" + $ws.Range("D5").Text + " F5=" + $ws.Range("F5").Text + " I5=" + $ws.Range("I5").Text)
$chk = $wb.Worksheets.Item("Checks")
Write-Host ("step=" + $chk.Range("B6").Text + " diff=" + $chk.Range("B8").Text)
$wb.Close($false)
$xl.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($wb) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($xl) | Out-Null
Write-Host "DONE"
