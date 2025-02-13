#!/usr/bin/env python3

import os
import socket
import json
import time
import subprocess
import unittest

class TestAudioServiceInstallation(unittest.TestCase):
    SOCKET_PATH = '/tmp/raycast_audio_service.sock'
    SERVICE_DIR = '/usr/local/bin/raycast-audio-service'
    LAUNCHD_PLIST = '/Library/LaunchDaemons/com.raycast.audio-service.plist'

    def test_01_files_installed(self):
        """Test if all required files are installed in the correct locations"""
        self.assertTrue(os.path.exists(self.SERVICE_DIR), "Service directory not found")
        self.assertTrue(os.path.exists(os.path.join(self.SERVICE_DIR, 'audio_service.py')), "audio_service.py not found")
        self.assertTrue(os.path.exists(self.LAUNCHD_PLIST), "LaunchDaemon plist not found")

    def test_02_service_running(self):
        """Test if the service is running"""
        result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
        self.assertIn('com.raycast.audio-service', result.stdout, "Service not running")

    def test_03_socket_available(self):
        """Test if the Unix socket is available"""
        self.assertTrue(os.path.exists(self.SOCKET_PATH), "Socket file not found")

        # Test socket connection
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(self.SOCKET_PATH)
        client.close()

    def test_04_basic_recording(self):
        """Test basic recording functionality"""
        test_output = '/tmp/test_recording.wav'
        if os.path.exists(test_output):
            os.remove(test_output)

        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(self.SOCKET_PATH)

        # Start recording
        start_cmd = json.dumps({'action': 'start', 'output_path': test_output})
        client.send(start_cmd.encode('utf-8'))
        response = json.loads(client.recv(1024).decode('utf-8'))
        self.assertEqual(response['status'], 'success', "Failed to start recording")

        # Wait a bit and stop recording
        time.sleep(1)
        stop_cmd = json.dumps({'action': 'stop'})
        client.send(stop_cmd.encode('utf-8'))
        response = json.loads(client.recv(1024).decode('utf-8'))
        self.assertEqual(response['status'], 'success', "Failed to stop recording")

        client.close()

        # Check if file was created
        self.assertTrue(os.path.exists(test_output), "Recording file not created")
        self.assertTrue(os.path.getsize(test_output) > 0, "Recording file is empty")

        # Cleanup
        os.remove(test_output)

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("Please run tests as root")
        exit(1)
    unittest.main(verbosity=2)
