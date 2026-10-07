@echo off
set B2_HOST=www.ascendum.pt
cd /d "%~dp0"
python _sweep_host.py > _host_www.ascendum.pt.log 2> _host_www.ascendum.pt.err
