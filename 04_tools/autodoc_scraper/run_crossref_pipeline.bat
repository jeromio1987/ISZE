@echo off
cd /d "%~dp0"

echo ============================================================
echo   ISZE Cross-Reference Pipeline
echo ============================================================
echo.

echo [1/3] Extracting OE cross-references from Autodoc UK...
python autodoc_crossref_scraper.py
if errorlevel 1 (
    echo ERROR in step 1 - autodoc_crossref_scraper.py failed.
    pause
    exit /b 1
)
echo.

echo [2/3] Searching cross-refs on EU/DE/Mekonomen...
python crossref_search_runner.py
if errorlevel 1 (
    echo ERROR in step 2 - crossref_search_runner.py failed.
    pause
    exit /b 1
)
echo.

echo [3/3] Vehicle-based search for unmatched PNs...
python vehicle_search_mapper.py
if errorlevel 1 (
    echo ERROR in step 3 - vehicle_search_mapper.py failed.
    pause
    exit /b 1
)
echo.

echo ============================================================
echo   Done. Refresh dashboard (F5).
echo ============================================================
pause
