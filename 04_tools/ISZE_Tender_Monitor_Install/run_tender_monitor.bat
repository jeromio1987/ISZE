@echo off
:: ============================================================
::  ISZE Tender Monitor — Weekly Auto-Run (v3)
::  Scraper -> live Data\dashboards\tender_data.json + local HTML
:: ============================================================

chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

set LOGFILE="%~dp0tender_monitor_log.txt"
echo. >> %LOGFILE%
echo ============================================================ >> %LOGFILE%
echo Run started: %DATE% %TIME% >> %LOGFILE%
echo ============================================================ >> %LOGFILE%

echo [1/3] Running tender scraper v3...
python tender_scraper_v3.py >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: Scraper failed. Check log: %LOGFILE%
    exit /b 1
)

echo [2/3] Publishing live JSON to Data\dashboards...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_live_tender_json.ps1" >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: JSON publish failed. Check log: %LOGFILE%
    exit /b 1
)

echo [3/3] Rebuilding local preview HTML in this folder...
python build_dashboard_v2.py >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: Local HTML build failed. Check log: %LOGFILE%
    exit /b 1
)

echo Done: %DATE% %TIME% >> %LOGFILE%
echo All done. Live: ..\..\Data\dashboards\tender_data.json
