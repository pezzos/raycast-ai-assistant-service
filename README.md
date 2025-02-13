# Raycast AI Assistant Audio Service

A background service that handles audio recording for the Raycast AI Assistant extension.

## Installation

```bash
# Install the service
sudo ./install.sh
```

The install script will:
1. Install sox if not present (via Homebrew or apt-get)
2. Set up the service in `/usr/local/bin/raycast-audio-service`
3. Create and start a LaunchDaemon for automatic startup

## Testing

Run the test suite to verify the installation:
```bash
sudo python3 test_installation.py
```

## Manual Testing

You can test the service directly using a Python client:

```python
import socket
import json

# Connect to the service
client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.connect('/tmp/raycast_audio_service.sock')

# Start recording
start_cmd = json.dumps({'action': 'start', 'output_path': '/tmp/test.wav'})
client.send(start_cmd.encode('utf-8'))
print(client.recv(1024).decode('utf-8'))  # Should print {"status": "success"}

# Wait a bit and say something...
input("Press Enter to stop recording...")

# Stop recording
stop_cmd = json.dumps({'action': 'stop'})
client.send(stop_cmd.encode('utf-8'))
print(client.recv(1024).decode('utf-8'))  # Should print {"status": "success"}

# Close connection
client.close()

# Play back the recording
import subprocess
subprocess.run(['afplay', '/tmp/test.wav'])
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Alexandre "Pezzos" Pezzotta
- GitHub: [https://github.com/pezzos](https://github.com/pezzos)

## Acknowledgments

- Raycast team for their amazing platform
- Contributors who help improve this service
