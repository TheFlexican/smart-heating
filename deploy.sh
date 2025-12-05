#!/bin/bash
# Deploy script voor Zone Heater Manager naar HAOS

# Configuratie
HA_HOST="homeassistant.local"  # Pas aan naar jouw HA IP/hostname
SOURCE_DIR="$(pwd)/smart_heating"
DEST_DIR="/Volumes/config/custom_components/smart_heating"

echo "🚀 Deploying Smart Heating to Home Assistant OS..."

# Build frontend first
echo "🔨 Building frontend..."
cd smart_heating/frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi
cd ../..
echo "✅ Frontend built successfully!"

# Check of Samba share gemount is
if [ ! -d "/Volumes/config" ]; then
    echo "📁 Mounting Samba share..."
    open "smb://${HA_HOST}"
    sleep 3
fi

# Check nogmaals
if [ ! -d "/Volumes/config" ]; then
    echo "❌ Error: Could not mount Samba share"
    echo "   Make sure Samba add-on is installed and running"
    exit 1
fi

# Maak custom_components directory aan als die niet bestaat
mkdir -p /Volumes/config/custom_components

# Kopieer bestanden
echo "📦 Copying files..."
mkdir -p /Volumes/config/custom_components
cp -r "${SOURCE_DIR}" "${DEST_DIR}"

if [ $? -eq 0 ]; then
    echo "✅ Files copied successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Go to Settings → System → Restart → Quick Reload"
    echo "2. Go to Settings → Devices & Services → Add Integration"
    echo "3. Search for 'Smart Heating'"
    echo ""
    echo "Or restart HA completely for clean start"
else
    echo "❌ Error copying files"
    exit 1
fi
