import os

from src.service.peer_service import PeerService
from src.app.config import Config
from src.utils.uuid_generator import UuidGenerator

class PeerManager:
    def __init__(self, peerService):
        self.ip = Config.IP
        self.starport = Config.STAR_PORT
        self.com_uuid = UuidGenerator.generate_com_uuid
        self.peerService = peerService

    """
    Übernimmt die Verwaltung der Verbindungen des Peers.
    """
    def manage(self):

        #Search for a star
        responses = self.peerService.broadcast_hello_and_initialize()
        chosen_response, address = self.peerService.choose_sol(responses)

        registration_response, status = self.peerService.request_registration_with_sol(
            chosen_response["sol-ip"],
            chosen_response["sol-tcp"],
            chosen_response["star"],
            chosen_response["sol"],
            chosen_response["component"]
        )
        #Todo optimize by using config

        if status != 200:
            os.abort()

        while True:
            self.peerService.send_status_update(chosen_response["sol-ip"], chosen_response["sol-tcp"])
