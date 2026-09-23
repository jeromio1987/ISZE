@echo off
:: ============================================================
::  Install the ISZE daily brief task (needs Administrator).
::  Double-click this file, then approve the Windows prompt.
::  To remove it again, run:  schtasks /delete /tn "ISZE_Daily_Brief" /f
:: ============================================================

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo Registering ISZE_Daily_Brief ...
schtasks /create /tn "ISZE_Daily_Brief" /xml "%~dp0ISZE_Daily_BriefTask.xml" /f
if %errorlevel% neq 0 (
    echo.
    echo FAILED to register. The task was not created.
    pause
    exit /b 1
)

echo.
echo Registered. Current state:
schtasks /query /tn "ISZE_Daily_Brief" /v /fo LIST | findstr /i "TaskName Next Status Schedule Start"
echo.
echo Runs daily at 07:15 and again ~2 minutes after you log on.
echo It writes 05_memory\briefs\daily_brief_YYYY-MM-DD.md and saves an
echo Outlook DRAFT to you. It never sends mail.
echo.
pause
