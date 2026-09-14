@echo off
setlocal
cd /d "%~dp0"
set "HTML=%~dp0ISZE_Exec_Aftersales_Paper.html"
if not exist "%HTML%" (
  echo HTML is not next to this launcher:
  echo %HTML%
  pause
  exit /b 1
)
start "" "%HTML%"
if errorlevel 1 (
  echo Browser did not start. Opening the folder instead.
  explorer.exe "%~dp0"
  pause
)
endlocal
