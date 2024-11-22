import time
from datetime import datetime
from random import randint
import hashlib


from src.service.sol_service import SOLService


class PeerService:
    def __init__(self, udp_service, component_model, logger):
        self.udp_service = udp_service
        self.component_model = component_model
        self.logger = logger
        self.sol_service = None

    def broadcast_hello_and_initialize(self, retries=2, wait_time=10, max_components=4):
        """
        Broadcast a HELLO? message, wait for SOL responses, and initialize as SOL if no responses are received.

        Args:
            retries (int): Number of retries if no SOL responses are received.
            wait_time (int): Wait time (in seconds) between retries.
            max_components (int): Maximum number of components allowed in the new star.
        """
        self.logger.info("Broadcasting HELLO? to discover SOL...")

        for attempt in range(retries + 1):
            # Step 1: Broadcast HELLO?
            try:
                self.udp_service.broadcast_udp_message("HELLO?")
            except Exception as e:
                self.logger.error(f"Failed to broadcast HELLO?: {e}")
                continue

            # Step 2: Listen for SOL responses
            self.logger.info("Waiting for responses from SOL components...")
            try:
                responses = self.udp_service.listen_for_responses(self.udp_service.port, timeout=5)
            except Exception as e:
                self.logger.error(f"Error while listening for responses: {e}")
                continue

            # Step 3: Validate and collect responses
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

            self.logger.warning(f"No responses received. Retrying... ({attempt + 1}/{retries})")
            time.sleep(wait_time)

        # Step 4: No SOL responses received, initialize as new SOL
        self.logger.warning("No SOL components found after retries. Initializing as new SOL...")
        self.initialize_as_sol(max_components)
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

        # Wähle den SOL mit der größten UUID (lexikografisch sortiert)
        # TODO: Im Aufgabenblatt steht:  (Vorsicht Falle! Hatten wir in der Vorlesung 😉 ), also eventuell anpassen !!
        chosen_response, chosen_addr = max(valid_responses, key=lambda x: x[0]["sol"])
        self.logger.info(f"Gewählter SOL: {chosen_response} von {chosen_addr[0]}:{chosen_addr[1]}")
        return chosen_response, chosen_addr

    def initialize_as_sol(self, max_components=4):
        """
        Initialisiert die Komponente als Mittelpunkt eines neuen Sterns (SOL).
        """
        # Generiere eine <COM-UUID>
        com_uuid = self.generate_com_uuid()

        # Generiere eine <STAR-UUID>
        star_uuid = self.generate_star_uuid(com_uuid)

        # Zeitstempel der Initialisierung
        init_timestamp = datetime.now().isoformat()

        self.logger.info(f"Initializing as new SOL with STAR-UUID: {star_uuid}, COM-UUID: {com_uuid}")

        # Starte den SOLService mit den initialisierten Daten
        self.sol_service = SOLService(
            udp_service=self.udp_service,
            logger=self.logger,
            star_uuid=star_uuid,
            sol_uuid=com_uuid,
            ip=self.udp_service.ip,
            star_port=self.udp_service.port,
            max_components=max_components,
            component_model = self.component_model
        )

        # Registriere die Komponente selbst
        self.sol_service.registered_components.append({
            "component": com_uuid,
            "com-ip": self.udp_service.ip,
            "com-tcp": self.udp_service.port,
            "integration_timestamp": init_timestamp,
            "last_interaction_timestamp": init_timestamp
        })
        self.logger.info(f"Self-registered as SOL with STAR-UUID: {star_uuid}")

    def generate_com_uuid(self):
        """
        Generiert eine einzigartige vierstellige COM-UUID.
        """
        while True:
            com_uuid = randint(1000, 9999)
            if not self.sol_service or all(
                    comp["component"] != com_uuid for comp in self.sol_service.registered_components):
                return com_uuid

    def generate_star_uuid(self, com_uuid):
        """
        Generiert die STAR-UUID basierend auf der IP-Adresse, dem SOL-ID und der COM-UUID.
        """
        identifier = f"{self.udp_service.ip}{com_uuid}{com_uuid}".encode('utf-8')
        return hashlib.md5(identifier).hexdigest()