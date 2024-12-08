import os
import threading
import socket
from flask import Flask
from manager.peer_manager import PeerManager
from app.config import Config
from model.peer import Peer
from service.peer_service import PeerService
from service.sol_service import SOLService
from service.input_reader import Input_Reader
from controller.controller import initialize_flask_endpoints

"""
Dieses Skript startet das Programm. Dazu initialisiert es alle nötigen Datenmodelle und Services.
"""

# Initialize Flask app
app = Flask(__name__)

if __name__ == "__main__":

    # parse potential port-argument
    parser = argparse.ArgumentParser()
    parser.add_argument('-port', type=int, required=False)
    args = parser.parse_args()

    if args.port:
        Config.STAR_PORT = args.port

    # Initialize Model, Services and Managers
    peer = Peer(Config.IP, Config.STAR_PORT)

    sol_service = SOLService(peer)

    peer_service = PeerService(peer, sol_service)

    peer_manager = PeerManager(peerService=peer_service)

    #start flask-server
    initialize_flask_endpoints(app, peer_service, sol_service)

    # start input-reader-thread
    reader = Input_Reader(peer_service, peer)
    reader_thread = threading.Thread(target=reader.read_input)
    reader_thread.start()

    peer_thread = threading.Thread(target=peer_manager.manage)
    peer_thread.start()

    app.run(host=Config.IP, port=Config.STAR_PORT)
