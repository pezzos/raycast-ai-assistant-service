#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Service paths
SERVICE_DIR="/usr/local/bin/raycast-audio-service"
CONFIG_DIR="/usr/local/etc"
CONFIG_FILE="$CONFIG_DIR/raycast-audio-service.json"
PLIST_FILE="/Library/LaunchDaemons/com.raycast.audio-service.plist"
SOCKET_PATH="/tmp/raycast_audio_service.sock"

# Stop and remove the service
echo "Stopping service..."
launchctl unload "$PLIST_FILE" 2>/dev/null || true

# Remove files
echo "Removing service files..."
rm -rf "$SERVICE_DIR"
rm -f "$CONFIG_FILE"
rm -f "$PLIST_FILE"
rm -f "/tmp/raycast-audio-service.err"
rm -f "/tmp/raycast-audio-service.log"
rm -f "$SOCKET_PATH"

echo "Uninstallation complete"
