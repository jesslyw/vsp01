import os
import threading
from src.controller.peer_controller import PeerController
from src.model.peer import Peer
from src.app.config import Config
from src.utils.uuid_generator import UuidGenerator
from src.utils.logger import Logger, global_logger


class PeerManager:
    def __init__(self, peerService):
        self.ip = Config.IP
        self.starport = Config.STAR_PORT
        self.peer = Peer(Config.IP, Config.PEER_PORT, UuidGenerator.generate_com_uuid())
        self.peerService = peerService

    """
    Übernimmt die Verwaltung der Verbindungen des Peers.
    """

    def manage(self):

        # Search for a star
        responses = self.peerService.broadcast_hello_and_initialize()

        #chose star, obtain response
        chosen_response, address = self.peerService.choose_sol(responses)

        #try to register
        registration_response, status = self.peerService.request_registration_with_sol(chosen_response)

        self.peerService.start_peer_api()

        # REST-API für den Peer starten
        try:
            peer_controller = PeerController(self.peerService, self.peer)
            peer_api_thread = threading.Thread(target=peer_controller.start, daemon=True)
            peer_api_thread.start()
        except Exception as e:
            global_logger.error(f"Failed to start listener thread: {e}")

        if status != 200:
            os.abort() #exit program if registration fails

        # Statusmeldung regelmäßig senden
        self.peerService.send_status_update_periodically()
