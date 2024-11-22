import socket
import json

def mock_sol(port=8013):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))
    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode('utf-8').strip('\0')
        if message == "HELLO?":
            response = {
                "star": "test-star-uuid",
                "sol": "test-sol-uuid",
                "sol-ip": "127.0.0.1",
                "sol-tcp": port
            }
            sock.sendto(json.dumps(response).encode('utf-8'), addr)
