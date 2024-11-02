# to run, use flask run --host=192.168.1.11
from flask import Flask
from dotenv import load_dotenv
from udp_broadcast import UdpBroadcast
import uuid

load_dotenv()

app = Flask(__name__)

# Initialize the component UUID
COM_UUID = str(uuid.uuid4())
is_sol = False
SOL_IP = "192.168.1.11"
STARPORT = 8013

# Generate STAR_UUID only if the component is SOL
if is_sol:
    STAR_UUID = str(uuid.uuid4())
else:
    STAR_UUID = None

# Initialize the UDP broadcast listener
udp_broadcast = UdpBroadcast(
    STARPORT, STAR_UUID, COM_UUID, SOL_IP, STARPORT, is_sol)

if not is_sol:
    udp_broadcast.broadcast_udp_message("HELLO?")
    print("HELLO?")


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
