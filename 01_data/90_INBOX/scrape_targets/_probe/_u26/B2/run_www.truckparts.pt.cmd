@echo off
set B2_HOST=www.truckparts.pt
cd /d "%~dp0"
python _sweep_host.py > _host_www.truckparts.pt.log 2> _host_www.truckparts.pt.err
