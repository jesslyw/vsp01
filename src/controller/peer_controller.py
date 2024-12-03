from flask import Flask, request


class PeerController:
    def __init__(self, service):
        self.service = service
        self.app = Flask(__name__)

    def start_tls_server(self):
        @self.app.route('/register', methods=['POST'])
        def register_with_sol():
            data = request.json
            return self.service.register_with_sol(data)

        self.app.run(port=443, ssl_context=('cert.pem', 'key.pem'))
