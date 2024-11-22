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





'''
TODOs aus dem Blatt 
'''
''' stern routes '''

#DONE: POST /vs/v1/system/
#TODO: PATCH /vs/v1/system/<COM-UUID>
#TODO: GET /vs/v1/system/<COM-UUID>?star=<STAR-UUID>
#TODO: DELETE /vs/v1/system/<COM-UUID>?star=<STAR-UUID>

''' messaging routes '''

#TODO: POST /vs/v1/messages/<MSG-UUID>
#TODO: DELETE /vs/v1/messages/<MSG-UUID>?star=<STAR-UUID>
#TODO: GET /vs/v1/messages?star=<STAR-UUID>&scope=<SCOPE>&info=<INFO>
#TODO: GET /vs/v1/messages/<MSG-UUID>?star=<STAR-UUID>
