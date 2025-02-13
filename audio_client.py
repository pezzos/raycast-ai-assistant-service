import socket
import json

SOCKET_PATH = '/tmp/raycast_audio_service.sock'

class AudioClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.sock.connect(SOCKET_PATH)
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def start_recording(self, output_path):
        command = {
            'action': 'start',
            'output_path': output_path
        }
        return self._send_command(command)

    def stop_recording(self):
        command = {
            'action': 'stop'
        }
        return self._send_command(command)

    def _send_command(self, command):
        try:
            self.sock.send(json.dumps(command).encode('utf-8'))
            response = json.loads(self.sock.recv(1024).decode('utf-8'))
            return response['status'] == 'success'
        except Exception as e:
            print(f"Error sending command: {e}")
            return False

    def close(self):
        self.sock.close()
