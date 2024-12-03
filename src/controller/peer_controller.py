from flask import Flask, request, jsonify

from src.app.config import Config


class PeerController:
    def __init__(self, service, peer):
        self.service = service
        self.app = Flask(__name__)
        self.peer = peer

        self.create_peer_api()

    def create_peer_api(self):
        @self.app.route(f"{Config.API_BASE_URL}<com_uuid>", methods=["GET"])
        def get_status(com_uuid):
            """
            Behandelt GET-Anfragen für den Status des Peers.
            """
            star_uuid = request.args.get("star")

            # Validierung
            if not star_uuid or star_uuid != self.peer.star_uuid:
                return "Unauthorized", 401
            if com_uuid != self.peer.com_uuid:
                return "Conflict", 409

            # Status zurückgeben
            return jsonify({
                "star": self.peer.star_uuid,
                "sol": self.peer.sol_uuid,
                "component": self.peer.com_uuid,
                "com-ip": self.peer.ip,
                "com-tcp": self.peer.port,
                "status": 200,  # Oder der aktuelle Status
            }), 200

    def start_tls_server(self):
        @self.app.route('/register', methods=['POST'])
        def register_with_sol():
            data = request.json
            return self.service.register_with_sol(data)

        self.app.run(port=443, ssl_context=('cert.pem', 'key.pem'))

    def start(self):
        """
        Startet die REST-API des Peers.
        """
        self.app.run(host=self.peer.ip, port=self.peer.port, debug=False)