from service.udp_service import UdpService
import time
from utils.logger import Logger


class SolService:

    logger = Logger()

    @staticmethod
    def listen_for_udp_broadcast_and_respond_with_star_info(star_uuid, com_uuid, ip, star_port):
        """
        Listen for HELLO messages on UDP and respond as SOL with information about the STAR.
        
        Parameters:
        - port: Port to listen on.
        - star_uuid: UUID of the STAR component.
        - com_uuid: UUID of this SOL component.
        - ip: IP address of this SOL.
        - star_port: TCP port used by the STAR component.
        """

        def handle_message(message, addr):
            if message == "HELLO?":
                SolService.logger.info(f"Received HELLO from {addr}. Responding...")
                response = {
                    "star": star_uuid,
                    "sol": com_uuid,
                    "sol-ip": ip,
                    "sol-tcp": star_port,
                    "component": com_uuid
                }
                sender_ip = addr[0]
                sender_port = addr[1]
                UdpService.send_response(response, sender_ip, sender_port)
                SolService.logger.info(f"Response sent to {addr}.")

        SolService.logger.info(f"Listening for HELLO messages on port {star_port}...")
        try:
            UdpService.listen(star_port, handle_message)
        except Exception as e:
            SolService.logger.error(f"Error while listening for UDP broadcasts: {e}")

