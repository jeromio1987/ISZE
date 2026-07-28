@echo off
REM Weekly bridge: summarise local Cursor sessions into ISZE\05_memory\briefs\
setlocal
set SCRIPT_DIR=%~dp0
set LOG=%SCRIPT_DIR%cursor_week_digest.log

if exist "C:\Program Files\nodejs\node.exe" (
  set NODE_EXE=C:\Program Files\nodejs\node.exe
) else (
  set NODE_EXE=node
)

echo [%date% %time%] start >> "%LOG%"
"%NODE_EXE%" "%SCRIPT_DIR%cursor_week_digest.mjs" --days 7 >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"

exit /b %ERRORLEVEL%
