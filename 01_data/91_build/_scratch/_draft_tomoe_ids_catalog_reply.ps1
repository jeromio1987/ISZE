# DRAFT ONLY — never Send. Reply to Tomoe re IDS Materials for DB's.
# Redo: dealer-level only, 3 options with one concrete example each.
$ErrorActionPreference = 'Stop'

$mailboxSmtp = 'jerome.van.der.pluym@isuzu-e.com'
$tomoeSmtp = 'Tomoe.Baumann@isuzu.de'

# Lean attachments: Option 1 = MT+CY ready + one Corte short so same dealer across formats
$attachPaths = @(
  # Option 1 — short dealer feedback
  'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_2026\reports\dealer_feedback\MALTA\GASANZAMMIT_MOTORS_LIMITED.html',
  'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_2026\reports\dealer_feedback\CYPRUS\A_Loutsios_and_Sons_Ltd.html',
  'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_2026\reports\dealer_feedback\BE\Garage_De_Corte.html',
  # Option 2 — exec summary one-pager
  'C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_DB_Feedback_Sheet_v0.4\Belgium\dealers\IDS_2026_Dealer_Feedback_Belgium_Garage_De_Corte_v0.4_exec_summary.html',
  # Option 3 — workshop pack (Kaizen); Excel companion available on request, not attached
  'C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_DB_Feedback_Sheet_v0.4\Belgium\dealers\IDS_2026_Dealer_Feedback_Belgium_Garage_De_Corte_v0.4_workshop_pack.html'
)

# Plain ASCII only (no en/em dash, smart quotes, arrows, accents) so Outlook/Windows-1252 does not mojibake.
$bodyText = @'
Hi Tomoe,

Thank you for your questions. Below are short answers, then the three dealer-level formats we use (each with an example attached).

--------------------------------------------------
Your three points
--------------------------------------------------

1) Why does the format look different?
We have more than one dealer deliverable. The short feedback sheet is not the same file as the exec summary or workshop pack - even for the same dealer (see Garage De Corte in Options 1-3). Different purpose -> different layout. That is intentional.

(Country / network comparison HTML is separate again - for the distributor overview, not a single-dealer leave-behind.)

2) Can you create the workshop pack yourself from the dealer comparison HTML?
No. From the comparison HTML you can review a country or dealer, but you cannot generate the workshop / Kaizen pack from that file. Please ask me for the dealer(s) you need - I will prepare them.

3) Malta and Cyprus - what is ready?
- Short dealer feedback sheets: ready (re-attached: Gasan Zammit and Loutsios).
- Full workshop packs (Garage De Corte style): not ready yet for these two. I can prepare them if you want them for the feedback meetings.

--------------------------------------------------
Dealer-level options (3)
--------------------------------------------------

Option 1 - Short dealer feedback HTML
What: one page per dealer - score, strengths / gaps, short improvement asks.
Example: Malta - Gasan Zammit; Cyprus - Loutsios (MT/CY ready); Belgium - Garage De Corte short sheet (attached - same dealer as Options 2-3).
When: quick share with a DB or before a light visit.

Option 2 - Executive summary (one-pager HTML)
What: meeting leave-behind - score context and suggested next steps (owner / date / proof fields for the meeting).
Example: Belgium - Garage De Corte exec summary (attached).
When: face-to-face feedback; short leave-behind for the dealer / DB.

Option 3 - Workshop pack with Kaizen (HTML; Excel companion available)
What: fuller meeting pack - checklist gaps and Kaizen proposals for the discussion. Excel fiche (actions / commitments) can be sent with the same dealer on request.
Example: Belgium - Garage De Corte workshop pack (attached).
When: formal IDS feedback meeting with a dealer.

--------------------------------------------------
How to ask
--------------------------------------------------

Please tell me: country / DB, dealer name(s), and option 1 / 2 / 3.
I will prepare and send the files.

Kind regards,
Jerome
'@

$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace('MAPI')

$store = $null
foreach ($s in $ns.Stores) {
  try {
    if ($s.DisplayName -match 'jerome\.van\.der\.pluym|isuzu-e\.com') {
      $store = $s
      break
    }
  } catch {}
}
if (-not $store) { throw 'Jerome mailbox store not found' }
Write-Host "STORE=$($store.DisplayName)"

$inbox = $store.GetDefaultFolder(6)   # Inbox
$drafts = $store.GetDefaultFolder(16) # Drafts

# Delete / supersede prior drafts on this thread so Jerome has only one
$deletedOld = 0
$draftItems = $drafts.Items
$draftItems.Sort('[LastModificationTime]', $true)
$toDelete = @()
foreach ($it in $draftItems) {
  try {
    $sub = [string]$it.Subject
    if ($sub -notmatch "(?i)IDS Materials for DB") { continue }
    $to = ''
    try { $to = [string]$it.To } catch {}
    if ($to -match '(?i)tomoe') {
      $toDelete += $it
    }
  } catch {}
}
foreach ($old in $toDelete) {
  try {
    Write-Host "DELETE_OLD_DRAFT subject=$($old.Subject) entry=$($old.EntryID)"
    $old.Delete()
    $deletedOld++
  } catch {
    Write-Host "DELETE_OLD_FAIL=$($_.Exception.Message)"
  }
}
Write-Host "DELETED_OLD_DRAFTS=$deletedOld"

function Find-TomoeIdsMaterials($folder, $maxScan) {
  $items = $folder.Items
  $items.Sort('[ReceivedTime]', $true)
  $n = 0
  foreach ($it in $items) {
    $n++
    if ($n -gt $maxScan) { break }
    try {
      $sub = [string]$it.Subject
      if ($sub -notmatch "(?i)IDS Materials for DB") { continue }
      $from = ''
      try { $from = [string]$it.SenderEmailAddress } catch {}
      $name = ''
      try { $name = [string]$it.SenderName } catch {}
      if (($from -match '(?i)tomoe') -or ($name -match '(?i)tomoe')) {
        return $it
      }
    } catch {}
  }
  return $null
}

$source = Find-TomoeIdsMaterials $inbox 3000
if (-not $source) {
  Write-Host 'No Tomoe IDS Materials in Inbox; scanning for any IDS Materials thread...'
  $items = $inbox.Items
  $items.Sort('[ReceivedTime]', $true)
  $n = 0
  foreach ($it in $items) {
    $n++; if ($n -gt 3000) { break }
    try {
      if ([string]$it.Subject -match "(?i)IDS Materials for DB") { $source = $it; break }
    } catch {}
  }
}

$mail = $null
$mode = ''
if ($source) {
  Write-Host "SOURCE_SUBJECT=$($source.Subject)"
  Write-Host "SOURCE_RECEIVED=$($source.ReceivedTime)"
  Write-Host "SOURCE_ENTRYID=$($source.EntryID)"
  $mail = $source.Reply()
  $mode = 'Reply'
} else {
  Write-Host 'SOURCE_NOT_FOUND — creating new draft'
  $mail = $outlook.CreateItem(0)
  $mail.Subject = "Re: IDS Materials for DB's"
  $mail.To = $tomoeSmtp
  $mode = 'New'
}

$mail.To = $tomoeSmtp
try { $mail.BCC = $mailboxSmtp } catch {}

$mail.BodyFormat = 1  # olFormatPlain
$mail.Body = $bodyText

while ($mail.Attachments.Count -gt 0) {
  $mail.Attachments.Item(1).Delete()
}

$attached = @()
foreach ($p in $attachPaths) {
  if (-not (Test-Path -LiteralPath $p)) {
    Write-Host "MISSING_ATTACH=$p"
    continue
  }
  [void]$mail.Attachments.Add($p)
  $attached += $p
  Write-Host "ATTACHED=$p"
}

$mail.Save()
try {
  $saved = $mail.Move($drafts)
  $mail = $saved
} catch {
  Write-Host "MOVE_DRAFTS_NOTE=$($_.Exception.Message)"
}
$mail.Save()

Write-Host 'DRAFT_SAVED'
Write-Host "MODE=$mode"
Write-Host "SUBJECT=$($mail.Subject)"
Write-Host "TO=$($mail.To)"
Write-Host "BCC=$($mail.BCC)"
Write-Host "ENTRYID=$($mail.EntryID)"
Write-Host "ATTACH_COUNT=$($mail.Attachments.Count)"
Write-Host 'NOT_SENT=true'
$attached | ForEach-Object { Write-Host "ATTACH_PATH=$_" }

$out = [pscustomobject]@{
  mode = $mode
  subject = [string]$mail.Subject
  to = [string]$mail.To
  bcc = [string]$mail.BCC
  entryId = [string]$mail.EntryID
  attachCount = [int]$mail.Attachments.Count
  attachments = $attached
  deletedOldDrafts = $deletedOld
  notSent = $true
  options = @(
    @{ n = 1; name = 'Short dealer feedback HTML'; examples = @('Gasan Zammit (Malta)', 'Loutsios (Cyprus)', 'Garage De Corte (Belgium) short') },
    @{ n = 2; name = 'Executive summary one-pager HTML'; examples = @('Garage De Corte (Belgium) exec summary') },
    @{ n = 3; name = 'Workshop pack with Kaizen (HTML; Excel on request)'; examples = @('Garage De Corte (Belgium) workshop pack') }
  )
  body = $bodyText
}
$outPath = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_draft_tomoe_ids_catalog_reply.json'
$out | ConvertTo-Json -Depth 5 | Set-Content -Path $outPath -Encoding UTF8
Write-Host "JSON=$outPath"
