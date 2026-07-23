@echo off
setlocal
cd /d "%~dp0"
set SCRIPT=%~dp0upload_ids_data.py

echo.
echo ============================================================
echo  IDS 2026 -- Upload to GitHub (IDS/ folder)
echo ============================================================
echo.

python "%SCRIPT%"       && goto done
py "%SCRIPT%"           && goto done
"%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" "%SCRIPT%"   && goto done
"%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%SCRIPT%"   && goto done
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%SCRIPT%"   && goto done
"%LOCALAPPDATA%\Programs\Python\Python311\python.exe" "%SCRIPT%"   && goto done

echo.
echo ERROR: Python not found. Install Python and the 'requests' library:
echo   pip install requests
echo.
goto end

:done
echo.
echo Upload complete. Check GitHub: https://github.com/jeromio1987/isuzu-docs/tree/main/IDS
echo.

:end
pause
endlocal
