@echo off
cd /d "%~dp0.."
set "DRY_RUN=0"
for %%A in (%*) do if /I "%%~A"=="--dry-run" set "DRY_RUN=1"
echo Scraping sparse brand-series groups...
".venv\Scripts\python.exe" -m src.ingestion.series_gap_scraper %*
if errorlevel 1 exit /b %errorlevel%
if "%DRY_RUN%"=="1" exit /b 0
echo Rebuilding cleaned analysis table...
".venv\Scripts\python.exe" -m src.maintenance.clean_vehicle_data
