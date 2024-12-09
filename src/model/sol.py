# Definiert die Star-Klasse, die den Stern und seine Eigenschaften beschreibt.
from threading import Lock


class SOL:
    def __init__(self, com_uuid, star_uuid):
        self.ip = None
        self.port = None
        self.com_uuid = com_uuid
        self.is_sol = True
        self.star_uuid = star_uuid
        self.num_active_components = None
        self.max_active_components = None
        self.sol_initialized_at = None
        self.registered_peers = []
        self.peers_lock = Lock()

    def add_peer(self, peer):
        with self.peers_lock:
            self.registered_peers.append(peer)

    def remove_peer(self, peer):
        with self.peers_lock:
            self.registered_peers.remove(peer)

    def find_peer(self, com_uuid):
        with self.peers_lock:
            return next((p for p in self.registered_peers if p.com_uuid == com_uuid), None)

