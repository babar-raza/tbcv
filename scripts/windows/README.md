# Windows Task Scheduler Setup for TBCV Recommendation Generation

This directory contains scripts for scheduling automatic recommendation generation on Windows.

## Installation (Windows)

### Option 1: Using PowerShell Script (Recommended)

1. **Open PowerShell as Administrator**
   - Right-click the Start button
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Navigate to the TBCV directory:**
   ```powershell
   cd C:\path\to\tbcv
   ```

3. **Run the scheduling script:**
   ```powershell
   .\scripts\windows\schedule_recommendations.ps1
   ```

   Or with custom parameters:
   ```powershell
   .\scripts\windows\schedule_recommendations.ps1 `
       -PythonPath "C:\Python311\python.exe" `
       -TbcvPath "C:\path\to\tbcv" `
       -IntervalMinutes 10 `
       -TaskName "TBCV-RecommendationGeneration"
   ```

4. **The script will:**
   - Create a scheduled task that runs every 10 minutes
   - Open Task Scheduler so you can verify the task

### Option 2: Manual Task Scheduler Configuration

1. Open Task Scheduler (taskschd.msc)
2. Click "Create Task" in the Actions panel
3. **General tab:**
   - Name: TBCV-RecommendationGeneration
   - Description: Automatically generates recommendations for TBCV validations
   - Run whether user is logged on or not: No
   - Run with highest privileges: No

4. **Triggers tab:**
   - New trigger
   - Begin the task: On a schedule
   - Settings: Daily, recur every 1 day
   - Advanced settings:
     - Repeat task every: 10 minutes
     - For a duration of: Indefinitely
     - Enabled: Yes

5. **Actions tab:**
   - New action
   - Action: Start a program
   - Program/script: `python` (or full path to python.exe)
   - Add arguments: `scripts\generate_recommendations_cron.py --batch-size 10 --min-age 5`
   - Start in: `C:\path\to\tbcv`

6. **Conditions tab:**
   - Uncheck "Start the task only if the computer is on AC power"
   - Check "Start the task only if the following network connection is available: Any connection"

7. **Settings tab:**
   - Allow task to be run on demand: Yes
   - Run task as soon as possible after scheduled start is missed: Yes
   - If the running task does not end when requested, force it to stop: Yes
   - Stop the task if it runs longer than: 5 minutes

## Managing the Task

### Using PowerShell:

```powershell
# View task details
Get-ScheduledTask -TaskName "TBCV-RecommendationGeneration"

# Run manually
Start-ScheduledTask -TaskName "TBCV-RecommendationGeneration"

# Stop running task
Stop-ScheduledTask -TaskName "TBCV-RecommendationGeneration"

# Disable task
Disable-ScheduledTask -TaskName "TBCV-RecommendationGeneration"

# Enable task
Enable-ScheduledTask -TaskName "TBCV-RecommendationGeneration"

# View task history
Get-ScheduledTaskInfo -TaskName "TBCV-RecommendationGeneration"

# Remove task
Unregister-ScheduledTask -TaskName "TBCV-RecommendationGeneration" -Confirm:$false
```

### Using Task Scheduler GUI:

1. Open Task Scheduler (Win+R, type `taskschd.msc`)
2. Navigate to "Task Scheduler Library"
3. Find "TBCV-RecommendationGeneration"
4. Right-click for options: Run, End, Disable, Delete, Properties

## Configuration

To change the run frequency, edit the task:
1. Open Task Scheduler
2. Right-click the task → Properties
3. Triggers tab → Edit trigger
4. Change "Repeat task every" value

## Manual Execution

To run the script manually:
```powershell
cd C:\path\to\tbcv
python scripts\generate_recommendations_cron.py --batch-size 10 --min-age 5
```

Or with dry-run to test:
```powershell
python scripts\generate_recommendations_cron.py --dry-run --log-level DEBUG
```

## Viewing Logs

Task execution logs are stored in:
- Windows Event Viewer → Windows Logs → Application
- Look for events with source "Task Scheduler"
- Filter by task name: TBCV-RecommendationGeneration

Or view TBCV application logs:
```powershell
Get-Content data\logs\tbcv.log -Tail 50 -Wait
```

## Troubleshooting

### Task not running:
1. Check if Python is in system PATH or use full path to python.exe
2. Verify working directory is set correctly
3. Check Task Scheduler history is enabled:
   - Task Scheduler → Actions → Enable All Tasks History

### Script errors:
1. Run manually to see error messages:
   ```powershell
   python scripts\generate_recommendations_cron.py --log-level DEBUG
   ```

2. Check Python dependencies are installed:
   ```powershell
   pip install -r requirements.txt
   ```

3. Verify database is accessible:
   ```powershell
   python -c "from core.database import db_manager; print('DB OK')"
   ```

## Uninstallation

### Using PowerShell:
```powershell
Unregister-ScheduledTask -TaskName "TBCV-RecommendationGeneration" -Confirm:$false
```

### Using Task Scheduler:
1. Open Task Scheduler
2. Find "TBCV-RecommendationGeneration"
3. Right-click → Delete
