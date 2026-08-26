$ErrorActionPreference = 'Stop'
$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace('MAPI')

# Prefer Jerome's mailbox store
$mailboxSmtp = 'jerome.van.der.pluym@isuzu-e.com'
$inbox = $null
foreach ($store in $ns.Stores) {
  try {
    $root = $store.GetRootFolder()
    if ($store.DisplayName -match 'jerome\.van\.der\.pluym|isuzu-e\.com' -or $root.FolderPath -match 'jerome') {
      $inbox = $store.GetDefaultFolder(6)
      Write-Host "STORE=$($store.DisplayName)"
      break
    }
  } catch {}
}
if (-not $inbox) {
  $recipient = $ns.CreateRecipient($mailboxSmtp)
  [void]$recipient.Resolve()
  $inbox = $ns.GetSharedDefaultFolder($recipient, 6)
  Write-Host "SHARED_INBOX_OK"
}

$folders = @($inbox)
# Also Sent? No - looking for mail FROM Tomoe. Check Inbox + maybe Recent/Search.
# Add Conversation History / all mail if exists
try {
  $parent = $inbox.Parent
  foreach ($f in $parent.Folders) {
    if ($f.Name -match '^(Inbox|All Mail|Archive|IDS|MIDI)$') {
      $folders += $f
    }
  }
} catch {}

$cutoff = (Get-Date).AddDays(-60)
$hits = New-Object System.Collections.Generic.List[object]

foreach ($folder in $folders) {
  Write-Host "SCAN=$($folder.FolderPath)"
  $items = $folder.Items
  $items.Sort('[ReceivedTime]', $true)
  $n = 0
  foreach ($item in $items) {
    $n++
    if ($n -gt 1500) { break }
    try {
      $rt = $item.ReceivedTime
      if ($rt -lt $cutoff) { break }
      $name = [string]$item.SenderName
      $from = [string]$item.SenderEmailAddress
      $subject = [string]$item.Subject
      $match = ($name -match '(?i)tomoe') -or ($from -match '(?i)tomoe\.baumann') -or ($from -match '(?i)tomoe@')
      if (-not $match) { continue }
      $attachNames = @()
      for ($a = 1; $a -le $item.Attachments.Count; $a++) {
        $attachNames += $item.Attachments.Item($a).FileName
      }
      $hits.Add([pscustomobject]@{
        Received = $rt.ToString('yyyy-MM-dd HH:mm')
        Subject  = $subject
        FromName = $name
        FromAddr = $from
        EntryID  = $item.EntryID
        Unread   = [bool]$item.UnRead
        AttachCount = $item.Attachments.Count
        Attachments = ($attachNames -join '; ')
        Folder   = $folder.FolderPath
        BodyLen  = ([string]$item.Body).Length
      }) | Out-Null
    } catch {}
  }
}

$sorted = $hits | Sort-Object Received -Descending
Write-Host "HIT_COUNT=$($sorted.Count)"
$sorted | Select-Object -First 15 | ConvertTo-Json -Depth 4
