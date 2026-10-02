@echo off
:: ============================================================
::  ISZE Tender Monitor — Weekly Auto-Run (v3)
::  Scraper -> live Data\dashboards\tender_data.json + local HTML
:: ============================================================

chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

:: Optionally load Nordics API keys into this process (gitignored file).
:: Scraper also reads nordics_api_keys.env via nordics_keys.py.
if exist "%~dp0nordics_api_keys.env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%~dp0nordics_api_keys.env") do (
    if not "%%A"=="" set "%%A=%%B"
  )
)

set LOGFILE="%~dp0tender_monitor_log.txt"
echo. >> %LOGFILE%
echo ============================================================ >> %LOGFILE%
echo Run started: %DATE% %TIME% >> %LOGFILE%
echo ============================================================ >> %LOGFILE%

echo [1/5] Running tender scraper v3 (UK/TED/DE+OV/BE/NL/FR/PL/ES/IT/Nordics/ISR)...
:: FR BOAMP + PL BZP + ES PLACSP + IT PNCP + DE OV included in full weekly scrape
:: ES may stay CODE_READY if WAF-denied. DE OV uses oeffentlichevergabe csv.zip.
:: Do not invent Nordics keys here.
python tender_scraper_v3.py >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: Scraper failed. Check log: %LOGFILE%
    exit /b 1
)

echo [2/5] Publishing live JSON to Data\dashboards...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_live_tender_json.ps1" >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: JSON publish failed. Check log: %LOGFILE%
    exit /b 1
)

echo [2b/5] Reading vehicle lists in the tender documents (fleet-brand check)...
:: Public documents only: no login, robots.txt respected. Non-fatal: if a portal is down
:: the feed keeps the gate result and the run continues. Evidence: tender_docs folder
python tender_doc_reader.py --apply >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo WARNING: tender document reader failed - feed left with the gate result. Check log: %LOGFILE%
)

echo [3/5] Rebuilding local preview HTML (v2) in this folder...
python build_dashboard_v2.py >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: Local HTML build failed. Check log: %LOGFILE%
    exit /b 1
)

echo [4/5] Rebuilding GPS/PMS opportunity dashboard (v4)...
python build_dashboard_v4.py >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: v4 dashboard build failed. Check log: %LOGFILE%
    exit /b 1
)

echo [5/5] Building weekly R&M distributor digest...
python build_rm_digest.py >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: R&M digest build failed. Check log: %LOGFILE%
    exit /b 1
)

echo Done: %DATE% %TIME% >> %LOGFILE%
echo All done. Live: ..\..\Data\dashboards\tender_data.json
echo v4: isze_dashboard_v4_opportunity.html
