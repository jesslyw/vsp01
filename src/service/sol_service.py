import sys
import threading
import time
from datetime import datetime

import requests

from src.app.config import Config
from src.controller.sol_controller import create_sol_api
from src.service.udp_service import UdpService


# TODO: Starport ist jetzt in der Config-Datei und hier: Passt das so?
class SOLService:
    def __init__(self, component_model, logger, star_uuid, sol_uuid, ip, star_port=None):
        self.component_model = component_model  # TODO: Macht aktuell nichts
        self.logger = logger  # TODO: Muss das übergeben werden?
        self.star_uuid = star_uuid
        self.sol_uuid = sol_uuid
        self.ip = ip
        self.star_port = star_port or Config.STAR_PORT
        self.registered_peers = [] # TODO: potenzielle Racing-Conditions
        self.num_active_components = 1
        self.max_active_components = 4

        # Start the SOL API in a separate thread
        self.start_sol_api()


    def start_sol_api(self):
        """Starts the SOL API in a separate thread."""
        app = create_sol_api(self)
        api_thread = threading.Thread(target=app.run, kwargs={"port": Config.PEER_PORT, "debug": False}, daemon=True)
        api_thread.start()
        self.logger.info(f"SOL API started on port {Config.PEER_PORT}")  # TODO: Ist das der richtige Port?

    def listen_for_hello(self):
        """Listens for HELLO? messages and responds with the required JSON blob."""
        self.logger.info("SOL is listening for HELLO? messages...")
        try:
            def handle_message(message, addr):
                if message.strip() == "HELLO?":
                    self.logger.info(f"Received HELLO? from {addr[0]}:{addr[1]}")
                    self.send_response(addr[0], addr[1])
                else:
                    self.logger.warning(f"Unexpected message from {addr[0]}:{addr[1]}: {message}")
            print("about to listen....")
            UdpService.listen(Config.STAR_PORT, callback=handle_message)
            print("Just started listening!")
        except Exception as e:
            self.logger.error(f"Error while listening for HELLO? messages: {e}")

    def send_response(self, target_ip, target_port):
        """Send the JSON blob response to the sender of the HELLO? message."""
        response = {
            "star": self.star_uuid,
            "sol": self.sol_uuid,
            "sol-ip": self.ip,
            "sol-tcp": self.star_port,
            "component": self.sol_uuid,
        }
        self.logger.info(f"Sending response to {target_ip}:{target_port}: {response}")
        try:
            UdpService.send_response(response, target_ip, target_port)
        except Exception as e:
            self.logger.error(f"Failed to send response to {target_ip}:{target_port}: {e}")

    def check_peer_health(self):
        """Checks the health of registered peers and updates their status."""
        while True:
            current_time = datetime.now()
            for peer in self.registered_peers:
                last_interaction = datetime.fromisoformat(peer["last_interaction_timestamp"])
                if (current_time - last_interaction).total_seconds() > Config.PEER_INACTIVITY_THRESHOLD:
                    self.logger.warning(f"Component {peer['component']} is inactive. Marking as disconnected.")
                    peer["status"] = "disconnected"
            time_after_check = datetime.now()
            time_elapsed = int((current_time-time_after_check).total_seconds())
            time.sleep(Config.HEALTH_CHECK_INTERVAL-time_elapsed)

    def unregister_all_peers_and_exit(self):
        """
        Unregister all peers from the star and exit SOL.
        """
        self.logger.info("Unregistering all peers before exiting...")
        for peer in self.registered_peers:
            peer_uuid = peer["component"]
            peer_ip = peer["com-ip"]
            peer_tcp = peer["com-tcp"]

            url = f"http://{peer_ip}:{peer_tcp}/vs/v1/system/{peer_uuid}?sol={self.star_uuid}"
            for attempt in range(Config.UNREGISTER_RETRY_COUNT):  # Retry logic
                try:
                    self.logger.info(f"Sending DELETE request to peer {peer_uuid} at {url}")
                    response = requests.delete(url)
                    if response.status_code == 200:
                        self.logger.info(f"Peer {peer_uuid} unregistered successfully.")
                        break
                    elif response.status_code == 401:
                        self.logger.warning(f"Unauthorized attempt to unregister peer {peer_uuid}. Skipping.")
                        break
                    else:
                        self.logger.warning(f"Unexpected response from peer {peer_uuid}: {response.status_code}")
                except requests.RequestException as e:
                    self.logger.error(f"Failed to contact peer {peer_uuid}: {e}")

                self.logger.warning(
                    f"Retrying DELETE request to peer {peer_uuid}... ({attempt + 1}/{Config.UNREGISTER_RETRY_COUNT})")
                time.sleep(Config.UNREGISTER_RETRY_DELAY)

            peer["status"] = "disconnected"
            self.logger.info(f"Marked peer {peer_uuid} as disconnected.")

        self.logger.info("All peers processed. Exiting SOL...")
        exit(Config.SOL_EXIT_CODE)
