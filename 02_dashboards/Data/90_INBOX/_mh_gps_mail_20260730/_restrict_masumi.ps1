$ErrorActionPreference = "Continue"
$outDir = "C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_mh_gps_mail_20260730"
$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace("MAPI")
$inbox = $ns.GetDefaultFolder(6)
$sent = $ns.GetDefaultFolder(5)
$filter = "@SQL=""urn:schemas:httpmail:fromname"" LIKE '%Hayakawa%' OR ""urn:schemas:httpmail:fromemail"" LIKE '%hayakawa%' OR ""urn:schemas:httpmail:fromname"" LIKE '%Masumi%'"
$hits = New-Object System.Collections.Generic.List[object]
function Pull($folder, $label) {
  $items = $null
  try { $items = $folder.Items.Restrict($filter) } catch {
    try { $items = $folder.Items.Restrict("[SenderName] LIKE '%Hayakawa%'") } catch { Write-Host "FAIL $label $_"; return }
  }
  try { $items.Sort("[ReceivedTime]", $true) } catch {}
  $n = 0; try { $n = $items.Count } catch { $n = 0 }
  Write-Host "$label matches=$n"
  $max = [Math]::Min($n, 120)
  for ($i=1; $i -le $max; $i++) {
    $it = $null; try { $it = $items.Item($i) } catch { continue }
    if ([int]$it.Class -ne 43) { continue }
    $subj = [string]$it.Subject
    $body = ""
    try { $body = [string]$it.Body } catch {}
    if ($body.Length -gt 8000) { $body = $body.Substring(0,8000) + "`n...[truncated]" }
    $from = ""; try { $from = [string]$it.SenderName } catch {}
    $rec = ""; try { $rec = $it.ReceivedTime.ToString("s") } catch {}
    $hits.Add([pscustomobject]@{Folder=$label; Received=$rec; From=$from; Subject=$subj; Body=$body}) | Out-Null
  }
}
Pull $inbox "Inbox"
# Sent: subject-based GPS/Masumi related
$sentFilter = "@SQL=""urn:schemas:httpmail:subject"" LIKE '%GPS%' OR ""urn:schemas:httpmail:subject"" LIKE '%KPI_targets%' OR ""urn:schemas:httpmail:subject"" LIKE '%Minutes ITUK%' OR ""urn:schemas:httpmail:subject"" LIKE '%sales to dealer%' OR ""urn:schemas:httpmail:subject"" LIKE '%PMS%' OR ""urn:schemas:httpmail:subject"" LIKE '%Action plan FY2027%' OR ""urn:schemas:httpmail:subject"" LIKE '%incentive%'"
try {
  $sitems = $sent.Items.Restrict($sentFilter)
  try { $sitems.Sort("[SentOn]", $true) } catch {}
  $sn = 0; try { $sn = $sitems.Count } catch {}
  Write-Host "Sent subject matches=$sn"
  $max = [Math]::Min($sn, 80)
  for ($i=1; $i -le $max; $i++) {
    $it = $null; try { $it = $sitems.Item($i) } catch { continue }
    if ([int]$it.Class -ne 43) { continue }
    $subj = [string]$it.Subject
    $to = ""; try { $to = [string]$it.To } catch {}
    if ($to -notmatch "(?i)hayakawa|masumi" -and $subj -notmatch "(?i)GPS|Minutes ITUK|KPI_targets|sales to dealer|PMS|Action plan|incentive|lubricant|IDS") { continue }
    $body = ""; try { $body = [string]$it.Body } catch {}
    if ($body.Length -gt 8000) { $body = $body.Substring(0,8000) + "`n...[truncated]" }
    $rec = ""; try { $rec = $it.SentOn.ToString("s") } catch {}
    $hits.Add([pscustomobject]@{Folder="Sent"; Received=$rec; From="Jerome (Sent)"; Subject=$subj; Body=$body; To=$to}) | Out-Null
  }
} catch { Write-Host "Sent fail $_" }
$hits | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $outDir "mh_restrict_hits.json")
$hits | Select-Object Folder, Received, From, Subject | Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $outDir "mh_restrict_index.csv")
Write-Host "TOTAL:" $hits.Count
$hits | Select-Object -First 40 Folder, Received, Subject | Format-Table -AutoSize
