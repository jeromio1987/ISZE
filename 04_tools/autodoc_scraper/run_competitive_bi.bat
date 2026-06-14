@echo off
cd /d "%~dp0"
echo Starting ISZE Competitive BI...
echo Browser will open at http://localhost:8501
echo Press Ctrl+C to stop.
echo.
python -m streamlit run competitive_bi.py
pause
