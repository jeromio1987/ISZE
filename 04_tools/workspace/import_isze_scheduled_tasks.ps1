# Import ISZE weekly scheduled tasks (Stream S7)
# Run in elevated PowerShell (Run as administrator)
# Date: 2026-07-21

$ErrorActionPreference = 'Stop'

$tasks = @(
  @{
    Name = 'ISZE_TenderMonitor_Weekly'
    Xml  = Join-Path $PSScriptRoot '..\ISZE_Tender_Monitor_Install\ISZE_TenderMonitor_WeeklyTask.xml'
  },
  @{
    Name = 'ISZE_ScraperRefresh_Weekly'
    Xml  = Join-Path $PSScriptRoot '..\autodoc_scraper\ISZE_ScraperRefresh_WeeklyTask.xml'
  },
  @{
    Name = 'ISZE_DiscountScanner_Weekly'
    Xml  = Join-Path $PSScriptRoot '..\discount-scanner\ISZE_DiscountScanner_WeeklyTask.xml'
  }
)

Write-Host 'Existing ISZE_* tasks:'
schtasks /Query /FO LIST 2>$null | Select-String -Pattern 'ISZE_'

foreach ($t in $tasks) {
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
