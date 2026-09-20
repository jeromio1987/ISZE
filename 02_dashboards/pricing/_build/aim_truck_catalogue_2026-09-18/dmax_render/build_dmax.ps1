# Build the hero D-Max render.
#
# Run from PowerShell:
#   powershell -ExecutionPolicy Bypass -File build_dmax.ps1
#
# Everything below is free and needs no account or key.  The model is the
# Objaverse mirror of the CC-BY "2021 Isuzu D-Max" by David_Holiday.

param(
  [string]$OutDir = $PSScriptRoot,
  [int]$Samples   = 400,
  [int]$ResX      = 2400,
  [int]$ResY      = 1086,
  [double]$Az     = 76,
  [double]$El     = 12,
  [string]$Paint  = "white"
)

$ErrorActionPreference = "Stop"
$blender = "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
if (-not (Test-Path $blender)) { throw "Blender not found at $blender" }

New-Item -ItemType Directory -Force -Path (Join-Path $OutDir "_raw") | Out-Null
$raw = Join-Path $OutDir "_raw"

Write-Host "=== D-Max hero render ==="
Write-Host "out   : $OutDir"
Write-Host "paint : $Paint   samples: $Samples   res: ${ResX}x${ResY}   az: $Az  el: $El"

$args = @(
  "--background", "--python", (Join-Path $OutDir "build_dmax_render.py"), "--",
  "--outdir", $OutDir, "--tag", "hero",
  "--samples", "$Samples", "--resx", "$ResX", "--resy", "$ResY",
  "--az", "$Az", "--el", "$El", "--paint", $Paint
)
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath $blender -ArgumentList $args -Wait -NoNewWindow -PassThru `
     -RedirectStandardOutput (Join-Path $raw "hero_build.log") `
     -RedirectStandardError  (Join-Path $raw "hero_build_err.log")
$sw.Stop()
Write-Host ("blender exit {0} in {1:N1} s" -f $p.ExitCode, $sw.Elapsed.TotalSeconds)

# The compositing / hotspot step needs Pillow, which is present in the system Python.
python (Join-Path $OutDir "compose_dmax.py") --raw $raw --out $OutDir --tag hero
if ($LASTEXITCODE -ne 0) { throw "compose_dmax.py failed with $LASTEXITCODE" }

Write-Host ""
Write-Host "Deliverables in $OutDir :"
Get-ChildItem $OutDir -File | Where-Object { $_.Name -match '\.(png|json|md)$' } |
  Select-Object Name, Length | Format-Table -AutoSize | Out-String -Width 120 | Write-Host
Write-Host "Done."
