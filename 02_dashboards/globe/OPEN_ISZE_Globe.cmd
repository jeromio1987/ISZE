@echo off
REM ===========================================================================
REM  ISZE Globe - launcher
REM
REM  Double-click this file. Do NOT double-click index.html.
REM
REM  The globe needs a local web server. MapLibre GL JS runs its geometry work
REM  in a Web Worker, and browsers refuse to start a Worker from a file://
REM  origin; the page also reads its numbers with fetch(), which file:// blocks
REM  for the same reason. Served over http://localhost both work normally.
REM
REM  This script:
REM    1. starts the server on port 8511 (walking up if that port is taken)
REM    2. waits until the page actually answers over HTTP
REM    3. opens the browser at the port that ended up being used
REM
REM  Close the minimised "python" window when you are finished to stop it.
REM ===========================================================================

setlocal
set "ROOT=%~dp0"
set "PORTFILE=%TEMP%\isze_globe_port.txt"

if exist "%PORTFILE%" del "%PORTFILE%" >nul 2>&1

echo Starting the ISZE Globe server...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%run_globe_server.ps1" -StartPort 8511 -PortFile "%PORTFILE%"

if not exist "%PORTFILE%" (
  echo.
  echo Could not start the local web server. Nothing was opened.
  echo Run this to see the reason:
  echo   powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%run_globe_server.ps1"
  echo.
  pause
  endlocal
  exit /b 1
)

set /p PORT=<"%PORTFILE%"
del "%PORTFILE%" >nul 2>&1

echo.
echo Opening http://localhost:%PORT%/index.html
start "" "http://localhost:%PORT%/index.html"

endlocal
