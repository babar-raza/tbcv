# PowerShell script to schedule TBCV recommendation generation on Windows
# Run this script as Administrator to create the scheduled task

param(
    [string]$PythonPath = "python",
    [string]$TbcvPath = $PSScriptRoot + "\..\.",
    [int]$IntervalMinutes = 10,
    [string]$TaskName = "TBCV-RecommendationGeneration"
)

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Error "This script must be run as Administrator"
    exit 1
}

Write-Host "Creating scheduled task: $TaskName"
Write-Host "  Python: $PythonPath"
Write-Host "  TBCV Path: $TbcvPath"
Write-Host "  Interval: Every $IntervalMinutes minutes"
Write-Host ""

# Create the action
$scriptPath = Join-Path $TbcvPath "scripts\generate_recommendations_cron.py"
$action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "$scriptPath --batch-size 10 --min-age 5" `
    -WorkingDirectory $TbcvPath

# Create the trigger (repeat every N minutes, indefinitely)
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

# Create the settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

# Create the principal (run as current user)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# Register the task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Automatically generates recommendations for TBCV validations" `
        -Force

    Write-Host "SUCCESS: Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To manage the task:"
    Write-Host "  View:    Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Start:   Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Stop:    Stop-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Disable: Disable-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Remove:  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
    Write-Host ""
    Write-Host "Opening Task Scheduler..."
    Start-Process taskschd.msc

} catch {
    Write-Error "Failed to create scheduled task: $_"
    exit 1
}
