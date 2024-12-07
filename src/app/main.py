import os
import threading
import socket
from flask import Flask, request
from src.manager.peer_manager import PeerManager
from src.manager.sol_manager import SolManager
from src.app.config import Config
from src.model.peer import Peer
from src.utils.uuid_generator import UuidGenerator
from src.service.peer_service import PeerService
from src.service.sol_service import SOLService
from src.utils.logger import Logger
from src.service.input_reader import Input_Reader
from src.controller.controller import initialize_flask_endpoints

"""
Dieses Skript startet das Programm. Dazu initialisiert es alle nötigen Datenmodelle und Services.
"""

# Initialize Flask app
app = Flask(__name__)


# Function to run Flask app
# def run_flask():
#     app.run(host=Config.IP, port=Config.STAR_PORT, debug=True)
#
#
# # Start Flask in a separate thread
# flask_thread = threading.Thread(target=run_flask)
# flask_thread.start()
#
# # Wait for Flask to complete its execution
# flask_thread.join()

# Initialize Model, Services and Managers
peer = Peer(Config.IP, Config.PEER_PORT)

sol_service = SOLService(peer)

peer_service = PeerService(peer, sol_service)

peer_manager = PeerManager(peerService=peer_service)

#start flask-server
initialize_flask_endpoints(app, peer_service, sol_service)
print(Config.IP)
print(Config.STAR_PORT)

# start input-reader-thread
reader = Input_Reader(peer_service, peer)
reader_thread = threading.Thread(target=reader.read_input)
reader_thread.start()

peer_thread = threading.Thread(target=peer_manager.manage)
peer_thread.start()
