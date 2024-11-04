import socket
import threading

class CommunicationService:
    def __init__(self, ip="127.0.0.1", port=8013):
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_listening(self):
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(5)
        print(f"Listening for connections on {self.ip}:{self.port}...")

        # Start a thread to handle incoming connections
        thread = threading.Thread(target=self._handle_connections)
        thread.start()

    def _handle_connections(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection received from {addr}")
            thread = threading.Thread(target=self._handle_client, args=(client_socket,))
            thread.start()

    def _handle_client(self, client_socket):
        with client_socket:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                print(f"Received: {data.decode('utf-8')}")
                # Echo the received message back to the client
                client_socket.sendall(data)

    def send_message(self, ip, port, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, port))
            sock.sendall(message.encode('utf-8'))
            print(f"Sent message to {ip}:{port}")