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

echo -e "${YELLOW}[2/3]${NC} Packing integration files..."

# Create tarball excluding unnecessary files
cd "$INTEGRATION_DIR"
tar czf /tmp/smart_heating_sync.tar.gz \
    --exclude='frontend/node_modules' \
    --exclude='frontend/src' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='coverage' \
    --exclude='venv' \
    --exclude='._*' \
    .

cd - > /dev/null

# Extract in production container
echo -e "${YELLOW}[2/3]${NC} Unpacking integration files..."
tar xzf /tmp/smart_heating_sync.tar.gz -C /Volumes/config/custom_components/smart_heating

# Need to restart Home Assistant for changes to take effect
echo -e "${YELLOW}[2/3]${NC} Restarting Home Assistant..."
ssh root@192.168.2.2 -p 22222 "ha core restart"

# Clean up
rm /tmp/smart_heating_sync.tar.gz



echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Sync Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
