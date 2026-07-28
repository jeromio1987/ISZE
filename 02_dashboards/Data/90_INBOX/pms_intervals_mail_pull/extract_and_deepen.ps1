$ErrorActionPreference = 'Continue'
$outDir = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull'
$attDir = Join-Path $outDir 'attachments'
$pdfTextDir = Join-Path $outDir 'pdf_text'
New-Item -ItemType Directory -Force -Path $pdfTextDir | Out-Null

# --- Extract PDF text via Word COM (available on Jerome's PC) ---
$pdfs = Get-ChildItem $attDir -Filter '*.pdf'
$word = $null
try {
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
} catch {
  Write-Host 'Word COM unavailable, will try pdftotext/python'
}

foreach ($pdf in $pdfs) {
  $outTxt = Join-Path $pdfTextDir ($pdf.BaseName + '.txt')
  Write-Host ('PDF: ' + $pdf.Name)
  if ($word) {
    try {
      $doc = $word.Documents.Open($pdf.FullName, $false, $true)
      $doc.SaveAs([ref]$outTxt, [ref]2) # wdFormatText = 2
      $doc.Close([ref]$false)
      Write-Host ('  saved via Word: ' + $outTxt)
      continue
    } catch {
      Write-Host ('  Word fail: ' + $_.Exception.Message)
    }
  }
}

if ($word) {
  try { $word.Quit() } catch {}
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}

# Fallback python pypdf/pdfminer if any missing
$missing = @()
foreach ($pdf in $pdfs) {
  $outTxt = Join-Path $pdfTextDir ($pdf.BaseName + '.txt')
  if (-not (Test-Path $outTxt) -or ((Get-Item $outTxt).Length -lt 50)) { $missing += $pdf.FullName }
}
if ($missing.Count -gt 0) {
  $py = @'
import sys, pathlib
paths = sys.argv[1:]
outdir = pathlib.Path(r''' + ($pdfTextDir -replace '\\','\\\\') + ''')
try:
    from pypdf import PdfReader
except Exception:
    try:
        from PyPDF2 import PdfReader
    except Exception as e:
        print('NO_PDF_LIB', e)
        sys.exit(2)

for p in paths:
    path = pathlib.Path(p)
    reader = PdfReader(str(path))
    texts = []
    for i, page in enumerate(reader.pages):
        try:
            t = page.extract_text() or ''
        except Exception as ex:
            t = f'[page {i} extract error: {ex}]'
        texts.append(f'\n\n===== PAGE {i+1} =====\n' + t)
    out = outdir / (path.stem + '.txt')
    out.write_text('\n'.join(texts), encoding='utf-8', errors='replace')
    print('WROTE', out, 'chars', sum(len(x) for x in texts))
'@
  $pyFile = Join-Path $outDir 'extract_pdfs.py'
  Set-Content -Path $pyFile -Value $py -Encoding UTF8
  python $pyFile @missing
}

# --- Outlook deepen: pull full bodies for Interval maintenance + Duncan PDFs; search attachment names ---
$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace('MAPI')
$inbox = $ns.GetDefaultFolder(6)

$targets = @(
  'Interval maintenance',
  'Parts Business',
  'Service Maintenance Schedule',
  'GIDSS_maint',
  'RT56_Service',
  'RT88',
  'RG_Service',
  'RG21_Service',
  'BEV_RG20',
  'service interval',
  'PMS interval',
  'maintenance schedule',
  'oil change'
)

$deep = New-Object System.Collections.Generic.List[object]
$extraPdfs = New-Object System.Collections.Generic.List[object]
$seen = @{}

function Scan-FolderDeep($folder, $depth) {
  if ($depth -gt 10) { return }
  $items = $folder.Items
  try { $items.Sort('[ReceivedTime]', $true) } catch {}
  $count = 0
  try { $count = $items.Count } catch { return }

  # Subject restrict for each target
  foreach ($t in $targets) {
    $restr = $null
    try {
      $restr = $items.Restrict("@SQL=""urn:schemas:httpmail:subject"" LIKE '%$t%'")
    } catch {
      try { $restr = $items.Restrict("[Subject] LIKE '%$t%'") } catch { continue }
    }
    $rc = 0
    try { $rc = $restr.Count } catch { $rc = 0 }
    for ($i = 1; $i -le $rc; $i++) {
      $item = $null
      try { $item = $restr.Item($i) } catch { continue }
      if ($null -eq $item) { continue }
      $class = 0
      try { $class = [int]$item.Class } catch { continue }
      if ($class -ne 43) { continue }
      $eid = ''
      try { $eid = [string]$item.EntryID } catch {}
      if ($eid -and $seen.ContainsKey($eid)) { continue }
      if ($eid) { $seen[$eid] = $true }

      $from = ''
      $email = ''
      try { $from = [string]$item.SenderName } catch {}
      try { $email = [string]$item.SenderEmailAddress } catch {}
      try {
        if ($item.Sender) {
          $eu = $item.Sender.GetExchangeUser()
          if ($eu -and $eu.PrimarySmtpAddress) { $email = [string]$eu.PrimarySmtpAddress }
        }
      } catch {}
      $subj = ''
      try { $subj = [string]$item.Subject } catch {}
      $body = ''
      try { $body = [string]$item.Body } catch {}
      $recv = $null
      try { $recv = $item.ReceivedTime } catch {}
      $attNames = New-Object System.Collections.Generic.List[string]
      try {
        foreach ($att in $item.Attachments) {
          $fn = [string]$att.FileName
          $attNames.Add($fn) | Out-Null
          if ($fn -match '\.pdf$') {
            $safeFrom = ($from -replace '[^\w\-]+','_')
            $safeDate = if ($recv) { $recv.ToString('yyyyMMdd') } else { 'nodate' }
            $safeFn = ($fn -replace '[^\w\.\-]+','_')
            $dest = Join-Path $attDir ($safeDate + '_' + $safeFrom + '_' + $safeFn)
            if (-not (Test-Path $dest)) {
              try { $att.SaveAsFile($dest) } catch {}
            }
            $extraPdfs.Add([pscustomobject]@{
              Received = if ($recv) { $recv.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
              From = $from
              Email = $email
              Subject = $subj
              Filename = $fn
              SavedAs = $dest
              MatchTerm = $t
              Folder = $folder.FolderPath
            }) | Out-Null
          }
        }
      } catch {}

      $deep.Add([pscustomobject]@{
        MatchTerm = $t
        Received = if ($recv) { $recv.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
        From = $from
        Email = $email
        Subject = $subj
        Folder = $folder.FolderPath
        Atts = ($attNames -join ' | ')
        Body = if ($body.Length -gt 12000) { $body.Substring(0,12000) } else { $body }
        EntryID = $eid
      }) | Out-Null
    }
  }

  # Also: any mail with attachment name containing Service Maintenance / GIDSS / maint_
  # (scan recent items only if folder is Inbox-ish - skip huge folders)
  $pathL = $folder.FolderPath.ToLowerInvariant()
  if ($pathL -match 'inbox|sent|archive\\inbox\\archive\\customers\\(img|ituk|iml)') {
    $maxScan = [Math]::Min($count, 800)
    for ($i = 1; $i -le $maxScan; $i++) {
      $item = $null
      try { $item = $items.Item($i) } catch { continue }
      if ($null -eq $item) { continue }
      $class = 0
      try { $class = [int]$item.Class } catch { continue }
      if ($class -ne 43) { continue }
      $attHit = $false
      $attNames = New-Object System.Collections.Generic.List[string]
      try {
        if ($item.Attachments.Count -eq 0) { continue }
        foreach ($att in $item.Attachments) {
          $fn = [string]$att.FileName
          $attNames.Add($fn) | Out-Null
          if ($fn -match '(?i)(GIDSS_maint|Service Maintenance|maint_|maintenance schedule|service schedule|interval)') {
            $attHit = $true
          }
        }
      } catch { continue }
      if (-not $attHit) { continue }

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

      try {
        foreach ($att in $item.Attachments) {
          $fn = [string]$att.FileName
          if ($fn -notmatch '\.pdf$') { continue }
          $safeFrom = ($from -replace '[^\w\-]+','_')
          $safeDate = if ($recv) { $recv.ToString('yyyyMMdd') } else { 'nodate' }
          $safeFn = ($fn -replace '[^\w\.\-]+','_')
          $dest = Join-Path $attDir ($safeDate + '_' + $safeFrom + '_' + $safeFn)
          if (-not (Test-Path $dest)) { try { $att.SaveAsFile($dest) } catch {} }
          $extraPdfs.Add([pscustomobject]@{
            Received = if ($recv) { $recv.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
            From = $from
            Email = $email
            Subject = $subj
            Filename = $fn
            SavedAs = $dest
            MatchTerm = 'attachment-name'
            Folder = $folder.FolderPath
          }) | Out-Null
        }
      } catch {}

      $deep.Add([pscustomobject]@{
        MatchTerm = 'attachment-name'
        Received = if ($recv) { $recv.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
        From = $from
        Email = $email
        Subject = $subj
        Folder = $folder.FolderPath
        Atts = ($attNames -join ' | ')
        Body = if ($body.Length -gt 12000) { $body.Substring(0,12000) } else { $body }
        EntryID = $eid
      }) | Out-Null
    }
  }

  try {
    foreach ($sub in $folder.Folders) { Scan-FolderDeep $sub ($depth+1) }
  } catch {}
}

# Search Jerome store root + focus folders
$store = $null
foreach ($s in $ns.Stores) {
  if ($s.DisplayName -match 'jerome') { $store = $s; break }
}
if ($store) {
  Write-Host ('Deep store: ' + $store.DisplayName)
  Scan-FolderDeep $store.GetRootFolder() 0
} else {
  Scan-FolderDeep $inbox 0
}

$deep | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outDir 'deep_subject_hits.json') -Encoding UTF8
$extraPdfs | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outDir 'extra_pdf_hits.json') -Encoding UTF8
Write-Host ("Deep mails=$($deep.Count) extraPdfs=$($extraPdfs.Count)")
$deep | Select-Object Received, From, Subject, Atts, MatchTerm | Format-Table -AutoSize -Wrap
Write-Host '--- attachments now ---'
Get-ChildItem $attDir | Select-Object Name, Length | Format-Table -AutoSize
Write-Host '--- pdf_text ---'
Get-ChildItem $pdfTextDir -ErrorAction SilentlyContinue | Select-Object Name, Length | Format-Table -AutoSize
