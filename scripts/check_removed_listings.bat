@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m src.maintenance.check_removed_listings %*
