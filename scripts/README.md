Test scripts utilities

- `./scripts/setup_test.sh` - build and configure the test HA env

Usage example:

```bash
# Make scripts executable (if you create any custom test scripts)
# chmod +x scripts/<my-script>.sh

# Use the standard setup_test.sh to provision the test HA environment and configure devices via the UI
./scripts/setup_test.sh
```

Notes:
- The add script attempts to modify the HA core config entry store. This is a test-only approach and will restart the Home Assistant test container to apply changes.
- Be careful using this on live systems. Use only in test container 'homeassistant-test'.
