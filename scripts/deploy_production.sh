#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HA_CONTAINER="homeassistant-test"
INTEGRATION_DIR="smart_heating"
FRONTEND_DIR="$INTEGRATION_DIR/frontend"

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Smart Heating - Sync Script${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""


echo -e "${YELLOW}[1/3]${NC} Building frontend..."
if [[ -d "$FRONTEND_DIR" ]]; then
    cd "$FRONTEND_DIR"

    # Check if node_modules exists
    if [[ ! -d "node_modules" ]]; then
        echo "  Installing dependencies..."
        npm install --silent
    fi

    # Build frontend
    echo "  Building React app..."
    npm run build --silent

    if [[ ! -d "dist" ]]; then
        echo -e "${RED}✗${NC} Frontend build failed - dist directory not found"
        exit 1
    fi

    cd - > /dev/null
    echo -e "${GREEN}✓${NC} Frontend built successfully"
else
    echo -e "${RED}✗${NC} Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi
echo ""

# Need to stop Home Assistant for changes to take effect
echo -e "${YELLOW}[4/4]${NC} Stopping Home Assistant..."
ssh root@192.168.2.2 -p 22222 "ha core stop"

# echo -e "${YELLOW}[2/3]${NC} Backing up current installation..."
# BACKUP_DIR="/Users/ralf/backup/smart_heating_backup_$(date +%Y%m%d_%H%M%S)"
# cp -R /Volumes/config/custom_components/smart_heating "$BACKUP_DIR"
# echo -e "${GREEN}✓${NC} Backup created: $BACKUP_DIR"
# echo ""

echo -e "${YELLOW}[3/3]${NC} Syncing files to production..."

# Check if destination is accessible
if [[ ! -d "/Volumes/config/custom_components" ]]; then
    echo -e "${RED}✗${NC} Destination not accessible: /Volumes/config/custom_components"
    echo "  Please ensure the network mount is connected"
    exit 1
fi

# Use rsync for much faster incremental sync (no compression/decompression overhead)
# --ignore-errors: continue even if some files fail (but still report exit code)
# Exit code 23 = partial transfer (some files failed, but most succeeded)
# Temporarily disable exit-on-error for rsync since we handle the exit code ourselves
set +e
rsync -av --delete --ignore-errors \
    --exclude='frontend/node_modules' \
    --exclude='frontend/src' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='.DS_Store' \
    --exclude='coverage' \
    --exclude='coverage_html' \
    --exclude='venv' \
    --exclude='frontend/test-results/' \
    --exclude='frontend/tests/' \
    "$INTEGRATION_DIR/" /Volumes/config/custom_components/smart_heating/

RSYNC_EXIT=$?
set -e
if [[ $RSYNC_EXIT -eq 0 ]]; then
    echo -e "${GREEN}✓${NC} All files synced successfully"
elif [[ $RSYNC_EXIT -eq 23 ]]; then
    echo -e "${YELLOW}⚠${NC} Files synced with warnings (some files may have failed)"
    echo "  This is usually safe - core files were transferred"
else
    echo -e "${RED}✗${NC} Sync failed with exit code: $RSYNC_EXIT"
    exit 1
fi
echo ""

# Need to start Home Assistant for changes to take effect
echo -e "${YELLOW}[4/4]${NC} Starting Home Assistant..."
ssh root@192.168.2.2 -p 22222 "ha core start"

echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Sync Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
