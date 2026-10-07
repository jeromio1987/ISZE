@echo off
set B2_HOST=www.isuzu.pt
cd /d "%~dp0"
python _sweep_host.py > _host_www.isuzu.pt.log 2> _host_www.isuzu.pt.err
