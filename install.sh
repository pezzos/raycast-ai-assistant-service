#!/bin/bash

# set -x  # Enable debug mode

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

SOCKET_PATH="/tmp/raycast_audio_service.sock"
SOX_PATH="/opt/homebrew/bin/sox"
CONFIG_DIR="/usr/local/etc"
CONFIG_FILE="$CONFIG_DIR/raycast-audio-service.json"

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

# List available audio inputs
echo -e "\nAvailable audio input devices:"
system_profiler -json SPAudioDataType | jq -r '.SPAudioDataType[0]._items[] | select(.coreaudio_input_source) | ._name'

# Find default input device
default_device=$(system_profiler -json SPAudioDataType | jq -r '.SPAudioDataType[0]._items[] | select(.coreaudio_input_source) | select(.coreaudio_default_audio_input_device) | ._name')
if [ -n "$default_device" ]; then
    echo -e "\nCurrent default input device: $default_device"
else
    echo -e "\nWarning: Could not detect default input device"
fi

# Ask if user wants to configure a specific input device
read -p "Do you want to use the default input device? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    # Create config directory if it doesn't exist
    mkdir -p "$CONFIG_DIR"

    # Get list of input devices (only actual devices, no technical details)
    devices=$(system_profiler -json SPAudioDataType | jq -r '.SPAudioDataType[0]._items[] | select(.coreaudio_input_source) | ._name' | sort -u)

    echo -e "\nAvailable devices:"
    i=1
    while IFS= read -r device; do
        echo "$i) $device"
        ((i++))
    done <<< "$devices"

    read -p "Enter the number of the device to use (or press Enter for MacBook internal mic): " choice

    if [ -n "$choice" ]; then
        selected_device=$(echo "$devices" | sed -n "${choice}p")
        if [ -n "$selected_device" ]; then
            echo "{\"input_device\": \"$selected_device\"}" > "$CONFIG_FILE"
            echo "Configured to use: $selected_device"
        else
            echo "Invalid choice, using default microphone"
            rm -f "$CONFIG_FILE"
        fi
    else
        echo "Using default MacBook internal microphone"
        rm -f "$CONFIG_FILE"
    fi
fi

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
