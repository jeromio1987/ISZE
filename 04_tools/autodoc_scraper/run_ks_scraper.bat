@echo off
title ISZE — KS International Price Scraper
color 0B
cd /d "%~dp0"

echo ============================================================
echo   ISZE KS International Price Scraper
echo   Scrapes aftermarket + genuine OEM prices for top 300 PNs
echo   Site: ks-international.com (UK's largest Isuzu parts stockist)
echo ============================================================
echo.
echo No browser required — much faster than Autodoc scraper.
echo Expected time: ~10-15 minutes for 300 PNs.
echo.
pause

echo.
echo [1/3] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found.
    pause & exit /b 1
)
python --version & echo OK.

echo.
echo [2/3] Installing required packages...
python -m pip install requests beautifulsoup4 pandas openpyxl lxml --quiet --upgrade
if %ERRORLEVEL% NEQ 0 (
    echo ERROR installing packages.
    pause & exit /b 1
)
echo OK.

echo.
echo [3/3] Starting scraper...
echo Results saved to: %~dp0ks_results.csv
echo (Updated after every PN — safe to stop and restart)
echo.

python ks_scraper.py --top 300 --delay 1 3

echo.
echo ============================================================
echo   Done! Open ks_results.csv in Excel to review.
echo   Then run build_chain_pricing.bat to build full analysis.
echo ============================================================
echo.
pause
