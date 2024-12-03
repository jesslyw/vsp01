import os

from src.service.peer_service import PeerService
from src.app.config import Config
from src.utils.uuid_generator import UuidGenerator
from src.utils.logger import Logger

class PeerManager:
    def __init__(self, peerService):
        self.ip = Config.IP
        self.starport = Config.STAR_PORT
        self.com_uuid = UuidGenerator.generate_com_uuid()
        self.peerService = peerService
        self.logger = Logger(self.com_uuid)

    """
    Übernimmt die Verwaltung der Verbindungen des Peers.
    """
    def manage(self):

        #Search for a star
        responses = self.peerService.broadcast_hello_and_initialize()
        chosen_response, address = self.peerService.choose_sol(responses)

        registration_response, status = self.peerService.request_registration_with_sol(chosen_response)

        if status != 200:
            os.abort()

        sol_ip = chosen_response[Config.SOL_IP_FIELD]
        sol_tcp = chosen_response[Config.SOL_TCP_FIELD]
        sol_uuid = chosen_response[Config.SOL_UUID_FIELD]

        while True:
            update_successful = self.peerService.send_status_update(sol_ip, sol_tcp, sol_uuid)
            if not update_successful:
                os.abort()
