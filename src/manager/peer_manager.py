import os
import threading
from app.config import Config
from controller import peer_controller
from utils.logger import global_logger


class PeerManager:
    def __init__(self, app, peerService):
        self.peerService = peerService
        self.app = app
        self.is_sol = self.peerService.peer.is_sol

    def run_flask(self):
        self.app.run(host=Config.IP, port=Config.STAR_PORT)

    """
    Übernimmt die Verwaltung der Verbindungen des Peers.
    """

    def manage(self):

        # Search for a star
        responses = self.peerService.broadcast_hello_and_initialize()

        if responses == None:  # if no response, become sol and start the sol controller
            self.is_sol = True
            self.peerService.initialize_as_sol(self.app)

        # chose star, obtain response
        chosen_response, address = self.peerService.choose_sol(responses)

        # try to register
        registration_response, status = self.peerService.request_registration_with_sol(
            chosen_response
        )

        if status != 200:
            os.abort()  # exit program if registration fails

        # registration with star successful
        # initialize peer endpoints and start flask server in a new thread
        peer_controller.initialize_peer_endpoints(self.app, self.peerService)
        flask_thread = threading.Thread(target=self.run_flask)
        flask_thread.daemon = True
        flask_thread.start()

        # Statusmeldung regelmäßig senden
        self.peerService.send_status_update_periodically()
