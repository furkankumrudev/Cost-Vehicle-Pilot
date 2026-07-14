@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m src.ingestion.city_transmission_segment_scraper %*
