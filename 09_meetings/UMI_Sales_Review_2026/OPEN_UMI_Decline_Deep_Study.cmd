@echo off
cd /d "%~dp0"
set "HTML=%~dp0ISZE_UMI_Decline_Deep_Study.html"
if not exist "%HTML%" (
  echo Missing %HTML%
  pause
  exit /b 1
)
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" "%HTML%"
  exit /b 0
)
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" "%HTML%"
  exit /b 0
)
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
  start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" "%HTML%"
  exit /b 0
)
start "" "%HTML%"
