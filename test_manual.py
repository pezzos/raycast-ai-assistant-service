#!/usr/bin/env python3

import socket
import json
import os
import subprocess
import time

def check_audio_file(file_path):
    """Check if the audio file is valid using sox"""
    try:
        # Get audio file info
        result = subprocess.run(['sox', '--i', file_path],
                              capture_output=True,
                              text=True)
        if result.returncode != 0:
            print(f"Error: Invalid audio file: {result.stderr}")
            return False

        print("\nAudio file information:")
        print(result.stdout)

        # Check audio duration
        result = subprocess.run(['soxi', '-D', file_path],
                              capture_output=True,
                              text=True)
        duration = float(result.stdout)
        print(f"Audio duration: {duration:.2f} seconds")

        if duration < 0.1:
            print("Error: Audio file is too short (no audio recorded)")
            # Get more info about what went wrong
            result = subprocess.run(['sox', '--i', '-V', file_path],
                                  capture_output=True,
                                  text=True)
            print("\nDetailed file info:")
            print(result.stdout)
            print(result.stderr)
            return False

        return True
    except Exception as e:
        print(f"Error checking audio file: {e}")
        return False

def play_audio(file_path):
    """Play audio file using sox"""
    try:
        print("\nPlaying back recording using sox...")
        # Use same parameters as recording
        result = subprocess.run([
            'play',
            '-V0',               # Minimal verbosity
            '-t', 'wav',        # Force WAV format
            '-r', '24000',      # Same sample rate as recording
            '-b', '16',         # Same bit depth
            '-c', '1',          # Same channel count
            '--buffer', '128',   # Small buffer for low latency
            '-q',               # Quiet mode
            file_path,          # Input file
            '-d'                # Default output device
        ])

        if result.returncode != 0:
            print(f"Error playing audio")
            return False
        return True
    except KeyboardInterrupt:
        print("\nPlayback stopped by user")
        return True
    except Exception as e:
        print(f"Error playing audio: {e}")
        return False

def main():
    print("Connecting to audio service...")
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect('/tmp/raycast_audio_service.sock')

    print("\nStarting recording...")
    start_cmd = json.dumps({'action': 'start', 'output_path': '/tmp/test.wav'})
    client.send(start_cmd.encode('utf-8'))
    response = client.recv(1024).decode('utf-8')
    print("Response:", response)

    if '"status": "error"' in response:
        print("Error starting recording. Check /tmp/raycast-audio-service.err for details")
        return

    print("\n🎤 Say something... Recording will stop after 3s of silence")
    print("(Recording in progress...)")

    # Wait for the recording process to finish by itself (silence detection)
    time.sleep(1)  # Give time for the process to start
    while True:
        stop_cmd = json.dumps({'action': 'stop'})
        client.send(stop_cmd.encode('utf-8'))
        response = client.recv(1024).decode('utf-8')

        if '"status": "success"' in response:
            print("\nRecording stopped (silence detected)")
            break

        time.sleep(0.5)  # Check every 500ms

    client.close()

    print("\nTest if recording is saved to /tmp/test.wav")
    if not os.path.exists('/tmp/test.wav'):
        print("Error: Recording file not found")
        return
    else:
        print("Recording saved to /tmp/test.wav")

    print("\nTest if the file is not empty")
    if os.path.getsize('/tmp/test.wav') == 0:
        print("Error: Recording file is empty")
        return
    else:
        print("Recording file is not empty: %d bytes" % os.path.getsize('/tmp/test.wav'))

    print("\nTest if the file timestamp is recent (less than 10 seconds old)")
    if os.path.getmtime('/tmp/test.wav') < time.time() - 10:
        print("Error: Recording file is older than 10 seconds")
        return
    else:
        print("Recording file is recent: %s" % time.ctime(os.path.getmtime('/tmp/test.wav')))

    # Verify audio file is valid and contains audio
    if check_audio_file('/tmp/test.wav'):
        play_audio('/tmp/test.wav')
    else:
        print("\nSkipping playback due to invalid audio file")
        print("\nCheck the service logs for more details:")
        print("cat /tmp/raycast-audio-service.err")

if __name__ == '__main__':
    main()
