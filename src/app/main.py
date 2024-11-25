import threading
from flask import Flask
from src.manager.peer_manager import PeerManager
from src.manager.sol_manager import SolManager
from config import Config


"""
Dieses Skript startet das Programm. Dazu initialisiert es alle nötigen Datenmodelle und Services.
"""

# Initialize Flask app
app = Flask(__name__)


# Initialize SolManager and PeerManager
sol_manager = SolManager()
peer_manager = PeerManager()

# Function to run Flask app
def run_flask():
    app.run(host=Config.IP, port=Config.STAR_PORT, debug=True)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Main loop to handle SOL or Peer role initialization
while not sol_manager.is_sol:
    if not peer_manager.join_star():
        print("No response from existing SOL, becoming SOL...")

        # Become SOL by generating unique STAR_UUID and initializing attributes
        sol_manager.become_sol()

        break

# Wait for Flask to complete its execution
flask_thread.join()
