$ErrorActionPreference = 'Stop'
$pptx = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\ISZE_Kickback_FY2026_Year_End_Jump_Case.pptx"
$qa   = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\_qa"
New-Item -ItemType Directory -Force -Path $qa | Out-Null
Get-ChildItem "$qa\*.png" -ErrorAction SilentlyContinue | Remove-Item -Force

$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($pptx, $true, $false, $false)
$n = $pres.Slides.Count
Write-Output "slides: $n"
for ($i = 1; $i -le $n; $i++) {
    $out = Join-Path $qa ("slide_{0:D2}.png" -f $i)
    $pres.Slides.Item($i).Export($out, "PNG", 1600, 900)
    Write-Output "  $out"
}
$pres.Close()
$app.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
Write-Output "done"
