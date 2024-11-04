#Implementiert die TCP- und UDP-Kommunikation.
import socket
from app.config import Config
from utils.logger import Logger

class DiscoveryService:
    def __init__(self):
        self.star_port = Config.STAR_PORT
        self.broadcast_interval = Config.BROADCAST_INTERVAL
        self.logger = Logger()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def broadcast_hello(self):
        """Sendet in regelmäßigen Abständen Broadcast-Meldungen, um andere Peers zu finden."""
        try:
            self.logger.info("Starte Broadcast von HELLO-Nachrichten...")
            message = "HELLO?".encode('utf-8')
            self.sock.sendto(message, ('<broadcast>', self.star_port))
            self.logger.info("HELLO-Nachricht gesendet.")
        except Exception as e:
            self.logger.error(f"Fehler beim Broadcast: {e}")

    def listen_for_hello(self):
        """Hört auf eingehende HELLO-Nachrichten von anderen Peers."""
        try:
            self.sock.bind(('', self.star_port))
            self.logger.info(f"Hört auf Port {self.star_port} nach HELLO-Nachrichten...")
            while True:
                data, addr = self.sock.recvfrom(1024)
                self.logger.info(f"HELLO-Nachricht empfangen von {addr}: {data.decode()}")
        except Exception as e:
            self.logger.error(f"Fehler beim Empfang von Nachrichten: {e}")
