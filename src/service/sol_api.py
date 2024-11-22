from datetime import datetime

from flask import Flask, request, jsonify


def create_sol_api(sol_service):
    app = Flask(__name__)

    @app.route('/vs/v1/system/', methods=['POST'])
    def register_component():
        """
        Empfängt eine Registrierung für eine neue Komponente und verarbeitet diese.
        Erwartet folgende JSON-Payload:
        {
            "star": <STAR-UUID>,
            "sol": <SOL-UUID>,
            "component": <COM-UUID>,
            "com-ip": <IP>,
            "com-tcp": <PORT>,
            "status": <STATUS>
        }
        """
        data = request.get_json()

        # 1. Daten validieren
        star_uuid = data.get("star")
        sol_uuid = data.get("sol")
        component_uuid = data.get("component")
        com_ip = data.get("com-ip")
        com_tcp = data.get("com-tcp")
        status = data.get("status")

        # Fehlende Felder prüfen
        if not all([star_uuid, sol_uuid, component_uuid, com_ip, com_tcp, status]):
            sol_service.logger.error("Missing required fields in registration data.")
            return jsonify({"error": "Missing required fields"}), 400

        # Prüfen, ob die STAR-UUID mit dem aktuellen Stern übereinstimmt
        if star_uuid != sol_service.star_uuid:
            sol_service.logger.warning(f"Unauthorized registration attempt for STAR {star_uuid}")
            return jsonify({"error": "Unauthorized: STAR UUID mismatch"}), 401

        # Prüfen, ob SOL "voll" ist
        if len(sol_service.registered_components) >= sol_service.max_components:
            sol_service.logger.warning("Registration failed: SOL is full.")
            return jsonify({"error": "No room left"}), 403

        # Prüfen, ob die Komponente bereits registriert ist
        if any(comp['component'] == component_uuid for comp in sol_service.registered_components):
            sol_service.logger.warning(f"Conflict: Component {component_uuid} already registered.")
            return jsonify({"error": "Conflict: Component already registered"}), 409

        # 2. Komponente registrieren #TODO: Eventuell sind hier noch andere Schritte zur Registierung nötig
        component_data = {
            "component": component_uuid,
            "com-ip": com_ip,
            "com-tcp": com_tcp,
            "status": status
        }
        sol_service.registered_peers.append(component_data)

        sol_service.logger.info(f"Component registered successfully: {component_data}")
        return jsonify({"message": "Component registered successfully", "details": component_data}), 200

    @app.route('/vs/v1/system/<com_uuid>', methods=['PATCH'])
    def update_component_status(com_uuid):
        """
        Aktualisiert den Status einer registrierten Komponente.
        """
        data = request.get_json()
        star_uuid = data.get("star")
        sol_uuid = data.get("sol")
        component_uuid = data.get("component")
        com_ip = data.get("com-ip")
        com_tcp = data.get("com-tcp")
        status = data.get("status")

        # Validierung der Daten
        if not all([star_uuid, sol_uuid, component_uuid, com_ip, com_tcp, status]):
            return jsonify({"error": "Missing required fields"}), 400

        # Prüfen, ob die STAR-UUID übereinstimmt
        if star_uuid != sol_service.star_uuid:
            return jsonify({"error": "Unauthorized: STAR UUID mismatch"}), 401

        # Prüfen, ob die Komponente existiert
        component = next((comp for comp in sol_service.registered_components if comp["component"] == com_uuid), None)
        if not component:
            return jsonify({"error": "Component does not exist"}), 404

        # Prüfen, ob die Angaben stimmen
        if component["com-ip"] != com_ip or component["com-tcp"] != com_tcp or status != 200:
            return jsonify({"error": "Conflict: Component data mismatch"}), 409

        # Aktualisieren der Komponente
        component["last_interaction_timestamp"] = datetime.now().isoformat()
        component["status"] = status
        return "ok", 200

    @app.route('/vs/v1/system/<com_uuid>', methods=['GET'])
    def get_component_status(com_uuid):
        """
        Kontrolliert den Status einer registrierten Komponente.
        """
        star_uuid = request.args.get("sol")

        # Validierung
        if not star_uuid or star_uuid != sol_service.star_uuid:
            return jsonify({"error": "Unauthorized: STAR UUID mismatch"}), 401

        # Komponente suchen
        component = next((comp for comp in sol_service.registered_components if comp["component"] == com_uuid), None)
        if not component:
            return jsonify({"error": "Component does not exist"}), 404

        # Status zurückgeben
        return jsonify({
            "star": sol_service.star_uuid,
            "sol": sol_service.sol_uuid,
            "component": component["component"],
            "com-ip": component["com-ip"],
            "com-tcp": component["com-tcp"],
            "status": component["status"]
        }), 200

    return app
