$ErrorActionPreference = "Continue"
$outDir = "C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_mh_gps_mail_20260730"
$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace("MAPI")
$sent = $ns.GetDefaultFolder(5)
Write-Host "Sent count:" $sent.Items.Count

# Walk Sent for 2024-2025 GPS/dealer - restrict by subject then filter year
$likes = @("%GPS%","%sales to dealer%","%Genuine Parts%","%dealer%share%","%parts share%")
$hits = New-Object System.Collections.Generic.List[object]
foreach ($like in $likes) {
  try {
    $f = "@SQL=""urn:schemas:httpmail:subject"" LIKE '$like'"
    $items = $sent.Items.Restrict($f)
    $n = 0; try { $n = $items.Count } catch {}
    Write-Host "Sent $like = $n"
    for ($i=1; $i -le [Math]::Min($n,100); $i++) {
      $it = $null; try { $it = $items.Item($i) } catch { continue }
      if ([int]$it.Class -ne 43) { continue }
      $rec = ""; try { $rec = $it.SentOn.ToString("s") } catch {}
      $subj = [string]$it.Subject
      $to = ""; try { $to = [string]$it.To } catch {}
      $body = ""; try { $body = [string]$it.Body } catch {}
      $yr = 0; if ($rec -match "^(\d{4})") { $yr = [int]$Matches[1] }
      if ($yr -ge 2024 -and $yr -le 2025) {
        if ($body.Length -gt 10000) { $body = $body.Substring(0,10000) }
        $hits.Add([pscustomobject]@{Received=$rec; To=$to; Subject=$subj; Body=$body}) | Out-Null
      }
    }
  } catch { Write-Host "fail $like $_" }
}

# Also InstantSearch / filter Inbox for received before 2026-01-01 with GPS
$inbox = $ns.GetDefaultFolder(6)
try {
  $f = "@SQL=(""urn:schemas:httpmail:subject"" LIKE '%GPS%' OR ""urn:schemas:httpmail:subject"" LIKE '%sales to dealer%' OR ""urn:schemas:httpmail:subject"" LIKE '%Genuine Parts Share%') AND (""urn:schemas:httpmail:datereceived"" < '2026-01-01')"
  $items = $inbox.Items.Restrict($f)
  $n = 0; try { $n = $items.Count } catch {}
  Write-Host "Inbox pre-2026 GPS/S2D subject=$n"
  for ($i=1; $i -le [Math]::Min($n,50); $i++) {
    $it = $null; try { $it = $items.Item($i) } catch { continue }
    if ([int]$it.Class -ne 43) { continue }
    $rec = ""; try { $rec = $it.ReceivedTime.ToString("s") } catch {}
    $subj = [string]$it.Subject
    $from = ""; try { $from = [string]$it.SenderName } catch {}
    $body = ""; try { $body = [string]$it.Body } catch {}
    if ($body.Length -gt 8000) { $body = $body.Substring(0,8000) }
    $hits.Add([pscustomobject]@{Received=$rec; From=$from; Subject=$subj; Body=$body; Folder="InboxPre2026"}) | Out-Null
    Write-Host "  $rec | $from | $subj"
  }
} catch { Write-Host "pre2026 fail $_" }

# Walk stores for Archive folders with Hayakawa 2025
function Walk($folder, $depth) {
  if ($depth -gt 5) { return }
  $path = ""
  try { $path = $folder.FolderPath } catch { return }
  if ($path -match "(?i)junk|spam|rss|conversation history|sync issues") { return }
  try {
    $items = $folder.Items.Restrict("@SQL=""urn:schemas:httpmail:fromemail"" LIKE '%hayakawa%' OR ""urn:schemas:httpmail:fromname"" LIKE '%Hayakawa%'")
    $n = 0; try { $n = $items.Count } catch {}
    if ($n -gt 0) {
      Write-Host "FOLDER $path MH=$n"
      for ($i=1; $i -le $n; $i++) {
        $it = $null; try { $it = $items.Item($i) } catch { continue }
        if ([int]$it.Class -ne 43) { continue }
        $rec = ""; try { $rec = $it.ReceivedTime.ToString("s") } catch {}
        if ($rec -notmatch "^202[45]") { continue }
        $subj = [string]$it.Subject
        $body = ""; try { $body = [string]$it.Body } catch {}
        $blob = ($subj+" "+$body).ToLower()
        if ($blob -match "gps|dealer|share|sales to") {
          if ($body.Length -gt 6000) { $body = $body.Substring(0,6000) }
          $hits.Add([pscustomobject]@{Received=$rec; From="Masumi"; Subject=$subj; Body=$body; Folder=$path}) | Out-Null
          Write-Host "  HIT $rec | $subj"
        }
      }
    }
  } catch {}
  try { foreach ($sf in $folder.Folders) { Walk $sf ($depth+1) } } catch {}
}
foreach ($store in $ns.Folders) {
  try { Walk $store 0 } catch {}
}

$hits | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 "$outDir\s2d_2025_archive_hunt.json"
Write-Host "HITS $($hits.Count)"
$hits | Select-Object Folder, Received, From, To, Subject | Format-Table -AutoSize
