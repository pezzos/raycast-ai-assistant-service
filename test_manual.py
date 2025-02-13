#!/usr/bin/env python3

import socket
import json
import subprocess

def main():
    print("Connecting to audio service...")
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect('/tmp/raycast_audio_service.sock')

    print("\nStarting recording...")
    start_cmd = json.dumps({'action': 'start', 'output_path': '/tmp/test.wav'})
    client.send(start_cmd.encode('utf-8'))
    print("Response:", client.recv(1024).decode('utf-8'))

    input("\n🎤 Say something... Press Enter when done.")

    print("\nStopping recording...")
    stop_cmd = json.dumps({'action': 'stop'})
    client.send(stop_cmd.encode('utf-8'))
    print("Response:", client.recv(1024).decode('utf-8'))

    client.close()

    print("\nPlaying back recording...")
    subprocess.run(['afplay', '/tmp/test.wav'])

if __name__ == '__main__':
    main()
