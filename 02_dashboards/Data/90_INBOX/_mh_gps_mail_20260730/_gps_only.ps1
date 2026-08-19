$ErrorActionPreference = "Continue"
$outDir = "C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_mh_gps_mail_20260730"
$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace("MAPI")
$inbox = $ns.GetDefaultFolder(6)
$sent = $ns.GetDefaultFolder(5)
$hits = New-Object System.Collections.Generic.List[object]
function Pull($folder, $label, $like) {
  $f = "@SQL=""urn:schemas:httpmail:subject"" LIKE '$like'"
  try {
    $items = $folder.Items.Restrict($f)
    try { $items.Sort("[ReceivedTime]", $true) } catch { try { $items.Sort("[SentOn]", $true) } catch {} }
    $n = 0; try { $n = $items.Count } catch {}
    Write-Host "$label $like = $n"
    $max = [Math]::Min($n, 30)
    for ($i=1; $i -le $max; $i++) {
      $it = $null; try { $it = $items.Item($i) } catch { continue }
      if ([int]$it.Class -ne 43) { continue }
      $subj = [string]$it.Subject
      $body = ""; try { $body = [string]$it.Body } catch {}
      if ($body.Length -gt 16000) { $body = $body.Substring(0,16000) + "`n...[truncated]" }
      $from = ""; try { $from = [string]$it.SenderName } catch {}
      $to = ""; try { $to = [string]$it.To } catch {}
      $rec = ""
      try { $rec = $it.ReceivedTime.ToString("s") } catch { try { $rec = $it.SentOn.ToString("s") } catch {} }
      $hits.Add([pscustomobject]@{Folder=$label; Received=$rec; From=$from; To=$to; Subject=$subj; Body=$body}) | Out-Null
    }
  } catch { Write-Host "fail $label $like $_" }
}
$likes = @("%GPS //%","%GPS and the target%","%KPI_targets%","%SPAs shown in the waterfall%","%IX Study Waterfall%")
foreach ($like in $likes) {
  Pull $inbox "Inbox" $like
  Pull $sent "Sent" $like
}
$uniq = @{}; $final = New-Object System.Collections.Generic.List[object]
foreach ($h in $hits) {
  $k = "$($h.Received)|$($h.From)|$($h.Subject)"
  if ($uniq.ContainsKey($k)) { continue }
  $uniq[$k]=$true; $final.Add($h)|Out-Null
}
$final | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 "$outDir\gps_threads_only.json"
Write-Host "UNIQUE $($final.Count)"
$final | Sort-Object Received | ForEach-Object {
  $safe = ($_.Subject -replace '[^\w\-]+','_').Substring(0, [Math]::Min(60, ($_.Subject -replace '[^\w\-]+','_').Length))
  $fn = "$($_.Received.Substring(0,10))_$($_.Folder)_$safe.txt"
  @"
FROM: $($_.From)
TO: $($_.To)
RECV: $($_.Received)
SUBJ: $($_.Subject)

$($_.Body)
"@ | Set-Content -Encoding UTF8 (Join-Path $outDir $fn)
  Write-Host $fn
}
