# Import ISZE weekly scheduled tasks (Stream S7)
# Run in elevated PowerShell (Run as administrator)
# Date: 2026-07-21
#
# Two entries here duplicate tasks that already exist under a different name, so
# importing them creates two tasks running the same batch file at the same time.
# That happened once: both duplicates were deleted on 2026-07-26 and the older
# names ('ISZE Tender Monitor', 'ISZE_PMS_IAM_Refresh') are canonical. The entries
# are kept for reference but skipped unless -Force, so a plain re-run of this
# script cannot recreate the double-run.

[CmdletBinding()]
param([switch]$Force)

$ErrorActionPreference = 'Stop'

$tasks = @(
  @{
    Name         = 'ISZE_TenderMonitor_Weekly'
    Xml          = Join-Path $PSScriptRoot '..\ISZE_Tender_Monitor_Install\ISZE_TenderMonitor_WeeklyTask.xml'
    RedundantWith = 'ISZE Tender Monitor'
  },
  @{
    Name         = 'ISZE_ScraperRefresh_Weekly'
    Xml          = Join-Path $PSScriptRoot '..\autodoc_scraper\ISZE_ScraperRefresh_WeeklyTask.xml'
    RedundantWith = 'ISZE_PMS_IAM_Refresh'
  },
  @{
    Name = 'ISZE_DiscountScanner_Weekly'
    Xml  = Join-Path $PSScriptRoot '..\discount-scanner\ISZE_DiscountScanner_WeeklyTask.xml'
  },
  @{
    Name = 'ISZE_CursorWeekDigest_Weekly'
    Xml  = Join-Path $PSScriptRoot 'ISZE_CursorWeekDigest_WeeklyTask.xml'
  },
  @{
    Name = 'ISZE_LiveStateAudit_Weekly'
    Xml  = Join-Path $PSScriptRoot 'ISZE_LiveStateAudit_WeeklyTask.xml'
  }
)

Write-Host 'Existing ISZE_* tasks:'
schtasks /Query /FO LIST 2>$null | Select-String -Pattern 'ISZE_'

foreach ($t in $tasks) {
  if ($t.RedundantWith -and -not $Force) {
    Write-Warning ("Skipping " + $t.Name + " - duplicates '" + $t.RedundantWith + "', which would double-run. Use -Force to override.")
    continue
  }

  $xml = Resolve-Path $t.Xml -ErrorAction SilentlyContinue
  if (-not $xml) {
    Write-Warning ("Missing XML: " + $t.Xml)
    continue
  }
  Write-Host ''
  Write-Host ("Importing " + $t.Name + " from " + $xml)
  schtasks /Create /TN $t.Name /XML $xml.Path /F
  if ($LASTEXITCODE -eq 0) {
    Write-Host ("OK " + $t.Name) -ForegroundColor Green
  } else {
    Write-Warning ("Failed " + $t.Name + " exit=" + $LASTEXITCODE + " - try elevated shell or Task Scheduler GUI")
  }
}

Write-Host ''
Write-Host 'After import:'
schtasks /Query /FO LIST 2>$null | Select-String -Pattern 'ISZE_'
