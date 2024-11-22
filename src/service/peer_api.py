from flask import Flask, jsonify, request
import requests


def create_peer_api(peer_service):
    """
    Erstellt die Peer-API für die Kommunikation mit einer SOL-Komponente.

    Args:
        peer_service: Eine Instanz des PeerService, der die API verwendet.

    Returns:
        Flask-App-Instanz.
    """
    app = Flask(__name__)

    @app.route('/vs/v1/register/', methods=['POST'])
    def register_with_sol():
        """
        Registriert den Peer bei einem SOL via POST-Anfrage.

        Erwartet folgende JSON-Payload:
        {
            "sol-ip": <SOL-IP>,
            "sol-tcp": <SOL-PORT>,
            "star": <STAR-UUID>,
            "component": <COM-UUID>,
            "status": <STATUS>
        }

        Returns:
            JSON-Antwort mit entsprechendem Statuscode (200, 401, 403, 409, 500).
        """
        # Extrahiere die Daten aus der Anfrage
        data = request.get_json()
        sol_ip = data.get("sol-ip")
        sol_tcp = data.get("sol-tcp")
        star_uuid = data.get("star")
        component_uuid = data.get("component")
        status = data.get("status", 200)

        # Validierung der erforderlichen Felder
        missing_fields = [field for field in ["sol-ip", "sol-tcp", "star", "component"] if not data.get(field)]
        if missing_fields:
            peer_service.logger.error(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify({"error": "Missing required fields", "fields": missing_fields}), 400

        # Aufbau der Anfrage an die SOL-API
        url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/"
        payload = {
            "star": star_uuid,
            "sol": component_uuid,
            "component": component_uuid,
            "com-ip": peer_service.udp_service.ip,
            "com-tcp": peer_service.udp_service.port,
            "status": status
        }

        try:
            # Logge die Anfrageinformationen
            peer_service.logger.info(f"Sending registration request to SOL at {url} with payload: {payload}")

            # Sende die Anfrage
            response = requests.post(url, json=payload)

            # Verarbeite die Antwort der SOL-API
            if response.status_code == 200:
                peer_service.logger.info(f"Component registered successfully: {response.text}")
                return jsonify({"message": "Registered successfully", "details": response.json()}), 200
            elif response.status_code == 401:
                peer_service.logger.warning(f"Unauthorized: Star UUID mismatch. Response: {response.text}")
                return jsonify({"error": "Unauthorized", "details": response.json()}), 401
            elif response.status_code == 403:
                peer_service.logger.warning(f"Registration failed: SOL is full. Response: {response.text}")
                return jsonify({"error": "SOL is full", "details": response.json()}), 403
            elif response.status_code == 409:
                peer_service.logger.warning(f"Conflict: Component data mismatch. Response: {response.text}")
                return jsonify({"error": "Conflict", "details": response.json()}), 409
            else:
                peer_service.logger.error(f"Unexpected response from SOL: {response.status_code}, {response.text}")
                return jsonify({"error": "Unexpected error", "details": response.text}), response.status_code
        except requests.RequestException as e:
            # Logge Verbindungsfehler
            peer_service.logger.error(f"Failed to connect to SOL at {url}. Error: {e}")
            return jsonify({"error": "Connection error", "details": str(e)}), 500

    return app
