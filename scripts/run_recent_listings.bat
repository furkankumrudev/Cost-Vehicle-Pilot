@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m src.ingestion.recent_listing_scraper %*
