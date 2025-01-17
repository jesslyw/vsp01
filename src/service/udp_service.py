import json
import socket
from app.config import Config

'''
stellt die funktionalitäten listen, broadcast message, send response über udp bereit 
'''


class UdpService:
    @staticmethod
    def broadcast_message(port, message):
        """Broadcast a UDP message."""
        if len(message) > 1024:
            raise ValueError("Broadcast message exceeds max 1024 bytes.")
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = message.encode('utf-8') + b'\0'
        udp_socket.sendto(message, ('<broadcast>', port))
        udp_socket.close()

    @staticmethod
    def send_response(response, target_ip, target_port):
        """Send a JSON response over UDP."""
        response_message = json.dumps(response)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.sendto(response_message.encode('utf-8'), (target_ip, target_port))
        udp_socket.close()

    @staticmethod
    def listen(port, callback):
        """
        Listen for incoming UDP messages and invoke the callback function if a response is recieved
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('', port))

            while True:
                # recvform speichert ankommende Nachrichten im Buffer damit keine verloren gehen
                data, addr = sock.recvfrom(1024)  # response data and sender address in the form of ip,port
                message = data.decode('utf-8').strip(chr(0))
                callback(message, addr)

    @staticmethod
    def listen_for_responses(port, timeout=5):
        """Listen for responses to a broadcast for a specified timeout."""
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('', port))
        udp_socket.settimeout(timeout)

        responses = []
        try:
            while True:
                data, addr = udp_socket.recvfrom(1024)
                message = data.decode('utf-8').strip(chr(0))
                try:
                    # Parse JSON response
                    response = json.loads(message)
                    responses.append((response, addr))
                except json.JSONDecodeError:
                    print(f"Invalid response from {addr[0]}:{addr[1]}: {message}")
        except socket.timeout:
            # Timeout reached, stop listening
            pass
        finally:
            udp_socket.close()

        return responses
