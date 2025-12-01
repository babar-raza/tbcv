@echo off
echo ========================================
echo Starting TBCV Server with Anaconda LLM
echo ========================================
echo.

REM Change to project directory
cd /d "c:\Users\prora\OneDrive\Documents\GitHub\tbcv"

echo Checking for existing server on port 8585...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8585 ^| findstr LISTENING') do (
    echo Killing existing process %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo Starting server on http://127.0.0.1:8585
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start server with full Python path from anaconda llm environment
C:\Users\prora\anaconda3\envs\llm\python.exe -m uvicorn api.server:app --host 127.0.0.1 --port 8585 --reload
