import argparse
import os
import threading
from flasgger import Swagger
from flask import Flask
from manager.peer_manager import PeerManager
from app.config import Config
from model.peer import Peer
from service.peer_service import PeerService
from service.sol_service import SolService
from service.input_reader import Input_Reader

import os

"""
Dieses Skript startet das Programm. Dazu initialisiert es alle nötigen Datenmodelle und Services.
"""

# Initialize Flask app
app = Flask(__name__)

swagger = Swagger(app, template_file=os.path.join(os.getcwd(), "docs", "swagger.yml"))

if __name__ == "__main__":

    # parse potential port-argument
    parser = argparse.ArgumentParser()
    parser.add_argument('-spt', type=int, required=False)  # spt = star port
    parser.add_argument('-gpt', type=int, required=False)  # gpt = galaxy port
    args = parser.parse_args()

    if args.spt:
        Config.STAR_PORT = args.spt

    if args.gpt:
        Config.GALAXY_PORT = args.gpt

    # Initialize Model, Services and Managers
    peer = Peer(Config.IP, Config.STAR_PORT)

    sol_service = SolService(peer)

    peer_service = PeerService(peer, sol_service)

    peer_manager = PeerManager(app, peerService=peer_service)

    # start input-reader-thread
    reader = Input_Reader(peer_service, sol_service, peer)
    reader_thread = threading.Thread(target=reader.read_input)
    reader_thread.start()

    # start peer manager thread
    peer_manager_thread = threading.Thread(target=peer_manager.manage)
    peer_manager_thread.start()
