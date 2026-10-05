# Full round trip: restore all four, check they match the before state, re-apply, check the after state.
$ErrorActionPreference = 'Stop'
$Pack = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920'
$Dir  = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_pack_3f'

$Names = @('00_READ_ME_FIRST.md','01_BRIEF_FOR_THE_MODEL.md','02_CORRECTION_LOG.md','04_FILE_CATALOG.csv')
$Before = @{
  '00_READ_ME_FIRST.md'       = 'eeb18190b0fb3993'
  '01_BRIEF_FOR_THE_MODEL.md' = 'e4ddeae56ad73983'
  '02_CORRECTION_LOG.md'      = 'ae8103974b96f7e2'
  '04_FILE_CATALOG.csv'       = '7a0d310327b73b2a'
}
$After = @{
  '00_READ_ME_FIRST.md'       = '9a193f446619754a'
  '01_BRIEF_FOR_THE_MODEL.md' = '8c0d04ea7969dad8'
  '02_CORRECTION_LOG.md'      = '022b2ef186fc5082'
  '04_FILE_CATALOG.csv'       = 'c0bda488f6d627db'
}

Write-Host '=== STEP 1: restore all four ==='
& (Join-Path $Dir 'restore.ps1')
Write-Host ''
Write-Host '=== STEP 2: do they match the BEFORE hashes? ==='
$fail = 0
foreach ($n in $Names) {
  $h = (Get-FileHash -LiteralPath (Join-Path $Pack $n) -Algorithm SHA256).Hash.ToLower().Substring(0,16)
  if ($h -eq $Before[$n]) { Write-Host ("  [ok]   {0,-28} {1}" -f $n, $h) }
  else { Write-Host ("  [FAIL] {0,-28} {1} expected {2}" -f $n, $h, $Before[$n]); $fail++ }
}

Write-Host ''
Write-Host '=== STEP 3: re-apply the correction ==='
python (Join-Path $Dir '_apply_3f.py')
python (Join-Path $Dir '_apply_3f_b.py')
python (Join-Path $Dir '_patch_3f_readme.py')
python (Join-Path $Dir '_patch_3f_readme_b.py')

Write-Host ''
Write-Host '=== STEP 4: do they match the AFTER hashes? ==='
foreach ($n in $Names) {
  $h = (Get-FileHash -LiteralPath (Join-Path $Pack $n) -Algorithm SHA256).Hash.ToLower().Substring(0,16)
  if ($h -eq $After[$n]) { Write-Host ("  [ok]   {0,-28} {1}" -f $n, $h) }
  else { Write-Host ("  [FAIL] {0,-28} {1} expected {2}" -f $n, $h, $After[$n]); $fail++ }
}

Write-Host ''
if ($fail -eq 0) { Write-Host 'ROUND_TRIP_OK' } else { Write-Host "ROUND_TRIP_FAILED ($fail)"; exit 1 }
