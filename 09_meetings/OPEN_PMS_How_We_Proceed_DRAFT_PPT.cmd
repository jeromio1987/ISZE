@echo off
set "PPT=C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"
set "FILE=%~dp0ISZE_PMS_How_We_Proceed_DRAFT.pptx"
if not exist "%PPT%" (
  echo PowerPoint not found at:
  echo %PPT%
  pause
  exit /b 1
)
start "" "%PPT%" "%FILE%"
