import threading
import socket
from flask import Flask, request
from src.manager.peer_manager import PeerManager
from src.manager.sol_manager import SolManager
from config import Config
from src.model.peer import Component
from src.utils.uuid_generator import UuidGenerator
from src.service.peer_service import PeerService
from src.utils.logger import Logger


"""
Dieses Skript startet das Programm. Dazu initialisiert es alle nötigen Datenmodelle und Services.
"""

# Initialize Flask app
app = Flask(__name__)


# Function to run Flask app
def run_flask():
    app.run(host=Config.IP, port=Config.STAR_PORT, debug=True)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()


# Wait for Flask to complete its execution
flask_thread.join()

# Initialize Model, Services and Managers
logger = Logger()
print(Config.IP)
peer = Component(Config.IP, Config.PEER_PORT, UuidGenerator.generate_com_uuid())

peer_service = PeerService(peer, logger)

peer_manager = PeerManager(peerService=peer_service)

peer_manager.manage() #Startet Peer-Manager
#Todo starte Input-Handler