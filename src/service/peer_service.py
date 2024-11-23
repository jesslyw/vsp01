from service.udp_service import UdpService
import json
import sys
from utils.logger import Logger
from app.config import Config
from service.tcp_service import send_tcp_request

class PeerService:
    logger = Logger()  # Singleton logger shared across all calls to this class

    @staticmethod
    def broadcast_hello_and_listen_for_sol_response(com_uuid, ip, port):
        """
        Broadcast a HELLO message and listen for SOL responses
        If a response is recieved, attempts to register with SOL 
        In the case of more than one response, 
        Retries twice 
        """
        for attempt in range(2):  # Retry twice
            PeerService.logger.info(f"Attempt {attempt + 1}: Broadcasting HELLO message...")
            UdpService.broadcast_message(Config.STAR_PORT, "HELLO")

            PeerService.logger.info("Waiting 5 seconds for SOL responses...")
            try:
                # Listen for a single response
                response = UdpService.listen(
                    Config.STAR_PORT, 
                    lambda message, addr: PeerService._handle_sol_response_to_hello(message, addr, com_uuid, ip, port), 
                    timeout=5
                )
                if response:  # If a valid SOL response is received
                    return True
            except TimeoutError:
                PeerService.logger.error("No SOL response received. Retrying...")
        return False
    
  
    def _handle_sol_response_to_hello(message, addr, com_uuid, ip, port):
        """
        Handle incoming SOL responses to HELLO messages.
        """
        PeerService.logger.info(f"COM: Received response (JSON blob): {message} from SOL at {addr}")
        try:
            response = json.loads(message)
            star = response.get("star")
            sol = response.get("sol")
            sol_ip = response.get("sol-ip")
            sol_tcp = response.get("sol-tcp")

            # Attempt to register with the SOL
            response_status_code = PeerService._request_registration_with_sol(
                sol_ip, sol_tcp, star, sol, com_uuid, ip, port, 200
            )
            
            if response_status_code == 200:
                PeerService.logger.info("Registration successful.")
                return True
            elif response_status_code == 401:
                PeerService.logger.error("Error 401: Unauthorized registration - terminating component.")
                sys.exit(1)
            elif response_status_code == 403:
                PeerService.logger.error("Error 403: No room left - terminating component.")
                sys.exit(1)
            elif response_status_code == 409:
                PeerService.logger.error("Error 409: Conflict in registration - terminating component.")
                sys.exit(1)
        except json.JSONDecodeError:
            PeerService.logger.error("Invalid response received. Ignoring message.")
        return False

 
    def _request_registration_with_sol(sol_ip, sol_tcp, star, sol, com_uuid, ip, port, status):
        """
        Send status to SOL and return the HTTP status code.
        """
        sol_url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/"
        post_data = {
            "star": star,
            "sol": sol,
            "component": com_uuid,
            "com-ip": ip,
            "com-tcp": port,
            "status": status,
        }
        headers = {"Content-Type": "application/json"}

        return send_tcp_request("POST", sol_url, body=post_data, headers=headers)
