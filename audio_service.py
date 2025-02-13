#!/usr/bin/env python3

import os
import socket
import subprocess
import json
import signal
import sys
from threading import Thread, Lock

SOCKET_PATH = '/tmp/raycast_audio_service.sock'

class AudioService:
    def __init__(self):
        self.recording_process = None
        self.process_lock = Lock()

    def start_recording(self, output_path):
        with self.process_lock:
            if self.recording_process:
                self.stop_recording()

            cmd = [
                'sox',
                '-d',  # Use default audio input
                '-c', '1',  # Mono
                '-r', '44100',  # Sample rate
                output_path,
                'silence', '1', '0.1', '3%', '1', '3.0', '3%'  # Stop after 3 seconds of silence
            ]

            self.recording_process = subprocess.Popen(cmd)
            return True

    def stop_recording(self):
        with self.process_lock:
            if self.recording_process:
                self.recording_process.terminate()
                self.recording_process.wait()
                self.recording_process = None
                return True
        return False

def handle_client(client_socket, audio_service):
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            command = json.loads(data)
            response = {'status': 'error', 'message': 'Invalid command'}

            if command['action'] == 'start':
                success = audio_service.start_recording(command['output_path'])
                response = {'status': 'success' if success else 'error'}
            elif command['action'] == 'stop':
                success = audio_service.stop_recording()
                response = {'status': 'success' if success else 'error'}

            client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"Error handling client: {e}")
            break

    client_socket.close()

def main():
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    audio_service = AudioService()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(5)

    def cleanup(signum, frame):
        print("\nCleaning up...")
        server.close()
        os.unlink(SOCKET_PATH)
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("Audio service started, waiting for connections...")

    while True:
        client, _ = server.accept()
        Thread(target=handle_client, args=(client, audio_service)).start()

if __name__ == '__main__':
    main()
