@echo off
set B2_HOST=www.sotecnica.pt
cd /d "%~dp0"
python _sweep_host.py > _host_www.sotecnica.pt.log 2> _host_www.sotecnica.pt.err
