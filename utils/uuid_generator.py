from random import randint

def generate_uuid():
    uuid = randint(1000,9999)
    list = []
    while uuid in list:
        uuid += 1
    list.append(uuid)
    return uuid