
import threading

from flasgger import Swagger
from flask import Flask
from manager.peer_manager import PeerManager
from app.config import Config
from model.peer import Peer
from service.peer_service import PeerService
from service.sol_service import SOLService
from service.input_reader import Input_Reader
from controller.controller import initialize_flask_endpoints
import os

from service.message_service import MessageService

"""
Dieses Skript startet das Programm. Dazu initialisiert es alle nötigen Datenmodelle und Services.
"""

# Initialize Flask app
app = Flask(__name__)



swagger = Swagger(app, template_file=os.path.join(os.getcwd(), "docs", "swagger.yml"))


if __name__ == "__main__":
    # Initialize Model, Services and Managers
    peer = Peer(Config.IP, Config.PEER_PORT)

    sol_service = SOLService(peer)

    peer_service = PeerService(peer, sol_service)

    peer_manager = PeerManager(peerService=peer_service)

    message_service= MessageService()

    #start flask-server
    initialize_flask_endpoints(app, peer_service, sol_service, message_service)

    # start input-reader-thread
    reader = Input_Reader(peer_service, peer, message_service)
    reader_thread = threading.Thread(target=reader.read_input)
    reader_thread.start()

    peer_thread = threading.Thread(target=peer_manager.manage)
    peer_thread.start()

    app.run(host=Config.IP, port=Config.STAR_PORT)

