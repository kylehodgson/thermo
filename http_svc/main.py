from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import TemperatureSetting
import sensor_service as sensor

app = FastAPI()
origins=["http://192.168.2.21"]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])


@app.get("/")
async def root():
    return {"message": "Jello Furled"}

@app.get("/config/")
async def getConfig():
    return sensor.getSensorConfig()

@app.get("/config/{code}")
async def getConfigFor(code: str):
    return sensor.getSensorConfig()[code]

@app.post("/config/")
async def setConfig(p: TemperatureSetting):
    return sensor.setSensorTemp(p.code, p.temperature)
