param(
    [Parameter(Mandatory=$true)][string]$Pptx,
    [Parameter(Mandatory=$true)][string]$Qa,
    [int]$W = 1600,
    [int]$H = 900,
    [int]$Only = 0
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $Qa | Out-Null
Get-ChildItem "$Qa\*.png" -ErrorAction SilentlyContinue | Remove-Item -Force

$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($Pptx, $true, $false, $false)
$n = $pres.Slides.Count
Write-Output "slides: $n"
$first = 1; $last = $n
if ($Only -gt 0) { $first = $Only; $last = $Only }
for ($i = $first; $i -le $last; $i++) {
    $out = Join-Path $Qa ("slide_{0:D2}.png" -f $i)
    $pres.Slides.Item($i).Export($out, "PNG", $W, $H)
    Write-Output "  $out"
}
$pres.Close()
$app.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
Write-Output "done"
