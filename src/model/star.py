class Star:
    def __init__(self, star_uuid, sol_uuid, sol_ip, sol_tcp, no_com, status):
        self.star_uuid = star_uuid
        self.sol_uuid = sol_uuid
        self.sol_ip = sol_ip
        self.sol_tcp = sol_tcp
        self.no_com = no_com
        self.status = status

    def to_dict(self):
        return {
            "star": self.star_uuid,
            "sol": self.sol_uuid,
            "sol-ip": self.sol_ip,
            "sol-tcp": self.sol_tcp,
            "no-com": self.no_com,
            "status": self.status
        }