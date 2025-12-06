#!/bin/bash

# Smart Heating Production Debug Script
# Quick access to production HA logs and debugging

PROD_HOST="root@192.168.2.2"
PROD_PORT="22222"

echo "==================================="
echo "Smart Heating Production Debug"
echo "==================================="
echo ""

# Function to show menu
show_menu() {
    echo "Select an option:"
    echo "1) View Smart Heating discovery logs"
    echo "2) Follow live logs (filtered)"
    echo "3) View all recent Smart Heating logs"
    echo "4) View entity list (climate entities)"
    echo "5) View entity list (sensor entities)"
    echo "6) Check integration status"
    echo "7) SSH into production"
    echo "8) Exit"
    echo ""
    read -p "Choice: " choice
    echo ""
}

# Main loop
while true; do
    show_menu
    
    case $choice in
        1)
            echo "=== Device Discovery Logs ==="
            ssh -p $PROD_PORT $PROD_HOST "ha core logs | grep -i 'SMART HEATING.*discovery\|DISCOVERED:' | tail -50"
            echo ""
            ;;
        2)
            echo "=== Following Live Logs (Ctrl+C to stop) ==="
            ssh -p $PROD_PORT $PROD_HOST "ha core logs --follow" | grep --line-buffered -i "smart_heating\|DISCOVERED"
            ;;
        3)
            echo "=== Recent Smart Heating Logs ==="
            ssh -p $PROD_PORT $PROD_HOST "ha core logs | grep -i smart_heating | tail -100"
            echo ""
            ;;
        4)
            echo "=== Climate Entities ==="
            ssh -p $PROD_PORT $PROD_HOST "ha core info | grep climate"
            echo ""
            echo "To list all climate entities, run in SSH:"
            echo "  ha entity list | grep climate"
            echo ""
            ;;
        5)
            echo "=== Temperature Sensor Entities ==="
            ssh -p $PROD_PORT $PROD_HOST "ha entity list | grep -i 'sensor.*temp'"
            echo ""
            ;;
        6)
            echo "=== Integration Status ==="
            ssh -p $PROD_PORT $PROD_HOST "ha core info"
            echo ""
            ;;
        7)
            echo "=== Opening SSH Session ==="
            echo "Run these commands to debug:"
            echo "  ha core logs | grep DISCOVERED"
            echo "  ha core logs --follow"
            echo "  ha entity list | grep climate"
            echo ""
            ssh -p $PROD_PORT $PROD_HOST
            ;;
        8)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            echo ""
            ;;
    esac
    
    read -p "Press Enter to continue..."
    echo ""
done
