import threading
from app.config import Config
from controller import sol_controller
from utils.logger import global_logger
from service.message_service import MessageService


class SolManager:
    def __init__(self, sol_service, app):

        self.sol_service = sol_service
        self.app = app
        self.message_service = MessageService()

        # initialize sol endpoints and start flask server in a new thread
        sol_controller.initialize_sol_endpoints(self.app, self.sol_service, self.message_service)
        flask_thread = threading.Thread(target=self.run_flask)
        flask_thread.daemon = (
            True  # This will ensure the thread ends when the main program ends
        )
        flask_thread.start()

    def run_flask(self):
        self.app.run(host=Config.IP, port=Config.STAR_PORT)

    def manage(self):

        # setting up a thread to listen for Hello?-messages
        try:
            # Start a thread to listen for HELLO? messages
            listener_thread = threading.Thread(target=self.sol_service.listen_for_hello)
            listener_thread.start()
        except Exception as e:
            global_logger.error(f"Failed to start listener thread: {e}")

        try:
            # Start a thread for health checks
            health_check_thread = threading.Thread(
                target=self.sol_service.check_peer_health
            )
            health_check_thread.start()
        except Exception as e:
            global_logger.error(f"Failed to start health-check thread: {e}")
