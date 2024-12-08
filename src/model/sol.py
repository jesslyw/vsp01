# Definiert die Star-Klasse, die den Stern und seine Eigenschaften beschreibt.

class SOL:
    def __init__(self, com_uuid, star_uuid):
        self.ip = None
        self.port = None
        self.com_uuid = com_uuid
        self.is_sol = True
        self.star_uuid = star_uuid
        self.num_active_components = None
        self.max_active_components = None
        self.sol_initialized_at = None