@echo off
:: ---------------------------------------------------------------------------
:: Data gap ping - read-only launcher. Nothing is written, nothing is scheduled.
::
::   Double-click        -> full list of open gaps, grouped by action owner
::   -WhatIOwe           -> only the gaps waiting on Jerome
::   -Quiet              -> scheduled-task mode (silent when nothing is owed)
::   -Json               -> JSON for a dashboard or another tool
::
:: Example: RUN_Data_Gap_Ping.cmd -WhatIOwe
:: ---------------------------------------------------------------------------
setlocal
set "SCRIPT=%~dp0Get-DataGapPing.ps1"
if not exist "%SCRIPT%" (
    echo ERROR: Get-DataGapPing.ps1 is not next to this launcher.
    echo Expected: %SCRIPT%
    echo.
    pause
    exit /b 1
)

if "%~1"=="" goto interactive

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" %*
exit /b %ERRORLEVEL%

:interactive
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
set "RC=%ERRORLEVEL%"
echo.
pause
exit /b %RC%
