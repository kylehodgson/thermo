import json

CONFIG_FILE='/home/pi/projects/thermo/config.json'

def getSensorConfig():
    return getSensorConfigFile(CONFIG_FILE)

def getSensorConfigFile(path: str):
    with open(path, 'r') as f:
        return json.load(f)

def setSensorTemp(code: str, temp: float):
    return setSensorTempFile(CONFIG_FILE, code, temp)

def setSensorTempFile(path: str, code: str, temp: float):
    with open(path, 'r') as f:
        config=json.load(f)
        
    config[code]['temp']=temp

    with open(path, 'w') as f:
        json.dump(config, f)

    return config[code]