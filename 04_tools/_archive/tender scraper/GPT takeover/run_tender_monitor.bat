@echo off
:: ============================================================
::  ISZE Tender Monitor — Weekly Auto-Run
::  Runs the scraper then rebuilds the dashboard.
::  Schedule this via Windows Task Scheduler (see XML below).
:: ============================================================

:: --- Set UTF-8 code page so emoji + special chars print correctly ---
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: --- Locate this script's folder (works from any CWD) ---
cd /d "%~dp0"

:: --- Timestamp for the log file ---
set LOGFILE="%~dp0tender_monitor_log.txt"
echo. >> %LOGFILE%
echo ============================================================ >> %LOGFILE%
echo Run started: %DATE% %TIME% >> %LOGFILE%
echo ============================================================ >> %LOGFILE%

:: --- Run the scraper ---
echo [1/2] Running tender scraper...
python tender_scraper_v3.py >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: Scraper failed. Check log: %LOGFILE%
    exit /b 1
)

:: --- Rebuild the dashboard ---
echo [2/2] Rebuilding dashboard...
python build_dashboard_v2.py >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: Dashboard build failed. Check log: %LOGFILE%
    exit /b 1
)

echo Done: %DATE% %TIME% >> %LOGFILE%
echo All done. Dashboard updated.
