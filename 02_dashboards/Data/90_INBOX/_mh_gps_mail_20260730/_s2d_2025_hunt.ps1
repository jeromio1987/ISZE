$ErrorActionPreference = "Continue"
$outDir = "C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_mh_gps_mail_20260730"
$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace("MAPI")
$inbox = $ns.GetDefaultFolder(6)
$sent = $ns.GetDefaultFolder(5)
$hits = New-Object System.Collections.Generic.List[object]

function Pull($folder, $label, $like, $maxN) {
  $f = "@SQL=""urn:schemas:httpmail:subject"" LIKE '$like'"
  try {
    $items = $folder.Items.Restrict($f)
    try { $items.Sort("[ReceivedTime]", $true) } catch { try { $items.Sort("[SentOn]", $true) } catch {} }
    $n = 0; try { $n = $items.Count } catch {}
    Write-Host "$label $like = $n"
    $max = [Math]::Min($n, $maxN)
    for ($i=1; $i -le $max; $i++) {
      $it = $null; try { $it = $items.Item($i) } catch { continue }
      if ([int]$it.Class -ne 43) { continue }
      $subj = [string]$it.Subject
      $body = ""; try { $body = [string]$it.Body } catch {}
      $from = ""; try { $from = [string]$it.SenderName } catch {}
      $to = ""; try { $to = [string]$it.To } catch {}
      $rec = ""
      try { $rec = $it.ReceivedTime.ToString("s") } catch { try { $rec = $it.SentOn.ToString("s") } catch {} }
      # Keep 2024-2026 and S2D/GPS related
      $blob = ($subj + " " + $body).ToLower()
      $yr = 0
      if ($rec -match "^(\d{4})") { $yr = [int]$Matches[1] }
      $want = $false
      if ($blob -match "sales to dealer|sales-to-dealer|s2d|dealer level|dealer way|to the dealer") { $want = $true }
      if ($blob -match "gps" -and $blob -match "dealer|distributor|angry|upset|not agree|disagree|push back|pushback|against|refuse|not accept") { $want = $true }
      if ($yr -ge 2024 -and $yr -le 2025 -and $blob -match "gps" -and $blob -match "dealer|share|potential") { $want = $true }
      if (-not $want -and $subj -notmatch "(?i)GPS|sales to dealer|Genuine Parts|dealer sales") { continue }
      if ($body.Length -gt 12000) { $body = $body.Substring(0,12000) + "`n...[truncated]" }
      $hits.Add([pscustomobject]@{Folder=$label; Received=$rec; From=$from; To=$to; Subject=$subj; Body=$body}) | Out-Null
    }
  } catch { Write-Host "fail $label $like $_" }
}

$likes = @(
  "%GPS%",
  "%sales to dealer%",
  "%Sales to Dealer%",
  "%Genuine Parts Share%",
  "%genuine parts share%",
  "%dealer way%",
  "%S2D%"
)
foreach ($like in $likes) {
  Pull $inbox "Inbox" $like 80
  Pull $sent "Sent" $like 80
}

# Hayakawa all + filter body for 2025 / angry / S2D
$hf = "@SQL=""urn:schemas:httpmail:fromname"" LIKE '%Hayakawa%' OR ""urn:schemas:httpmail:fromemail"" LIKE '%hayakawa%'"
try {
  $items = $inbox.Items.Restrict($hf)
  $n = $items.Count
  Write-Host "Hayakawa total=$n"
  for ($i=1; $i -le $n; $i++) {
    $it = $null; try { $it = $items.Item($i) } catch { continue }
    if ([int]$it.Class -ne 43) { continue }
    $subj = [string]$it.Subject
    $body = ""; try { $body = [string]$it.Body } catch {}
    $rec = ""; try { $rec = $it.ReceivedTime.ToString("s") } catch {}
    $blob = ($subj + " " + $body).ToLower()
    if ($rec -match "^2025" -or $blob -match "2025") {
      if ($blob -match "gps|dealer|share|sales to") {
        if ($body.Length -gt 8000) { $body = $body.Substring(0,8000) }
        $hits.Add([pscustomobject]@{Folder="MH2025"; Received=$rec; From="Masumi Hayakawa"; Subject=$subj; Body=$body}) | Out-Null
      }
    }
  }
} catch { Write-Host "MH fail $_" }

$uniq = @{}; $final = New-Object System.Collections.Generic.List[object]
foreach ($h in $hits) {
  $k = "$($h.Received)|$($h.From)|$($h.Subject)"
  if ($uniq.ContainsKey($k)) { continue }
  $uniq[$k] = $true
  $final.Add($h) | Out-Null
}
$final | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 "$outDir\s2d_2025_hunt.json"
$final | Select-Object Folder, Received, From, Subject | Sort-Object Received | Export-Csv -NoTypeInformation -Encoding UTF8 "$outDir\s2d_2025_hunt_index.csv"
Write-Host "UNIQUE $($final.Count)"
$final | Sort-Object Received | Select-Object Folder, Received, From, Subject | Format-Table -AutoSize
