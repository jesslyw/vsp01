import os
import sys
import threading
import time
from datetime import datetime
from threading import Lock
import requests
from app.config import Config
from service.udp_service import UdpService
from utils.logger import global_logger
from utils.uuid_generator import UuidGenerator


class SOLService:
    def __init__(self, peer, star_port=None):
        self.peer = peer
        self.star_uuid = None
        self.sol_uuid = None
        self.star_port = star_port or Config.STAR_PORT
        self.num_active_components = 1
        self.sol = None


    def listen_for_hello(self):
        """Listens for HELLO? messages and responds with the required JSON blob."""
        global_logger.info("SOL is listening for HELLO? messages...")
        try:
            def handle_message(message, addr):
                if message.strip() == "HELLO?":
                    global_logger.info(f"Received HELLO? from {addr[0]}:{addr[1]}")
                    self.send_response(addr[0], Config.STAR_PORT)
                else:
                    global_logger.warning(
                        f"Unexpected message from {addr[0]}:{addr[1]}: {message}"
                    )

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
            global_logger.error(
                f"Failed to send response to {target_ip}:{target_port}: {e}"
            )

    def check_component_status(self, peer):
        """
        Überprüft den Status einer Komponente über eine GET-Anfrage.
        """
        url = f"http://{peer.com_ip}:{peer.com_tcp}/vs/v1/system/{peer.com_uuid}?star={self.star_uuid}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                global_logger.info(f"Component {peer.com_uuid} is active.")
                peer.set_last_interaction_timestamp()
            else:
                global_logger.warning(
                    f"Component {peer.com_uuid} returned status {response.status_code}."
                )
        except requests.RequestException as e:
            global_logger.error(f"Failed to contact component {peer.com_uuid}: {e}")
            peer.status = "disconnected"

    def check_peer_health(self):
        """Checks the health of registered peers and updates their status."""
        while True:
            try:
                current_time = datetime.now()
                with self.sol.peers_lock:
                    for peer in self.sol.registered_peers:

                        if peer.com_uuid == self.peer.com_uuid:
                            continue

                        last_interaction = datetime.fromisoformat(
                            peer.last_interaction_timestamp
                        )
                        if (
                            current_time - last_interaction
                        ).total_seconds() > Config.PEER_INACTIVITY_THRESHOLD:
                            global_logger.warning(
                                f"Component {peer.com_uuid} is inactive. Checking status."
                            )
                            self.check_component_status(peer)
                time_after_check = datetime.now()
                time_elapsed = int((time_after_check - current_time).total_seconds())
                time.sleep(Config.PEER_INACTIVITY_THRESHOLD - time_elapsed)
            except Exception as e:
                global_logger.error(f"Error in check_peer_health thread: {e}")

    def unregister_all_peers_and_exit(self):
        """Unregister all peers from the star and exit SOL."""
        global_logger.info("Unregistering all peers before exiting...")
        with self.sol.peers_lock:
            for peer in self.sol.registered_peers:
                self._unregister_peer(peer)
            self.sol.registered_peers.clear()

        # see all running threads
        # Print all active threads before exiting
        # global_logger.info("Active threads before exit:")
        # active_threads = threading.enumerate()
        # for thread in active_threads:
        #     global_logger.info(f"Thread ID: {thread.ident}, Name: {thread.name}, Daemon: {thread.daemon}")
        global_logger.info("All peers processed. Exiting SOL...")
        os._exit(Config.EXIT_CODE_SUCCESS)

    def _unregister_peer(self, peer):
        """Helper method to unregister a single peer."""
        url = f"http://{peer.ip}:{peer.com_tcp}/vs/v1/system/{peer.com_uuid}?star={self.star_uuid}"
        for attempt in range(Config.UNREGISTER_RETRY_COUNT):
            try:
                global_logger.info(
                    f"Sending DELETE request to peer {peer.com_uuid} at {url}"
                )
                response = requests.delete(url)
                if response.status_code == 200:
                    global_logger.info(
                        f"Peer {peer.com_uuid} unregistered successfully."
                    )
                    return
                elif response.status_code == 401:
                    global_logger.warning(
                        f"Unauthorized attempt to unregister peer {peer.com_uuid}. Skipping."
                    )
                    return
                else:
                    global_logger.warning(
                        f"Unexpected response from peer {peer.com_uuid}: {response.status_code}"
                    )
            except requests.RequestException as e:
                global_logger.error(f"Failed to contact peer {peer.com_uuid}: {e}")

            global_logger.warning(
                f"Retrying DELETE request to peer {peer.com_uuid}... ({attempt + 1}/{Config.UNREGISTER_RETRY_COUNT})"
            )
            time.sleep(Config.UNREGISTER_RETRY_DELAY[attempt])

        global_logger.error(
            f"Failed to unregister peer {peer.com_uuid} after {Config.UNREGISTER_RETRY_COUNT} attempts."
        )
        peer.status = "disconnected"
