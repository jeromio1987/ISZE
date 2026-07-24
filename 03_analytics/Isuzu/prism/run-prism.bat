@echo off
cd /d "%~dp0"
echo PRISM - installing/updating dependencies...
python -m pip install -r requirements.txt -q
if errorlevel 1 (
  echo.
  echo pip failed. Try: py -3 -m pip install -r requirements.txt
  pause
  exit /b 1
)
echo.
echo Starting PRISM at http://localhost:8501
echo.
python -m streamlit run app.py
pause
