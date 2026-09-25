@echo off
REM ===========================================================================
REM  ISZE - weekly price ledger + triggers  (delegation card C2)
REM  Written 2026-09-24. Runs AFTER the Monday 07:00 ISZE_PMS_IAM_Refresh so it
REM  reads that run's fresh scraper output, not last week's.
REM
REM  Order matters:
REM    1. refresh tiers   - rank parts by billed value (trailing 12 months)
REM    2. price triggers  - diff the price list vs its snapshot, queue checks
REM    3. scraped prices  - parse the saved web pages into candidate rows (no fetch)
REM    4. ledger          - rebuild the one price-observation table
REM    5. verbatim check  - every loaded price and part number must be printed on its
REM                         source page; FAIL loudly rather than trust a parser
REM    6. parser selftest - parse each saved page; FAIL loudly if a selector breaks
REM
REM  Nothing here fetches from the web. Step 3 reads pages already on disk; fetching
REM  them is a separate, deliberate action that goes through check_scrape_consent.py.
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
echo --- 1/6 refresh tiers (billed value) --- >> "%LOG_FILE%"
"%PYTHON%" "%SCRIPT_DIR%build_refresh_tiers.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 set FAILED=1

echo. >> "%LOG_FILE%"
echo --- 2/6 price-list triggers --- >> "%LOG_FILE%"
"%PYTHON%" "%SCRIPT_DIR%price_list_triggers.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 set FAILED=1

echo. >> "%LOG_FILE%"
echo --- 3/6 scraped prices from the saved pages (no fetch) --- >> "%LOG_FILE%"
"%PYTHON%" "%ROOT%\04_tools\price_ledger\build_scraped_observations.py" --emit >> "%LOG_FILE%" 2>&1
if errorlevel 1 set FAILED=1

echo. >> "%LOG_FILE%"
echo --- 4/6 price-observation ledger --- >> "%LOG_FILE%"
"%PYTHON%" "%ROOT%\04_tools\price_ledger\build_price_ledger.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 set FAILED=1

echo. >> "%LOG_FILE%"
echo --- 5/6 verbatim check: prices must be printed on their source pages --- >> "%LOG_FILE%"
"%PYTHON%" "%ROOT%\04_tools\price_ledger\verify_scraped_observations.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 set FAILED=1

echo. >> "%LOG_FILE%"
echo --- 6/6 parser selftest (saved pages, no fetch) --- >> "%LOG_FILE%"
"%PYTHON%" "%SCRIPT_DIR%parsers\price_parsers.py" --selftest >> "%LOG_FILE%" 2>&1
if errorlevel 1 set FAILED=1

echo. >> "%LOG_FILE%"
if "%FAILED%"=="1" (
  echo EXIT 2 - at least one step failed. See the lines above. >> "%LOG_FILE%"
  exit /b 2
)
echo EXIT 0 - all six steps completed. >> "%LOG_FILE%"
exit /b 0
