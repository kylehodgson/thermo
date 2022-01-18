#from urllib.request import Request
from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from jinja2 import Template
from fastapi.templating import Jinja2Templates
from zonemgr.models import TemperatureSetting
import zonemgr.room_config_service as Room
import zonemgr.temp_reading_service as TempReading

app = FastAPI()
origins=["http://192.168.2.21"]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
templates = Jinja2Templates(directory="zonemgr/templates")


@app.get("/")
async def root():
    return {"message": "Jello Furled"}

@app.get("/config/")
async def getConfig():
    return Room.getSensorConfig()

@app.get("/config-hx/", response_class=HTMLResponse)
async def getConfig(request: Request):
    return templates.TemplateResponse("configs.jinja", {"request": request, "config": Room.getSensorConfig()})

@app.get("/config/{code}")
async def getConfigFor(code: str):
    return Room.getSensorConfig()[code]

@app.get("/config/{code}/temperature")
async def getTemperatureFor(code: str):
    return Room.getSensorConfig()[code]['temp']

@app.get("/config-hx/{code}/temperature", response_class=HTMLResponse)
async def getTemperatureFor(request: Request, code: str):
    temp = Room.getSensorConfig()[code]['temp']
    return templates.TemplateResponse("conditions.jinja", {"request": Request, "sensor": code, "temperature": temp})

@app.post("/config/")
async def setConfig(p: TemperatureSetting):
    return Room.setSensorTemp(p.code, p.temperature)

@app.post("/config-hx/", response_class=HTMLResponse)
async def setConfig(request: Request, code: str = Form("code"), temperature: str = Form("temperature"), service: str = Form("service")):
    result = Room.setSensorTemp(code, temperature, service)
    config = Room.getSensorConfig()
    return templates.TemplateResponse("configs.jinja", {"request": request, "config": config})

@app.get("/conditions/{code}")
async def getConditions(code: str):
    return TempReading.getTemperatureReading(code)

@app.get("/conditions-hx/{code}", response_class=HTMLResponse)
async def getConditionsFor(request: Request, code: str):
    result = TempReading.getTemperatureReading(code)
    return templates.TemplateResponse("conditions.jinja", {"request": request, "conditions": result, "sensor": code})
