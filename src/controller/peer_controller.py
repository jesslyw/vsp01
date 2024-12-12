import os
import threading
import time
from app.config import Config
from flask import after_this_request, request, jsonify
from utils.logger import global_logger

from model.peer import Peer


def initialize_peer_endpoints(app, peer_service):
    @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=["GET"])
    def get_status(com_uuid):
        """
        PEER_API: Behandelt GET-Anfragen für den Status des Peers.
        """
        star_uuid = request.args.get(Config.STAR_UUID_FIELD)

        # Validierung
        if not star_uuid or star_uuid != peer_service.peer.star_uuid:
            return "Unauthorized", 401
        if com_uuid != peer_service.peer.com_uuid:
            return "Conflict", 409

        # Status zurückgeben
        return (
            jsonify(
                {
                    "star": peer_service.peer.star_uuid,
                    "sol": peer_service.peer.sol_uuid,
                    "peer": peer_service.peer.com_uuid,
                    "com-ip": peer_service.peer.ip,
                    "com-tcp": peer_service.peer.port,
                    "status": peer_service.peer.status,
                }
            ),
            200,
        )

    @app.route(f"{Config.API_BASE_URL}<req_com_uuid>", methods=["DELETE"])
    def accept_sol_shutdown(req_com_uuid):
        req_star_uuid = request.args.get("star")
        if (
            req_com_uuid != peer_service.peer.com_uuid
            or req_star_uuid != peer_service.peer.sol_connection.star_uuid
        ):
            return jsonify({"error": "Unexpected request parameters"}), 401

        @after_this_request
        def shutdown(response):
            # global_logger.info("Shutdown accepted, preparing to exit.")
            # Run shutdown in a separate thread to avoid blocking response
            threading.Thread(target=shutdown_system).start()
            return response

        return jsonify({"message": "Shutdown accepted, exiting."}), 200

    def shutdown_system():
        # global_logger.info("Waiting for the response to be sent before shutting down...")
        time.sleep(1)  # Add a small delay before exiting to ensure response is sent

        # Push the Flask application context to the new thread
        with app.app_context():
            global_logger.info("Shutting down system...")
            os._exit(Config.EXIT_CODE_ERROR)  # Exit with the defined error code
