from src.app.config import Config
from flask import request, jsonify
from src.utils.logger import global_logger
from datetime import datetime


def initialize_flask_endpoints(app, peerService, sol_service):
    @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=["GET"])
    def get_status(com_uuid):
        """
        Behandelt GET-Anfragen für den Status des Peers.
        """
        star_uuid = request.args.get("star")

        # Validierung
        if not star_uuid or star_uuid != peerService.peer.star_uuid:
            return "Unauthorized", 401
        if com_uuid != peerService.peer.com_uuid:
            return "Conflict", 409

        # Status zurückgeben
        return jsonify({
            "star": peerService.peer.star_uuid,
            "sol": peerService.peer.sol_uuid,
            "component": peerService.peer.com_uuid,
            "com-ip": peerService.peer.ip,
            "com-tcp": peerService.peer.port,
            "status": 200,  # Oder der aktuelle Status
        }), 200

    @app.route(f"{Config.API_BASE_URL}<req_com_uuid>?=<req_star_uuid>", methods=['DELETE'])
    def accept_sol_shutdown(req_com_uuid, req_star_uuid):

        if req_com_uuid != peerService.peer.com_uuid or req_star_uuid != peerService.peer.sol_connection.star_uuid:
            return jsonify({"error": "Unexpected request parameters"}), 401

        return jsonify({"message": "Shutdown accepted"}), 200

    @app.route(Config.API_BASE_URL, methods=['POST'])
    def register_component():
        """
        Handles registration of a new component.
        """
        data = request.get_json()

        # Validate data
        star_uuid = data.get(Config.STAR_UUID_FIELD)
        sol_uuid = data.get(Config.SOL_UUID_FIELD)
        component_uuid = data.get(Config.COMPONENT_UUID_FIELD)
        com_ip = data.get(Config.COMPONENT_IP_FIELD)
        com_tcp = data.get(Config.COMPONENT_TCP_FIELD)
        status = data.get(Config.STATUS_FIELD)

        if not all([star_uuid, sol_uuid, component_uuid, com_ip, com_tcp, status]):
            global_logger.error("Missing required fields in registration data.")
            return jsonify({"error": "Missing required fields"}), 400

        if star_uuid != sol_service.star_uuid:
            global_logger.warning(f"Unauthorized registration attempt for STAR {star_uuid}")
            return jsonify({"error": "Unauthorized: STAR UUID mismatch"}), 401

        if len(sol_service.registered_peers) >= Config.MAX_COMPONENTS:
            global_logger.warning("Registration failed: SOL is full.")
            return jsonify({"error": "No room left"}), 403

        if any(comp['component'] == component_uuid for comp in sol_service.registered_peers):
            global_logger.warning(f"Conflict: Component {component_uuid} already registered.")
            return jsonify({"error": "Conflict: Component already registered"}), 409

        component_data = {
            "component": component_uuid,
            "com-ip": com_ip,
            "com-tcp": com_tcp,
            "status": status
        }
        sol_service.registered_peers.append(component_data)
        global_logger.info(f"Component registered successfully: {component_data}")
        return jsonify({"message": "Component registered successfully", "details": component_data}), 200

    @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=['GET'])
    def get_component_status(com_uuid):
        """
        Retrieves the status of a registered component.
        """
        star_uuid = request.args.get(Config.STAR_UUID_FIELD)

        if not star_uuid or star_uuid != sol_service.star_uuid:
            return jsonify({"error": "Unauthorized: STAR UUID mismatch"}), 401

        component = next((comp for comp in sol_service.registered_peers if comp["component"] == com_uuid), None)
        if not component:
            return jsonify({"error": "Component does not exist"}), 404

        return jsonify({
            Config.STAR_UUID_FIELD: sol_service.star_uuid,
            Config.SOL_UUID_FIELD: sol_service.sol_uuid,
            Config.COMPONENT_UUID_FIELD: component["component"],
            Config.COMPONENT_IP_FIELD: component["com-ip"],
            Config.COMPONENT_TCP_FIELD: component["com-tcp"],
            Config.STATUS_FIELD: component["status"]
        }), 200

    @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=['DELETE'])
    def unregister_component(com_uuid):
        """
        Unregisters a registered component from the star.
        """
        star_uuid = request.args.get(Config.STAR_UUID_FIELD)

        if not star_uuid or star_uuid != sol_service.star_uuid:
            global_logger.warning(f"Unauthorized unregister attempt for STAR {star_uuid}")
            return "Unauthorized", 401

        component = next((comp for comp in sol_service.registered_peers if comp["component"] == com_uuid), None)
        if not component:
            global_logger.warning(f"Component {com_uuid} not found for unregister.")
            return "Not found", 404

        requester_ip = request.remote_addr
        if component[Config.COMPONENT_IP_FIELD] != requester_ip:
            global_logger.warning(
                f"Unauthorized unregister attempt from IP {requester_ip} for component {com_uuid}.")
            return "Unauthorized", 401

        component["status"] = "left"
        component["last_interaction_timestamp"] = datetime.now().isoformat()
        sol_service.registered_peers.remove(component)
        global_logger.info(f"Component {com_uuid} unregistered successfully.")
        return "ok", 200

    @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=["PATCH"])
    def update_component_status(com_uuid):
        data = request.get_json()

        # Validierung
        if data["star"] != sol_service.star_uuid or data["sol"] != sol_service.sol_uuid:
            return "Unauthorized", 401

        with sol_service._peers_lock:
            peer = next((p for p in sol_service.registered_peers if p["component"] == com_uuid), None)

        if not peer:
            return "Not Found", 404

        if peer["com-ip"] != data["com-ip"] or peer["com-tcp"] != data["com-tcp"] or data["status"] != 200:
            return "Conflict", 409

        peer["last_interaction_timestamp"] = datetime.now().isoformat()
        peer["status"] = data["status"]
        return "ok", 200