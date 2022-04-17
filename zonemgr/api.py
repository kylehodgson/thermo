from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from zonemgr.models import TemperatureSetting
from zonemgr.services.temp_reading_db_service import TempReadingService
from zonemgr.services.config_db_service import ConfigService
from zonemgr.db import ZoneManagerDB

# poor dev's dependency injection
zmdb=ZoneManagerDB()
configsvc = ConfigService(zmdb)
tempsvc=TempReadingService(zmdb)
templates = Jinja2Templates(directory="zonemgr/templates")

app = FastAPI(root_path="/thermo/api/v1")
origins=["http://192.168.2.36"]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.on_event("shutdown")
def shutdown_event():
    zmdb.shutDown()

@app.get("/thermo/", response_class=HTMLResponse)
async def root():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/config/")
async def getConfig():
    return configsvc.load_config()

@app.get("/config/{code}")
async def getConfigFor(code: str):
    return configsvc.load_config()

@app.get("/config/{code}/temperature")
async def getTemperatureFor(code: str):
    return configsvc.load_config()

@app.post("/config/")
async def setConfig(p: TemperatureSetting):
    return configsvc.set_sensor_config(p.code, p.temperature)

@app.get("/conditions/{code}")
async def getConditions(code: str):
    return tempsvc.getTemperatureReading(code)

@app.get("/config-hx/", response_class=HTMLResponse)
async def getConfig(request: Request):
    return templates.TemplateResponse("configs.jinja", {"request": request, "config": configsvc.load_config()})

@app.post("/config-hx/", response_class=HTMLResponse)
async def setConfig(request: Request, code: str = Form("code"), temperature: str = Form("temperature"), service: str = Form("service")):
    config = configsvc.set_sensor_config(code, temperature, service) 
    return templates.TemplateResponse("configs.jinja", {"request": request, "config": config})

@app.get("/conditions-hx/{code}", response_class=HTMLResponse)
async def getConditionsFor(request: Request, code: str):
    result = tempsvc.getTemperatureReading(code)
    return templates.TemplateResponse("conditions.jinja", {"request": request, "conditions": result, "sensor": code})
