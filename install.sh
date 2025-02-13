#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Create service directory
SERVICE_DIR="/usr/local/bin/raycast-audio-service"
mkdir -p "$SERVICE_DIR"

# Copy files
cp audio_service.py "$SERVICE_DIR/"
chmod +x "$SERVICE_DIR/audio_service.py"

# Install launchd service
cp com.raycast.audio-service.plist /Library/LaunchDaemons/
launchctl load /Library/LaunchDaemons/com.raycast.audio-service.plist

echo "Service installed successfully!"
