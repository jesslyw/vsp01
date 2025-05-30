import threading
import time
from app.config import Config
from controller import sol_controller
from utils.logger import global_logger
from service.message_service import MessageService
from service.udp_service import UdpService


class SolManager:
    def __init__(self, sol_service, app):

        self.sol_service = sol_service
        self.app = app
        self.message_service = MessageService()

        # initialize sol endpoints and start flask server in a new thread
        sol_controller.initialize_sol_endpoints(
            self.app, self.sol_service, self.message_service
        )

        self.run_flask()


    def run_flask(self):

        flask_thread_1 = threading.Thread(target=self.run_flask_on_port, args=(Config.STAR_PORT,))
        flask_thread_1.daemon = True  # Ensure thread ends when the main program ends
        flask_thread_1.start()

        flask_thread_2 = threading.Thread(target=self.run_flask_on_port, args=(Config.GALAXY_PORT,))
        flask_thread_2.daemon = True  # Ensure thread ends when the main program ends
        flask_thread_2.start()

    def run_flask_on_port(self, port):
        """Run the Flask app on a specific port."""
        self.app.run(host=Config.IP, port=port)

    def manage(self):

        # setting up a thread to listen for Hello?-messages
        try:
            # Start a thread to listen for HELLO? messages
            listener_thread = threading.Thread(
                target=self.sol_service.listen_for_hello, args=(Config.STAR_PORT,)
            )
            listener_thread.start()
        except Exception as e:
            global_logger.error(f"Failed to start listener thread: {e}")

        # setting up a thread to listen for Galaxy Hello?-messages
        try:
            # Start a thread to listen for Galaxy HELLO? messages
            listener_thread = threading.Thread(
                target=self.sol_service.listen_for_hello, args=(Config.GALAXY_PORT,)
            )
            listener_thread.start()
        except Exception as e:
            global_logger.error(f"Failed to start galaxy listener thread: {e}")

        try:
            # Start a thread for health checks
            health_check_thread = threading.Thread(
                target=self.sol_service.check_peer_health
            )
            health_check_thread.start()
        except Exception as e:
            global_logger.error(f"Failed to start health-check thread: {e}")

        for attempt in range(Config.GALAXY_BROADCAST_RETRY_ATTEMPTS):
            # Broadcast Galaxy HELLO?
            global_logger.info("Sending galaxy-broadcast...")
            try:
                UdpService.broadcast_message(
                    Config.GALAXY_PORT, f"HELLO? I AM {self.sol_service.star_uuid}"
                )
            except Exception as e:
                global_logger.error(
                    f"Failed to broadcast Galaxy HELLO?: {self.sol_service.star_uuid}"
                )
                continue

            time.sleep(4)
