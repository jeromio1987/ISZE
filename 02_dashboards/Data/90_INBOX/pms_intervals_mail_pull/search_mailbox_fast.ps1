$ErrorActionPreference = 'Continue'
$outDir = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull'
$attDir = Join-Path $outDir 'attachments'
New-Item -ItemType Directory -Force -Path $attDir | Out-Null

$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace('MAPI')

# DASL / Jet filters for sender name/address fragments
$filterSpecs = @(
  @{ Name = 'Duncan'; Filter = "@SQL=""urn:schemas:httpmail:fromname"" LIKE '%Duncan%' OR ""urn:schemas:httpmail:fromemail"" LIKE '%duncan%' OR ""urn:schemas:httpmail:fromemail"" LIKE '%young%'" },
  @{ Name = 'Suzuki'; Filter = "@SQL=""urn:schemas:httpmail:fromname"" LIKE '%Suzuki%' OR ""urn:schemas:httpmail:fromemail"" LIKE '%suzuki%' OR ""urn:schemas:httpmail:fromemail"" LIKE '%takayoshi%'" },
  @{ Name = 'Rene'; Filter = "@SQL=""urn:schemas:httpmail:fromname"" LIKE '%Rene%' OR ""urn:schemas:httpmail:fromname"" LIKE '%René%' OR ""urn:schemas:httpmail:fromemail"" LIKE '%rene%'" }
)

$keywordPatterns = @(
  'pms', 'interval', 'oil change', 'oil filter', 'air filter', 'fuel filter',
  'brake', 'clutch', 'service schedule', 'maintenance', 'mileage',
  'n75', 'n35', '4hk1', '4jz1', 'iml', 'img', 'visits', 'service interval',
  'periodic', 'every ', 'km/', '/km', '10,000', '10000', '20,000', '20000',
  '40,000', '40000', 'schedule'
)

function Test-MatchAny($text, $patterns) {
  if ([string]::IsNullOrEmpty($text)) { return $false }
  $t = $text.ToLowerInvariant()
  foreach ($p in $patterns) {
    if ($t.Contains($p.ToLowerInvariant())) { return $true }
  }
  return $false
}

$results = New-Object System.Collections.Generic.List[object]
$pdfHits = New-Object System.Collections.Generic.List[object]
$seenIds = @{}
$script:scannedFolders = 0

function Search-FolderFiltered($folder, $depth) {
  if ($depth -gt 14) { return }
  $script:scannedFolders++
  $path = $folder.FolderPath
  Write-Host ("FOLDER: " + $path)

  foreach ($spec in $filterSpecs) {
    $items = $null
    try {
      $items = $folder.Items.Restrict($spec.Filter)
    } catch {
      # fallback: try Jet syntax
      try {
        if ($spec.Name -eq 'Duncan') {
          $items = $folder.Items.Restrict("[SenderName] LIKE '%Duncan%'")
        } elseif ($spec.Name -eq 'Suzuki') {
          $items = $folder.Items.Restrict("[SenderName] LIKE '%Suzuki%'")
        } else {
          $items = $folder.Items.Restrict("[SenderName] LIKE '%Rene%'")
        }
      } catch {
        continue
      }
    }
    if ($null -eq $items) { continue }
    try { $items.Sort('[ReceivedTime]', $true) } catch {}

    $count = 0
    try { $count = $items.Count } catch { $count = 0 }
    Write-Host ("  " + $spec.Name + " matches=" + $count)

    for ($i = 1; $i -le $count; $i++) {
      $item = $null
      try { $item = $items.Item($i) } catch { continue }
      if ($null -eq $item) { continue }
      $class = 0
      try { $class = [int]$item.Class } catch { continue }
      if ($class -ne 43) { continue }

      $eid = ''
      try { $eid = [string]$item.EntryID } catch {}
      if ($eid -and $seenIds.ContainsKey($eid)) { continue }
      if ($eid) { $seenIds[$eid] = $true }

      $subj = ''
      try { $subj = [string]$item.Subject } catch {}
      $body = ''
      try { $body = [string]$item.Body } catch {}
      $recv = $null
      try { $recv = $item.ReceivedTime } catch {}
      $from = ''
      try { $from = [string]$item.SenderName } catch {}
      $email = ''
      try { $email = [string]$item.SenderEmailAddress } catch {}
      try {
        if ($item.Sender) {
          $eu = $item.Sender.GetExchangeUser()
          if ($eu -and $eu.PrimarySmtpAddress) { $email = [string]$eu.PrimarySmtpAddress }
        }
      } catch {}

      $attNames = New-Object System.Collections.Generic.List[string]
      $hasPdf = $false
      try {
        foreach ($att in $item.Attachments) {
          $fn = [string]$att.FileName
          $attNames.Add($fn) | Out-Null
          if ($fn -match '\.pdf$') { $hasPdf = $true }
        }
      } catch {}

      $hasKw = Test-MatchAny ($subj + ' ' + $body + ' ' + ($attNames -join ' ')) $keywordPatterns

      $rec = [pscustomobject]@{
        Group = $spec.Name
        Received = if ($recv) { $recv.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
        From = $from
        Email = $email
        Subject = $subj
        Folder = $path
        Atts = ($attNames -join ' | ')
        HasPdf = $hasPdf
        HasKeyword = $hasKw
        EntryID = $eid
        BodyPreview = if ($body.Length -gt 4000) { $body.Substring(0,4000) } else { $body }
      }
      $results.Add($rec) | Out-Null

      if ($hasPdf) {
        try {
          foreach ($att in $item.Attachments) {
            $fn = [string]$att.FileName
            if ($fn -notmatch '\.pdf$') { continue }
            $safeFrom = ($from -replace '[^\w\-]+','_')
            $safeDate = if ($recv) { $recv.ToString('yyyyMMdd') } else { 'nodate' }
            $safeFn = ($fn -replace '[^\w\.\-]+','_')
            $dest = Join-Path $attDir ($safeDate + '_' + $safeFrom + '_' + $safeFn)
            if (-not (Test-Path $dest)) {
              $att.SaveAsFile($dest)
            }
            $pdfHits.Add([pscustomobject]@{
              Group = $spec.Name
              Received = $rec.Received
              From = $from
              Email = $email
              Subject = $subj
              Filename = $fn
              SavedAs = $dest
              EntryID = $eid
              HasKeyword = $hasKw
            }) | Out-Null
          }
        } catch {
          Write-Host ('ATT SAVE FAIL: ' + $_.Exception.Message)
        }
      }
    }
  }

  try {
    foreach ($sub in $folder.Folders) {
      Search-FolderFiltered $sub ($depth + 1)
    }
  } catch {}
}

# Prefer Jerome mailbox + recurse; also search Sales/Parts stores
foreach ($store in $ns.Stores) {
  Write-Host ('STORE: ' + $store.DisplayName)
  try {
    Search-FolderFiltered $store.GetRootFolder() 0
  } catch {
    Write-Host ('STORE FAIL: ' + $_.Exception.Message)
  }
}

$results | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outDir 'sender_hits.json') -Encoding UTF8
$pdfHits | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outDir 'pdf_hits.json') -Encoding UTF8

$kw = $results | Where-Object { $_.HasKeyword -or $_.HasPdf }
$kw | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outDir 'keyword_or_pdf_hits.json') -Encoding UTF8

$unique = $results | Select-Object Group, From, Email -Unique | Sort-Object Group, From
$unique | ConvertTo-Json | Set-Content (Join-Path $outDir 'unique_senders.json') -Encoding UTF8

# Interval-ish body extract: lines with km / interval / filter / oil
$intervalSnippets = New-Object System.Collections.Generic.List[object]
foreach ($r in $kw) {
  $lines = ($r.BodyPreview -split "`r?`n")
  $hits = @()
  foreach ($line in $lines) {
    $l = $line.Trim()
    if ($l.Length -lt 8) { continue }
    if ($l -match '(?i)(\d[\d,\.]*\s*(km|miles|mi|year|years|yr|hrs|hours)|interval|oil|filter|brake|clutch|service|pms|every\s+\d|visits)') {
      $hits += $l
    }
  }
  if ($hits.Count -gt 0) {
    $intervalSnippets.Add([pscustomobject]@{
      Group = $r.Group
      Received = $r.Received
      From = $r.From
      Email = $r.Email
      Subject = $r.Subject
      Atts = $r.Atts
      Folder = $r.Folder
      EntryID = $r.EntryID
      SnippetLines = ($hits | Select-Object -First 40)
    }) | Out-Null
  }
}
$intervalSnippets | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $outDir 'interval_snippets.json') -Encoding UTF8

Write-Host "DONE folders=$script:scannedFolders totalSenderMails=$($results.Count) kwOrPdf=$($kw.Count) pdfs=$($pdfHits.Count) snippets=$($intervalSnippets.Count)"
Write-Host 'Unique senders:'
$unique | ForEach-Object { Write-Host (' - [' + $_.Group + '] ' + $_.From + ' <' + $_.Email + '>') }
