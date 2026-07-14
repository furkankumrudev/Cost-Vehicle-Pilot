@echo off
cd /d "%~dp0.."
echo Pulling today's newest listings...
".venv\Scripts\python.exe" -m src.ingestion.recent_listing_scraper --days 0 --max-pages 0 --page-size 50 --delay-min 2 --delay-max 5 --manual-wait-seconds 120 --max-old-pages 2 --max-stale-pages 5 --max-repeated-pages 1 --stop-on-access --checkpoint-path data\runtime\daily_recent_checkpoint.json %*
if errorlevel 1 exit /b %errorlevel%
echo Rebuilding cleaned analysis table...
".venv\Scripts\python.exe" -m src.maintenance.clean_vehicle_data
