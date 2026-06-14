@echo off
title ISZE — Build Chain Pricing Intelligence
color 0B
cd /d "%~dp0"

echo ============================================================
echo   ISZE Chain Pricing Intelligence Builder
echo   Converts Autodoc results into competitive analysis Excel
echo ============================================================
echo.

:: Check autodoc_results.csv exists
if not exist "autodoc_results.csv" (
    echo ERROR: autodoc_results.csv not found.
    echo Run run_autodoc_scraper.bat first to collect Autodoc data.
    pause
    exit /b 1
)

echo Found autodoc_results.csv - proceeding...
echo.
echo Parameters:
echo   DB gross margin:   40%%
echo   DLR gross margin:  27.5%%
echo   GBP/EUR FX rate:   1.18  (adjust with --fx flag if needed)
echo   Trade discount:    35%% off Autodoc retail
echo.

python enrich_chain_pricing.py --db-gm 0.40 --dlr-gm 0.275 --fx 1.18 --trade-disc 0.35

echo.
pause
