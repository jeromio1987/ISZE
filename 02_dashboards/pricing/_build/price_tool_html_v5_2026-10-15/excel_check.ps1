param([string]$Scen = 'holds')
$dir = Join-Path $PSScriptRoot '_xl_test'
$wbp = Join-Path $dir "wb_$Scen.xlsx"
$page = Get-Content (Join-Path $dir "page_$Scen.json") -Raw | ConvertFrom-Json
$spots = Get-Content (Join-Path $dir "spots_$Scen.json") -Raw | ConvertFrom-Json
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false
try {
  $wb = $xl.Workbooks.Open($wbp, 0, $true)
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $xl.CalculateFull()
  "recalc seconds: " + [math]::Round($sw.Elapsed.TotalSeconds, 1)
  "sheets: " + (($wb.Worksheets | ForEach-Object { $_.Name }) -join ', ')
  $ck = $wb.Worksheets.Item('Checks')
  for ($r = 4; $r -le 12; $r++) {
    "{0,-42} page={1,18} excel={2,18} diff={3,12} {4}" -f $ck.Cells.Item($r,1).Text, $ck.Cells.Item($r,2).Value2, $ck.Cells.Item($r,3).Value2, $ck.Cells.Item($r,4).Value2, $ck.Cells.Item($r,5).Text
  }
  $se = $wb.Worksheets.Item('Settings')
  "Settings B14 s1={0} B17 s2={1} B22={2}" -f $se.Range('B14').Value2, $se.Range('B17').Value2, $se.Range('B22').Text
  $pt = $wb.Worksheets.Item('Parts')
  $maxd = 0
  foreach ($s in $spots) {
    $row = [int]$s.row
    for ($k = 0; $k -lt 4; $k++) {
      $v = $pt.Cells.Item($row, 31 + $k).Value2
      $d = [math]::Abs($v - $s.mv[$k]); if ($d -gt $maxd) { $maxd = $d }
    }
  }
  "max move difference on $($spots.Count) spot parts x 4 lists: $maxd"
  $pm = $wb.Worksheets.Item('By PMS category'); $pl = $pm.Cells($pm.Rows.Count, 2).End(-4162).Row; "By PMS category last rows: " + $pm.Cells.Item($pl-1,2).Text + " billed=" + $pm.Cells.Item($pl-1,3).Value2 + " extra=" + $pm.Cells.Item($pl-1,5).Value2 + " | " + $pm.Cells.Item($pl,2).Text + " billed=" + $pm.Cells.Item($pl,3).Value2 + " extra=" + $pm.Cells.Item($pl,5).Value2
  $errs = 0
  foreach ($sh in $wb.Worksheets) { $ur = $sh.UsedRange; try { $x = $ur.SpecialCells(-4123, 16); $errs += $x.Count } catch {} }
  "formula cells with errors: $errs"
  $alt = Get-Content (Join-Path $dir "alt_$Scen.json") -Raw | ConvertFrom-Json
  $se.Range('B4').Value2 = $alt.target
  $xl.Calculate()
  "after typing 4% in Settings!B4: extra excel={0} model={1} | s2 excel={2} model={3} | status={4}" -f $se.Range('B20').Value2, $alt.extra, $se.Range('B17').Value2, $alt.s2, $se.Range('B22').Text
  $wb.Close($false)
} finally { $xl.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($xl) }
