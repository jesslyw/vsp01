import sys
import threading
import time
from datetime import datetime
from random import randint
import hashlib

import requests

from src.app.config import Config
from src.service.sol_service import SOLService
from src.service.udp_service import UdpService
from src.manager.sol_manager import SolManager
from src.service.tcp_service import send_tcp_request


class PeerService:
    def __init__(self, component_model, logger):
        self.component_model = component_model  # TODO: Wird hier gerade nicht benutzt
        self.logger = logger  # TODO: Muss eventuell gar nicht übergeben werden
        self.sol_service = None  # Wird initialisiert, wenn Peer zu Sol wird

    def broadcast_hello_and_initialize(self):
        """
        Broadcast a HELLO? message, wait for SOL responses, and initialize as SOL if no responses are received.
        """
        self.logger.info("Broadcasting HELLO? to discover SOL...")

        for attempt in range(Config.STATUS_UPDATE_RETRIES):
            # Broadcast HELLO?
            try:
                UdpService.broadcast_message(Config.STAR_PORT, "HELLO?")
            except Exception as e:
                self.logger.error(f"Failed to broadcast HELLO?: {e}")
                continue

            # Listen for SOL responses
            self.logger.info("Waiting for responses from SOL components...")
            try:
                responses = UdpService.listen_for_responses(self.component_model.port,
                                                                  timeout=Config.TIMEOUT_LISTENING_FOR_UPD_RESPONSE) #TODO port anpassen???
            except Exception as e:
                self.logger.error(f"Error while listening for responses: {e}")
                continue

            # Validate and collect responses #TODO: Diesen Step eventuell auslagern?
            valid_responses = []
            for response, addr in responses:
                if "star" in response and "sol" in response and "sol-ip" in response and "sol-tcp" in response:
                    valid_responses.append((response, addr))
                    self.logger.info(f"Discovered SOL: {response} from {addr[0]}:{addr[1]}")
                else:
                    self.logger.warning(f"Invalid SOL response from {addr[0]}:{addr[1]}: {response}")

            if valid_responses:
                self.logger.info(f"Discovered {len(valid_responses)} valid SOL component(s).")
                return valid_responses

            self.logger.warning(f"No responses received. Retrying... ({attempt + 1}/{Config.STATUS_UPDATE_RETRIES})")
            time.sleep(Config.STATUS_UPDATE_WAIT)

        # No SOL responses received, initialize as new SOL
        self.logger.warning("No SOL components found after retries. Initializing as new SOL...")
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
            self.logger.warning("Keine validen SOL-Komponenten verfügbar.")
            return None, None
        # TODO: Es war nicht klar, was genau das Auswahlkriterium füpr einen Sol ist
        # Wähle Sol mit größter UUID (lexikographisch)
        chosen_response, chosen_addr = max(valid_responses, key=lambda x: x[0]["sol"])
        self.logger.info(f"Gewählter SOL: {chosen_response} von {chosen_addr[0]}:{chosen_addr[1]}")
        return chosen_response, chosen_addr

    def initialize_as_sol(self):
        """
        Initialisiert die Komponente als Mittelpunkt eines neuen Sterns (SOL).
        """
        com_uuid = self.generate_com_uuid()
        star_uuid = self.generate_star_uuid(com_uuid)
        init_timestamp = datetime.now().isoformat()

        self.logger.info(f"Initializing as new SOL with STAR-UUID: {star_uuid}, COM-UUID: {com_uuid}")

        self.sol_service = SOLService(
            component_model=self.component_model,
            logger=self.logger,
            star_uuid=star_uuid,
            sol_uuid=com_uuid,
            ip=self.component_model.ip,
        )

        self.sol_service.registered_peers.append({
            "component": com_uuid,
            "com-ip": self.component_model.ip,
            "com-tcp": self.component_model.port,
            "integration_timestamp": init_timestamp,
            "last_interaction_timestamp": init_timestamp
        })
        self.logger.info(f"Self-registered as SOL with STAR-UUID: {star_uuid}")

        self.component_model.is_sol = True
        sol_manager = SolManager(self.sol_service)
        sol_thread = threading.Thread(target=sol_manager.manage())
        sol_thread.start()
        sys.exit()

    def request_registration_with_sol(self, sol_ip, sol_tcp, star, sol, com_uuid):
        """
        Send status to SOL and return the HTTP status code.
        """
        sol_url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/"
        post_data = {
            "star": star,
            "sol": sol,
            "component": com_uuid,
            "com-ip": self.component_model.ip,
            "com-tcp": self.component_model.port,
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
        identifier = f"{self.component_model.ip}{com_uuid}{com_uuid}".encode('utf-8')
        return hashlib.md5(identifier).hexdigest()

    def send_status_update(self, sol_ip, sol_tcp):
        """
        Sendet eine Statusmeldung an SOL.
        """
        payload = {
            "star": self.sol_service.star_uuid,
            "sol": self.sol_service.sol_uuid,
            "component": self.sol_service.sol_uuid,
            "com-ip": self.component_model.ip,
            "com-tcp": self.component_model.port,
            "status": 200
        }

        url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/{self.sol_service.sol_uuid}"
        for attempt in range(Config.STATUS_UPDATE_RETRIES + 1):
            try:
                self.logger.info(f"Sending status update to SOL at {url}: {payload}")
                response = requests.patch(url, json=payload)
                if response.status_code == 200:
                    self.logger.info("Status update successful.")
                    return True
                else:
                    self.logger.warning(f"Status update failed: {response.status_code} {response.text}")
            except requests.RequestException as e:
                self.logger.error(f"Error sending status update: {e}")

            self.logger.warning(f"Retrying status update... ({attempt + 1}/{Config.STATUS_UPDATE_RETRIES +1})")
            time.sleep(Config.STATUS_UPDATE_WAIT)

        self.logger.error("Status update failed after retries. Exiting.")
        return False

    def send_exit_request(self, sol_ip, sol_tcp):
        """
        Sendet eine Abmeldeanforderung (EXIT) an SOL.
        """
        url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/{self.sol_service.sol_uuid}?sol={self.sol_service.star_uuid}"
        for attempt in range(Config.EXIT_REQUEST_RETRIES):
            try:
                self.logger.info(f"Sending EXIT request to SOL at {url}")
                response = requests.delete(url)
                if response.status_code == 200:
                    self.logger.info("Component successfully unregistered from SOL.")
                    return True
                elif response.status_code == 401:
                    self.logger.warning("Unauthorized to unregister from SOL. Exiting with error.")
                    return False
                elif response.status_code == 404:
                    self.logger.warning("Component not found in SOL. Exiting with error.")
                    return False
                else:
                    self.logger.warning(f"Unexpected response: {response.status_code} {response.text}")
            except requests.RequestException as e:
                self.logger.error(f"Error sending EXIT request: {e}")

            self.logger.warning(f"Retrying EXIT request... ({attempt + 1}/{Config.EXIT_REQUEST_RETRIES})")
            time.sleep(Config.EXIT_REQUEST_WAIT)

        self.logger.error("Failed to unregister after retries. Exiting forcefully.")
        return False