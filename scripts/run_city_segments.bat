@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m src.ingestion.city_segment_scraper %*
