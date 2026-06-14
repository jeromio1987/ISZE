@echo off

REM Autodoc DE/EU + Mister Auto + Oscaro (optional shops)

cd /d "%~dp0"

set PYTHON=python -u



echo === EU scraper run ===

echo PN list: autodoc_results.csv if v3 xlsx missing

echo Autodoc DE/EU use Playwright (like UK). First run may take 10-20 min.

echo.



echo [1/4] Autodoc DE ...

%PYTHON% autodoc_tld_scraper.py --tld de --top 50 --delay 2 4 --retry-errors

echo DE exit=%ERRORLEVEL%

echo.



echo [2/4] Autodoc EU ...

%PYTHON% autodoc_tld_scraper.py --tld eu --top 40 --delay 2 4

echo EU exit=%ERRORLEVEL%

echo.



echo [3/4] Mister Auto FR ...

%PYTHON% mister_auto_scraper.py --top 40 --delay 2 4

echo Mister Auto exit=%ERRORLEVEL%

echo.



echo [4/4] Oscaro FR ...

%PYTHON% oscaro_scraper.py --top 40 --delay 2 4

echo Oscaro exit=%ERRORLEVEL%

echo.



cd /d C:\Users\jerom\.cursor\projects\empty-window\iam_threat_engine

%PYTHON% scripts\check_eu_scrapers.py

echo.

pause

