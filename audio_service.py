#!/usr/bin/env python3

import os
import socket
import subprocess
import json
import signal
import sys
import logging
from threading import Thread, Lock
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/raycast-audio-service.err')  # Remove console handler
    ]
)

SOCKET_PATH = '/tmp/raycast_audio_service.sock'
SOX_PATH = '/opt/homebrew/bin/sox'
CONFIG_PATH = '/usr/local/etc/raycast-audio-service.json'

def get_audio_devices():
    """Get detailed info about audio devices"""
    try:
        # Get default input device
        result = subprocess.run([SOX_PATH, '--help'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("Sox help output:")
            logging.info(result.stderr)  # Sox prints help to stderr
            return result.stderr
    except Exception as e:
        logging.error(f"Error getting sox help: {e}")
        return None

class AudioService:
    def __init__(self):
        self.recording_process = None
        self.process_lock = Lock()
        self.config = self.load_config()

        # Log only essential info
        logging.info("Starting audio service")
        logging.info(f"Using sox at: {SOX_PATH}")

        # Test sox with version check
        try:
            result = subprocess.run([SOX_PATH, '--version'], capture_output=True, text=True, check=True)
            if result.returncode == 0:
                logging.info("Sox is working")
            else:
                logging.error("Sox test failed")
                sys.exit(1)
        except Exception as e:
            logging.error(f"Sox is not working: {e}")
            sys.exit(1)

        # Log audio setup
        inputs = self.get_available_inputs()
        logging.info(f"Found audio inputs: {inputs}")

        # Log current input device
        if self.config.get('input_device'):
            logging.info(f"Using configured input: {self.config['input_device']}")
        else:
            logging.info("Using default input device")

            # Try to identify default device
            for input_device in inputs:
                if "Default Input Device: Yes" in input_device:
                    logging.info(f"Default device appears to be: {input_device}")
                    break

    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
        return {}

    def get_available_inputs(self):
        """Get list of available audio input devices"""
        inputs = []
        try:
            result = subprocess.run(['system_profiler', 'SPAudioDataType'],
                                  capture_output=True, text=True)

            current_device = None
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.endswith(':'):
                    current_device = line[:-1]
                elif current_device and "Input Channels:" in line:
                    inputs.append(current_device)

            return inputs
        except Exception as e:
            logging.error(f"Error getting audio inputs: {e}")
            return []

    def get_device_name(self):
        """Get the sox device name for the configured or default input"""
        try:
            # If we have a configured device, use it directly
            if self.config.get('input_device'):
                device = self.config['input_device'].strip()
                logging.info(f"Using configured device: {device}")
                return device

            # Otherwise try to find the default device
            result = subprocess.run(['system_profiler', 'SPAudioDataType'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if "Default Input Device: Yes" in line:
                    # Get the device name from the previous line
                    lines = result.stdout.split('\n')
                    idx = lines.index(line)
                    if idx > 0:
                        device = lines[idx-1].strip()
                        logging.info(f"Using default device: {device}")
                        return device

            logging.error("No default device found")
            return None
        except Exception as e:
            logging.error(f"Error getting device name: {e}")
            return None

    def start_recording(self, output_path):
        with self.process_lock:
            if self.recording_process:
                self.stop_recording()

            try:
                # Test if output directory exists
                output_dir = os.path.dirname(output_path)
                if not os.path.exists(output_dir):
                    logging.error(f"Output directory doesn't exist: {output_dir}")
                    return False

                # Get the device name
                device = self.get_device_name()
                if not device:
                    logging.error("Could not determine input device")
                    return False

                logging.info(f"Using audio device: {device}")

                # Use simple sox command with silence detection like Raycast
                cmd = [
                    SOX_PATH,
                    '-t', 'coreaudio',   # Force CoreAudio driver
                    device,              # Specific input device
                    '-t', 'wav',         # Output format
                    output_path,         # Output file
                    'silence',           # Enable silence detection
                    '1', '0.1', '3%',    # Start recording when sound > 3%
                    '1', '3.0', '3%'     # Stop after 3s of sound < 3%
                ]

                logging.info(f"Starting recording to: {output_path}")
                logging.info(f"Command: {' '.join(cmd)}")
                logging.info(f"Environment PATH: {os.environ.get('PATH', 'Not set')}")
                logging.info(f"Sox version: {subprocess.check_output([SOX_PATH, '--version'], text=True)}")

                # Don't use shell=True to avoid potential issues
                self.recording_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env={
                        **os.environ,
                        'PATH': f"/opt/homebrew/bin:{os.environ.get('PATH', '')}"
                    }
                )

                # Check if process started successfully
                time.sleep(0.1)
                if self.recording_process.poll() is not None:
                    stderr = self.recording_process.stderr.read().decode()
                    logging.error(f"Recording failed: {stderr}")
                    return False

                # Test if file is being created
                time.sleep(0.5)
                if not os.path.exists(output_path):
                    logging.error("Output file not created")
                    return False

                logging.info("Recording started successfully")
                return True

            except Exception as e:
                logging.error(f"Error starting recording: {e}", exc_info=True)
                return False

    def stop_recording(self):
        with self.process_lock:
            if self.recording_process:
                try:
                    self.recording_process.terminate()
                    self.recording_process.wait(timeout=5)
                    logging.info("Recording stopped")

                    # Get process output
                    stdout = self.recording_process.stdout.read().decode()
                    stderr = self.recording_process.stderr.read().decode()
                    if stdout:
                        logging.info(f"Process output: {stdout}")
                    if stderr:
                        logging.error(f"Process errors: {stderr}")

                    return True
                except subprocess.TimeoutExpired:
                    logging.warning("Process didn't stop, killing it")
                    self.recording_process.kill()
                finally:
                    self.recording_process = None
        return False

def handle_client(client_socket, audio_service):
    logging.info("New client connected")
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            command = json.loads(data)
            logging.info(f"Received command: {command}")
            response = {'status': 'error', 'message': 'Invalid command'}

            if command['action'] == 'start':
                success = audio_service.start_recording(command['output_path'])
                response = {'status': 'success' if success else 'error'}
            elif command['action'] == 'stop':
                success = audio_service.stop_recording()
                response = {'status': 'success' if success else 'error'}

            client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            logging.error(f"Error handling client: {e}")
            break

    logging.info("Client disconnected")
    client_socket.close()

def main():
    logging.info("Starting audio service")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Current working directory: {os.getcwd()}")

    if os.path.exists(SOCKET_PATH):
        logging.info(f"Removing existing socket at {SOCKET_PATH}")
        os.unlink(SOCKET_PATH)

    try:
        audio_service = AudioService()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(SOCKET_PATH)
        server.listen(5)
        os.chmod(SOCKET_PATH, 0o666)  # Make socket writable by all users

        logging.info(f"Socket created and listening at {SOCKET_PATH}")

        def cleanup(signum, frame):
            logging.info("\nCleaning up...")
            server.close()
            if os.path.exists(SOCKET_PATH):
                os.unlink(SOCKET_PATH)
            sys.exit(0)

        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)

        logging.info("Audio service started, waiting for connections...")

        while True:
            client, _ = server.accept()
            Thread(target=handle_client, args=(client, audio_service)).start()

    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
