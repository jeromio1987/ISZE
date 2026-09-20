@echo off
REM ISZE delegator watch - AIM change detector. Registered task: every 20 minutes.
REM
REM Detect-only by default. Pass -RefreshDerived to also rebuild the artifacts this
REM workstream owns; the protected pricing deliverables are never written either way.
REM
REM Logging: this wrapper captures the raw console output (including any crash before the
REM script's own logging starts). The script writes its own structured log separately, to
REM delegator_watch.log. The two must stay in different files - pointing both at one file
REM makes them fight over the handle and the run fails.
REM
REM The script always exits 0 on a clean run, whether or not a change was detected.
REM Only a crash (exit 1) propagates, so the task shows as failed only when it truly is.
setlocal
set SCRIPT_DIR=%~dp0
set LOG=%SCRIPT_DIR%delegator_watch_task.log

echo [%date% %time%] start >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%isze_delegator_watch.ps1" >> "%LOG%" 2>&1
set RC=%ERRORLEVEL%
echo [%date% %time%] exit=%RC% >> "%LOG%"
exit /b %RC%
