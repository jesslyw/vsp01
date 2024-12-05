import threading
import socket
from flask import Flask, request
from src.manager.peer_manager import PeerManager
from src.manager.sol_manager import SolManager
from src.app.config import Config
from src.model.peer import Peer
from src.utils.uuid_generator import UuidGenerator
from src.service.peer_service import PeerService
from src.utils.logger import Logger
from src.service.input_reader import Input_Reader


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
uuid = UuidGenerator.generate_com_uuid()
# Initialize Model, Services and Managers
logger = Logger()
peer = Component(Config.IP, Config.PEER_PORT, UuidGenerator.generate_com_uuid())
peer = Peer(Config.IP, Config.PEER_PORT, uuid)

peer_service = PeerService(peer, logger)

peer_manager = PeerManager(peerService=peer_service)

#start input-reader-thread
reader = Input_Reader(peer_service, peer)
reader_thread = threading.Thread(target=reader.read_input)
reader_thread.start()

peer_manager.manage() #Startet Peer-Manager
