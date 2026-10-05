@echo off
setlocal
set "F=%~dp0Universe_Opportunity_Page.html"
set "CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe"
if exist "%CHROME%" (
  start "" "%CHROME%" --new-window "%F%"
) else (
  start "" "%F%"
)
