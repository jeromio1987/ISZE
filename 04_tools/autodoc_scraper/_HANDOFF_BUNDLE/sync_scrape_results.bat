@echo off
REM Optional: copy scraper CSVs from parent only IF you chose to re-scrape. Not required for PMS BI.
set SRC=%~dp0..
set DST=%~dp0
echo Syncing scrape results from %SRC% to %DST%
for %%F in (autodoc_results.csv ks_results.csv mekonomen_results.csv) do (
  if exist "%SRC%\%%F" copy /Y "%SRC%\%%F" "%DST%\%%F"
)
echo Done. Restart Streamlit (run_bi.bat) to reload.
