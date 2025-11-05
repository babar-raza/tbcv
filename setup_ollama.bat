@echo off
REM Ollama Setup Helper for Windows
REM This script helps diagnose and fix Ollama connection issues

echo ================================================================================
echo OLLAMA SETUP HELPER FOR TBCV
echo ================================================================================
echo.

REM Check if Ollama is in PATH
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Ollama is not installed or not in PATH
    echo.
    echo Please install Ollama:
    echo   1. Download from: https://ollama.ai/download
    echo   2. Run the installer
    echo   3. Restart this script
    echo.
    pause
    exit /b 1
)

echo [OK] Ollama is installed
echo.

REM Check if Ollama service is running
echo Checking if Ollama service is running...
curl -s http://127.0.0.1:11434/api/tags >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Ollama service is not running
    echo.
    echo Starting Ollama service...
    start "Ollama Server" ollama serve
    timeout /t 3 /nobreak >nul
    echo.
)

echo [OK] Ollama service is running
echo.

REM Check if mistral model is installed
echo Checking if mistral model is installed...
ollama list | findstr /i "mistral" >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Mistral model not found
    echo.
    echo Downloading mistral model (this may take a few minutes)
    ollama pull mistral
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to download mistral model
        pause
        exit /b 1
    )
    echo.
)

echo [OK] Mistral model is installed
echo.

REM Set environment variables
echo Setting environment variables...
set OLLAMA_BASE_URL=http://127.0.0.1:11434
set OLLAMA_MODEL=mistral
set OLLAMA_ENABLED=true
set OLLAMA_TIMEOUT=30

echo [OK] Environment variables set:
echo   OLLAMA_BASE_URL=%OLLAMA_BASE_URL%
echo   OLLAMA_MODEL=%OLLAMA_MODEL%
echo   OLLAMA_ENABLED=%OLLAMA_ENABLED%
echo   OLLAMA_TIMEOUT=%OLLAMA_TIMEOUT%
echo.

REM Run diagnostic test
echo Running connection diagnostic test...
echo.
python test_ollama_connection.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Diagnostic test failed
    echo.
    echo Troubleshooting steps:
    echo   1. Check if Ollama is running: tasklist ^| findstr ollama
    echo   2. Try manually: ollama serve
    echo   3. Test connection: curl http://127.0.0.1:11434/api/tags
    echo   4. Check firewall settings
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo [SUCCESS] Ollama is configured and ready for TBCV validation!
echo ================================================================================
echo.
echo You can now run TBCV validation with LLM support:
echo   python -m cli.main validate-file your-file.md
echo.
echo NOTE: Keep this window open to keep Ollama service running,
echo       or run 'ollama serve' in a separate window.
echo.
pause
