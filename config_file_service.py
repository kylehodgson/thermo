import json
CONFIGFILE='config.json'
def load_config():
    try:
        with open(CONFIGFILE) as f:
            config=json.load(f)
    except OSError:
        print("Could not read from config.json in config_file_service.load_config")
        return
    return config