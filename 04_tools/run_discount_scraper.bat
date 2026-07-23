@echo off
cd /d "%~dp0discount-scanner"
python -m pip install -r requirements.txt -q
python -m playwright install chromium 2>nul
python discount_scraper.py
exit /b %ERRORLEVEL%
