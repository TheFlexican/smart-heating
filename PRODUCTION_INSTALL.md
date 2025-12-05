# Production Installation Guide

## Method 1: Download from GitHub Releases (Recommended)

1. **Download the latest release:**
   - Go to https://github.com/TheFlexican/smart_heating/releases
   - Download `smart_heating.zip` from the latest release

2. **Extract to Home Assistant:**
   ```bash
   # SSH into your production Home Assistant server
   ssh your-ha-server
   
   # Navigate to config directory
   cd /config
   
   # Create custom_components directory if it doesn't exist
   mkdir -p custom_components
   
   # Extract the zip file
   unzip smart_heating.zip -d .
   
   # Verify the structure
   ls -la custom_components/smart_heating/
   ```

3. **Restart Home Assistant:**
   - Configuration → Settings → System → Restart

## Method 2: Using Samba Share (Your deploy.sh)

Your `deploy.sh` script already handles this! Just update it to build the frontend first:

```bash
#!/bin/bash

# Build frontend
cd smart_heating/frontend
npm run build
cd ../..

# Deploy to production via Samba
# (rest of your existing deploy.sh script)
```

## Method 3: Git Clone + Build (Manual)

```bash
# SSH into production HA
ssh your-ha-server

# Clone repository (if not already cloned)
cd /config/custom_components
git clone https://github.com/TheFlexican/smart_heating.git

# Install Node.js if needed (for building frontend)
# This varies by HA installation type

# Build frontend
cd smart_heating/smart_heating/frontend
npm install
npm run build
cd ../../..

# Move to correct location
mv smart_heating /config/custom_components/

# Restart Home Assistant
```

## Verification

After installation, verify:

1. **Integration loads:**
   - Check Configuration → Settings → Integrations
   - Look for "Smart Heating" integration

2. **Frontend accessible:**
   - Navigate to http://your-ha-ip:8123/smart_heating/
   - Check browser console for errors

3. **Check logs:**
   ```bash
   tail -f /config/home-assistant.log | grep smart_heating
   ```

## Updating

### Using GitHub Releases:
1. Download new `smart_heating.zip`
2. Extract and overwrite existing files
3. Restart Home Assistant

### Using Git:
```bash
cd /config/custom_components/smart_heating
git pull
cd smart_heating/frontend
npm run build
cd /config
# Restart Home Assistant
```

## Troubleshooting

**Frontend not loading:**
- Clear browser cache (Cmd+Shift+R / Ctrl+Shift+F5)
- Check `/config/custom_components/smart_heating/frontend/dist/` exists
- Verify `index.html` is in `frontend/` directory

**Integration not found:**
- Check `/config/custom_components/smart_heating/manifest.json` exists
- Verify file permissions (should be readable by HA user)
- Check HA logs for errors: `grep -i "smart_heating" /config/home-assistant.log`

**API errors:**
- Ensure all Python dependencies are available (Home Assistant 2024.1+)
- Check coordinator is initialized: look for "Smart Heating initialized" in logs
