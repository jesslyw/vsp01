import socket
import threading
import json
import time
import requests
import sys

#test
class UdpBroadcast:
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

    # returns false when no SOL response received
    def broadcast_and_listen_for_response(self, message) -> bool:
        broadcast_round = 2  # try 2 times with 10 sec break to connect to SOL
        while broadcast_round > 0:
            # send HELLO?
            self.broadcast_udp_message(message)
            print("broadcasting HELLO?")

            # start temporary UDP listener to wait for SOL's response
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.bind(('', self.port))
            udp_socket.settimeout(5)  # 5 sec wait

            try:
                print(
                    f"COM: Waiting 5 sec for response on port {self.port}...")
                # first message received will be processed (in case of more than one SOL response)
                data, addr = udp_socket.recvfrom(1024)
                received_message = data.decode('utf-8').strip(chr(0))
                print(
                    f"COM: Received response: {received_message} from SOL at {addr}")
                sol_response = True
                response = json.loads(received_message)
                # send POST request to this SOL
                star = response.get("star")
                sol = response.get("sol")
                sol_ip = response.get("sol-ip")
                sol_tcp = response.get("sol-tcp")
                response_status_code = self.send_status_to_sol(sol_ip, sol_tcp, star, sol,
                                                               self.com_uuid, self.ip, self.port, 200)
                if response_status_code == 200:
                    print("Registration successful.")
                    return True
                elif response_status_code == 401:
                    print(
                        "Error 401: Unauthorized registration - terminating component.")
                    sys.exit(1)
                elif response_status_code == 403:
                    print("Error 403: No room left - terminating component.")
                    sys.exit(1)
                elif response_status_code == 409:
                    print(
                        "Error 409: Conflict in registration - terminating component.")
                    sys.exit(1)
                return False  # Exit loop if response received

            except socket.timeout:
                print("No response received from SOL.")
                broadcast_round -= 1
                if broadcast_round > 0:  # pause 10 seconds then retry
                    print("Retrying after 10 seconds...")
                    time.sleep(10)

            finally:
                udp_socket.close()  # Ensure socket is closed after each attempt

        return False

    def broadcast_udp_message(self, message):
        if len(message) > 1024:
            print("Error: Broadcast message exceeds max. 1024 bytes")
            return
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = message.encode('utf-8') + b'\0'
        udp_socket.sendto(message, ('<broadcast>', self.port))
        udp_socket.close()

    # Listen for incoming UDP messages if SOL
    def listen_for_udp_broadcast(self):
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
        response_message = json.dumps(response)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.sendto(response_message.encode(
            'utf-8'), (target_ip, target_port))
        udp_socket.close()

    # returns sol's response status code
    def send_status_to_sol(self, sol_ip, sol_tcp, star, sol, com_uuid, ip, port, status):
        sol_url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/"
        # format data as text/plain
        post_data = (
            f"star: {star}\n"
            f"sol: {sol}\n"
            f"component: {com_uuid}\n"
            f"com-ip: {ip}\n"
            f"com-tcp: {port}\n"
            f"status: {status}"
        )
        try:
            post_response = requests.post(sol_url, data=post_data, headers={
                'Content-Type': 'text/plain'})
            return post_response.status_code
        except requests.Timeout:
            print(f"Timeout occurred while trying to reach {sol_url}")
            return None
