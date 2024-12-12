import os
import sys
import threading
import socket
from flask import Flask, request
from manager.peer_manager import PeerManager
from app.config import Config
from model.peer import Peer
from service.peer_service import PeerService
from service.sol_service import SOLService
from service.input_reader import Input_Reader
from controller.controller import initialize_flask_endpoints
from utils.logger import global_logger

"""
Dieses Skript startet das Programm. Dazu initialisiert es alle nötigen Datenmodelle und Services.
"""

# Initialize Flask app
app = Flask(__name__)


if __name__ == "__main__":

    shutdown_event = threading.Event()

    # Initialize Model, Services and Managers
    peer = Peer(Config.IP, Config.PEER_PORT)

    sol_service = SOLService(peer)

    peer_service = PeerService(peer, sol_service, shutdown_event)

    peer_manager = PeerManager(peerService=peer_service)

    initialize_flask_endpoints(app, peer_service, sol_service)

    # start input-reader-thread
    reader = Input_Reader(peer_service, sol_service, peer)
    reader_thread = threading.Thread(target=reader.read_input)
    reader_thread.start()

    # start peer thread
    peer_thread = threading.Thread(target=peer_manager.manage)
    peer_thread.start()

    app.run(host=Config.IP, port=Config.STAR_PORT)
