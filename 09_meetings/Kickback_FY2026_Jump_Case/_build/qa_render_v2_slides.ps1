# Render every slide of the v2 kickback deck (with the new slide 21) to PNG via PowerPoint COM.
$ErrorActionPreference = 'Stop'
$pptx = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"
$qa   = "C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\_qa_v2"
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
