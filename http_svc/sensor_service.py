import json

CONFIG_FILE='/home/pi/projects/thermo/config.json'

def getSensorConfig():
    return getSensorConfigFile(CONFIG_FILE)

def getSensorConfigFile(path: str):
    with open(path, 'r') as f:
        return json.load(f)

def setSensorTemp(code: str, temp: float, service: str):
    return setSensorTempFile(CONFIG_FILE, code, temp, service)

def setSensorTempFile(path: str, code: str, temp: float, service: str):
    with open(path, 'r') as f:
        config=json.load(f)
        
    config[code]['temp']=temp
    config[code]['service']=service

    with open(path, 'w') as f:
        json.dump(config, f)

    return config[code]
