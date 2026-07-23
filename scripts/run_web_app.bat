@echo off
setlocal
cd /d "%~dp0..\web"
if not exist "node_modules" (
  echo Once web klasorunde npm install calistirin.
  exit /b 1
)
npm.cmd run dev
