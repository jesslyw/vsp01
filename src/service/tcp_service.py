from flask import Flask
import requests

def send_tcp_request(method, url, body=None, headers=None):
    ''' 
    send a tcp request to a given url 
    '''
    try:
        response = requests.request(method, url, json=body, headers=headers, timeout=5)
        response.raise_for_status() 
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

app = Flask(__name__)

''' test route '''
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

