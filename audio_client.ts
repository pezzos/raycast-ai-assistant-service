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
   * Connect to the audio service
   * @throws Error if connection fails
   */
  private async connect(): Promise<void> {
    if (this.client) return;

    this.client = new net.Socket();

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Connection timeout'));
      }, 5000);

      this.client!.connect('/tmp/raycast_audio_service.sock', () => {
        clearTimeout(timeout);
        resolve();
      });

      this.client!.on('error', (error) => {
        clearTimeout(timeout);
        reject(new Error(`Failed to connect: ${error.message}`));
      });
    });
  }

  /**
   * Send a command to the audio service and wait for response
   * @param command Command object to send
   * @returns Response from the service
   */
  private async sendCommand(command: object): Promise<any> {
    if (!this.client) {
      throw new Error('Not connected');
    }

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Response timeout'));
      }, 5000);

      // Handle the response
      const handleData = (data: Buffer) => {
        clearTimeout(timeout);
        this.client!.removeListener('data', handleData);

        try {
          const response = JSON.parse(data.toString());
          if (response.status === 'error') {
            reject(new Error(response.message || 'Unknown error'));
          } else {
            resolve(response);
          }
        } catch (e) {
          reject(new Error('Invalid response format'));
        }
      };

      this.client!.on('data', handleData);
      this.client!.write(JSON.stringify(command));
    });
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
      // Clean up connection
      if (this.client) {
        this.client.end();
        this.client = null;
      }
    }
  }
}

// Example usage in a Raycast command:
export default async function command() {
  const recorder = new AudioRecorder();

  try {
    // Start recording when the command is triggered
    await recorder.startRecording();

    // You might want to show some UI here to indicate recording is in progress
    // and provide a way to stop recording (e.g., a detail view with a stop button)

    // For this example, we'll just wait 5 seconds
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Stop recording and get the file path
    const audioFile = await recorder.stopRecording();

    // Now you can use the audio file (e.g., send it to an API)
    console.log('Recording saved to:', audioFile);

  } catch (error) {
    console.error('Recording failed:', error);
    await showHUD('Recording failed');
  }
}
