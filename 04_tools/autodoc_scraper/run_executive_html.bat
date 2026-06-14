@echo off
cd /d "%~dp0"
echo Building ISZE HTML: PMS Intelligence + IAM Lookup Lab + combined...
python build_executive_dashboard.py --variant all
if %ERRORLEVEL% NEQ 0 (
  echo Build failed.
  pause
  exit /b 1
)
echo.
echo Opening dashboard in default browser...
start "" "_html_previews\isze_executive_pms.html"
pause
