from flask import Flask, request

class SolController:
    def __init__(self, service):
        self.service = service
        self.app = Flask(__name__)

    def start_tls_server(self):
        @self.app.route('/add_peer', methods=['POST'])
        def add_peer():
            data = request.json
            return self.service.add_peer(data)

        self.app.run(port=443, ssl_context=('cert.pem', 'key.pem'))