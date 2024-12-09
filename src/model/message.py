import time


class Message:
    def __init__(self, origin, sender, subject, message, msg_id=None, version=1):
        self.msg_id = msg_id
        self.origin = origin
        self.sender = sender
        self.subject = subject.split('\n', 1)[0].replace('\r', '')  # Kürzen auf die erste Zeile
        self.message = message
        self.version = version
        self.status = "active"
        self.created = int(time.time())  # UNIX-Zeitstempel
        self.changed = self.created

    def update(self, subject, message):
        self.subject = subject.split('\n', 1)[0].replace('\r', '')
        self.message = message
        self.version += 1
        self.changed = int(time.time())

    def mark_deleted(self):
        self.status = "deleted"
        self.changed = int(time.time())

    def to_dict(self, view="header"):
        if view == "header":
            return {
                "msg-id": self.msg_id,
                "version": self.version,
                "status": self.status,
                "origin": self.origin,
                "created": self.created,
                "changed": self.changed,
                "subject": self.subject,
            }
        elif view == "id":
            return {"msg-id": self.msg_id, "status": self.status}
