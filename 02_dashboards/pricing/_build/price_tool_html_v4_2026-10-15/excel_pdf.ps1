param([string]$Path, [string]$OutDir)
New-Item -ItemType Directory -Force $OutDir | Out-Null
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false
try {
  $wb = $xl.Workbooks.Open($Path, 0, $false)
  $xl.CalculateFull()
  $spec = @{ 'Read me' = 'A1:A20'; 'Settings' = 'A1:C30'; 'Checks' = 'A1:E11'; 'By L1' = 'A1:G16'; 'Parts' = 'A1:AV24'; 'By market' = 'A1:F28' }
  foreach ($n in $spec.Keys) {
    $ws = $wb.Worksheets.Item($n)
    $ws.PageSetup.PrintArea = $spec[$n]
    $ws.PageSetup.Orientation = 2
    $ws.PageSetup.Zoom = $false
    $ws.PageSetup.FitToPagesWide = 1
    $ws.PageSetup.FitToPagesTall = 1
    $out = Join-Path $OutDir (($n -replace ' ', '_') + '.pdf')
    $ws.ExportAsFixedFormat(0, $out)
  }
  $wb.Close($false)
} finally { $xl.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($xl) }
Get-ChildItem $OutDir -Filter *.pdf | Select-Object Name, Length
