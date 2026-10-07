@echo off
set B2_HOST=www.turbopecas.pt
cd /d "%~dp0"
python _sweep_host.py > _host_www.turbopecas.pt.log 2> _host_www.turbopecas.pt.err
