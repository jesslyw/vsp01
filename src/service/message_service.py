from threading import Lock

import requests

from app.config import Config
from utils.logger import global_logger


class MessageService:
    def __init__(self):
        self.messages = {}
        self.nonce = 1
        self.lock = Lock()

    def generate_msg_id(self, com_uuid):
        with self.lock:
            msg_id = f"{self.nonce}@{com_uuid}"
            self.nonce += 1
        return msg_id

    def add_message(self, message):
        if message.msg_id in self.messages:
            raise ValueError("Message ID already exists")
        self.messages[message.msg_id] = message

    def delete_message(self, msg_id):
        if msg_id in self.messages:
            self.messages[msg_id].mark_deleted()
            return True
        return False

    def get_message(self, msg_id):
        return self.messages.get(msg_id)

    def list_messages(self, scope="active", view="id"):
        messages = [
            message.to_dict(view)
            for message in self.messages.values()
            if scope == "all" or message.status == "active"
        ]
        return messages


def send_create_message_request(sol_ip, port, star_uuid, origin, sender, subject, message, msg_id=None):
    """
    Erstellt eine neue Nachricht über die API.
    """
    url = f"http://{sol_ip}:{port}/vs/v1/system/messages"
    data = {
        "star": star_uuid,
        "origin": origin,
        "sender": sender,
        "subject": subject,
        "message": message
    }
    if msg_id:
        data["msg-id"] = msg_id

    try:
        response = requests.post(url, json=data, timeout=5)
        if response.status_code == 200:
            msg_id = response.json().get("msg-id")
            global_logger.info(f"Message created successfully with ID: {msg_id}")
            return msg_id
        elif response.status_code == 401:
            global_logger.warning("Unauthorized: Invalid STAR UUID.")
        elif response.status_code == 412:
            global_logger.warning("Precondition failed: Missing required fields.")
        elif response.status_code == 404:
            global_logger.warning("Conflict: Message ID already exists.")
        else:
            global_logger.warning(f"Unexpected response: {response.status_code} {response.text}")
    except requests.RequestException as e:
        global_logger.error(f"Error creating message: {e}")
    return None


def send_delete_message_request(sol_ip, port, star_uuid, msg_id, ):
    """
    Löscht eine Nachricht über die API.
    """
    url = f"http://{sol_ip}:{port}/vs/v1/system/messages/{msg_id}?star={star_uuid}"

    try:
        response = requests.delete(url, timeout=5)
        if response.status_code == 200:
            global_logger.info(f"Message with ID {msg_id} deleted successfully.")
            return True
        elif response.status_code == 401:
            global_logger.warning("Unauthorized: Invalid STAR UUID.")
        elif response.status_code == 404:
            global_logger.warning("Message not found.")
        else:
            global_logger.warning(f"Unexpected response: {response.status_code} {response.text}")
    except requests.RequestException as e:
        global_logger.error(f"Error deleting message: {e}")
    return False


def send_list_messages_request(sol_ip, port, star_uuid, scope="active", view="id"):
    """
    Ruft die Liste aller Nachrichten ab.
    """
    url = f"http://{sol_ip}:{port}/vs/v1/system/messages?star={star_uuid}&scope={scope}&view={view}"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            messages = response.json().get("messages", [])
            global_logger.info(f"Retrieved {len(messages)} messages.")
            return messages
        elif response.status_code == 401:
            global_logger.warning("Unauthorized: Invalid STAR UUID.")
        else:
            global_logger.warning(f"Unexpected response: {response.status_code} {response.text}")
    except requests.RequestException as e:
        global_logger.error(f"Error listing messages: {e}")
    return []


def send_get_message_request(sol_ip, port, msg_id, star_uuid):
    """
    Ruft eine spezifische Nachricht ab.
    """
    url = f"http://{sol_ip}:{port}/vs/v1/system/messages/{msg_id}?star={star_uuid}"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            message = response.json().get("messages", [])[0]
            global_logger.info(f"Message retrieved successfully: {message}")
            return message
        elif response.status_code == 401:
            global_logger.warning("Unauthorized: Invalid STAR UUID.")
        elif response.status_code == 404:
            global_logger.warning("Message not found.")
        else:
            global_logger.warning(f"Unexpected response: {response.status_code} {response.text}")
    except requests.RequestException as e:
        global_logger.error(f"Error retrieving message: {e}")
    return None
