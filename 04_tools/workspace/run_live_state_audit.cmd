@echo off
REM Weekly ISZE live-state audit: register vs Task Scheduler vs FACTS.
REM
REM The script exits 2 when it finds HIGH-severity drift. That is a useful signal
REM interactively, but as a scheduled task it would make this job show up in its
REM own report as "last exited with code 2" every week. So a completed audit is
REM reported as success here and only a crash (exit 1) propagates.
setlocal
set SCRIPT_DIR=%~dp0
set LOG=%SCRIPT_DIR%live_state_audit.log

echo [%date% %time%] start >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%isze_live_state_audit.ps1" >> "%LOG%" 2>&1
set RC=%ERRORLEVEL%
echo [%date% %time%] exit=%RC% >> "%LOG%"

if "%RC%"=="2" exit /b 0
exit /b %RC%
