# Definiert die Peer-Klasse, die die Eigenschaften und Methoden eines Peers repräsentiert.
from datetime import datetime


class Peer:
    def __init__(self, ip, port, com_uuid=None, com_tcp=None, status=None):
        self.ip = ip
        self.port = port
        self.com_uuid = com_uuid
        self.com_tcp = com_tcp
        self.is_sol = False
        self.status = status or 200
        self.sol_connection = None
        self.last_interaction_timestamp = None

    class SolConnection:
        def __init__(self, ip, port, uuid, star_uuid):
            self.ip = ip
            self.port = port
            self.uuid = uuid
            self.star_uuid = star_uuid

    def set_last_interaction_timestamp(self):
        self.last_interaction_timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            "ip": self.ip,
            "port": self.port,
            "com_uuid": self.com_uuid,
            "com_tcp": self.com_tcp,
            "status": self.status
        }