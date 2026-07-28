$ErrorActionPreference = 'Continue'
$outDir = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull'
$outlook = New-Object -ComObject Outlook.Application
$ns = $outlook.GetNamespace('MAPI')
$inbox = $ns.GetDefaultFolder(6)

# Dump ALL Duncan / Suzuki / Rene primary mails with full body
$filterSpecs = @(
  @{ Name='Duncan'; Filter="@SQL=""urn:schemas:httpmail:fromname"" LIKE '%Duncan%'" },
  @{ Name='Suzuki'; Filter="@SQL=""urn:schemas:httpmail:fromname"" LIKE '%Suzuki%'" },
  @{ Name='Rene'; Filter="@SQL=""urn:schemas:httpmail:fromname"" LIKE '%Rene%' OR ""urn:schemas:httpmail:fromemail"" LIKE '%rene.paul%'" }
)

$all = New-Object System.Collections.Generic.List[object]
foreach ($spec in $filterSpecs) {
  $items = $inbox.Items.Restrict($spec.Filter)
  try { $items.Sort('[ReceivedTime]', $true) } catch {}
  $count = $items.Count
  Write-Host ($spec.Name + ' count=' + $count)
  for ($i=1; $i -le $count; $i++) {
    $item = $items.Item($i)
    if ([int]$item.Class -ne 43) { continue }
    $body = [string]$item.Body
    $atts = @()
    foreach ($a in $item.Attachments) { $atts += $a.FileName }
    $rec = [pscustomobject]@{
      Group=$spec.Name
      Received=$item.ReceivedTime.ToString('yyyy-MM-dd HH:mm:ss')
      From=[string]$item.SenderName
      Email=[string]$item.SenderEmailAddress
      Subject=[string]$item.Subject
      Atts=($atts -join ' | ')
      Body=$body
    }
    $all.Add($rec) | Out-Null
    # Write individual body files for keyword scan
    $fn = '{0}_{1}_{2}.txt' -f $spec.Name, $item.ReceivedTime.ToString('yyyyMMdd_HHmm'), ($item.Subject -replace '[^\w\-]+','_').Substring(0, [Math]::Min(60, ($item.Subject -replace '[^\w\-]+','_').Length))
    Set-Content -Path (Join-Path $outDir $fn) -Value $body -Encoding UTF8
  }
}
$all | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $outDir 'all_three_senders_full.json') -Encoding UTF8

# Grep-like scan for interval numbers in bodies
$patterns = '(?i)(\d[\d,\.]*\s*(km|miles|mi\b|years?|yr\b|hours?|hrs?)|every\s+\d|oil\s*(change|filter)|air\s*filter|fuel\s*filter|brake|clutch|interval|visits?\s*/\s*yr|service\s+every)'
$hits = New-Object System.Collections.Generic.List[object]
foreach ($r in $all) {
  $lines = $r.Body -split "`r?`n"
  $matched = @()
  foreach ($line in $lines) {
    if ($line -match $patterns) { $matched += $line.Trim() }
  }
  if ($matched.Count -gt 0) {
    $hits.Add([pscustomobject]@{
      Group=$r.Group; Received=$r.Received; From=$r.From; Subject=$r.Subject; Atts=$r.Atts
      Lines=($matched | Select-Object -First 50)
    }) | Out-Null
  }
}
$hits | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outDir 'body_interval_lines.json') -Encoding UTF8
Write-Host "mails=$($all.Count) withIntervalLines=$($hits.Count)"
$hits | ForEach-Object {
  Write-Host ('==== ' + $_.Group + ' | ' + $_.Received + ' | ' + $_.Subject)
  $_.Lines | Select-Object -First 15 | ForEach-Object { Write-Host ('  ' + $_) }
}
