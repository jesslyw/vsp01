#Implementiert die TCP- und UDP-Kommunikation für den Broadcast und Anmeldung einer Komponente in den Stern 

from utils.logger import Logger
import threading
from communication.udp_service import UdpService


'''
vars for sol response 

starport 
star-uuid
com-uuid von sol
solip
soltcp

'''


class DiscoveryService:
    logger = Logger()

    @staticmethod
    def broadcast_hello(port):
        """Sendet eine Broadcast-Meldung, um andere Peers zu finden.""" 
        try:
            DiscoveryService.logger.info("Broadcasting HELLO message...")
            UdpService.broadcast_message(port, "HELLO?")
            DiscoveryService.logger.info("HELLO message sent.")
        except Exception as e:
            DiscoveryService.logger.error(f"Error broadcasting HELLO: {e}")

    @staticmethod
    def listen_for_udp_broadcast(port, star_uuid, com_uuid, ip, star_port):
        """Listen for HELLO messages and respond as SOL with information about the star"""
        def handle_message(message, addr):
            if message == "HELLO?":
                DiscoveryService.logger.info(f"HELLO received from {addr}. Responding...")
                response = {
                    "star": star_uuid,
                    "sol": com_uuid,
                    "sol-ip": ip,
                    "sol-tcp": star_port,
                    "component": com_uuid
                }
                UdpService.send_response(response, addr[0], addr[1])

        DiscoveryService.logger.info(f"Listening for HELLO messages on port {port}...")
        try:
            UdpService.listen(port, handle_message)
        except Exception as e:
            DiscoveryService.logger.error(f"Error while listening for UDP broadcasts: {e}")

    @staticmethod
    def start_listener_thread(port, star_uuid, com_uuid, ip, star_port): 
        """Start a listener thread for HELLO messages."""
        thread = threading.Thread(
            target=DiscoveryService.listen_for_udp_broadcast,
            args=(port, star_uuid, com_uuid, ip, star_port),
            daemon=True
        )
        thread.start()

    @staticmethod
    def register_component_in_sol(sol_ip, sol_tcp, star, sol, com_uuid, ip, port, status):
        '''
        try to register in sol and return sol's response status code 
        '''
        sol_url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/"

        post_data = {
            "star": star, #star uuid
            "sol": sol, #sol's com uuid 
            "component": com_uuid,
            "com-ip": ip,
            "com-tcp": port,
            "status": status
        }

        headers = {'Content-Type': 'application/json'}
        status_code = UdpService.send_tcp_request('POST', sol_url, body=post_data, headers=headers)
        return status_code