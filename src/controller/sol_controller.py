import os
import threading
import time
from app.config import Config
from flask import after_this_request, app, request, jsonify
from utils.logger import global_logger
from model.message import Message

from model.peer import Peer


def initialize_sol_endpoints(app, sol_service, message_service):

    def error_response(logger_message, error_message, status_code):
        """Generates a standardized error response."""
        global_logger.error(logger_message)
        return jsonify({"error": error_message}), status_code

    def validate_star_uuid(star_uuid, expected_star_uuid):
        return star_uuid == expected_star_uuid

    @app.route(Config.API_BASE_URL, methods=["POST"])
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
            return error_response(
                f"Registration attempt failed: Missing fields in data {data}",
                "Registration failed: Missing required fields in the request.",
                400,
            )

        star_uuid = data[Config.STAR_UUID_FIELD]
        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(
                f"Unauthorized registration attempt for STAR {star_uuid}",
                "Unauthorized: STAR UUID mismatch",
                401,
            )

        if len(sol_service.sol.registered_peers) >= Config.MAX_COMPONENTS:
            return error_response(
                f"Registration failed: SOL is full. Max components: {Config.MAX_COMPONENTS}",
                "Registration failed: Maximum number of components reached.",
                403,
            )

        if sol_service.sol.find_peer(data[Config.COMPONENT_UUID_FIELD]):
            global_logger.warning()
            return error_response(
                f"Registration failed: Component is already registered.",
                "Conflict: Component {data[Config.COMPONENT_UUID_FIELD]} is already registered.",
                409,
            )

        peer = Peer(
            ip=data[Config.COMPONENT_IP_FIELD],
            port=data[Config.COMPONENT_TCP_FIELD],
            com_uuid=data[Config.COMPONENT_UUID_FIELD],
            com_tcp=data[Config.COMPONENT_TCP_FIELD],
            status=data[Config.STATUS_FIELD],
        )
        # TODO: Ist port===com_tcp
        sol_service.sol.add_peer(peer)
        global_logger.info(f"Component registered successfully: {peer}")
        return (
            jsonify(
                {
                    "message": "Component registered successfully",
                    "details": peer.com_uuid,
                }
            ),
            200,
        )

    @app.route(f"{Config.API_BASE_URL}/<com_uuid>", methods=["GET"])
    def get_component_status(com_uuid):
        """
        Retrieves the status of a registered peer.
        """
        com_uuid = int(com_uuid)

        star_uuid = request.args.get(Config.STAR_UUID_FIELD)

        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(
                f"Unauthorized status request with STAR UUID: {star_uuid}",
                "Access denied: Invalid STAR UUID.",
                401,
            )

        peer = sol_service.sol.find_peer(com_uuid)
        if not peer:
            return error_response(
                f"Status request failed: Component UUID {com_uuid} not found.",
                "Component not found: The specified UUID does not exist.",
                404,
            )

        peer.set_last_interaction_timestamp()
        return (
            jsonify(
                {
                    Config.STAR_UUID_FIELD: sol_service.star_uuid,
                    Config.SOL_UUID_FIELD: sol_service.sol_uuid,
                    Config.COMPONENT_UUID_FIELD: peer.com_uuid,
                    Config.COMPONENT_IP_FIELD: peer.ip,
                    Config.COMPONENT_TCP_FIELD: peer.com_tcp,
                    Config.STATUS_FIELD: peer.status,
                }
            ),
            200,
        )

    @app.route(f"{Config.API_BASE_URL}/<com_uuid>", methods=["DELETE"])
    def unregister_component(com_uuid):
        """
        Unregisters a registered peer from the star.
        """
        com_uuid = int(com_uuid)

        star_uuid = request.args.get(Config.STAR_UUID_FIELD)
        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(
                f"Unauthorized unregister attempt with STAR UUID: {star_uuid}",
                "Unregister failed: Unauthorized STAR UUID.",
                401,
            )

        peer = sol_service.sol.find_peer(com_uuid)
        if not peer:
            return error_response(
                f"Unregister attempt failed: Component UUID {com_uuid} not found.",
                "Unregister failed: The specified component does not exist.",
                401,
            )

        requester_ip = request.remote_addr
        if peer.ip != requester_ip:
            return error_response(
                f"Unregister failed: Unauthorized IP {requester_ip} for component UUID {com_uuid}",
                "Unregister failed: Unauthorized IP address.",
                404,
            )

        peer.status = "left"
        peer.set_last_interaction_timestamp()
        sol_service.sol.remove_peer(peer)
        global_logger.info(f"Component {com_uuid} unregistered successfully.")
        return "ok", 200

    @app.route(f"{Config.API_BASE_URL}/<com_uuid>", methods=["PATCH"])
    def update_component_status(com_uuid):
        data = request.get_json()
        com_uuid = int(com_uuid)
        # Validierung
        if (
            data[Config.STAR_UUID_FIELD] != sol_service.star_uuid
            or data[Config.SOL_UUID_FIELD] != sol_service.sol_uuid
        ):
            return error_response(
                f"Unauthorized update request with STAR UUID: {data[Config.STAR_UUID_FIELD]}, SOL UUID: {data[Config.SOL_UUID_FIELD]}",
                "Update failed: Invalid STAR or SOL UUID.",
                401,
            )

        peer = sol_service.sol.find_peer(com_uuid)
        if not peer:
            return error_response(
                "Update failed: Component UUID {com_uuid} not found.",
                "Update failed: Component does not exist.",
                404,
            )

        if (
            peer.ip != data[Config.COMPONENT_IP_FIELD]
            or peer.com_tcp != data[Config.COMPONENT_TCP_FIELD]
        ):
            return error_response(
                "Conflict: Mismatch in data for Component UUID {com_uuid}. IP: {data[Config.COMPONENT_IP_FIELD]}, TCP: {data[Config.COMPONENT_TCP_FIELD]}",
                "Update failed: Component data does not match the registered details.",
                409,
            )

        peer.set_last_interaction_timestamp()
        peer.status = data[Config.STATUS_FIELD]
        return jsonify({"message": "Status updated successfully"}), 200

    # TODO: Funktioniert aktuell komplett unabhängig von SOL. In der Aufgabe steht aber, dass nur SOL das kann, also eventuell sol_service.message_service?
    @app.route(f"{Config.API_BASE_URL}/messages", methods=["POST"])
    def create_message():
        data = request.get_json()
        star_uuid = data.get(Config.STAR_UUID_FIELD)
        origin = data.get("origin")
        sender = data.get("sender", "")
        subject = data.get("subject", "")
        message = data.get("message", "")

        # Validierungen
        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(
                f"Unauthorized update request with STAR UUID: {data[Config.STAR_UUID_FIELD]}",
                "Unauthorized: Invalid STAR UUID.",
                401,
            )
        if not origin or not subject.strip():
            return error_response(
                "Precondition failed: Missing required field subject.",
                "Precondition failed: Missing required fields.",
                412,
            )

        # "Die <MSG-UUID> wird im Body immer leer gelassen, weil SOL für die Vergabe zuständig ist." aus der Aufgabe
        # msg_id = data.get("msg-id", "")
        # if not msg_id:
        #     msg_id = message_service.generate_msg_id(origin if "@" not in origin else peer.com_uuid)
        msg_id = message_service.generate_msg_id(
            origin if "@" not in origin else sender
        )

        # Überprüfen, ob die Nachricht existiert
        if msg_id in message_service.messages:
            return error_response(
                f"Conflict: Message ID {msg_id}already exists.",
                "Conflict: Message ID already exists.",
                404,
            )

        new_message = Message(origin, sender, subject, message, msg_id)
        message_service.add_message(new_message)

        # TODO: Sollte hier nochmal last_interaction_timestamp gesetzt werden?

        return jsonify({"msg-id": msg_id}), 200

    @app.route(f"{Config.API_BASE_URL}/messages/<msg_id>", methods=["DELETE"])
    def delete_message(msg_id):
        star_uuid = request.args.get(Config.STAR_UUID_FIELD)
        msg_id = int(msg_id)

        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(
                f"Unauthorized: Invalid STAR UUID {star_uuid}",
                "Unauthorized: Invalid STAR UUID.",
                401,
            )

        if not message_service.delete_message(msg_id):
            return error_response(
                f"Message with ID {msg_id} not found", "Message not found.", 404
            )
        return "ok", 200

    # TODO: "Alle Komponenten, die in den Stern integriert sind – also auch SOL, können die Liste der Nachrichten abfragen." also doch nicht sol_service.message_service?
    @app.route(f"{Config.API_BASE_URL}messages", methods=["GET"])
    def list_messages():
        star_uuid = request.args.get(Config.STAR_UUID_FIELD)
        allowed_scopes = {"active", "all"}
        allowed_views = {"id", "header"}

        scope = request.args.get("scope", "active")
        view = request.args.get("view", "id")

        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(
                f"Unauthorized: Invalid STAR UUID {star_uuid}",
                "Unauthorized: Invalid STAR UUID.",
                401,
            )
        if scope not in allowed_scopes:
            return error_response(
                f"Invalid scope value {scope}", "Invalid scope value.", 400
            )
        if view not in allowed_views:
            return error_response(
                f"Invalid view value {view}", "Invalid view value.", 400
            )

        messages = message_service.list_messages(scope=scope, view=view)
        return (
            jsonify(
                {
                    "star": star_uuid,
                    "totalResults": len(messages),
                    "scope": scope,
                    "view": view,
                    "messages": messages,
                }
            ),
            200,
        )

    @app.route(f"{Config.API_BASE_URL}/messages/<msg_id>", methods=["GET"])
    def get_message(msg_id):
        msg_id = int(msg_id)

        star_uuid = request.args.get(Config.STAR_UUID_FIELD)

        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(
                f"Unauthorized: Invalid STAR UUID {star_uuid}",
                "Unauthorized: Invalid STAR UUID.",
                401,
            )
        if not msg_id:
            return (
                jsonify(
                    {
                        "star": star_uuid,
                        "totalResults": 0,
                        "messages": [],
                    }
                ),
                404,
            )

        message = message_service.get_message(msg_id)
        if not message:
            return (
                jsonify(
                    {
                        "star": star_uuid,
                        "totalResults": 0,
                        "messages": [],
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "star": star_uuid,
                    "totalResults": 1,
                    "messages": [
                        message.to_dict(
                            view="header" if message.status == "active" else "id"
                        )
                    ],
                }
            ),
            200,
        )

    @app.route(f"{Config.API_BASE_URL_STAR}", methods=["GET"])
    def get_star_info(star_uuid):
        """
        Gibt Informationen zu einem spezifischen Stern aus.
        """
        if not validate_star_uuid(star_uuid, sol_service.star_uuid):
            return error_response(
                f"STAR UUID {star_uuid} nicht bekannt", "STAR not found", 404
            )

        return (
            jsonify(
                {
                    "star": star_uuid,
                    "sol": sol_service.peer.com_uuid,
                    "sol-ip": Config.IP,
                    "sol-tcp": sol_service.star_port,
                    "no-com": sol_service.num_active_com,
                    "status": "active",
                }
            ),
            200,
        )

    @app.route(f"{Config.API_BASE_URL_STAR}", methods=["GET"])
    def list_all_stars():
        """
        Gibt alle bekannten Sterne und deren SOL-Komponenten aus.
        """
        stars = [star.to_dict() for star in sol_service.get_star_list()]

        return jsonify({"totalResults": len(stars), "stars": stars}), 200

    @app.route(f"{Config.API_BASE_URL_STAR}/<star_uuid>", methods=["DELETE"])
    def unregister_star(star_uuid):
        """
        Endpunkt, um ein SOL bei einem Star abzumelden.
        """
        star = sol_service.get_star(star_uuid)
        if star is None or star.status != 200 and star.status != '200':
            return error_response(
                f"Unauthorized: STAR not registered {star_uuid}",
                "Unauthorized: Invalid STAR.",
                404,
            )

        if not star.sol_ip == request.remote_addr:
            return error_response(
                f"Unauthorized: Incorrect STAR IP {star_uuid}",
                "Unauthorized: Invalid STAR IP.",
                401,
            )

        # Logge die Abmeldung
        global_logger.info(f"Received unregister request for Star {star_uuid}.")

        # Führe Abmelde-Logik aus (falls erforderlich, z. B. Peer-Status ändern oder SOL entfernen)
        star.status = "unregistered"

        return (
            jsonify(
                {"message": f"Star {star_uuid} successfully unregistered from STAR."}
            ),
            200,
        )

    @app.route(f"{Config.API_BASE_URL_STAR}", methods=["POST"])
    def handle_galaxy_star_entry():
        data = request.get_json()

        response = {
            "star": sol_service.star_uuid,
            "sol": sol_service.sol_uuid,
            "sol-ip": Config.IP,
            "sol-tcp": sol_service.star_port,
            "no-com": sol_service.sol.num_active_components,
            "status": 200,
        }

        star = data.get("star")
        sol = data.get("sol")
        sol_ip = data.get("sol-ip")
        sol_tcp = data.get("sol-tcp")
        no_com = data.get("no-com")
        status = data.get("status")

        sol_service.add_star(star, sol, sol_ip, sol_tcp, no_com, status)

        return jsonify(response), 200

    @app.route(f"{Config.API_BASE_URL_STAR}/<star_uuid>", methods=["PATCH"])
    def handle_galaxy_star_update(star_uuid):
        data = request.get_json()

        sol = data.get("sol")
        sol_ip = data.get("sol-ip")
        sol_tcp = data.get("sol-tcp")
        no_com = data.get("no-com")
        status = data.get("status")

        sol_service.add_star(star_uuid, sol, sol_ip, sol_tcp, no_com, status)

        return jsonify("Patch successful"), 200
