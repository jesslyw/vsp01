import requests

#send tcp Methode request, type, endpoint, body
def send_tcp_request(method, url, body, type):
    try:
        response = requests.request(method, url, data=body, headers={'Content-Type': type})
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(e)


def register_component_in_sol(self, sol_ip, sol_tcp, star, sol, com_uuid, ip, port, status):
    sol_url = f"http://{sol_ip}:{sol_tcp}/vs/v1/system/"
    # format data as text/plain
    post_data = (
        f"star: {star}\n"
        f"sol: {sol}\n"
        f"component: {com_uuid}\n"
        f"com-ip: {ip}\n"git branch --set-upstream-to=origin/<branch> feature/restructure
        f"com-tcp: {port}\n"
        f"status: {status}"
    )
    try:
        post_response = requests.post(sol_url, data=post_data, headers={
            'Content-Type': 'text/plain'})
        return post_response.status_code
    except requests.Timeout:
        print(f"Timeout occurred while trying to reach {sol_url}")
        return None

#need to listen for response from SOL

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"