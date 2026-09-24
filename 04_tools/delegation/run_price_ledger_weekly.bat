@echo off
REM ===========================================================================
REM  ISZE - weekly price ledger + triggers  (delegation card C2)
REM  Written 2026-09-24. Runs AFTER the Monday 07:00 ISZE_PMS_IAM_Refresh so it
REM  reads that run's fresh scraper output, not last week's.
REM
REM  Order matters:
REM    1. refresh tiers   - rank parts by billed value (trailing 12 months)
REM    2. price triggers  - diff the price list vs its snapshot, queue checks
REM    3. ledger          - rebuild the one price-observation table
REM    4. parser selftest - parse the saved Amayama page; FAIL loudly if that selector breaks
REM    4. parser selftest - parse the saved Amayama page; FAIL loudly if that selector breaks
REM
REM  Nothing here fetches from the web. Phase 1 scraping is still gated on
REM  Jerome's explicit go.
REM
REM  Log: 04_tools\delegation\_logs\ledger_YYYY-MM-DD.log
REM ===========================================================================
setlocal
set SCRIPT_DIR=%~dp0
set ROOT=%SCRIPT_DIR%..\..
set PYTHON=C:\Python314\python.exe
if not exist "%PYTHON%" set PYTHON=python

set LOG_DIR=%SCRIPT_DIR%_logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
for /f %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set DATESTAMP=%%d
set LOG_FILE=%LOG_DIR%\ledger_%DATESTAMP%.log

cd /d "%ROOT%"

echo =================================================== >> "%LOG_FILE%"
echo   ISZE price ledger weekly run - %DATESTAMP% %TIME% >> "%LOG_FILE%"
echo =================================================== >> "%LOG_FILE%"

set FAILED=0

echo. >> "%LOG_FILE%"
echo --- 1/3 refresh tiers (billed value) --- >> "%LOG_FILE%"
"%PYTHON%" "%SCRIPT_DIR%build_refresh_tiers.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 set FAILED=1

echo. >> "%LOG_FILE%"
echo --- 2/3 price-list triggers --- >> "%LOG_FILE%"
"%PYTHON%" "%SCRIPT_DIR%price_list_triggers.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 set FAILED=1

echo. >> "%LOG_FILE%"
echo --- 3/4 price-observation ledger --- >> "%LOG_FILE%"
"%PYTHON%" "%ROOT%\04_tools\price_ledger\build_price_ledger.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 set FAILED=1

echo. >> "%LOG_FILE%"
echo --- 4/4 parser selftest (saved page, no fetch) --- >> "%LOG_FILE%"
"%PYTHON%" "%SCRIPT_DIR%parsers\price_parsers.py" --selftest >> "%LOG_FILE%" 2>&1
if errorlevel 1 set FAILED=1

echo. >> "%LOG_FILE%"
if "%FAILED%"=="1" (
  echo EXIT 2 - at least one step failed. See the lines above. >> "%LOG_FILE%"
  exit /b 2
)
echo EXIT 0 - all four steps completed. >> "%LOG_FILE%"
exit /b 0
