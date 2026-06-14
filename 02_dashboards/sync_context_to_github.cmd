@echo off
REM Run context sync via PowerShell (safe from cmd.exe — do not run .ps1 directly in cmd)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_context_to_github.ps1" %*
exit /b %ERRORLEVEL%
