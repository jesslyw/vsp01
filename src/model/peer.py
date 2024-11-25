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
        self.udp_broadcast = None
