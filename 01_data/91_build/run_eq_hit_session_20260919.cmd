@echo off
REM Wrapper for Task Scheduler — EQ-Hit session 2026-09-19 23:00
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_eq_hit_session_20260919.ps1"
exit /b %ERRORLEVEL%
