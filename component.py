# to run, use flask run --host=192.168.1.11
import hashlib
import random
import threading
import time
from flask import Flask
from dotenv import load_dotenv
from udp_broadcast import UdpBroadcast


'''
a distributed system component
'''

load_dotenv()

app = Flask(__name__)

COM_UUID = str(random.randint(1000, 9999))

is_sol = False

IP = "192.168.1.11"
STARPORT = 8013  # starport 8000 + group nr

# attributes if it becomes SOL
STAR_INITIALIZED_AT = None
STAR_UUID = None
NUM_ACTIVE_COMPONENTS = None
MAX_ACTIVE_COMPONENTS = None
STAR_COMPONENTS = []  # list for all the star's components


# start UDP discovery
udp_broadcast = UdpBroadcast(
    STARPORT, STAR_UUID, COM_UUID, IP, STARPORT, is_sol)


def run_flask():
    app.run(host=IP, port=STARPORT, debug=True)


# Start the Flask app in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

while not is_sol:
    managed_to_join_star = udp_broadcast.broadcast_and_listen_for_response(
        "HELLO?")
    if not managed_to_join_star:
        print("No response from existing SOL, becoming SOL...")

        # become sol
        star_uuid_source = f"{IP}-{COM_UUID}"
        STAR_UUID = hashlib.md5(star_uuid_source.encode()).hexdigest()
        is_sol = True
        STAR_INITIALIZED_AT = time.time()
        NUM_ACTIVE_COMPONENTS = 1
        MAX_ACTIVE_COMPONENTS = 4  # can be overridden via terminal args

        # Add the SOL's own details to the STAR_COMPONENTS list
        component_info = {
            "com_uuid": COM_UUID,
            "ip": IP,
            "starport": STARPORT,
            "time_joined_star": STAR_INITIALIZED_AT,
            "last_interaction_with_star": STAR_INITIALIZED_AT
        }
        STAR_COMPONENTS.append(component_info)

        is_sol = True
        # start UDP discovery as sol
        udp_broadcast = UdpBroadcast(
            STARPORT, STAR_UUID, COM_UUID, IP, STARPORT, is_sol)
        print(f"SOL: Became SOL with STAR_UUID: {STAR_UUID}")
        print(f"SOL: Current active components: {STAR_COMPONENTS}")

        break

flask_thread.join()


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
