from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from models import TemperatureSetting
from jinja2 import Template
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

@app.get("/config-hx/", response_class=HTMLResponse)
async def getConfig():
    with open('show_configs.jinja') as f:
        template = Template(f.read())
    return template.render(config=sensor.getSensorConfig())

@app.get("/config/{code}")
async def getConfigFor(code: str):
    return sensor.getSensorConfig()[code]

@app.get("/config/{code}/temperature")
async def getTemperatureFor(code: str):
    return sensor.getSensorConfig()[code]['temp']

@app.get("/config-hx/{code}/temperature", response_class=HTMLResponse)
async def getTemperatureFor(code: str):
    temp = sensor.getSensorConfig()[code]['temp']
    with open('temperature_input.jinja') as f:
            template = Template(f.read())
    return template.render(temperature=temp, sensor=code)

@app.post("/config/")
async def setConfig(p: TemperatureSetting):
    return sensor.setSensorTemp(p.code, p.temperature)

@app.post("/config-hx/", response_class=HTMLResponse)
async def setConfig(code: str = Form("code"), temperature: str = Form("temperature"), service: str = Form("servicetype")):
    result = sensor.setSensorTemp(code, temperature, service)
    with open('temperature_input.jinja') as f:
        template = Template(f.read())
    return template.render(temperature=result['temp'])

