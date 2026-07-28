$ErrorActionPreference = 'Continue'
$outDir = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull'
$attDir = Join-Path $outDir 'attachments'

$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace('MAPI')

# Get full body of Rene Interval maintenance + Duncan Parts Business emails by EntryID from prior hits
$entryIds = @(
  '00000000174BC82B22520D429348932087CC34F0070058934DF1ED3C4D4EA4EA4D7658026CCA00000000010C000058934DF1ED3C4D4EA4EA4D7658026CCA0008C5EDB49F0000', # Rene Interval
  '00000000174BC82B22520D429348932087CC34F0070058934DF1ED3C4D4EA4EA4D7658026CCA00000000010C000058934DF1ED3C4D4EA4EA4D7658026CCA0008E38BF11F0000'  # Duncan Parts Business
)

$full = New-Object System.Collections.Generic.List[object]
foreach ($eid in $entryIds) {
  try {
    $item = $ns.GetItemFromID($eid)
    $body = [string]$item.Body
    $full.Add([pscustomobject]@{
      Received = $item.ReceivedTime.ToString('yyyy-MM-dd HH:mm:ss')
      From = [string]$item.SenderName
      Email = [string]$item.SenderEmailAddress
      Subject = [string]$item.Subject
      Atts = (($item.Attachments | ForEach-Object { $_.FileName }) -join ' | ')
      Body = $body
      EntryID = $eid
    }) | Out-Null
    # save body
    $safe = ($item.Subject -replace '[^\w\-]+','_')
    Set-Content -Path (Join-Path $outDir ("fullbody_" + $safe + ".txt")) -Value $body -Encoding UTF8
    Write-Host ('OK body: ' + $item.Subject + ' len=' + $body.Length)
  } catch {
    Write-Host ('FAIL eid: ' + $_.Exception.Message)
  }
}
$full | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $outDir 'key_full_bodies.json') -Encoding UTF8

# Subject search ONLY on Inbox + Sent + key archive customer folders (not whole tree)
$targets = @(
  'Interval maintenance',
  'Service Maintenance Schedule',
  'GIDSS_maint',
  'maintenance schedule',
  'service interval',
  'PMS interval'
)

$folders = @()
$folders += $ns.GetDefaultFolder(6) # Inbox
$folders += $ns.GetDefaultFolder(5) # Sent
# Try locate archive customer folders
function Find-NamedFolder($root, $namePart, $depth) {
  if ($depth -gt 8) { return @() }
  $found = @()
  try {
    if ($root.Name -match $namePart) { $found += $root }
    foreach ($sub in $root.Folders) {
      $found += Find-NamedFolder $sub $namePart ($depth+1)
    }
  } catch {}
  return $found
}

$jerome = $null
foreach ($s in $ns.Stores) { if ($s.DisplayName -match 'jerome') { $jerome = $s; break } }
if ($jerome) {
  $root = $jerome.GetRootFolder()
  $folders += Find-NamedFolder $root '^IMG$' 0
  $folders += Find-NamedFolder $root '^ITUK$' 0
  $folders += Find-NamedFolder $root '^IML$' 0
  $folders += Find-NamedFolder $root 'archive' 0 | Select-Object -First 5
}

$seen = @{}
$hits = New-Object System.Collections.Generic.List[object]
$pdfs = New-Object System.Collections.Generic.List[object]

foreach ($folder in ($folders | Select-Object -Unique)) {
  if ($null -eq $folder) { continue }
  Write-Host ('SCAN: ' + $folder.FolderPath)
  foreach ($t in $targets) {
    $restr = $null
    try {
      $restr = $folder.Items.Restrict("@SQL=""urn:schemas:httpmail:subject"" LIKE '%$t%'")
    } catch {
      try { $restr = $folder.Items.Restrict("[Subject] LIKE '%$t%'") } catch { continue }
    }
    $rc = 0
    try { $rc = $restr.Count } catch { continue }
    Write-Host ("  '$t' => $rc")
    for ($i = 1; $i -le $rc; $i++) {
      $item = $null
      try { $item = $restr.Item($i) } catch { continue }
      if ($null -eq $item) { continue }
      try { if ([int]$item.Class -ne 43) { continue } } catch { continue }
      $eid = ''
      try { $eid = [string]$item.EntryID } catch {}
      if ($eid -and $seen.ContainsKey($eid)) { continue }
      if ($eid) { $seen[$eid] = $true }

      $from = ''; $email = ''; $subj = ''; $body = ''; $recv = $null
      try { $from = [string]$item.SenderName } catch {}
      try { $email = [string]$item.SenderEmailAddress } catch {}
      try { $subj = [string]$item.Subject } catch {}
      try { $body = [string]$item.Body } catch {}
      try { $recv = $item.ReceivedTime } catch {}
      $attNames = @()
      try {
        foreach ($att in $item.Attachments) {
          $fn = [string]$att.FileName
          $attNames += $fn
          if ($fn -match '\.pdf$') {
            $safeFrom = ($from -replace '[^\w\-]+','_')
            $safeDate = if ($recv) { $recv.ToString('yyyyMMdd') } else { 'nodate' }
            $safeFn = ($fn -replace '[^\w\.\-]+','_')
            $dest = Join-Path $attDir ($safeDate + '_' + $safeFrom + '_' + $safeFn)
            if (-not (Test-Path $dest)) { try { $att.SaveAsFile($dest) } catch {} }
            $pdfs.Add([pscustomobject]@{
              Received = if ($recv) { $recv.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
              From = $from; Email = $email; Subject = $subj; Filename = $fn; SavedAs = $dest
              Folder = $folder.FolderPath; MatchTerm = $t
            }) | Out-Null
          }
        }
      } catch {}

      $hits.Add([pscustomobject]@{
        MatchTerm = $t
        Received = if ($recv) { $recv.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
        From = $from; Email = $email; Subject = $subj
        Folder = $folder.FolderPath
        Atts = ($attNames -join ' | ')
        BodyPreview = if ($body.Length -gt 8000) { $body.Substring(0,8000) } else { $body }
        EntryID = $eid
      }) | Out-Null
    }
  }
}

$hits | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outDir 'subject_deep_hits.json') -Encoding UTF8
$pdfs | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outDir 'subject_deep_pdfs.json') -Encoding UTF8
Write-Host "hits=$($hits.Count) pdfs=$($pdfs.Count)"
$hits | Select-Object Received, From, Subject, Atts | Format-Table -AutoSize -Wrap
Get-ChildItem $attDir | Select-Object Name, Length | Format-Table -AutoSize
