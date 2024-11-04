import json
import socket
import threading

#make methods to function (static)
class Udp_Service:
    def __init__(self, port, star_uuid, com_uuid, ip, star_port, is_sol):
        self.port = port
        self.star_uuid = star_uuid
        self.com_uuid = com_uuid
        self.ip = ip
        self.star_port = star_port
        self.is_sol = is_sol

        # Start the listener thread if the component is SOL
        if self.is_sol:
            self.udp_listener_thread = threading.Thread(
                target=self.listen_for_udp_broadcast, daemon=True)
            self.udp_listener_thread.start()

    def broadcast_udp_message(self, message):
        """broadcast udp message as peer"""
        if len(message) > 1024:
            print("Error: Broadcast message exceeds max. 1024 bytes")
            return
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = message.encode('utf-8') + b'\0'
        udp_socket.sendto(message, ('<broadcast>', self.port))
        udp_socket.close()

    def listen_for_udp_broadcast(self):
        """listen to udp broadcast messages as SOL"""
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('', self.port))
        print(f"Listening for UDP broadcasts on port {self.port}...")
        while True:
            data, addr = udp_socket.recvfrom(1024)
            received_message = data.decode('utf-8').strip(chr(0))
            if received_message == "HELLO?":
                # Respond with the JSON blob
                response = {
                    "star": self.star_uuid,
                    "sol": self.com_uuid,
                    "sol-ip": self.ip,
                    "sol-tcp": self.star_port,
                    "component": self.com_uuid
                }
                self.send_response(response, addr[0], addr[1])

    def send_response(self, response, target_ip, target_port):
        """respond with json blob as SOL"""
        response_message = json.dumps(response)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.sendto(response_message.encode(
            'utf-8'), (target_ip, target_port))
        udp_socket.close()