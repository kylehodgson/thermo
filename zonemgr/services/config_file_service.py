import json
CONFIGFILE='config.json'

def load_config():
    try:
        with open(CONFIGFILE) as f:
            config=json.load(f)
    except OSError as e:
        print(f"Could not read from config.json in config_file_service.load_config: {e}")
        return
    except ValueError as e:
        print(f"Could not read from config.json in config_file_service.load_config: {e}")
        return
    return config

def set_sensor_config(sensor: str, temp: float, service: str):
    config=load_config()
    config[sensor]['temp']=temp
    config[sensor]['service']=service
    try:
        with open(CONFIGFILE, 'w') as f:
            json.dump(config, f)
    except OSError as e:
        print(f"Could not write to config.json in config_file_service.set_sensor_config: {e}")
        return
    except ValueError as e:
        print(f"Could not read from config.json in config_file_service.load_config: {e}")
        return
    return config[sensor]
