class PeerService:
    def __init__(self, udp_service, component_model, logger):
        self.udp_service = udp_service
        self.component_model = component_model
        self.logger = logger

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
