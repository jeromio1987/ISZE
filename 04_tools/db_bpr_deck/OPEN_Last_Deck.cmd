@echo off
:: Opens the most recently built distributor deck.
:: Finds the newest .pptx under 09_meetings\*_BPR_* and opens it in PowerPoint.

setlocal
cd /d "%~dp0"

set "NEWEST="
for /f "delims=" %%F in ('dir /b /s /o-d "%~dp0..\..\09_meetings\*_BPR_*\*.pptx" 2^>nul') do (
  if not defined NEWEST set "NEWEST=%%F"
)

if not defined NEWEST (
  echo.
  echo   No deck has been built yet.
  echo   Run RUN_Generate_Deck.cmd first.
  echo.
  pause
  exit /b 1
)

echo.
echo   Opening: %NEWEST%
echo.
start "" "%NEWEST%"
exit /b 0
