@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m src.ingestion.district_segment_scraper %*
