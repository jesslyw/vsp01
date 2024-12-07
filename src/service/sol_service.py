import sys
import threading
import time
from datetime import datetime
from threading import Lock
import requests

from src.app.config import Config
from src.controller.sol_controller import create_sol_api
from src.service.udp_service import UdpService
from src.utils.logger import global_logger
from src.utils.uuid_generator import UuidGenerator


# TODO: Starport ist jetzt in der Config-Datei und hier: Passt das so?
class SOLService:
    def __init__(self, peer, star_port=None):
        self.peer = peer
        self.star_uuid = None
        self.sol_uuid = None
        self.star_port = star_port or Config.STAR_PORT
        self.registered_peers = []
        self._peers_lock = Lock()
        self.num_active_components = 1
        self.max_active_components = 4

        # Start the SOL API in a separate thread
        #self.start_sol_api()

    def start_sol_api(self):
        """Starts the SOL API in a separate thread."""
        try:
            app = create_sol_api(self)
            app.run(port=Config.STAR_PORT, debug=False)
            # api_thread = threading.Thread(target=app.run, kwargs={"port": Config.PEER_PORT, "debug": False}, daemon=True)
            # api_thread.start()
            global_logger.info(f"SOL API started on port {Config.STAR_PORT}")  # TODO: Ist das der richtige Port?
        except Exception as e:
            global_logger.error(f"Failed to start SOL API: {e}")

    def listen_for_hello(self):
        """Listens for HELLO? messages and responds with the required JSON blob."""
        global_logger.info("SOL is listening for HELLO? messages...")
        try:
            def handle_message(message, addr):
                if message.strip() == "HELLO?":
                    global_logger.info(f"Received HELLO? from {addr[0]}:{addr[1]}")
                    self.send_response(addr[0], Config.STAR_PORT)
                else:
                    global_logger.warning(f"Unexpected message from {addr[0]}:{addr[1]}: {message}")

            UdpService.listen(Config.STAR_PORT, callback=handle_message)

        except Exception as e:
            global_logger.error(f"Error while listening for HELLO? messages: {e}")

    def send_response(self, target_ip, target_port):
        """Send the JSON blob response to the sender of the HELLO? message."""
        response = {
            "star": self.star_uuid,
            "sol": self.sol_uuid,
            "sol-ip": Config.IP,
            "sol-tcp": self.star_port,
            "component": UuidGenerator.generate_com_uuid(),
        }
        global_logger.info(f"Sending response to {target_ip}:{target_port}: {response}")
        try:
            UdpService.send_response(response, target_ip, target_port)
        except Exception as e:
            global_logger.error(f"Failed to send response to {target_ip}:{target_port}: {e}")

    def check_component_status(self, peer):
        """
        Überprüft den Status einer Komponente über eine GET-Anfrage.
        """
        url = f"http://{peer['com-ip']}:{peer['com-tcp']}/vs/v1/system/{peer['component']}?star={self.star_uuid}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                global_logger.info(f"Component {peer['component']} is active.")
                peer["last_interaction_timestamp"] = datetime.now().isoformat()
            else:
                global_logger.warning(f"Component {peer['component']} returned status {response.status_code}.")
        except requests.RequestException as e:
            global_logger.error(f"Failed to contact component {peer['component']}: {e}")
            peer["status"] = "disconnected"

    def check_peer_health(self):
        """Checks the health of registered peers and updates their status."""
        while True:
            try:
                current_time = datetime.now()
                with self._peers_lock:
                    for peer in self.registered_peers:
                        last_interaction = datetime.fromisoformat(peer["last_interaction_timestamp"])
                        if (current_time - last_interaction).total_seconds() > Config.PEER_INACTIVITY_THRESHOLD:
                            global_logger.warning(f"Component {peer['component']} is inactive. Checking stauts.")
                            self.check_component_status(peer)
                time_after_check = datetime.now()
                time_elapsed = int((time_after_check-current_time).total_seconds())
                time.sleep(Config.PEER_INACTIVITY_THRESHOLD-time_elapsed)
            except Exception as e:
                global_logger.error(f"Error in check_peer_health thread: {e}")

    def unregister_all_peers_and_exit(self):
        """Unregister all peers from the star and exit SOL."""
        global_logger.info("Unregistering all peers before exiting...")
        with self._peers_lock:
            for peer in self.registered_peers:
                self._unregister_peer(peer)
            self.registered_peers.clear()

        global_logger.info("All peers processed. Exiting SOL...")
        sys.exit(Config.SOL_EXIT_CODE)

    def _unregister_peer(self, peer):
        """Helper method to unregister a single peer."""
        peer_uuid = peer["component"]
        peer_ip = peer["com-ip"]
        peer_tcp = peer["com-tcp"]

        url = f"http://{peer_ip}:{peer_tcp}/vs/v1/system/{peer_uuid}?sol={self.star_uuid}"
        for attempt in range(Config.UNREGISTER_RETRY_COUNT):
            try:
                global_logger.info(f"Sending DELETE request to peer {peer_uuid} at {url}")
                response = requests.delete(url)
                if response.status_code == 200:
                    global_logger.info(f"Peer {peer_uuid} unregistered successfully.")
                    return
                elif response.status_code == 401:
                    global_logger.warning(f"Unauthorized attempt to unregister peer {peer_uuid}. Skipping.")
                    return
                else:
                    global_logger.warning(f"Unexpected response from peer {peer_uuid}: {response.status_code}")
            except requests.RequestException as e:
                global_logger.error(f"Failed to contact peer {peer_uuid}: {e}")

            global_logger.warning(
                f"Retrying DELETE request to peer {peer_uuid}... ({attempt + 1}/{Config.UNREGISTER_RETRY_COUNT})"
            )
            time.sleep(Config.UNREGISTER_RETRY_DELAY)

        global_logger.error(f"Failed to unregister peer {peer_uuid} after {Config.UNREGISTER_RETRY_COUNT} attempts.")
        peer["status"] = "disconnected"

    def add_peer(self, peer):
        with self._peers_lock:
            self.registered_peers.append(peer)

    def remove_peer(self, peer):
        with self._peers_lock:
            self.registered_peers.remove(peer)