from random import randint

@staticmethod
def generate_uuid():
    uuid = randint(1000,9999)
    list = []
    while uuid in list:
        uuid += 1
    list.append(uuid)
    return uuid