@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m src.maintenance.clean_vehicle_data %*
