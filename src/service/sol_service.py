import threading
from src.service.sol_api import create_sol_api


class SOLService:
    def __init__(self, udp_service, component_model, logger, star_uuid, sol_uuid, ip, star_port,  max_components=10):
        self.udp_service = udp_service
        self.component_model = component_model
        self.logger = logger
        self.star_uuid = star_uuid
        self.sol_uuid = sol_uuid
        self.ip = ip
        self.star_port = star_port
        self.max_components = max_components
        self.registered_components = []

        # Start the SOL API in a separate thread
        self.start_sol_api()

        # Start a thread to listen for HELLO? messages
        listener_thread = threading.Thread(target=self.listen_for_hello, daemon=True)
        listener_thread.start()


    def start_sol_api(self):
        """Starts the SOL API in a separate thread."""
        app = create_sol_api(self)
        api_thread = threading.Thread(target=app.run, kwargs={"port": self.star_port, "debug": False}, daemon=True)
        api_thread.start()
        self.logger.info(f"SOL API started on port {self.star_port}")

    def listen_for_hello(self):
        """Listens for HELLO? messages and responds with the required JSON blob."""
        self.logger.info("SOL is listening for HELLO? messages...")
        try:
            def handle_message(message, addr):
                if message.strip() == "HELLO?":
                    self.logger.info(f"Received HELLO? from {addr[0]}:{addr[1]}")

                    # Sende die Antwort zurück
                    self.send_response(addr[0], addr[1])
                else:
                    self.logger.warning(f"Unexpected message from {addr[0]}:{addr[1]}: {message}")

            # Starte das UDP-Listening und leite Nachrichten weiter
            self.udp_service.listen(self.star_port, callback=handle_message)
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
            self.udp_service.send_response(response, target_ip, target_port)
        except Exception as e:
            self.logger.error(f"Failed to send response to {target_ip}:{target_port}: {e}")

