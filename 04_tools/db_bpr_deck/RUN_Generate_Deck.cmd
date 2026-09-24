@echo off
:: ISZE distributor business review - deck generator.
:: Double-click this file, or drag an answers file onto it.
::
:: It asks which distributor, which slide blocks, dark or light, and which period,
:: then writes one PowerPoint file. Nothing existing is changed.

setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

:: find the workspace root (the folder holding paths.yaml and FACTS.md)
set "ROOT=%~dp0..\.."
if "%ISZE_ROOT%"=="" set "ISZE_ROOT=%ROOT%"

echo.
echo ==============================================================================
echo   ISZE distributor business review - deck generator
echo ==============================================================================
echo.

:: prefer the workspace virtual environment when it exists
set "PY=python"
if exist "%~dp0..\workspace\venv\Scripts\python.exe" set "PY=%~dp0..\workspace\venv\Scripts\python.exe"

"%PY%" --version > nul 2>&1
if errorlevel 1 (
  echo   ERROR: Python was not found on this computer.
  echo.
  echo   What to do: install Python from python.org, then run this file again.
  echo   If Python is installed but not on the PATH, run this from a terminal:
  echo       py "%~dp0build_bpr.py"
  echo.
  pause
  exit /b 1
)

:: pass through any arguments; with none it starts the guided questions
"%PY%" "%~dp0build_bpr.py" %*

set "CODE=%ERRORLEVEL%"
echo.
if "%CODE%"=="0" (
  echo   Finished. The deck is in its own folder under 09_meetings.
) else if "%CODE%"=="5" (
  echo   Stopped at your request. Nothing was written.
) else (
  echo   Stopped with code %CODE%. The reason is printed above, and repeated in:
  echo       _logs\last_error.json
  echo   Send that block to GPT, or read TROUBLESHOOTING.md next to this file.
)
echo.
pause
exit /b %CODE%
