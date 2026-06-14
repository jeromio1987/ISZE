@echo off
:: ISZE GPS Dashboard Launcher
:: Run this file to start the dashboard in your browser

echo ==========================================
echo  ISZE GPS ^& Spend per Unit Dashboard
echo  Isuzu Motors Europe
echo ==========================================
echo.

:: Check if Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

:: Install dependencies if needed
echo Installing/checking dependencies...
pip install streamlit pandas plotly openpyxl --quiet

echo.
echo Starting dashboard... (browser will open automatically)
echo Press Ctrl+C to stop the dashboard.
echo.

:: Change to the dashboard directory
cd /d "%~dp0"

:: Start Streamlit
python -m streamlit run app.py --server.headless false --browser.gatherUsageStats false

pause
