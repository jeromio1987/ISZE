# fetch_spa_baskets_from_outlook.ps1
#
# Reads ONE folder in Jerome's own mailbox over local Outlook COM and saves the
# spreadsheet attachments it finds into a predictable local folder, so the SPA
# application builder has a basket to read without anyone retyping it.
#
# WHY THIS EXISTS
# ---------------
# Eran (and now other distributors) send the SPA basket as an attachment. Today
# that list is retyped into the optimizer. This script removes the retype: the
# attachment lands in 01_data\90_INBOX\_spa_baskets\ and the builder reads it.
#
# HOW IT PAIRS WITH THE MAIL RULE
# -------------------------------
# A rule in Outlook on the web copies mail that has an attachment into a folder
# named "SPA attachments". This script reads that folder. The rule cannot save an
# attachment to a disk - only classic Outlook can, and Microsoft lists "save to
# disk" among the client-only actions that the web rule engine does not support.
# So the split is: the rule files the mail, this script takes the files out.
#
# READ-ONLY ON MAIL. This script never moves, copies, deletes, flags, marks read
# or sends anything. It reads attachment content and writes new files locally.
# It writes NOTHING back into the mailbox.
#
# ATTACHMENT TYPES KEPT  : .xlsx .xls .xlsm .csv
# ATTACHMENT TYPES SKIPPED: everything else, including the inline signature
#                          images (image001.png and friends) that every mail
#                          carries, and .msg forwards.
#
# USAGE
#   .\fetch_spa_baskets_from_outlook.ps1 -DryRun      # list, save nothing
#   .\fetch_spa_baskets_from_outlook.ps1              # real run
#   .\fetch_spa_baskets_from_outlook.ps1 -Folder "Inbox\SPA attachments"

[CmdletBinding()]
param(
    # The mailbox folder the web rule copies into. May be a subfolder of Inbox.
    [string]$Folder = "SPA attachments",

    # Where the spreadsheets land. Default is the git-ignored drop zone.
    [string]$DestRoot = "",

    # List what would be saved and write nothing.
    [switch]$DryRun,

    # Only consider mail received on or after this date. Blank = all mail in the folder.
    [string]$Since = "",

    # Cap the number of messages examined, for a quick trial run.
    [int]$MaxMessages = 0,

    # Overwrite a same-named file instead of adding a timestamp.
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# ----------------------------------------------------------------- preflight
$IszeRootPs1 = Join-Path $PSScriptRoot '..\workspace\isze_root.ps1'
if (Test-Path $IszeRootPs1) {
    . $IszeRootPs1
}

function Get-Root {
    if ($env:ISZE_ROOT -and (Test-Path (Join-Path $env:ISZE_ROOT 'paths.yaml'))) {
        return (Resolve-Path $env:ISZE_ROOT).Path
    }
    $p = $PSScriptRoot
    while ($p) {
        if ((Test-Path (Join-Path $p 'paths.yaml')) -and (Test-Path (Join-Path $p 'FACTS.md'))) {
            return $p
        }
        $parent = Split-Path $p -Parent
        if ($parent -eq $p) { break }
        $p = $parent
    }
    return $null
}

$root = Get-Root
if (-not $root) {
    Write-Host "ABORTED - missing input: ISZE root (no paths.yaml + FACTS.md found; set `$env:ISZE_ROOT)" -ForegroundColor Red
    exit 1
}

if (-not $DestRoot) {
    $DestRoot = Join-Path $root '01_data\90_INBOX\_spa_baskets'
}

# Classic Outlook present? ClickToRun does not put it on PATH.
$outlookExe = $null
foreach ($p in @(
        'C:\Program Files\Microsoft Office\Root\Office16\OUTLOOK.EXE',
        'C:\Program Files (x86)\Microsoft Office\Root\Office16\OUTLOOK.EXE'
    )) {
    if (Test-Path $p) { $outlookExe = $p; break }
}
if (-not $outlookExe) {
    try {
        $reg = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE' -ErrorAction Stop
        if ($reg.'(default)') { $outlookExe = $reg.'(default)' }
    } catch { }
}
if (-not $outlookExe) {
    Write-Host "ABORTED - missing input: classic Outlook (no OUTLOOK.EXE found)." -ForegroundColor Red
    Write-Host "  This script needs classic desktop Outlook for Windows. The new Outlook and" -ForegroundColor Yellow
    Write-Host "  Outlook on the web do not expose COM, so this route stops working if IT" -ForegroundColor Yellow
    Write-Host "  moves this machine to the new Outlook." -ForegroundColor Yellow
    exit 1
}

if (-not $DryRun) {
    if (-not (Test-Path $DestRoot)) {
        New-Item -ItemType Directory -Force -Path $DestRoot | Out-Null
        Write-Host "created output folder: $DestRoot"
    }
}

$KeepExt = @('.xlsx', '.xls', '.xlsm', '.csv')

Write-Host ""
Write-Host "SPA basket attachment fetch" -ForegroundColor Cyan
Write-Host "  mailbox folder : $Folder"
Write-Host "  output folder  : $DestRoot"
Write-Host "  keeping        : $($KeepExt -join ', ')"
if ($DryRun) { Write-Host "  mode           : DRY RUN (nothing will be saved)" -ForegroundColor Yellow }
Write-Host ""

# ------------------------------------------------------------- connect to Outlook
$ol = $null
try {
    $ol = New-Object -ComObject Outlook.Application
} catch {
    Write-Host "ABORTED - could not reach Outlook over COM: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Start classic Outlook and sign in, then run this again." -ForegroundColor Yellow
    exit 1
}

try {
    $ns = $ol.GetNamespace("MAPI")

    # Own store only. Never the shared Sales or Parts mailboxes.
    $refused = @('sales', 'parts')
    $storeName = ""
    try { $storeName = $ns.GetDefaultFolder(6).Store.DisplayName } catch { }
    $storeLower = $storeName.ToLower()
    if ($refused | Where-Object { $storeLower -eq $_ -or ($storeLower -split '\s+') -contains $_ }) {
        Write-Host "REFUSED - the default store is '$storeName', which looks like a shared mailbox." -ForegroundColor Red
        Write-Host "  This script is scoped to your own mailbox." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "store: $storeName"

    # ---------------------------------------------------- find the named folder
    # The rule-created folder may sit under Inbox, or at the top level. Look in
    # both, and accept either the leaf name or an Inbox-qualified path.
    $leaf = ($Folder -split '\\')[-1]

    function Find-Folder {
        param($parent, [string]$wantLeaf)
        try { $subs = $parent.Folders } catch { return $null }
        foreach ($f in $subs) {
            if ($f.Name -ieq $wantLeaf) { return $f }
        }
        foreach ($f in $subs) {
            $hit = Find-Folder -parent $f -wantLeaf $wantLeaf
            if ($hit) { return $hit }
        }
        return $null
    }

    # The Inbox root itself is a valid answer - it is not found by searching its
    # own subfolders, so check it by name first.
    $target = $null
    $inbox = $null
    try { $inbox = $ns.GetDefaultFolder(6) } catch { }
    if ($inbox) {
        if ($inbox.Name -ieq $leaf -or $leaf -ieq 'Inbox') {
            $target = $inbox
        } else {
            try { $target = Find-Folder -parent $inbox -wantLeaf $leaf } catch { }
        }
    }

    if (-not $target) {
        Write-Host ""
        Write-Host "ABORTED - missing input: mailbox folder '$leaf' not found." -ForegroundColor Red
        Write-Host "  Create the folder in Outlook on the web first (the rule steps are in the" -ForegroundColor Yellow
        Write-Host "  handover note), or point -Folder at an existing folder:" -ForegroundColor Yellow
        Write-Host "    .\fetch_spa_baskets_from_outlook.ps1 -Folder `"Inbox\Some folder`"" -ForegroundColor Yellow
        exit 1
    }

    $folderPath = ""
    try { $folderPath = $target.FolderPath } catch { $folderPath = $leaf }
    Write-Host "found folder: $folderPath"

    # ------------------------------------------------------------- read the mail
    $items = $target.Items
    $items.Sort("[ReceivedTime]", $true)

    $cutoff = $null
    if ($Since) {
        try { $cutoff = [datetime]::Parse($Since) } catch {
            Write-Host "ABORTED - bad -Since value '$Since'. Use YYYY-MM-DD." -ForegroundColor Red
            exit 1
        }
    }

    # Ledger of what has already been taken, keyed on file hash. Lets a re-run
    # skip anything already saved without ever creating a duplicate copy.
    $ledgerPath = Join-Path $DestRoot '_spa_baskets_ledger.csv'
    $known = @{}
    if (Test-Path $ledgerPath) {
        foreach ($row in (Import-Csv $ledgerPath)) {
            if ($row.hash) { $known[$row.hash] = $true }
        }
    }

    $seen = 0
    $saved = 0
    $dupes = 0
    $skipped = 0
    $mailsWithFiles = 0
    $newRows = New-Object System.Collections.Generic.List[object]

    foreach ($mail in $items) {
        if ($MaxMessages -gt 0 -and $seen -ge $MaxMessages) { break }

        if ($mail.Class -ne 43) { continue }   # 43 = olMail
        $seen++

        $attCount = 0
        try { $attCount = $mail.Attachments.Count } catch { $attCount = 0 }
        if ($attCount -eq 0) { continue }

        $received = $null
        try { $received = $mail.ReceivedTime } catch { }
        if ($cutoff -and $received -and $received -lt $cutoff) { continue }

        $stamp = if ($received) { ([datetime]$received).ToString('yyyyMMdd') } else { 'nodate' }
        $mailHadFile = $false

        for ($i = 1; $i -le $attCount; $i++) {
            $att = $null
            try { $att = $mail.Attachments.Item($i) } catch { continue }

            $name = ""
            try { $name = [string]$att.FileName } catch { }
            if (-not $name) { continue }

            $ext = [System.IO.Path]::GetExtension($name).ToLowerInvariant()
            if ($ext -notin $KeepExt) {
                $skipped++
                continue
            }

            # Hash the attachment content. Saved to a temp file first because
            # that is the only reliable way to read attachment bytes over COM.
            $tmp = Join-Path $env:TEMP ("spa_att_{0}_{1}{2}" -f $PID, [guid]::NewGuid().ToString('N'), $ext)
            try {
                $att.SaveAsFile($tmp)
            } catch {
                Write-Host "  could not read attachment '$name' - skipped ($($_.Exception.Message))" -ForegroundColor Yellow
                $skipped++
                continue
            }

            $hash = (Get-FileHash -Path $tmp -Algorithm SHA256).Hash

            if ($known.ContainsKey($hash)) {
                $dupes++
                Remove-Item $tmp -Force -ErrorAction SilentlyContinue
                continue
            }

            $safe = ($name -replace '[^\w\.\-]', '_')
            $outName = "{0}_{1}" -f $stamp, $safe
            $outPath = Join-Path $DestRoot $outName

            if ((Test-Path $outPath) -and -not $Force) {
                $outName = "{0}_{1}_{2}" -f $stamp, $hash.Substring(0, 8), $safe
                $outPath = Join-Path $DestRoot $outName
            }

            if ($DryRun) {
                Write-Host ("  would save: {0}  ({1:N0} bytes)" -f $outName, (Get-Item $tmp).Length)
            } else {
                Move-Item -Path $tmp -Destination $outPath -Force
                Write-Host ("  saved: {0}  ({1:N0} bytes)" -f $outName, (Get-Item $outPath).Length)
            }
            Remove-Item $tmp -Force -ErrorAction SilentlyContinue

            # No subject and no sender is recorded: the workspace mail rule keeps
            # message subjects out of anything written to disk.
            $newRows.Add([pscustomobject]@{
                    hash          = $hash
                    saved_name    = $outName
                    original_name = $name
                    received      = if ($received) { ([datetime]$received).ToString('yyyy-MM-dd HH:mm') } else { '' }
                    bytes         = (Get-Item $outPath -ErrorAction SilentlyContinue).Length
                })

            $known[$hash] = $true
            $saved++
            $mailHadFile = $true
        }

        if ($mailHadFile) { $mailsWithFiles++ }
    }

    if (-not $DryRun -and $newRows.Count -gt 0) {
        $newRows | Export-Csv -Path $ledgerPath -NoTypeInformation -Encoding UTF8 -Append
    }

    Write-Host ""
    Write-Host "SUMMARY" -ForegroundColor Cyan
    Write-Host ("  messages examined   : {0:N0}" -f $seen)
    Write-Host ("  messages with a file: {0:N0}" -f $mailsWithFiles)
    Write-Host ("  spreadsheets saved  : {0:N0}" -f $saved)
    Write-Host ("  already saved before: {0:N0}" -f $dupes)
    Write-Host ("  non-spreadsheets    : {0:N0}  (signature images, .msg forwards, PDFs)" -f $skipped)
    if ($DryRun) {
        Write-Host "  DRY RUN - nothing was written." -ForegroundColor Yellow
    } else {
        Write-Host ("  output folder       : {0}" -f $DestRoot)
        Write-Host ("  ledger              : {0}" -f $ledgerPath)
    }
    Write-Host ""
    Write-Host "Nothing in the mailbox was moved, changed, deleted or sent." -ForegroundColor Green
}
finally {
    if ($ol) {
        try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ol) | Out-Null } catch { }
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
    }
}
