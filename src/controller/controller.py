from app.config import Config
from flask import request, jsonify
from utils.logger import global_logger

from model.peer import Peer


def initialize_flask_endpoints(app, peer_service, sol_service):
    """
    Initializes Flask API endpoints for managing peers and components.
    """

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

    @app.route(f"{Config.API_BASE_URL}<req_com_uuid>?=<req_star_uuid>", methods=['DELETE'])
    def accept_sol_shutdown(req_com_uuid, req_star_uuid):
        """
                Handles the shutdown request for a SOL connection.
        """

        if req_com_uuid != peer_service.peer.com_uuid or req_star_uuid != peer_service.peer.sol_connection.star_uuid:
            return error_response(
                f"Unauthorized shutdown request for STAR UUID: {req_star_uuid}, Component UUID: {req_com_uuid}",
                "Unauthorized request: Mismatched STAR or Component UUID.", 401)

        return jsonify({"message": "Shutdown accepted"}), 200

    @app.route(Config.API_BASE_URL, methods=['POST'])
    def register_component():
        """
        Handles registration of a new peer.
        """
        data = request.get_json()

        # Validate data
        required_fields = [
            Config.STAR_UUID_FIELD,
            Config.SOL_UUID_FIELD,
            Config.COMPONENT_UUID_FIELD,
            Config.COMPONENT_IP_FIELD,
            Config.COMPONENT_TCP_FIELD,
            Config.STATUS_FIELD,
        ]

        if not all(field in data for field in required_fields):
            return error_response(f"Registration attempt failed: Missing fields in data {data}",
                                  "Registration failed: Missing required fields in the request.", 400)

        star_uuid = data[Config.STAR_UUID_FIELD]
        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(f"Unauthorized registration attempt for STAR {star_uuid}",
                                  "Unauthorized: STAR UUID mismatch", 401)

        if len(sol_service.sol.registered_peers) >= Config.MAX_COMPONENTS:
            return error_response(f"Registration failed: SOL is full. Max components: {Config.MAX_COMPONENTS}",
                                  "Registration failed: Maximum number of components reached.", 403)

        if sol_service.sol.find_peer(data[Config.COMPONENT_UUID_FIELD]):
            global_logger.warning()
            return error_response(f"Registration failed: Component is already registered.",
                                  "Conflict: Component {data[Config.COMPONENT_UUID_FIELD]} is already registered.", 409)

        peer = Peer(
            ip=data[Config.COMPONENT_IP_FIELD],
            port=data[Config.COMPONENT_TCP_FIELD],
            com_uuid=data[Config.COMPONENT_UUID_FIELD],
            com_tcp=data[Config.COMPONENT_TCP_FIELD],
            status=data[Config.STATUS_FIELD]
        )
        # TODO: Ist port===com_tcp
        sol_service.sol.add_peer(peer)
        global_logger.info(f"Component registered successfully: {peer}")
        return jsonify({"message": "Component registered successfully", "details": peer.to_dict()}), 200

    @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=['GET'])
    def get_component_status(com_uuid):
        """
        Retrieves the status of a registered peer.
        """
        star_uuid = request.args.get(Config.STAR_UUID_FIELD)

        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(f"Unauthorized status request with STAR UUID: {star_uuid}",
                                  "Access denied: Invalid STAR UUID.", 401)

        peer = sol_service.sol.find_peer(com_uuid)
        if not peer:
            return error_response(f"Status request failed: Component UUID {com_uuid} not found.",
                                  "Component not found: The specified UUID does not exist.", 404)

        peer.set_last_interaction_timestamp()
        return jsonify({
            Config.STAR_UUID_FIELD: sol_service.star_uuid,
            Config.SOL_UUID_FIELD: sol_service.sol_uuid,
            Config.COMPONENT_UUID_FIELD: peer.com_uuid,
            Config.COMPONENT_IP_FIELD: peer.ip,
            Config.COMPONENT_TCP_FIELD: peer.com_tcp,
            Config.STATUS_FIELD: peer.status
        }), 200

    @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=['DELETE'])
    def unregister_component(com_uuid):
        """
        Unregisters a registered peer from the star.
        """
        star_uuid = request.args.get(Config.STAR_UUID_FIELD)
        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(f"Unauthorized unregister attempt with STAR UUID: {star_uuid}",
                                  "Unregister failed: Unauthorized STAR UUID.", 401)

        peer = sol_service.sol.find_peer(com_uuid)
        if not peer:
            return error_response(f"Unregister attempt failed: Component UUID {com_uuid} not found.",
                                  "Unregister failed: The specified component does not exist.", 401)

        requester_ip = request.remote_addr
        if peer.ip != requester_ip:
            return error_response(f"Unregister failed: Unauthorized IP {requester_ip} for component UUID {com_uuid}",
                                  "Unregister failed: Unauthorized IP address.", 404)

        peer.status = "left"
        peer.set_last_interaction_timestamp()
        sol_service.sol.remove_peer(peer)
        global_logger.info(f"Component {com_uuid} unregistered successfully.")
        return "ok", 200

    @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=["PATCH"])
    def update_component_status(com_uuid):
        data = request.get_json()

        # Validierung
        if data[Config.STAR_UUID_FIELD] != sol_service.star_uuid or data[Config.SOL_UUID_FIELD] != sol_service.sol_uuid:
            return error_response(
                f"Unauthorized update request with STAR UUID: {data[Config.STAR_UUID_FIELD]}, SOL UUID: {data[Config.SOL_UUID_FIELD]}",
                "Update failed: Invalid STAR or SOL UUID.", 401)

        peer = sol_service.sol.find_peer(com_uuid)
        if not peer:
            return error_response("Update failed: Component UUID {com_uuid} not found.",
                                  "Update failed: Component does not exist.", 404)

        if peer.ip != data[Config.COMPONENT_IP_FIELD] or peer.com_tcp != data[Config.COMPONENT_TCP_FIELD]:
            return error_response(
                "Conflict: Mismatch in data for Component UUID {com_uuid}. IP: {data[Config.COMPONENT_IP_FIELD]}, TCP: {data[Config.COMPONENT_TCP_FIELD]}",
                "Update failed: Component data does not match the registered details.", 409)

        peer.set_last_interaction_timestamp()
        peer.status = data[Config.STATUS_FIELD]
        return jsonify({"message": "Status updated successfully"}), 200
