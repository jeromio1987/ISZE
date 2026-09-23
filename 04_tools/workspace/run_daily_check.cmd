@echo off
:: ISZE daily run - Task Scheduler entry point.
::   1. writes the brief (read-only aggregation)
::   2. fires a Windows toast
::   3. runs the agent, which acts only on the allowlist and refuses the rest
:: No mail. No cloud writes. No scraper. See isze_daily_agent.py for the guard.
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0..\.."
if "%ISZE_ROOT%"=="" set "ISZE_ROOT=%CD%"

echo ============================================================ >> "%~dp0daily_check_task.log"
echo Run started: %DATE% %TIME% >> "%~dp0daily_check_task.log"
echo ============================================================ >> "%~dp0daily_check_task.log"

echo [1/3] daily brief ...
python "%~dp0isze_daily_check.py" --toast --quiet >> "%~dp0daily_check_task.log" 2>&1

echo [2/3] daily agent ...
python "%~dp0isze_daily_agent.py" --run --toast >> "%~dp0daily_check_task.log" 2>&1

echo [3/3] done: %DATE% %TIME% >> "%~dp0daily_check_task.log"
exit /b 0
