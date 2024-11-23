import json
import socket

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
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))
        
        while True:
            # recvform speichert ankommende Nachrichten im Buffer damit keine verloren gehen
            data, addr = sock.recvfrom(1024) # response data and sender address in the form of ip,port 
            message = data.decode('utf-8').strip(chr(0))
            callback(message, addr)