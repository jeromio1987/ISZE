# Fetch UTI "UTIPartSales" Excel attachments from Outlook (noreply2@uti.co.il).
# Targets monthly runs on 1 Jan 2025 and 1 Jan 2026 (DD/MM in subject: 01/01/YYYY).
param(
    [string]$DestRoot = "",
    [string]$Sender = "noreply2@uti.co.il",
    [string[]]$SubjectDateTokens = @("01/01/2025", "01/01/2026")
)

$ErrorActionPreference = "Stop"
$IszeRootPs1 = Join-Path $PSScriptRoot '..\workspace\isze_root.ps1'
. $IszeRootPs1
if (-not $DestRoot) {
    $DestRoot = Join-Path (Get-IszePath -Key 'data' -Legacy 'Data') 'raw\dealer_sales\UTI'
}
New-Item -ItemType Directory -Force -Path $DestRoot | Out-Null

$ol = New-Object -ComObject Outlook.Application
$ns = $ol.GetNamespace("MAPI")
$inbox = $ns.GetDefaultFolder(6)
$items = $inbox.Items
$items.Sort("[ReceivedTime]", $true)
$items.IncludeRecurrences = $false

$found = 0
foreach ($mail in $items) {
    if ($mail.Class -ne 43) { continue }  # olMail
    $from = ""
    try { $from = $mail.SenderEmailAddress } catch {}
    if ($from -notmatch [regex]::Escape($Sender)) { continue }
    $subj = [string]$mail.Subject
    if ($subj -notmatch "UTIPartSales") { continue }
    $matchToken = $SubjectDateTokens | Where-Object { $subj -like "*$_*" } | Select-Object -First 1
    if (-not $matchToken) { continue }

    $period = if ($matchToken -match "2025") { "2025-01" } else { "2026-01" }
    $periodDir = Join-Path $DestRoot $period
    New-Item -ItemType Directory -Force -Path $periodDir | Out-Null

    $attCount = $mail.Attachments.Count
    if ($attCount -eq 0) {
        Write-Warning "No attachments: $subj"
        continue
    }
    for ($i = 1; $i -le $attCount; $i++) {
        $att = $mail.Attachments.Item($i)
        $ext = [System.IO.Path]::GetExtension($att.FileName).ToLowerInvariant()
        if ($ext -notin @(".xlsx", ".xls", ".xlsm", ".csv")) { continue }
        $safe = $att.FileName -replace '[^\w\.\-]', '_'
        $out = Join-Path $periodDir ("Sales_to_Dealers_UTI_{0}_{1}" -f $period, $safe)
        $att.SaveAsFile($out)
        Write-Host "Saved: $out"
        $found++
    }
}

if ($found -eq 0) {
    Write-Error "No matching UTIPartSales attachments found. Check Outlook is running and emails exist for 01/01/2025 and 01/01/2026."
}
Write-Host "Done. Files in $DestRoot"
