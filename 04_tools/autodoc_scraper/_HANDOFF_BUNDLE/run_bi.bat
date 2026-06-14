@echo off
cd /d "%~dp0"
echo Starting ISZE PMS Intelligence (not the Autodoc scraper)...
echo Browser will open at http://localhost:8501
echo Press Ctrl+C to stop.
echo.
python -m streamlit run bi_shell.py
pause
