import threading
import time

from src.utils.uuid_generator import UuidGenerator
from src.app.config import Config
from src.service.sol_service import SOLService
class SolManager:
    def __init__(self, sol_service):

        self.sol_service = sol_service


    def manage(self):
        pass
