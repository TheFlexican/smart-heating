# Troubleshooting Guide

This guide helps resolve common issues with Smart Heating.

## Common Issues

### Integration Not Detected
- Ensure you restarted Home Assistant after installation
- Check for errors in Home Assistant logs

### Devices Not Appearing
- Confirm devices are assigned to Home Assistant areas
- Check device compatibility (must be climate entity)

### Schedules Not Working
- Verify schedule times and days
- Ensure area is enabled and devices are assigned

### Boost/Vacation Not Activating
- Check if area is in manual override or disabled
- Review logs for errors

### No Real-Time Updates
- Ensure WebSocket connection is active (browser dev tools)
- Refresh browser and clear cache

### Backup/Restore Fails
- Validate JSON before import
- Check for version compatibility

## Logs & Support
- View logs in Home Assistant (Supervisor → System → Logs)
- Use per-area logs in the Smart Heating UI
- For unresolved issues, open a GitHub issue with logs and details

---
For more help, see README.md and GitHub Issues.
