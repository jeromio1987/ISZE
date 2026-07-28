$ErrorActionPreference = 'Continue'
$outDir = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull'
$attDir = Join-Path $outDir 'attachments'
New-Item -ItemType Directory -Force -Path $attDir | Out-Null

$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace('MAPI')

$senderPatterns = @(
  'duncan', 'young@', 'takayoshi', 'suzuki',
  'rene ', 'rene.', 'rene@', 'rené', 'réné'
)
$keywordPatterns = @(
  'pms', 'interval', 'oil change', 'oil filter', 'air filter', 'fuel filter',
  'brake', 'clutch', 'service schedule', 'maintenance', 'km', 'mileage',
  'n75', 'n35', '4hk1', '4jz1', 'iml', 'img', 'visits', 'service interval',
  'periodic', 'every '
)

function Test-MatchAny($text, $patterns) {
  if ([string]::IsNullOrEmpty($text)) { return $false }
  $t = $text.ToLowerInvariant()
  foreach ($p in $patterns) {
    if ($t.Contains($p.ToLowerInvariant())) { return $true }
  }
  return $false
}

function Get-SenderBlob($item) {
  $parts = New-Object System.Collections.Generic.List[string]
  try { if ($item.SenderName) { $parts.Add([string]$item.SenderName) } } catch {}
  try { if ($item.SenderEmailAddress) { $parts.Add([string]$item.SenderEmailAddress) } } catch {}
  try {
    if ($item.Sender) {
      $eu = $item.Sender.GetExchangeUser()
      if ($eu -and $eu.PrimarySmtpAddress) { $parts.Add([string]$eu.PrimarySmtpAddress) }
    }
  } catch {}
  return ($parts -join ' | ')
}

$results = New-Object System.Collections.Generic.List[object]
$pdfHits = New-Object System.Collections.Generic.List[object]
$senderHits = New-Object System.Collections.Generic.List[object]
$script:scannedFolders = 0
$script:scannedItems = 0

function Search-Folder($folder, $depth) {
  if ($depth -gt 12) { return }
  $script:scannedFolders++
  Write-Host ("FOLDER: " + $folder.FolderPath)

  $items = $null
  try { $items = $folder.Items } catch { return }
  try { $items.Sort('[ReceivedTime]', $true) } catch {}

  $count = 0
  try { $count = $items.Count } catch { $count = 0 }
  for ($i = 1; $i -le $count; $i++) {
    $item = $null
    try { $item = $items.Item($i) } catch { continue }
    if ($null -eq $item) { continue }
    $script:scannedItems++
    $class = 0
    try { $class = [int]$item.Class } catch { continue }
    if ($class -ne 43) { continue }

    $fromBlob = Get-SenderBlob $item
    $subj = ''
    try { $subj = [string]$item.Subject } catch {}
    $body = ''
    try { $body = [string]$item.Body } catch {}
    $recv = $null
    try { $recv = $item.ReceivedTime } catch {}

    $fromOnly = ''
    try { $fromOnly = ([string]$item.SenderName) + ' ' + ([string]$item.SenderEmailAddress) } catch {}
    $isPrimarySender = Test-MatchAny $fromOnly $senderPatterns

    if (-not $isPrimarySender) { continue }

    $hasKw = Test-MatchAny ($subj + ' ' + $body) $keywordPatterns
    $attNames = New-Object System.Collections.Generic.List[string]
    $hasPdf = $false
    try {
      if ($item.Attachments.Count -gt 0) {
        foreach ($att in $item.Attachments) {
          $fn = [string]$att.FileName
          $attNames.Add($fn) | Out-Null
          if ($fn -match '\.pdf$') { $hasPdf = $true }
          if ($fn -match '\.(xlsx|xls|docx|doc|zip|pptx)$') { $hasKw = $true }
        }
      }
    } catch {}

    # Keep all primary-sender mails; keyword flag for prioritization
    $rec = [ordered]@{
      Received = if ($recv) { $recv.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
      From = $(try { [string]$item.SenderName } catch { '' })
      Email = $(try { [string]$item.SenderEmailAddress } catch { '' })
      FromBlob = $fromBlob
      Subject = $subj
      Folder = $folder.FolderPath
      Atts = ($attNames -join ' | ')
      HasPdf = $hasPdf
      HasKeyword = $hasKw
      EntryID = $(try { [string]$item.EntryID } catch { '' })
      BodyPreview = if ($body.Length -gt 3000) { $body.Substring(0,3000) } else { $body }
    }
    $obj = [pscustomobject]$rec
    $results.Add($obj) | Out-Null
    $senderHits.Add($obj) | Out-Null

    if ($hasPdf) {
      try {
        foreach ($att in $item.Attachments) {
          $fn = [string]$att.FileName
          if ($fn -notmatch '\.pdf$') { continue }
          $safeFrom = ($rec.From -replace '[^\w\-]+','_')
          $safeDate = if ($recv) { $recv.ToString('yyyyMMdd') } else { 'nodate' }
          $safeFn = ($fn -replace '[^\w\.\-]+','_')
          $dest = Join-Path $attDir ($safeDate + '_' + $safeFrom + '_' + $safeFn)
          if (-not (Test-Path $dest)) {
            $att.SaveAsFile($dest)
          }
          $pdfHits.Add([pscustomobject]@{
            Received = $rec.Received
            From = $rec.From
            Subject = $rec.Subject
            Filename = $fn
            SavedAs = $dest
            EntryID = $rec.EntryID
            HasKeyword = $hasKw
          }) | Out-Null
        }
      } catch {
        Write-Host ('ATT SAVE FAIL: ' + $_.Exception.Message)
      }
    }

    if (($script:scannedItems % 500) -eq 0) {
      Write-Host ("... scanned items=$script:scannedItems hits=$($results.Count)")
    }
  }

  try {
    foreach ($sub in $folder.Folders) {
      Search-Folder $sub ($depth + 1)
    }
  } catch {}
}

foreach ($store in $ns.Stores) {
  Write-Host ('STORE: ' + $store.DisplayName)
  try {
    Search-Folder $store.GetRootFolder() 0
  } catch {
    Write-Host ('STORE FAIL: ' + $_.Exception.Message)
  }
}

$results | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $outDir 'all_hits.json') -Encoding UTF8
$senderHits | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $outDir 'sender_hits.json') -Encoding UTF8
$pdfHits | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $outDir 'pdf_hits.json') -Encoding UTF8

$uniqueSenders = $senderHits | Select-Object From, Email -Unique | Sort-Object From
$uniqueSenders | ConvertTo-Json | Set-Content -Path (Join-Path $outDir 'unique_senders.json') -Encoding UTF8

$kwHits = $senderHits | Where-Object { $_.HasKeyword -or $_.HasPdf }
$kwHits | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $outDir 'keyword_or_pdf_hits.json') -Encoding UTF8

Write-Host "DONE folders=$script:scannedFolders items=$script:scannedItems hits=$($results.Count) pdfs=$($pdfHits.Count) kwOrPdf=$($kwHits.Count)"
Write-Host 'Unique senders:'
$uniqueSenders | ForEach-Object { Write-Host (' - ' + $_.From + ' <' + $_.Email + '>') }
