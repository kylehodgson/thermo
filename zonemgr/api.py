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

@app.on_event("shutdown")
def shutdown_event():
    zmdb.shutDown()

@app.get("/", response_class=HTMLResponse)
async def root():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/config-hx/", response_class=HTMLResponse)
async def getConfig(request: Request):
    mz_view = get_multizone_view()
    mz_view['request']=request
    return templates.TemplateResponse("configs.jinja", mz_view)

def get_multizone_view():
    sensor_conditions={}
    sensor_configs=configsvc.get_all_sensor_configs()
    for sensor in sensor_configs:
        sensor_conditions[sensor['sensor_id']] = tempsvc.get_latest_temperature_reading_for (sensor['sensor_id'])
    moer = moersvc.select_latest_moer_reading(moersvc.get_local_ba_id())
    return {
        "config": sensor_configs, 
        "moer": moer, 
        "sensor_conditions": sensor_conditions}
            

@app.post("/config-hx/", response_class=HTMLResponse)
async def setConfig(request: Request, sensor_id: str = Form("sensor_id"), temp: str = Form("temp"), service_type: str = Form("service_type")):
    sc = configsvc.set_sensor_config(sensor_id, float(temp), service_type) 
    mz_view = get_multizone_view()
    mz_view['request']=request
    return templates.TemplateResponse("configs.jinja", mz_view)

@app.get("/config-edit-hx/{sensor_id}", response_class=HTMLResponse)
async def getConfigEditorFor(request: Request, sensor_id: str):
    (id,sensor)=configsvc.get_sensor_config(sensor_id)
    return templates.TemplateResponse("edit_config.jinja", {"request": request, "sensor": sensor, "id": id})