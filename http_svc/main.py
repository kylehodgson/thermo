from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json


class TemperatureSetting(BaseModel):
    code: str
    temperature: float

app = FastAPI()
origins=["http://192.168.2.21"]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

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

@app.get("/")
async def root():
    return {"message": "Jello Furled"}

@app.get("/config/")
async def getConfig():
    return getSensorConfig()

@app.get("/config/{code}")
async def getConfigFor(code: str):
    return getSensorConfig()[code]

@app.post("/config/")
async def setConfig(p: TemperatureSetting):
    print(f"Got a new temperature setting with values {p.code} and {p.temperature}")
    return setSensorTemp(p.code, p.temperature)
