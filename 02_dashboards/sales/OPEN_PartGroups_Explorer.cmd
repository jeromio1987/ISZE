@echo off
REM Always open Part-Groups Sales Explorer via http:// — never double-click the HTML.
setlocal
set PORT=8766
set ROOT=%~dp0
cd /d "%ROOT%"

REM Reuse port if already listening; otherwise start a local server in this folder.
powershell -NoProfile -Command ^
  "$p=%PORT%; $ok=$false; try { $c=New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1',$p); $c.Close(); $ok=$true } catch {}; " ^
  "if(-not $ok){ Start-Process -WindowStyle Minimized python -ArgumentList '-m','http.server',$p -WorkingDirectory '%ROOT%' }; " ^
  "Start-Sleep -Seconds 1; Start-Process ('http://127.0.0.1:{0}/ISZE_PartGroups_Sales_Explorer.html' -f $p)"

echo Opened http://127.0.0.1:%PORT%/ISZE_PartGroups_Sales_Explorer.html
echo Do not double-click the .html for this explorer (multi-MB JSON needs HTTP).
endlocal
