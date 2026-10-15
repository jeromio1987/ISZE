$p = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\ISZE_Parts_Price_Revision_Workbook_Oct2026_clearer_labels_2026-10-15.xlsx'
$out = 'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_qa_sim_20261015\summary_labels.pdf'
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false
try {
  $wb = $xl.Workbooks.Open($p, 0, $true)
  $xl.Calculation = -4135
  $s = $wb.Worksheets.Item('Summary')
  $s.PageSetup.PrintArea = 'A1:E12'
  $s.PageSetup.Orientation = 2
  $s.PageSetup.Zoom = $false; $s.PageSetup.FitToPagesWide = 1; $s.PageSetup.FitToPagesTall = 1
  $s.PageSetup.PrintComments = 1
  $s.ExportAsFixedFormat(0, $out)
  "column A width: " + $s.Columns(1).ColumnWidth + " | comments: " + $s.Comments.Count
  $wb.Close($false)
} finally { $xl.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($xl) }
