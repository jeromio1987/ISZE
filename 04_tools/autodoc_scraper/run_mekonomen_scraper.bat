@echo off
title ISZE — Mekonomen Nordic Price Scraper
cd /d "%~dp0"
echo Mekonomen.se — Nordic market (SWE/NOR/FIN/DNK). France not in scope.
echo.
python -m pip install requests beautifulsoup4 pandas openpyxl lxml --quiet
python mekonomen_scraper.py --top 300 --delay 1 3
echo Results: %~dp0mekonomen_results.csv
pause
