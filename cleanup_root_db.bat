@echo off
REM Cleanup script to remove old database from root
REM Run this after closing all Python processes and applications

echo Checking for tbcv.db at root...
if exist tbcv.db (
    echo Found tbcv.db at root. Attempting to delete...
    del /F tbcv.db
    if exist tbcv.db (
        echo ERROR: Could not delete tbcv.db - file is locked
        echo Please close all Python processes and applications, then run this script again
        echo.
        echo You can also manually delete the file after closing processes.
        pause
        exit /b 1
    ) else (
        echo SUCCESS: tbcv.db deleted from root
        echo Database is now only at data/tbcv.db (correct location)
        git add -u tbcv.db
        echo Staged deletion in git
    )
) else (
    echo No tbcv.db found at root - already cleaned up
)

echo.
echo Done!
pause
