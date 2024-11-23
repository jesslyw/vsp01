import threading
from utils.uuid_generator import UuidGenerator
from app.config import Config
from service.sol_service import SolService
class SolManager:
    def __init__(self):

        self.ip = Config.IP
        self.starport = Config.STAR_PORT
        self.com_uuid = UuidGenerator.generate_com_uuid
        self.is_sol = False
        self.star_uuid = None
        self.star_initialized_at = None
        self.num_active_components = None
        self.max_active_components = None
        self.star_components = []
        

    def become_sol(self):
        self.star_uuid = UuidGenerator.generate_star_uuid
        self.is_sol = True
        self.star_initialized_at = time.time()
        self.num_active_components = 1
        self.max_active_components = 4

        component_info = {
            "com_uuid": self.com_uuid,
            "ip": self.ip,
            "starport": self.starport,
            "time_joined_star": self.star_initialized_at,
            "last_interaction_with_star": self.star_initialized_at
        }
        self.star_components.append(component_info)

        print(f"SOL: Became SOL with STAR_UUID: {self.star_uuid}")
        print(f"SOL: Current active components: {self.star_components}")

    def start_discovery(self):
        print("Starting UDP broadcast as SOL...")
        # Start broadcasting and listening for responses
        SolService.listen_for_udp_broadcast_and_respond_with_star_info(self.starport, self.star_uuid, self.com_uuid, self.ip)
    
 
    def start_discovery_in_thread(self):
        # Create a new thread to run the discovery process
        discovery_thread = threading.Thread(target=self.start_discovery)
        discovery_thread.start()