@echo off
REM Remove empty reorg stubs. Run from anywhere; targets ISZE root.
set "ROOT=%~dp0..\.."
rmdir /s /q "%ROOT%\Dashboards" 2>nul
rmdir /s /q "%ROOT%\Projects" 2>nul
if exist "%ROOT%\Dashboards" (echo FAIL Dashboards) else (echo OK Dashboards)
if exist "%ROOT%\Projects" (echo FAIL Projects) else (echo OK Projects)
