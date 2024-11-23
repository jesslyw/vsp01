#Definiert die Peer-Klasse, die die Eigenschaften und Methoden eines Peers repräsentiert.

import random
import time
import threading
from udp_broadcast import UdpBroadcast

class Peer:
    def __init__(self, ip, port, com_uuid):
        self.ip = ip
        self.port = port
        self.com_uuid = com_uuid
        self.is_sol = False
        self.udp_broadcast = None

    def join_star(self):
        self.udp_broadcast = UdpBroadcast(self.port, None, self.com_uuid, self.ip, self.port, self.is_sol)
        managed_to_join_star = self.udp_broadcast.broadcast_and_listen_for_response("HELLO?")
        if managed_to_join_star:
            print("Peer successfully joined the star!")
        else:
            print("Failed to join the star.")
    
    def start_flask(self):
        """Peer-specific flask route or behavior could be added here."""
        pass  # Implement peer-specific Flask routes if needed.

