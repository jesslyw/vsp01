#Definiert die Peer-Klasse, die die Eigenschaften und Methoden eines Peers repräsentiert.

import random
import time
import threading

class Peer:
    def __init__(self, ip, port, com_uuid):
        self.ip = ip
        self.port = port
        self.com_uuid = com_uuid
        self.is_sol = False
        self.sol_connection = None

    class SolConnection:
        def __init__(self, ip, port, uuid, star_uuid):
            self.ip = ip
            self.port = port
            self.uuid = uuid
            self.star_uuid = star_uuid
