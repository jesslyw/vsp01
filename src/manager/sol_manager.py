import threading


class SolManager:
    def __init__(self, sol_service):

        self.sol_service = sol_service


    def manage(self):

        #setting up a thread to listen for Hello?-messages

        # Start a thread to listen for HELLO? messages
        listener_thread = threading.Thread(target=self.sol_service.listen_for_hello)
        listener_thread.start()

        # Start a thread for health checks
        health_check_thread = threading.Thread(target=self.sol_service.check_peer_health)
        health_check_thread.start()
