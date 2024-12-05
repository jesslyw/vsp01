from flask import Flask, request, jsonify
from src.app.config import Config

def create_peer_controller(service, com_uuid, star_uuid):
    app = Flask(__name__)

    @app.route(f"{Config.API_BASE_URL}<req_com_uuid>?=<req_star_uuid>", methods=['DELETE'])
    def accept_sol_shutdown(req_com_uuid, req_star_uuid):

        if req_com_uuid != com_uuid or req_star_uuid != star_uuid:
            return jsonify({"error": "Unexpected request parameters"}), 401

        return jsonify({"message": "Shutdown accepted"}), 200

    return app
