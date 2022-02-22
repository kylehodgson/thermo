import requests

SERVER="http://linuxdev.local:8888/"

def load_config():
    try:
        response = requests.get(SERVER + "/config")
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Got unexpected http status for {SERVER} in config_http_service.load_config(): {e} ")
    except Exception as e:
        print(f"Could not read from server {SERVER} in config_http_service.load_config(): {e}")
        return
    return response.json()
