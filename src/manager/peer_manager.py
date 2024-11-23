from service.peer_service import PeerService
from app.config import Config
from utils.uuid_generator import UuidGenerator

class PeerManager:
    def __init__(self):
        self.ip = Config.IP
        self.starport = Config.STAR_PORT
        self.com_uuid = UuidGenerator.generate_com_uuid

    def join_star(self):
        managed_to_join_star = PeerService.broadcast_hello_and_listen_for_sol_response(self.com_uuid, self.ip, self.starport)
        if not managed_to_join_star:
            print("No response from existing SOL, becoming SOL...")
            return False
        return True
