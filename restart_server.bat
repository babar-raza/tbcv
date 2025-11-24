@echo off
echo Stopping old server...
taskkill /F /PID 274724 2>nul
timeout /t 2 /nobreak >nul
echo Starting new server with fixed CORS...
cd /d "c:\Users\prora\OneDrive\Documents\GitHub\tbcv"
python -m uvicorn api.server:app --host 127.0.0.1 --port 8080 --reload
