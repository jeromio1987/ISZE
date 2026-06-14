@echo off
title ISZE — Full Aftermarket Price Scrape
color 0A
cd /d "%~dp0"
set PYTHON=python -u

echo ============================================================
echo   ISZE Aftermarket Price Scraper — Full Run (updated 2026-05-30)
echo.
echo   [1] Autodoc UK      --force re-scrape (300 PNs, GBP)
echo   [2] Autodoc FR      --force re-scrape (200 PNs, EUR) [REPLACES EU]
echo   [3] Mekonomen SE    --force re-scrape (200 PNs, SEK)
echo   [4] Mister Auto FR  --force re-scrape (200 PNs, EUR) [FIXED: JS render]
echo   [5] KS International retry errors     (300 PNs, GBP)
echo.
echo   SKIPPED: Autodoc DE (URL broken — 404), Oscaro (Cloudflare hard block)
echo   NOTE: Autodoc EU replaced by FR — no more country-selector wall
echo ============================================================
echo.
pause

echo.
echo [1/5] Autodoc UK (top 300) — force refresh ...
%PYTHON% autodoc_scraper.py --top 300 --delay 3 7 --force
echo UK exit=%ERRORLEVEL%
echo.

echo [2/5] Autodoc FR (top 200) — fresh EUR prices ...
%PYTHON% autodoc_tld_scraper.py --tld fr --top 200 --delay 2 5 --force
echo FR exit=%ERRORLEVEL%
echo.

echo [3/5] Mekonomen SE (top 200) — force refresh ...
%PYTHON% mekonomen_scraper.py --top 200 --delay 2 4 --force
echo Mekonomen exit=%ERRORLEVEL%
echo.

echo [4/5] Mister Auto FR (top 200) — JS render fix applied ...
%PYTHON% mister_auto_scraper.py --top 200 --delay 3 6 --retry-errors
echo MisterAuto exit=%ERRORLEVEL%
echo.

echo [5/5] KS International — retry errors + new PNs ...
%PYTHON% ks_scraper.py --top 300 --delay 1 3
echo KS exit=%ERRORLEVEL%
echo.

echo ============================================================
echo   Done. Run build_chain_pricing.bat to rebuild Excel analysis.
echo   Then refresh the Competitiveness dashboard (F5).
echo ============================================================
pause
