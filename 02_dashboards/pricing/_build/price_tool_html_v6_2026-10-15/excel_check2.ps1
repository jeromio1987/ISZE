param([string]$Path)
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false
try {
  $wb = $xl.Workbooks.Open($Path, 0, $true)
  $xl.CalculateFull()
  "sheets: " + (($wb.Worksheets | ForEach-Object { $_.Name }) -join ', ')
  $ck = $wb.Worksheets.Item('Checks'); $bad = 0
  for ($r = 4; $r -le 14; $r++) {
    $res = $ck.Cells.Item($r,5).Text; if ($res -ne 'OK') { $bad++ }
    "{0,-42} page={1,18} excel={2,18} {3}" -f $ck.Cells.Item($r,1).Text, $ck.Cells.Item($r,2).Value2, $ck.Cells.Item($r,3).Value2, $res
  }
  "check lines not OK: $bad"
  $se = $wb.Worksheets.Item('Settings'); "Settings B21={0} B22={1} B17={2}" -f $se.Range('B21').Value2, $se.Range('B22').Text, $se.Range('B17').Value2
  $l1 = $wb.Worksheets.Item('By L1'); $last = $l1.Cells($l1.Rows.Count, 2).End(-4162).Row
  "By L1 total row {0}: billed={1} extra={2} (Settings B20={3})" -f $l1.Cells.Item($last,2).Text, $l1.Cells.Item($last,3).Value2, $l1.Cells.Item($last,5).Value2, $se.Range('B20').Value2
  $mk = $wb.Worksheets.Item('By market'); $ml = $mk.Cells($mk.Rows.Count, 1).End(-4162).Row
  "By market total row {0}: billed={1} extra={2}" -f $mk.Cells.Item($ml,1).Text, $mk.Cells.Item($ml,2).Value2, $mk.Cells.Item($ml,4).Value2
  $pt = $wb.Worksheets.Item('Parts')
  "Parts last row: " + $pt.Cells($pt.Rows.Count, 1).End(-4162).Row + " | A6=" + $pt.Range('A6').Text + " AE6=" + $pt.Range('AE6').Text + " AM6=" + $pt.Range('AM6').Text + " AV6=" + $pt.Range('AV6').Text
  $errs = 0
  foreach ($sh in $wb.Worksheets) { try { $x = $sh.UsedRange.SpecialCells(-4123, 16); $errs += $x.Count } catch {} }
  "formula cells with errors: $errs"
  $fy = $wb.Worksheets.Item('Fiscal year'); "Fiscal year: date={0} FY2027={1} FY2028={2} run rate={3}" -f $fy.Range('B4').Text, $fy.Range('B5').Value2, $fy.Range('B6').Value2, $fy.Range('B7').Value2
  $fy.Range('B4').Value2 = 46478; $xl.Calculate(); "Fiscal year after typing 1 Apr 2027: FY2027={0} FY2028={1}" -f $fy.Range('B5').Value2, $fy.Range('B6').Value2
  $se0 = $wb.Worksheets.Item('Settings'); "Reaction: e={0} extra after={1} given up={2} volume change={3}" -f $se0.Range('B33').Value2, $se0.Range('B34').Value2, $se0.Range('B36').Value2, $se0.Range('B35').Value2
  $se0.Range('B33').Value2 = -0.81; $xl.Calculate(); "Reaction after typing -0,81: extra after={0}" -f $se0.Range('B34').Value2
  $se.Range('B4').Value2 = 0.04; $xl.Calculate()
  "after typing 4% in B4: B21={0} status={1}" -f $se.Range('B21').Value2, $se.Range('B22').Text
  $fy = $wb.Worksheets.Item('Fiscal year'); "Fiscal year: date={0} FY2027={1} FY2028={2} run rate={3}" -f $fy.Range('B4').Text, $fy.Range('B5').Value2, $fy.Range('B6').Value2, $fy.Range('B7').Value2
  $fy.Range('B4').Value2 = 46478; $xl.Calculate(); "Fiscal year after typing 1 Apr 2027: FY2027={0} FY2028={1}" -f $fy.Range('B5').Value2, $fy.Range('B6').Value2
  $se0 = $wb.Worksheets.Item('Settings'); "Reaction: e={0} extra after={1} given up={2} volume change={3}" -f $se0.Range('B33').Value2, $se0.Range('B34').Value2, $se0.Range('B36').Value2, $se0.Range('B35').Value2
  $se0.Range('B33').Value2 = -0.81; $xl.Calculate(); "Reaction after typing -0,81: extra after={0}" -f $se0.Range('B34').Value2
  $wb.Close($false)
} finally { $xl.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($xl) }
