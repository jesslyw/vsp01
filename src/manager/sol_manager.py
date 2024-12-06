import threading
from src.utils.logger import global_logger


class SolManager:
    def __init__(self, sol_service):

        self.sol_service = sol_service

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
            health_check_thread = threading.Thread(target=self.sol_service.check_peer_health)
            health_check_thread.start()
        except Exception as e:
            global_logger.error(f"Failed to start health-check thread: {e}")
