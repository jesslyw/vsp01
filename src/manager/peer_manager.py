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



    """
    Eventuell brauchen wir diese Methode nicht mehr.
    """
    def join_star(self):
        managed_to_join_star = PeerService.broadcast_hello_and_listen_for_sol_response(self.com_uuid, self.ip, self.starport)
        if not managed_to_join_star:
            print("No response from existing SOL, becoming SOL...")
            return False
        return True
