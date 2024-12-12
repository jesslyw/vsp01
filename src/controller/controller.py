# import os
# import threading
# import time
# from app.config import Config
# from flask import after_this_request, request, jsonify
# from utils.logger import global_logger

# from model.peer import Peer


# def initialize_flask_endpoints(app, peer_service, sol_service):
#     @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=["GET"])
#     def get_status(com_uuid):
#         """
#         PEER_API: Behandelt GET-Anfragen für den Status des Peers.
#         """
#         star_uuid = request.args.get(Config.STAR_UUID_FIELD)

#         # Validierung
#         if not star_uuid or star_uuid != peer_service.peer.star_uuid:
#             return "Unauthorized", 401
#         if com_uuid != peer_service.peer.com_uuid:
#             return "Conflict", 409

#         # Status zurückgeben
#         return (
#             jsonify(
#                 {
#                     "star": peer_service.peer.star_uuid,
#                     "sol": peer_service.peer.sol_uuid,
#                     "peer": peer_service.peer.com_uuid,
#                     "com-ip": peer_service.peer.ip,
#                     "com-tcp": peer_service.peer.port,
#                     "status": peer_service.peer.status,
#                 }
#             ),
#             200,
#         )

#     @app.route(f"{Config.API_BASE_URL}<req_com_uuid>", methods=["DELETE"])
#     def accept_sol_shutdown(req_com_uuid):
#         req_star_uuid = request.args.get(
#             "sol"
#         )  # url: changed star to sol to differentiate delete endpoints
#         if (
#             req_com_uuid != peer_service.peer.com_uuid
#             or req_star_uuid != peer_service.peer.sol_connection.star_uuid
#         ):
#             return jsonify({"error": "Unexpected request parameters"}), 401

#         @after_this_request
#         def shutdown(response):
#             # global_logger.info("Shutdown accepted, preparing to exit.")
#             # Run shutdown in a separate thread to avoid blocking response
#             threading.Thread(target=shutdown_system).start()
#             return response

#         return jsonify({"message": "Shutdown accepted, exiting."}), 200

#     def shutdown_system():
#         # global_logger.info("Waiting for the response to be sent before shutting down...")
#         time.sleep(1)  # Add a small delay before exiting to ensure response is sent

#         # Push the Flask application context to the new thread
#         with app.app_context():
#             global_logger.info("Shutting down system...")
#             os._exit(Config.EXIT_CODE_ERROR)  # Exit with the defined error code

#     @app.route(Config.API_BASE_URL, methods=["POST"])
#     def register_component():
#         """
#         Handles registration of a new peer.
#         """
#         data = request.get_json()

#         # Validate data
#         star_uuid = data.get(Config.STAR_UUID_FIELD)
#         sol_uuid = data.get(Config.SOL_UUID_FIELD)
#         component_uuid = data.get(Config.COMPONENT_UUID_FIELD)
#         com_ip = data.get(Config.COMPONENT_IP_FIELD)
#         com_tcp = data.get(Config.COMPONENT_TCP_FIELD)
#         status = data.get(Config.STATUS_FIELD)

#         if not all([star_uuid, sol_uuid, component_uuid, com_ip, com_tcp, status]):
#             global_logger.error("Missing required fields in registration data.")
#             return jsonify({"error": "Missing required fields"}), 400

#         if star_uuid != sol_service.star_uuid:
#             global_logger.warning(
#                 f"Unauthorized registration attempt for STAR {star_uuid}"
#             )
#             return jsonify({"error": "Unauthorized: STAR UUID mismatch"}), 401

#         if len(sol_service.registered_peers) >= Config.MAX_COMPONENTS:
#             global_logger.warning("Registration failed: SOL is full.")
#             return jsonify({"error": "No room left"}), 403

#         if any(
#             p.com_uuid == component_uuid for p in sol_service.registered_peers
#         ):  # TODO: Hier lock einbauen?
#             global_logger.warning(
#                 f"Conflict: Component {component_uuid} already registered."
#             )
#             return jsonify({"error": "Conflict: Component already registered"}), 409

#         peer = Peer(
#             ip=com_ip,
#             port=com_tcp,
#             com_uuid=component_uuid,
#             com_tcp=com_tcp,
#             status=status,
#         )  # TODO: Ist port===com_tcp
#         sol_service.add_peer(peer)
#         global_logger.info(f"Component registered successfully: {peer}")
#         return (
#             jsonify(
#                 {
#                     "message": "Component registered successfully",
#                     "details": peer.to_dict(),
#                 }
#             ),
#             200,
#         )

#     @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=["GET"])
#     def get_component_status(com_uuid):
#         """
#         Retrieves the status of a registered peer.
#         """
#         star_uuid = request.args.get(Config.STAR_UUID_FIELD)

#         if not star_uuid or star_uuid != sol_service.star_uuid:
#             return jsonify({"error": "Unauthorized: STAR UUID mismatch"}), 401

#         peer = next(
#             (p for p in sol_service.registered_peers if p.com_uuid == com_uuid), None
#         )
#         if not peer:
#             return jsonify({"error": "Component does not exist"}), 404

#         peer.set_last_interaction_timestamp()
#         return (
#             jsonify(
#                 {
#                     Config.STAR_UUID_FIELD: sol_service.star_uuid,
#                     Config.SOL_UUID_FIELD: sol_service.sol_uuid,
#                     Config.COMPONENT_UUID_FIELD: peer.com_uuid,
#                     Config.COMPONENT_IP_FIELD: peer.ip,
#                     Config.COMPONENT_TCP_FIELD: peer.com_tcp,
#                     Config.STATUS_FIELD: peer.status,
#                 }
#             ),
#             200,
#         )

#     @app.route(
#         f"{Config.API_BASE_URL}<com_uuid>?star=<req_star_uuid>", methods=["DELETE"]
#     )
#     def unregister_component(com_uuid):
#         """
#         Unregisters a registered peer from the star.
#         """
#         # star_uuid = request.args.get(Config.STAR_UUID_FIELD)
#         star_uuid = star_uuid = request.args.get("star")
#         print(f"request: {star_uuid} sol_service.star_uuid {sol_service.star_uuid}")
#         if not star_uuid or star_uuid != sol_service.star_uuid:
#             global_logger.warning(
#                 f"Unauthorized unregister attempt for STAR {star_uuid}"
#             )
#             return "Unauthorized", 401

#         peer = next(
#             (p for p in sol_service.registered_peers if p.com_uuid == com_uuid), None
#         )  # TODO: Hier mit dem Lock arbeiten?
#         if not peer:
#             global_logger.warning(f"Component {com_uuid} not found for unregister.")
#             return "Not found", 404

#         requester_ip = request.remote_addr
#         if peer.ip != requester_ip:
#             global_logger.warning(
#                 f"Unauthorized unregister attempt from IP {requester_ip} for peer {com_uuid}."
#             )
#             return "Unauthorized", 401

#         peer.status = "left"
#         peer.set_last_interaction_timestamp()
#         sol_service.remove_peer(peer)
#         global_logger.info(f"Component {com_uuid} unregistered successfully.")
#         return "ok", 200

#     @app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=["PATCH"])
#     def update_component_status(com_uuid):
#         data = request.get_json()

#         # Validierung
#         if (
#             data["star"] != sol_service.sol.star_uuid
#             or data["sol"] != sol_service.sol.com_uuid
#         ):
#             return "Unauthorized", 401

#         with sol_service._peers_lock:  # TODO: Auslagern
#             peer = next(
#                 (p for p in sol_service.registered_peers if p.com_uuid == com_uuid),
#                 None,
#             )

#         if not peer:
#             return "Not Found", 404

#         if (
#             peer.ip != data["com-ip"]
#             or peer.com_tcp != data["com-tcp"]
#             or data["status"] != 200
#         ):
#             return "Conflict", 409

#         peer.set_last_interaction_timestamp()
#         peer.status = data["status"]
#         return "ok", 200
