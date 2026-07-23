@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m http.server 5173 -d frontend
