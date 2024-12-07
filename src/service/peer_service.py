import sys
import threading
import time
from datetime import datetime
from random import randint
import hashlib

import requests

from app.config import Config
from service.udp_service import UdpService
from manager.sol_manager import SolManager
from service.tcp_service import send_tcp_request
from model.peer import Peer
from model.sol import SOL
from utils.logger import global_logger
from utils.uuid_generator import UuidGenerator


class PeerService:
    def __init__(self, peer, sol_service):
        self.peer = peer  # TODO: Wird hier gerade nicht benutzt
        self.sol_service = sol_service  # Wird initialisiert, wenn Peer zu Sol wird

    def broadcast_hello_and_initialize(self):
        """
        Broadcast a HELLO? message, wait for SOL responses, and initialize as SOL if no responses are received.
        """
        global_logger.info("Broadcasting HELLO? to discover SOL...")

        for attempt in range(Config.STATUS_UPDATE_MAX_ATTEMPTS-1):
            # Broadcast HELLO?
            try:
                UdpService.broadcast_message(Config.STAR_PORT, "HELLO?")
            except Exception as e:
                global_logger.error(f"Failed to broadcast HELLO?: {e}")
                continue

            startTime = datetime.now()

            # Listen for SOL responses
            global_logger.info("Waiting for responses from SOL components...")
            try:
                responses = UdpService.listen_for_responses(Config.STAR_PORT,
                                                                  timeout=Config.TIMEOUT_LISTENING_FOR_UPD_RESPONSE) #TODO port anpassen???
            except Exception as e:
                global_logger.error(f"Error while listening for responses: {e}")
                continue

            # Validate and collect responses #TODO: Diesen Step eventuell auslagern?
            valid_responses = []
            for response, addr in responses:
                if "star" in response and "sol" in response and "sol-ip" in response and "sol-tcp" in response:
                    valid_responses.append((response, addr))
                    global_logger.info(f"Discovered SOL: {response} from {addr[0]}:{addr[1]}")
                else:
                    global_logger.warning(f"Invalid SOL response from {addr[0]}:{addr[1]}: {response}")

            if valid_responses:
                global_logger.info(f"Discovered {len(valid_responses)} valid SOL component(s).")
                return valid_responses

            global_logger.warning(f"No responses received. Retrying... ({attempt + 1}/{Config.STATUS_UPDATE_MAX_ATTEMPTS-1})")
            endTime = datetime.now()
            elapsed = int((endTime-startTime).total_seconds())
            time.sleep(max(0, Config.BROADCAST_INTERVAL-elapsed))

        # No SOL responses received, initialize as new SOL
        global_logger.warning("No SOL components found after retries. Initializing as new SOL...")
        self.initialize_as_sol()
        return []

    def choose_sol(self, valid_responses):
        """
        Wähle den SOL mit der größten UUID aus einer Liste von validen Antworten.

        Args:
            valid_responses (list): Liste von validen Antworten im Format (response, addr).

        Returns:
            tuple: (response, addr) des gewählten SOL oder None, falls keine valide Antwort existiert.
        """
        if not valid_responses:
            global_logger.warning("Keine validen SOL-Komponenten verfügbar.")
            return None, None
        # TODO: Es war nicht klar, was genau das Auswahlkriterium füpr einen Sol ist
        # Wähle Sol mit größter UUID (lexikographisch)
        chosen_response, chosen_addr = max(valid_responses, key=lambda x: x[0]["sol"])
        global_logger.info(f"Gewählter SOL: {chosen_response} von {chosen_addr[0]}:{chosen_addr[1]}")

        connection = Peer.SolConnection(
            chosen_response[Config.SOL_IP_FIELD],
            chosen_response[Config.SOL_TCP_FIELD],
            chosen_response[Config.SOL_UUID_FIELD],
            chosen_response[Config.STAR_UUID_FIELD]
        )
        self.peer.sol_connection = connection
        self.peer.com_uuid = chosen_response[Config.COMPONENT_UUID_FIELD]
        return chosen_response, chosen_addr

    def initialize_as_sol(self):
        """
        Initialisiert die Komponente als Mittelpunkt eines neuen Sterns (SOL).
        """
        com_uuid = UuidGenerator.generate_com_uuid()
        star_uuid = self.generate_star_uuid(com_uuid)
        init_timestamp = datetime.now().isoformat()

        global_logger.info(f"Initializing as new SOL with STAR-UUID: {star_uuid}, COM-UUID: {com_uuid}")

        self.sol_service.star_uuid = star_uuid
        self.sol_service.sol_uuid = com_uuid

        self.sol_service.add_peer({
            "component": com_uuid,
            "com-ip": self.peer.ip,
            "com-tcp": self.peer.port,
            "integration_timestamp": init_timestamp,
            "last_interaction_timestamp": init_timestamp
        })

        self.peer.is_sol = True
        self.peer.com_uuid = com_uuid
        self.sol_service.sol = SOL(self.peer.com_uuid, star_uuid)
        sol_manager = SolManager(self.sol_service)
        sol_thread = threading.Thread(target=sol_manager.manage())
        sol_thread.start()
        sys.exit()

    def request_registration_with_sol(self, sol_data):
        """
        Send status to SOL and return the HTTP status code.
        """
        star = sol_data[Config.STAR_UUID_FIELD]
        sol = sol_data[Config.COMPONENT_UUID_FIELD]
        sol_ip = sol_data[Config.SOL_IP_FIELD]
        sol_tcp = sol_data[Config.SOL_TCP_FIELD]

        sol_url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/"
        post_data = {
            "star": star,
            "sol": sol,
            "component": self.peer.com_uuid,
            "com-ip": self.peer.ip,
            "com-tcp": self.peer.port,
            "status": 200,
        }
        headers = {"Content-Type": "application/json"}

        return send_tcp_request("POST", sol_url, body=post_data, headers=headers)

    def generate_com_uuid(self):
        """
        Generiert eine einzigartige vierstellige COM-UUID.
        """
        while True:
            com_uuid = randint(Config.UUID_MIN, Config.UUID_MAX)
            if not self.sol_service or all(
                    comp["component"] != com_uuid for comp in self.sol_service.registered_components):
                return com_uuid

    def generate_star_uuid(self, com_uuid):
        """
        Generiert die STAR-UUID basierend auf der IP-Adresse, dem SOL-ID und der COM-UUID.
        """
        identifier = f"{self.peer.ip}{com_uuid}{com_uuid}".encode('utf-8')
        return hashlib.md5(identifier).hexdigest()

    def send_status_update(self):
        """
        Sendet eine Statusmeldung an SOL und informiert den Benutzer über den Statuscode.
        """
        payload = {
            "star": self.peer.sol_connection.star_uuid,
            "sol": self.peer.sol_connection.uuid,
            "component": self.peer.com_uuid,
            "com-ip": self.peer.ip,
            "com-tcp": self.peer.port,
            "status": 200  # Immer 200, um "OK" zu signalisieren
        }

        sol_ip = self.peer.sol_connection.ip
        sol_tcp = self.peer.sol_connection.port
        sol_uuid = self.peer.sol_connection.uuid

        url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/{self.peer.com_uuid}"
        global_logger.info(f"Preparing to send status update to {url} with payload: {payload}")

        try:
            response = requests.patch(url, json=payload, timeout=5)
            if response.status_code == 200:
                global_logger.info(f"Status update to SOL successful: {response.text}")
                return True
            elif response.status_code == 401:
                global_logger.warning(
                    "Unauthorized: SOL rejected the status update. Please verify the STAR-UUID and SOL-UUID.")
            elif response.status_code == 404:
                global_logger.warning("Not Found: The component is not registered with SOL.")
            elif response.status_code == 409:
                global_logger.warning("Conflict: Data mismatch in the status update. Verify the IP, port, and UUID.")
            else:
                global_logger.warning(f"Unexpected status code {response.status_code}: {response.text}")
            return False
        except requests.RequestException as e:
            global_logger.error(f"Error sending status update to SOL: {e}")
            return False

    def send_status_update_periodically(self):
        """
        Sendet regelmäßig eine Statusmeldung an SOL und handhabt Wiederholungen bei Fehlern.
        """
        attempt = 0

        while True:
            success = self.send_status_update()
            if success:
                global_logger.info("Periodic status update successful.")
                attempt = 0  # Rücksetzen der Versuche bei Erfolg
                time.sleep(Config.STATUS_UPDATE_INTERVAL)  # Wartezeit bis zum nächsten Update
            else:
                attempt += 1
                retry_interval = Config.STATUS_UPDATE_RETRY_INTERVALS[min(attempt - 1, len(Config.STATUS_UPDATE_RETRY_INTERVALS) - 1)]
                global_logger.warning(f"Retrying status update... Attempt {attempt}/{Config.STATUS_UPDATE_MAX_ATTEMPTS}")
                time.sleep(retry_interval)

                if attempt >= Config.STATUS_UPDATE_MAX_ATTEMPTS:
                    global_logger.error("Failed to send status update after maximum attempts. Exiting...")
                    self._shutdown_peer()

    def _shutdown_peer(self):
        """
        Beendet den Peer-Prozess sauber.
        """
        # TODO: Was muss hier noch rein?
        global_logger.error("Shutting down peer due to failed status updates.")
        sys.exit(1)

    def send_exit_request(self):
        """
        Sendet eine Abmeldeanforderung (EXIT) an SOL.
        """
        if self.peer.sol_connection is None:
            global_logger.info(f"Component shut down via terminal.")
            return

        sol_ip = self.peer.sol_connection.ip
        sol_tcp = self.peer.sol_connection.port
        url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/{self.peer.com_uuid}?star={self.peer.sol_connection.star_uuid}"
        for attempt in range(Config.EXIT_REQUEST_RETRIES):
            try:
                global_logger.info(f"Sending EXIT request to SOL at {url}")
                response = requests.delete(url)
                if response.status_code == 200:
                    global_logger.info("Component successfully unregistered from SOL.")
                    return True
                elif response.status_code == 401:
                    global_logger.warning("Unauthorized to unregister from SOL. Exiting with error.")
                    return False
                elif response.status_code == 404:
                    global_logger.warning("Component not found in SOL. Exiting with error.")
                    return False
                else:
                    global_logger.warning(f"Unexpected response: {response.status_code} {response.text}")
            except requests.RequestException as e:
                global_logger.error(f"Error sending EXIT request: {e}")

            global_logger.warning(f"Retrying EXIT request... ({attempt + 1}/{Config.EXIT_REQUEST_RETRIES})")
            time.sleep(Config.EXIT_REQUEST_WAIT)

        global_logger.error("Failed to unregister after retries. Exiting forcefully.")
        return False
