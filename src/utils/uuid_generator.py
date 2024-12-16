import random
import hashlib

class UuidGenerator:
  
    active_com_uuids = set() # track currently active com-uuids 

    @staticmethod
    def generate_com_uuid():
        """
        Generate a unique COM-UUID.
        COM-UUID is a 4-digit number (1000–9999) and must be unique.
        """
        while True:
            com_uuid = random.randint(1000, 9999)
            if com_uuid not in UuidGenerator.active_com_uuids:
                UuidGenerator.active_com_uuids.add(com_uuid)
                return com_uuid

    @staticmethod
    def generate_star_uuid(sol_ip, com_uuid):
        """
        Generate a STAR-UUID using MD5 hash.
        Combines the SOL's IP address, ID, and COM-UUID.
        """
        data = f"{sol_ip}-121-{com_uuid}"
        return str(hashlib.md5(data.encode('utf-8')).hexdigest())
