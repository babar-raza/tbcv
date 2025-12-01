@echo off
REM =============================================================================
REM TBCV Playwright UI Tests Runner (Windows)
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================
echo TBCV Playwright UI Tests
echo ============================================
echo.

REM Check if Playwright is installed
python -c "import playwright" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installing Playwright...
    pip install playwright pytest-playwright
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Playwright
        exit /b 1
    )
)

REM Check if browsers are installed
echo [INFO] Checking Playwright browsers...
playwright install chromium
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Playwright browsers
    exit /b 1
)

echo.
echo [INFO] Running UI tests...
echo.

REM Run tests with all arguments passed to this script
pytest tests/ui/ -v --browser chromium %*

set TEST_EXIT=%errorlevel%

echo.
if %TEST_EXIT% equ 0 (
    echo ============================================
    echo [SUCCESS] All UI tests passed!
    echo ============================================
) else (
    echo ============================================
    echo [FAILED] Some UI tests failed
    echo ============================================
)

exit /b %TEST_EXIT%
