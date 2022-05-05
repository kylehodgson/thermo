from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from zonemgr.models import SensorConfiguration
from zonemgr.services.temp_reading_db_service import TempReadingService
from zonemgr.services.config_db_service import ConfigService
from zonemgr.db import ZoneManagerDB
from discover import discover

# poor dev's dependency injection
zmdb=ZoneManagerDB()
configsvc = ConfigService(zmdb)
tempsvc=TempReadingService(zmdb)
templates = Jinja2Templates(directory="zonemgr/templates")

app = FastAPI()

@app.on_event("shutdown")
def shutdown_event():
    zmdb.shutDown()

@app.get("/", response_class=HTMLResponse)
async def root():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/config/")
async def getConfig():
    return configsvc.load_config()

@app.get("/discover",response_class=HTMLResponse)
async def getDiscoverUI():
    return templates.TemplateResponse("discover.html", {"request": {}})

@app.get("/discover-hx/",response_class=HTMLResponse)
async def getDiscover(request: Request):
    found = await discover.discover_all()
    return templates.TemplateResponse("discover.jinja", {"request": request, "found": found})

@app.get("/config/{sensor_id}")
async def getConfigFor(sensor_id: str):
    return configsvc.load_config()

@app.get("/config/{sensor_id}/temp")
async def getTemperatureFor(sensor_id: str):
    return configsvc.load_config()

# @app.post("/config/")
# async def setConfig(p: SensorConfiguration):
#     return configsvc.set_sensor_config(p.sensor_id, p.temp)

@app.get("/conditions/{sensor_id}")
async def getConditions(sensor_id: str):
    return tempsvc.getTemperatureReading(sensor_id)

@app.get("/config-hx/", response_class=HTMLResponse)
async def getConfig(request: Request):
    return templates.TemplateResponse("configs.jinja", {"request": request, "config": configsvc.load_config()})

@app.post("/config-hx/", response_class=HTMLResponse)
async def setConfig(request: Request, sensor_id: str = Form("sensor_id"), temp: str = Form("temp"), service_type: str = Form("service_type")):
    sc = configsvc.set_sensor_config(sensor_id, float(temp), service_type) 
    return templates.TemplateResponse("configs.jinja", {"request": request, "config": configsvc.load_config()})

@app.get("/conditions-hx/{sensor_id}", response_class=HTMLResponse)
async def getConditionsFor(request: Request, sensor_id: str):
    result = tempsvc.getTemperatureReading(sensor_id)
    return templates.TemplateResponse("conditions.jinja", {"request": request, "conditions": result, "sensor": sensor_id})

