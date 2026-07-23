@echo off
setlocal
cd /d "%~dp0.."
.venv\Scripts\python.exe -m src.maintenance.save_market_snapshot %*
