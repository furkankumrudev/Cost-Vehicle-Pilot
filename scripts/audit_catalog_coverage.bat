@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m src.maintenance.audit_catalog_coverage %*
