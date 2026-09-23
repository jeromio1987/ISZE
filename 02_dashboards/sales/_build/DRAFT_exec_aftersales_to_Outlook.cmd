@echo off
setlocal
cd /d "%~dp0"
python "%~dp0draft_exec_aftersales_outlook.py"
if errorlevel 1 pause
endlocal
