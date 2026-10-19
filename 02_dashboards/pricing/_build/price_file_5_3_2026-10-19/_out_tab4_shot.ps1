$f = "C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\price_file_5_3_2026-10-19\_out\ISZE_Price_Revision_5.3pct_2026-10-19.xlsx"
$x = New-Object -ComObject Excel.Application; $x.Visible = $false; $x.DisplayAlerts = $false
$wb = $x.Workbooks.Open($f, 0, $true)
try { $w = $wb.Worksheets.Item("3 All parts"); $w.PageSetup.PrintArea = "A1:AH30"; $w.PageSetup.Orientation = 2; $w.PageSetup.Zoom = $false; $w.PageSetup.FitToPagesWide = 1; $w.PageSetup.FitToPagesTall = 1
  $w.ExportAsFixedFormat(0, "C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\price_file_5_3_2026-10-19\_qa\tab4.pdf") } finally { $wb.Close($false); $x.Quit() }
