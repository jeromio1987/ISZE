@echo off
title ISZE — Autodoc Competitive Price Scraper
color 0A
cd /d "%~dp0"

echo ============================================================
echo   ISZE Autodoc Competitive Price Scraper
echo   Fetches aftermarket prices for top 300 PNs from Autodoc UK
echo ============================================================
echo.
echo BEFORE YOU START:
echo   1. Make sure ISZE_Parts_Intelligence_v3.xlsx is in this folder
echo      (or the script will find it automatically in your Isuzu/data folder)
echo   2. Keep this window open — it will take 30-60 minutes for 300 PNs
echo   3. You can stop and restart anytime — it resumes where it left off
echo.
pause

:: ─── Check Python ─────────────────────────────────────────────────────────────
echo.
echo [1/4] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Python not found.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
python --version
echo OK.

:: ─── Install packages ─────────────────────────────────────────────────────────
echo.
echo [2/4] Installing required packages...
python -m pip install playwright pandas openpyxl --quiet --upgrade
if %ERRORLEVEL% NEQ 0 (
    echo ERROR installing packages. Check your internet connection.
    pause
    exit /b 1
)
echo OK.

:: ─── Install Playwright browser ───────────────────────────────────────────────
echo.
echo [3/4] Installing Playwright Chromium browser (first time only, ~150MB)...
python -m playwright install chromium
if %ERRORLEVEL% NEQ 0 (
    echo ERROR installing Chromium. Try running as Administrator.
    pause
    exit /b 1
)
echo OK.

:: ─── Run scraper ──────────────────────────────────────────────────────────────
echo.
echo [4/4] Starting scraper...
echo.
echo Options used:
echo   - Top 300 PNs by CY2025 revenue
echo   - Random delay 3-7 seconds between requests
echo   - Visible browser window (safer — less bot detection)
echo.
echo Results saved to: %~dp0autodoc_results.csv
echo (File is updated after every PN — safe to stop and restart)
echo.

python autodoc_scraper.py --top 300 --delay 3 7

echo.
echo ============================================================
echo   Scraping complete!
echo   Open autodoc_results.csv in Excel to review results.
echo ============================================================
echo.
pause
