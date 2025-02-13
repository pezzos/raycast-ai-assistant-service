#!/bin/bash

set -x  # Enable debug mode

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

SOCKET_PATH="/tmp/raycast_audio_service.sock"
SOX_PATH="/opt/homebrew/bin/sox"

# Find Python path
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo "Python3 not found"
    exit 1
fi
echo "Using Python: $PYTHON_PATH"
$PYTHON_PATH --version

# Install sox if not present
if [ ! -x "$SOX_PATH" ]; then
    echo "Installing sox..."
    if command -v brew &> /dev/null; then
        brew install sox
    elif command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y sox
    else
        echo "Please install sox manually"
        exit 1
    fi
fi

if [ ! -x "$SOX_PATH" ]; then
    echo "Sox not found at $SOX_PATH"
    exit 1
fi
$SOX_PATH --version

# Create service directory
SERVICE_DIR="/usr/local/bin/raycast-audio-service"
mkdir -p "$SERVICE_DIR"
echo "Created service directory: $SERVICE_DIR"

# Copy files
cp audio_service.py "$SERVICE_DIR/"
chmod +x "$SERVICE_DIR/audio_service.py"
echo "Copied service file to: $SERVICE_DIR/audio_service.py"

# Create plist with correct Python path
cat > /Library/LaunchDaemons/com.raycast.audio-service.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.raycast.audio-service</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$SERVICE_DIR/audio_service.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/raycast-audio-service.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/raycast-audio-service.log</string>
    <key>WorkingDirectory</key>
    <string>$SERVICE_DIR</string>
</dict>
</plist>
EOF
echo "Created LaunchDaemon plist"

# Ensure clean service state
echo "Stopping existing service..."
launchctl unload /Library/LaunchDaemons/com.raycast.audio-service.plist 2>/dev/null || true
rm -f /tmp/raycast_audio_service.sock 2>/dev/null || true
rm -f /tmp/raycast-audio-service.err 2>/dev/null || true
rm -f /tmp/raycast-audio-service.log 2>/dev/null || true

echo "Starting service..."
launchctl load /Library/LaunchDaemons/com.raycast.audio-service.plist

# Wait for socket to be created
echo "Waiting for service to start..."
for i in {1..10}; do
    echo "Attempt $i..."
    if [ -S "$SOCKET_PATH" ]; then
        echo "Socket created successfully!"
        ls -l "$SOCKET_PATH"
        echo "Service logs:"
        tail -n 20 /tmp/raycast-audio-service.err
        exit 0
    fi
    sleep 1
done

echo "Service failed to start. Logs:"
echo "=== Error Log ==="
cat /tmp/raycast-audio-service.err
echo "=== Output Log ==="
cat /tmp/raycast-audio-service.log
echo "=== LaunchDaemon Status ==="
launchctl list | grep raycast-audio-service
exit 1
