@echo off
setlocal
set SCRIPT_DIR=%~dp0
set LOG_DIR=%SCRIPT_DIR%_logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
for /f %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set DATESTAMP=%%d
set LOG_FILE=%LOG_DIR%\refresh_%DATESTAMP%.log
cd /d "%SCRIPT_DIR%"
C:\Python314\python.exe refresh_and_check_drift.py >> "%LOG_FILE%" 2>&1
