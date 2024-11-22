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
        sol_service.registered_components.append(component_data)

        sol_service.logger.info(f"Component registered successfully: {component_data}")
        return jsonify({"message": "Component registered successfully", "details": component_data}), 200

    return app
