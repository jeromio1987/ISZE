$ErrorActionPreference = "Continue"
$outDir = "C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_mh_gps_mail_20260730"
$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace("MAPI")
$inbox = $ns.GetDefaultFolder(6)
$sent = $ns.GetDefaultFolder(5)

# Deeper Hayakawa: get ALL matches (not just 120), dump GPS-relevant + older
$filter = "@SQL=""urn:schemas:httpmail:fromname"" LIKE '%Hayakawa%' OR ""urn:schemas:httpmail:fromemail"" LIKE '%hayakawa%'"
$items = $inbox.Items.Restrict($filter)
try { $items.Sort("[ReceivedTime]", $true) } catch {}
$n = $items.Count
Write-Host "All Hayakawa inbox=$n"
$hits = New-Object System.Collections.Generic.List[object]
$subjWant = '(?i)GPS|KPI|target|PMS|incentive|lubricant|oil purchase|waterfall|Action plan|IDS|stretch|dealer|Minutes ITUK|sales to'
for ($i=1; $i -le $n; $i++) {
  $it = $null; try { $it = $items.Item($i) } catch { continue }
  if ([int]$it.Class -ne 43) { continue }
  $subj = [string]$it.Subject
  if ($subj -notmatch $subjWant) { continue }
  $body = ""; try { $body = [string]$it.Body } catch {}
  if ($body.Length -gt 10000) { $body = $body.Substring(0,10000) + "`n...[truncated]" }
  $from = ""; try { $from = [string]$it.SenderName } catch {}
  $rec = ""; try { $rec = $it.ReceivedTime.ToString("s") } catch {}
  $hits.Add([pscustomobject]@{Folder="Inbox"; Received=$rec; From=$from; Subject=$subj; Body=$body}) | Out-Null
}
Write-Host "Filtered Hayakawa strategic=$($hits.Count)"

# Sent to Masumi / GPS clarification threads
$sentHits = 0
$sentItems = $sent.Items
try { $sentItems.Sort("[SentOn]", $true) } catch {}
$checked = 0
foreach ($it in $sentItems) {
  $checked++
  if ($checked -gt 5000) { break }
  try {
    if ([int]$it.Class -ne 43) { continue }
    $subj = [string]$it.Subject
    $to = ""; try { $to = [string]$it.To } catch {}
    $cc = ""; try { $cc = [string]$it.CC } catch {}
    $blob = "$subj $to $cc"
    $want = $false
    if ($blob -match "(?i)hayakawa|masumi") { $want = $true }
    elseif ($subj -match "(?i)GPS //|Minutes ITUK|sales to dealer|KPI_targets|GPS and the target|Wrap Up PMS|Action plan FY2027|BP sales incentive") { $want = $true }
    if (-not $want) { continue }
    if ($subj -notmatch "(?i)GPS|KPI|target|PMS|incentive|lubricant|waterfall|Action plan|IDS|dealer|Minutes|stretch|oil") { continue }
    $body = ""; try { $body = [string]$it.Body } catch {}
    if ($body.Length -gt 10000) { $body = $body.Substring(0,10000) + "`n...[truncated]" }
    $rec = ""; try { $rec = $it.SentOn.ToString("s") } catch {}
    $hits.Add([pscustomobject]@{Folder="Sent"; Received=$rec; From="Jerome (Sent)"; Subject=$subj; Body=$body; To=$to}) | Out-Null
    $sentHits++
    if ($sentHits -ge 60) { break }
  } catch {}
}
Write-Host "Sent strategic added=$sentHits checked=$checked"

# Also AdvancedSearch-style subject restrict on Inbox for key subjects regardless of sender
$subjFilters = @(
  "%GPS //%",
  "%Minutes ITUK%",
  "%sales to dealer%",
  "%Wrap Up PMS%",
  "%BP sales incentive%",
  "%Centralised Purchasing%",
  "%oil purchase DBs%",
  "%Action plan FY2027%"
)
foreach ($sf in $subjFilters) {
  $f = "@SQL=""urn:schemas:httpmail:subject"" LIKE '$sf'"
  try {
    $si = $inbox.Items.Restrict($f)
    $cn = 0; try { $cn = $si.Count } catch {}
    Write-Host "Subj $sf count=$cn"
    $max = [Math]::Min($cn, 25)
    for ($i=1; $i -le $max; $i++) {
      $it = $null; try { $it = $si.Item($i) } catch { continue }
      if ([int]$it.Class -ne 43) { continue }
      $subj = [string]$it.Subject
      $body = ""; try { $body = [string]$it.Body } catch {}
      if ($body.Length -gt 10000) { $body = $body.Substring(0,10000) + "`n...[truncated]" }
      $from = ""; try { $from = [string]$it.SenderName } catch {}
      $rec = ""; try { $rec = $it.ReceivedTime.ToString("s") } catch {}
      $hits.Add([pscustomobject]@{Folder="InboxSubj"; Received=$rec; From=$from; Subject=$subj; Body=$body}) | Out-Null
    }
  } catch { Write-Host "fail $sf $_" }
}

$hits | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $outDir "mh_gps_deep.json")
$hits | Select-Object Folder, Received, From, Subject | Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $outDir "mh_gps_deep_index.csv")
Write-Host "TOTAL deep hits:" $hits.Count
$hits | Sort-Object Received -Descending | Select-Object Folder, Received, From, Subject | Format-Table -AutoSize
