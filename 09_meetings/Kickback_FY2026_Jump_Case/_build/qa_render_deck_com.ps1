param(
    [Parameter(Mandatory=$true)][string]$Pptx,
    [Parameter(Mandatory=$true)][string]$Qa
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $Qa | Out-Null
Get-ChildItem "$Qa\*.png" -ErrorAction SilentlyContinue | Remove-Item -Force

$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($Pptx, $true, $false, $false)
$n = $pres.Slides.Count
Write-Output "opened OK: $Pptx"
Write-Output "slides: $n"
for ($i = 1; $i -le $n; $i++) {
    $out = Join-Path $Qa ("slide_{0:D2}.png" -f $i)
    $pres.Slides.Item($i).Export($out, "PNG", 1600, 900)
}
$pres.Close()
$app.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
Write-Output "rendered to $Qa"
