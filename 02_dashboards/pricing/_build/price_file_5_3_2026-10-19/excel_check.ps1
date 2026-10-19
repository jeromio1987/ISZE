$f = "C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\ISZE_Price_Revision_5.3pct_2026-10-19.xlsx"
$qa = "C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\price_file_5_3_2026-10-19\_qa"
$x = New-Object -ComObject Excel.Application; $x.Visible = $false; $x.DisplayAlerts = $false
try {
  $wb = $x.Workbooks.Open($f); $x.CalculateFull()
  $s = $wb.Worksheets.Item("1 Summary")
  "billed=" + $s.Range("B5").Value2; "extra=" + $s.Range("B6").Value2; "pct=" + $s.Range("B7").Value2; "parts=" + $s.Range("B8").Value2
  $a = $wb.Worksheets.Item("3 All parts")
  "row2 " + $a.Range("A2").Value2 + " | " + $a.Range("M2").Text + " -> " + $a.Range("O2").Text + " | " + $a.Range("AF2").Text
  $err = 0; foreach ($c in $a.UsedRange.SpecialCells(-4123, 16)) { $err++ } ; "errors=" + $err
} catch { "errcheck: " + $_.Exception.Message }
try {
  foreach ($n in @("1 Summary","2 By market and family")) {
    $w = $wb.Worksheets.Item($n); $w.PageSetup.Orientation = 2; $w.PageSetup.Zoom = $false; $w.PageSetup.FitToPagesWide = 1; $w.PageSetup.FitToPagesTall = $false
  }
  $wb.Save()
  $wb.Worksheets.Item("1 Summary").Select(); 
  $sheets = @("1 Summary","2 By market and family")
  $i=0; foreach ($n in $sheets) { $i++; $wb.Worksheets.Item($n).ExportAsFixedFormat(0, "$qa\tab$i.pdf") }
} finally { $wb.Close($true); $x.Quit() }
