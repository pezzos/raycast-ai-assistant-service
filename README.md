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

You can test the service directly using the provided Python script:
```bash
./test_manual.py
```

This will:
1. Start recording
2. Wait for you to press Enter
3. Stop recording
4. Play back the recording

## Raycast Extension Integration

### 1. Install Dependencies

In your Raycast extension project:
```bash
npm install @types/node --save-dev
```

### 2. Add the Audio Client

Create a new file `src/utils/audio_client.ts`:

```typescript
/// <reference types="node" />

import * as net from 'net';
import { showHUD, environment } from "@raycast/api";

/**
 * Class to handle audio recording through the Unix socket service
 * Make sure the service is installed by running: sudo ./install.sh
 */
export class AudioRecorder {
  private client: net.Socket | null = null;
  private outputPath: string;

  constructor(outputPath = '/tmp/raycast_recording.wav') {
    this.outputPath = outputPath;
  }

  /**
   * Start recording audio
   * @throws Error if recording fails to start
   */
  async startRecording(): Promise<void> {
    try {
      await this.connect();
      await this.sendCommand({
        action: 'start',
        output_path: this.outputPath
      });
      await showHUD('Recording started...');
    } catch (error) {
      await showHUD('Failed to start recording');
      throw error;
    }
  }

  /**
   * Stop recording audio
   * @returns Path to the recorded audio file
   * @throws Error if recording fails to stop
   */
  async stopRecording(): Promise<string> {
    try {
      await this.sendCommand({
        action: 'stop'
      });
      await showHUD('Recording stopped');
      return this.outputPath;
    } catch (error) {
      await showHUD('Failed to stop recording');
      throw error;
    } finally {
      if (this.client) {
        this.client.end();
        this.client = null;
      }
    }
  }

  // ... see full code in audio_client.ts
}
```

### 3. Use in Your Commands

Example usage in a Raycast command:

```typescript
import { AudioRecorder } from "../utils/audio_client";

export default async function Command() {
  const recorder = new AudioRecorder();

  try {
    // When user clicks "Start Recording"
    await recorder.startRecording();

    // When user clicks "Stop Recording"
    const audioFile = await recorder.stopRecording();
    // Use audioFile path to send to your API

  } catch (error) {
    console.error('Recording failed:', error);
  }
}
```

The `AudioRecorder` class handles:
- Unix socket connection management
- Start/stop recording commands
- Error handling and timeouts
- Resource cleanup
- Raycast HUD notifications

By default, audio is saved to `/tmp/raycast_recording.wav`, but you can specify a custom path in the constructor.

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
