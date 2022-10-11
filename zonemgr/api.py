from urllib import response
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from zonemgr.models import MoerReading, MoerReadingFrom
from zonemgr.services.plug_db_service import PlugService
from zonemgr.services.temp_reading_db_service import TempReadingStore
from zonemgr.services.config_db_service import ConfigStore
from zonemgr.services.moer_reading_db_service import MoerReadingStore
from zonemgr.db import ZoneManagerDB
from thirdparty.watttime.WattTimeAPI import WattTime
# from discover import discover

# poor dev's dependency injection
zmdb=ZoneManagerDB()
configsvc = ConfigStore(zmdb)
tempsvc=TempReadingStore(zmdb)
moersvc=MoerReadingStore(zmdb)
plugsvc=PlugService(zmdb)
templates = Jinja2Templates(directory="zonemgr/templates")


WATTTIMEUSERNAME="longbranchflyer"
WATTTIMEPASSWORD="AJqPC4aXQLo*gm8mQEoWHcWK"

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    wt=WattTime(WATTTIMEUSERNAME, WATTTIMEPASSWORD)
    reading_json=wt.get_index_json(moersvc.get_local_ba_id())
    moer_reading=MoerReadingFrom(reading_json)
    moersvc.save_if_newer(moer_reading,10)

@app.on_event("shutdown")
def shutdown_event():
    zmdb.shutDown()

@app.get("/", response_class=HTMLResponse)
async def root():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/config/")
async def getConfig():
    return configsvc.load_config()

# @app.get("/discover",response_class=HTMLResponse)
# async def getDiscoverUI():
#     return templates.TemplateResponse("discover.html", {"request": {}})

# @app.get("/discover-hx/",response_class=HTMLResponse)
# async def getDiscover(request: Request):
#     found = await discover.discover_all(plugsvc)
#     return templates.TemplateResponse("discover.jinja", {"request": request, "found": found})

@app.get("/config/{sensor_id}")
async def getConfigFor(sensor_id: str):
    return configsvc.load_config()

@app.get("/config/{sensor_id}/temp")
async def getTemperatureFor(sensor_id: str):
    return configsvc.load_config()

@app.get("/conditions/{sensor_id}")
async def getConditions(sensor_id: str):
    return tempsvc.getTemperatureReading(sensor_id)

@app.get("/config-hx/", response_class=HTMLResponse)
async def getConfig(request: Request):
    (moer,reading_time) = moersvc.select_latest_moer_reading(moersvc.get_local_ba_id())
    return templates.TemplateResponse("configs.jinja", {"request": request, "config": configsvc.load_config(), "moer": moer})

@app.post("/config-hx/", response_class=HTMLResponse)
async def setConfig(request: Request, sensor_id: str = Form("sensor_id"), temp: str = Form("temp"), service_type: str = Form("service_type")):
    sc = configsvc.set_sensor_config(sensor_id, float(temp), service_type) 
    (moer,reading_time) = moersvc.select_latest_moer_reading(moersvc.get_local_ba_id())
    return templates.TemplateResponse("configs.jinja", {"request": request, "config": configsvc.load_config(), "moer": moer})

@app.get("/conditions-hx/{sensor_id}", response_class=HTMLResponse)
async def getConditionsFor(request: Request, sensor_id: str):
    result = tempsvc.getTemperatureReading(sensor_id)
    return templates.TemplateResponse("conditions.jinja", {"request": request, "conditions": result, "sensor": sensor_id})

@app.get("/moer-hx/", response_class=HTMLResponse)
async def getCurrentMoer(request: Request):
    (result,reading_time) = moersvc.select_latest_moer_reading(moersvc.get_local_ba_id())
    print(f"result from moersvc was {result}")
    return templates.TemplateResponse("moer.jinja", {"request": request, "moer": result})

@app.get("/config-edit-hx/{sensor_id}", response_class=HTMLResponse)
async def getConfigEditorFor(request: Request, sensor_id: str):
    (id,sensor)=configsvc.get_sensor_config(sensor_id)
    return templates.TemplateResponse("edit_config.jinja", {"request": request, "sensor": sensor, "id": id})