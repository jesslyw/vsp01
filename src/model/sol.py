# Definiert die Star-Klasse, die den Stern und seine Eigenschaften beschreibt.

# listen_for_incoming_udp_broadcasts()


# set_star_uuid()
# provide_component_uuid()
# monitor_active_components()

import hashlib
import random
import time


class SOL:
    def __init__(self, ip, port, com_uuid):
        self.ip = ip
        self.port = port
        self.com_uuid = com_uuid
        self.is_sol = True
        self.star_uuid = None
        self.num_active_components = None
        self.max_active_components = None
        self.star_initialized_at = None
        self.star_components = []

    def become_sol(self):
        star_uuid_source = f"{self.ip}-{self.com_uuid}"
        self.star_uuid = hashlib.md5(star_uuid_source.encode()).hexdigest()
        self.star_initialized_at = time.time()
        self.num_active_components = 1
        self.max_active_components = 4  # Can be overridden

        component_info = {
            "com_uuid": self.com_uuid,
            "ip": self.ip,
            "starport": self.port,
            "time_joined_star": self.star_initialized_at,
            "last_interaction_with_star": self.star_initialized_at
        }
        self.star_components.append(component_info)

        print(f"SOL: Became SOL with STAR_UUID: {self.star_uuid}")
        print(f"SOL: Current active components: {self.star_components}")

    def start_flask(self):
        """SOL-specific flask route or behavior could be added here."""
        pass  # Implement SOL-specific Flask routes if needed.
