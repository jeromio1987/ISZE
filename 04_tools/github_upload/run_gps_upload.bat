@echo off
echo ============================================================
echo  GPS Data Upload to GitHub
echo ============================================================
echo.

set SCRIPT=%~dp0upload_gps_data.py

python "%SCRIPT%" && goto done
py "%SCRIPT%" && goto done
"%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" "%SCRIPT%" && goto done
"%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%SCRIPT%" && goto done
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%SCRIPT%" && goto done

echo ERROR: Python not found. Please run: python upload_gps_data.py

:done
echo.
echo Press any key to close...
pause > nul
