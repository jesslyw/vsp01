import os
import threading
import time
from app.config import Config
from flask import after_this_request, request, jsonify
from utils.logger import global_logger

from model.peer import Peer


def initialize_peer_endpoints(app, peer_service):

    def error_response(logger_message, error_message, status_code):
        """Generates a standardized error response."""
        global_logger.error(logger_message)
        return jsonify({"error": error_message}), status_code

    def validate_star_uuid(star_uuid, expected_star_uuid):
        return star_uuid == expected_star_uuid

    @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=["GET"])
    def get_status(com_uuid):
        """
                Retrieves the status of the peer based on the com_uuid.

        """
        com_uuid = int(com_uuid)

        star_uuid = request.args.get(Config.STAR_UUID_FIELD)

        # Validierung
        if not validate_star_uuid(star_uuid, peer_service.peer.star_uuid):
            return error_response(f"Unauthorized access attempt with STAR UUID: {star_uuid}",
                                  "Unauthorized access: Invalid or missing STAR UUID.", 401)
        if com_uuid != peer_service.peer.com_uuid:
            return error_response(
                f"Conflict: Component UUID mismatch. Requested: {com_uuid}, Expected: {peer_service.peer.com_uuid}",
                "Conflict: Component UUID does not match the requested UUID.", 409)

        # Status zurückgeben
        return jsonify({
            "star": peer_service.peer.star_uuid,
            "sol": peer_service.peer.sol_uuid,
            "peer": peer_service.peer.com_uuid,
            "com-ip": peer_service.peer.ip,
            "com-tcp": peer_service.peer.port,
            "status": peer_service.peer.status,
        }), 200

    @app.route(f"{Config.API_BASE_URL}<req_com_uuid>", methods=["DELETE"])
    def accept_sol_shutdown(req_com_uuid):
        req_star_uuid = request.args.get("star")
        req_com_uuid = int(req_com_uuid)

        if (
            req_com_uuid != peer_service.peer.com_uuid
            or req_star_uuid != peer_service.peer.sol_connection.star_uuid
        ):
            return error_response(
                f"Unauthorized shutdown request for STAR UUID: {req_star_uuid}, Component UUID: {req_com_uuid}",
                "Unauthorized request: Mismatched STAR or Component UUID.", 401)

        @after_this_request
        def shutdown(response):
            # Run shutdown in a separate thread to avoid blocking response
            threading.Thread(target=shutdown_system).start()
            return response

        return jsonify({"message": "Shutdown accepted, exiting."}), 200

    def shutdown_system():
        # delay slightly before exiting to ensure response message to sol is sent
        time.sleep(1)
        # Push the Flask application context to the new thread
        with app.app_context():
            global_logger.info("Shutting down system...")
            os._exit(Config.EXIT_CODE_ERROR)
