@echo off
REM ISZE overnight orchestrator - the delegator cycle. Registered task: every 20 minutes.
REM
REM Inside the window (22:00-08:00 local) it checks every workstream's evidence and runs one
REM audit angle from a rotating queue. Outside the window it fingerprints and exits.
REM
REM READ-ONLY on all deliverables: it never rebuilds, publishes, syncs, mails, bumps a version
REM or moves a price. Corrective work is queued for Jerome to approve.
REM
REM Logging: this wrapper captures raw console output including any crash before the script's
REM own logging starts. The script writes its structured log separately. Pointing both at one
REM file makes them fight over the handle and the run fails.
setlocal
set SCRIPT_DIR=%~dp0
set LOG=%SCRIPT_DIR%overnight_orchestrator_task.log

echo [%date% %time%] start >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%isze_overnight_orchestrator.ps1" >> "%LOG%" 2>&1
set RC=%ERRORLEVEL%
echo [%date% %time%] exit=%RC% >> "%LOG%"
exit /b %RC%
