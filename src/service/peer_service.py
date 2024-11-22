from src.service.peer_api import create_peer_api
import threading


class PeerService:
    def __init__(self, udp_service, component_model, logger):
        self.udp_service = udp_service
        self.component_model = component_model
        self.logger = logger

        # Start the Peer API in a separate thread
        self.start_peer_api()

    def start_peer_api(self):
        """Starts the Peer API in a separate thread."""
        app = create_peer_api(self)
        # TODO: Eventuell Port in die Config?
        api_thread = threading.Thread(target=app.run, kwargs={"port": 5001, "debug": False}, daemon=True)
        api_thread.start()
        self.logger.info("Peer API started on port 5001")

    def broadcast_hello(self):
        """Broadcast a HELLO? message and wait for SOL responses."""
        # 1. Broadcast HELLO? Nachricht
        global valid_responses
        self.logger.info("Broadcasting HELLO? to discover SOL...")
        try:
            self.udp_service.broadcast_udp_message("HELLO?")
        except Exception as e:
            self.logger.error(f"Failed to broadcast HELLO?: {e}")
            return []

        # 2. Listen for responses
        self.logger.info("Waiting for responses from SOL components...")
        # TODO: Wie lange soll der Timeout sein? Eventuell in Conif auslagern
        try:
            responses = self.udp_service.listen_for_responses(self.udp_service.port, timeout=5)
        except Exception as e:
            self.logger.error(f"Error while listening for responses: {e}")
            return []

        # 3. Validate responses
        valid_responses = []
        if not responses:
            self.logger.warning("No SOL components discovered.")
        else:
            for response, addr in responses:
                # Validate the response structure
                if "star" in response and "sol" in response and "sol-ip" in response and "sol-tcp" in response:
                    valid_responses.append((response, addr))
                    self.logger.info(f"Discovered SOL: {response} from {addr[0]}:{addr[1]}")
                else:
                    self.logger.warning(f"Invalid SOL response from {addr[0]}:{addr[1]}: {response}")

            if not valid_responses:
                self.logger.warning("No valid SOL responses received.")
            else:
                self.logger.info(f"Discovered {len(valid_responses)} valid SOL component(s).")

        return valid_responses

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
