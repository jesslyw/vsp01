from flask import Flask, request, jsonify

from src.app.config import Config


class PeerController:
    def __init__(self, service):
        self.service = service
        self.app = Flask(__name__)

        self.create_peer_api()

    def create_peer_api(self):
        @self.app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=["GET"])
        def get_status(com_uuid):
            """
            Behandelt GET-Anfragen für den Status des Peers.
            """
            star_uuid = request.args.get("star")

            # Validierung
            if not star_uuid or star_uuid != self.service.peer.star_uuid:
                return "Unauthorized", 401
            if com_uuid != self.service.peer.com_uuid:
                return "Conflict", 409

            # Status zurückgeben
            return jsonify({
                "star": self.service.peer.star_uuid,
                "sol": self.service.peer.sol_uuid,
                "component": self.service.peer.com_uuid,
                "com-ip": self.service.peer.ip,
                "com-tcp": self.service.peer.port,
                "status": 200,  # Oder der aktuelle Status
            }), 200

        @self.app.route(f"{Config.API_BASE_URL}<req_com_uuid>?=<req_star_uuid>", methods=['DELETE'])
        def accept_sol_shutdown(req_com_uuid, req_star_uuid):

            if req_com_uuid != self.service.peer.com_uuid or req_star_uuid != self.service.peer.sol_connection.star_uuid:
                return jsonify({"error": "Unexpected request parameters"}), 401

            return jsonify({"message": "Shutdown accepted"}), 200

    def start(self):
        """
        Startet die REST-API des Peers.
        """
        self.app.run(host=self.peer.ip, port=self.peer.port, debug=False)
