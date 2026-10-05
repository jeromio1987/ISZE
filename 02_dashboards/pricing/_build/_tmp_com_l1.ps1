$path = "C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\Pricing_Revision_AIM_Source_Analysis.xlsx"
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$xl.AskToUpdateLinks = $false
$wb = $xl.Workbooks.Open($path)
$xl.CalculateFullRebuild()

$ws = $wb.Worksheets.Item("DB x AIM L1")
Write-Host ("D5=" + $ws.Range("D5").Text + " E5=" + $ws.Range("E5").Text + " F5=" + $ws.Range("F5").Text)
Write-Host ("G5=" + $ws.Range("G5").Text + " I5=" + $ws.Range("I5").Text + " J5=" + $ws.Range("J5").Text)
Write-Host ("D5.Value2=" + $ws.Range("D5").Value2)
Write-Host ("F5.Value2=" + $ws.Range("F5").Value2)
Write-Host ("D5.Formula=" + $ws.Range("D5").Formula)
Write-Host ("F5.Formula=" + $ws.Range("F5").Formula)

$blank = 0; $ok = 0
for ($r = 5; $r -le 24; $r++) {
  $v = $ws.Range("F$r").Value2
  if ($null -eq $v -or $v -eq "") { $blank++ } else { $ok++ }
}
Write-Host ("F5:F24 blank=$blank ok=$ok")

$ws2 = $wb.Worksheets.Item("DB summary")
Write-Host ("DB summary H5=" + $ws2.Range("H5").Text + " M5=" + $ws2.Range("M5").Text)

$chk = $wb.Worksheets.Item("Checks")
Write-Host ("Checks step=" + $chk.Range("B8").Text + " wtd=" + $chk.Range("B10").Text)

# Sample L2 / TH-JP
$l2 = $wb.Worksheets.Item("DB x AIM L2")
Write-Host ("L2 F5=" + $l2.Range("F5").Text + " G5=" + $l2.Range("G5").Text)
$th = $wb.Worksheets.Item("TH-JP source")
Write-Host ("THJP F5=" + $th.Range("F5").Text + " D5=" + $th.Range("D5").Text)

$wb.Close($false)
$xl.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($wb) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($xl) | Out-Null
Write-Host "DONE"
