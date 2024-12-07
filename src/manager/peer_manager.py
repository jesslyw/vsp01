import os
from utils.logger import global_logger


class PeerManager:
    def __init__(self, peerService):
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

        # REST-API für den Peer starten
        try:
            #peer_controller = PeerController(self.peerService)
            #peer_controller.start()
            pass
        except Exception as e:
            global_logger.error(f"Failed to start listener thread: {e}")

        if status != 200:
            os.abort() #exit program if registration fails

        # Statusmeldung regelmäßig senden
        self.peerService.send_status_update_periodically()
