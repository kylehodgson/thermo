import requests

SERVER="http://linuxdev.local:8888/"

def load_config():
    try:
        response = requests.get(SERVER + "/config")
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("Got unexpected http status for " + SERVER + " in config_http_service.load_config() error: " + e)
        return
    return response.json()
