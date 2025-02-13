#!/usr/bin/env python3

import os
import socket
import subprocess
import json
import signal
import sys
import logging
from threading import Thread, Lock

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/raycast-audio-service.err'),
        logging.StreamHandler()
    ]
)

SOCKET_PATH = '/tmp/raycast_audio_service.sock'
SOX_PATH = '/opt/homebrew/bin/sox'  # Full path to sox

class AudioService:
    def __init__(self):
        self.recording_process = None
        self.process_lock = Lock()

        logging.info("Initializing AudioService")

        # Verify sox is installed
        try:
            result = subprocess.run([SOX_PATH, '--version'], capture_output=True, text=True, check=True)
            logging.info(f"Sox version: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.error(f"Sox is not installed or not accessible at {SOX_PATH}: {e}")
            sys.exit(1)

    def start_recording(self, output_path):
        with self.process_lock:
            if self.recording_process:
                self.stop_recording()

            try:
                cmd = [
                    SOX_PATH,
                    '-d',  # Use default audio input
                    '-c', '1',  # Mono
                    '-r', '44100',  # Sample rate
                    output_path,
                    'silence', '1', '0.1', '3%', '1', '3.0', '3%'  # Stop after 3 seconds of silence
                ]
                logging.info(f"Starting recording with command: {' '.join(cmd)}")

                self.recording_process = subprocess.Popen(cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                return True
            except Exception as e:
                logging.error(f"Error starting recording: {e}")
                return False

    def stop_recording(self):
        with self.process_lock:
            if self.recording_process:
                try:
                    self.recording_process.terminate()
                    self.recording_process.wait(timeout=5)
                    logging.info("Recording stopped successfully")
                except subprocess.TimeoutExpired:
                    logging.warning("Recording process did not terminate, killing it")
                    self.recording_process.kill()
                finally:
                    self.recording_process = None
                    return True
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
