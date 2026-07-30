@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
  echo Sanal ortam bulunamadi. Once proje kokunde .venv olusturun.
  exit /b 1
)

.venv\Scripts\python.exe -m src.ml.predict_price_model %*
