@echo off
cd /d "%~dp0"
echo Starting ISZE IAM Lookup Lab (not PMS — use _HANDOFF_BUNDLE\run_bi.bat for PMS)...
echo Browser will open at http://localhost:8501
echo Press Ctrl+C in this window to stop the server.
echo.
python -m streamlit run autodoc_dashboard.py
pause
