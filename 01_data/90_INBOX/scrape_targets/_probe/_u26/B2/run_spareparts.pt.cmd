@echo off
set B2_HOST=spareparts.pt
cd /d "%~dp0"
python _sweep_host.py > _host_spareparts.pt.log 2> _host_spareparts.pt.err
