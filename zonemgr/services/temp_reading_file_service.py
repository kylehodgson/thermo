import json

READING_DIR='data/'

def getTemperatureReading(sensor: str):
    if not sensor:
        return False
    filename=READING_DIR + "thermo-state-" + sensor + ".json"
    with open(filename) as f:
        state=json.load(f)
    return state['temp']


