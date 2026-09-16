@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_prism_internal.ps1"
if errorlevel 1 pause
