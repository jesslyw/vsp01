from flask import Flask
import requests

from utils.logger import global_logger


def send_tcp_request(method, url, body=None, headers=None):
    '''
    send a tcp request to a given url
    '''

    try:
        response = requests.request(method, url, json=body, headers=headers, timeout=5)
        response.raise_for_status()
        global_logger.info(response)
        return response.status_code if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

