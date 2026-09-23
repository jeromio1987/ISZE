@echo off
REM EQ-Hit session pack opener — 2026-09-19
setlocal
set "INBOX=%~dp0"
set "ISZE=%INBOX%..\..\"
for %%I in ("%ISZE%") do set "ISZE=%%~fI"

set "BRIEF=%INBOX%_EQ_HIT_SESSION_20260919_BRIEF.md"
set "XLSX=%ISZE%\01_data\01_Pricing\EQ_HIT_SESSION_20260919.xlsx"
set "CSV=%INBOX%_EQ_HIT_SESSION_20260919_queue.csv"
set "EQURL=https://isuzu.snaponepc.com/epc/#/"

if exist "%BRIEF%" start "" "%BRIEF%"
if exist "%XLSX%" (
  start "" "%XLSX%"
) else if exist "%CSV%" (
  start "" "%CSV%"
)
start "" "%EQURL%"

echo Opened brief + worklist + EQ URL.
echo Do NOT apply AIM from this session.
endlocal
