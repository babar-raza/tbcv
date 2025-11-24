# Systemd Service Setup for TBCV Recommendation Generation

This directory contains systemd service and timer files for automatically generating recommendations in the background.

## Installation (Linux)

1. **Copy service files to systemd directory:**
   ```bash
   sudo cp scripts/systemd/tbcv-recommendations.service /etc/systemd/system/
   sudo cp scripts/systemd/tbcv-recommendations.timer /etc/systemd/system/
   ```

2. **Edit the service file to match your installation:**
   ```bash
   sudo nano /etc/systemd/system/tbcv-recommendations.service
   ```

   Update these lines:
   - `User=tbcv` - Change to your user
   - `Group=tbcv` - Change to your group
   - `WorkingDirectory=/opt/tbcv` - Change to your TBCV installation path
   - `ExecStart=/usr/bin/python3 /opt/tbcv/...` - Update paths

3. **Reload systemd and enable the timer:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tbcv-recommendations.timer
   sudo systemctl start tbcv-recommendations.timer
   ```

4. **Check status:**
   ```bash
   # Check timer status
   sudo systemctl status tbcv-recommendations.timer

   # List all timers
   sudo systemctl list-timers

   # Check service logs
   sudo journalctl -u tbcv-recommendations.service -f
   ```

## Configuration

The timer runs every 10 minutes by default. To change the frequency, edit `/etc/systemd/system/tbcv-recommendations.timer`:

```ini
[Timer]
# Run every 5 minutes instead
OnUnitActiveSec=5min
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart tbcv-recommendations.timer
```

## Manual Execution

To manually trigger the service:
```bash
sudo systemctl start tbcv-recommendations.service
```

Or run the script directly:
```bash
python scripts/generate_recommendations_cron.py --batch-size 10 --min-age 5
```

## Troubleshooting

### Check if timer is active:
```bash
systemctl is-active tbcv-recommendations.timer
```

### View recent service runs:
```bash
journalctl -u tbcv-recommendations.service --since "1 hour ago"
```

### Test the script manually:
```bash
# Dry run to see what would be processed
python scripts/generate_recommendations_cron.py --dry-run --log-level DEBUG
```

## Uninstallation

```bash
sudo systemctl stop tbcv-recommendations.timer
sudo systemctl disable tbcv-recommendations.timer
sudo rm /etc/systemd/system/tbcv-recommendations.service
sudo rm /etc/systemd/system/tbcv-recommendations.timer
sudo systemctl daemon-reload
```
