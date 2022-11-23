#!/usr/bin/env python
from dataclasses import dataclass
from enum import Enum
import time
import os
import sys
import asyncio
import datetime
from zonemgr.services.config_db_service import ConfigStore
from zonemgr.services.temp_reading_db_service import TempReadingStore
from zonemgr.services.moer_reading_db_service import MoerReadingStore
from zonemgr.db import ZoneManagerDB
from zonemgr.models import SensorConfiguration, TemperatureReading, ServiceType
#from thermostat.smartplug import SmartPlug
import kasa
from bleson import get_provider, Observer, UUID16
from discover.goveesensors import GoveeSensorsDiscovery

## if ble advertisements with temperature readings are appearing faster than this rate, ignore them 
## until this many seconds have passed so that the script isnt running constantly
CHECK_INTERVAL = int(5)
## the amount, in celcius, that the temperature may differ from the specified 
## temperature before starting/stopping the heater
ACCEPTABLE_DRIFT = float(1)
## integer of the hour to stop the system when its set to "schedule"
SCHEDULE_STOP = 10
## integer of the hour to start the system when its set to "schedule"
SCHEDULE_START = 21
## integer - the number of seconds that should pass before we write another record to the db
## for a given sensor
TEMPERATURE_RECORD_STEP = 60 * 10

ECO_REDUCTION=float(.75)


MAXMOER=50

## set the "last reading time" in the past so that the system will start immediately
last_reading_time=int(time.time()) - (CHECK_INTERVAL * 2)

zmdb=ZoneManagerDB()
tempStore=TempReadingStore(zmdb)
configStore=ConfigStore(zmdb)
moerStore=MoerReadingStore(zmdb)

def get_schedule_off():
    now = datetime.datetime.now()
    if now.hour > SCHEDULE_STOP and now.hour < SCHEDULE_START:
        return True
    return False

async def handle_reading(reading: TemperatureReading, config: SensorConfiguration):
    try:
        plugSvc=kasa.SmartPlug(config.plug)
        await plugSvc.update()
    except Exception as err:
        print(f"[{log_time()}] trouble connecting to plug {config.plug} in location {config.location} : {err} {type(err)}")
        return
    panelState=get_panel_state_from(plugSvc)
    ecoMode=get_eco_mode()
    scheduleOff=get_schedule_off()
    decision = get_decision_from(DecisionContext(
        panelState=DecisionContext.get_panel_state(panelState.name),
        serviceType=DecisionContext.get_service_type(config.service_type),
        scheduleOff=scheduleOff,
        readingTemp=reading.temp,
        configTemp=config.temp,
        allowableDrift=ACCEPTABLE_DRIFT,
        ecoMode=ecoMode,
        ecoReduction=ECO_REDUCTION
        ))
    if decision==PanelDecision.DO_NOTHING:
        return
    if decision==PanelDecision.TURN_OFF:
        await plugSvc.turn_off()
        return
    if decision==PanelDecision.TURN_ON:
        await plugSvc.turn_on()
        return

class EcoMode(Enum):
    ENABLED = 1
    DISABLED = 0

class PanelState(Enum):
    ON = 1
    OFF = 0

class PanelDecision(Enum):
    DO_NOTHING = 0
    TURN_ON = 1
    TURN_OFF = 2

@dataclass(frozen=True)
class DecisionContext:
    panelState: PanelState
    serviceType: ServiceType
    scheduleOff: bool
    readingTemp: float
    configTemp: float
    allowableDrift: float
    ecoMode: EcoMode
    ecoReduction: float

    def get_panel_state(value: str) -> PanelState:
        if str(PanelState.OFF.name).lower() == value.lower():
            return PanelState.OFF
        if str(PanelState.ON.name).lower() == value.lower():
            return PanelState.ON
        raise Exception(f"Value {value} is not a valid PanelState.")

    def get_service_type(value: str) -> ServiceType: 
        if str(ServiceType.SCHEDULED.name).lower() == value.lower():
            return ServiceType.SCHEDULED
        if str(ServiceType.OFF.name).lower() == value.lower():
            return ServiceType.OFF
        if str(ServiceType.ON.name).lower() == value.lower():
            return ServiceType.ON
        raise Exception(f"Value {value} is not a valid ServiceType.")

def get_eco_mode() -> EcoMode:
    moer=get_moer()
    if moer>MAXMOER:
        return EcoMode.ENABLED
    return EcoMode.DISABLED

def get_panel_state_from(plugSvc) -> PanelState:
    if plugSvc.is_off: 
        return PanelState.OFF
    if plugSvc.is_on:
        return PanelState.ON

def get_decision_from(context: DecisionContext) -> PanelDecision:
    ## figure out if we should be off based on service type.
    if context.serviceType==ServiceType.OFF and context.panelState.OFF:
        return PanelDecision.DO_NOTHING
    if context.serviceType==ServiceType.OFF and context.panelState.ON:
        return PanelDecision.TURN_OFF
    
    #figrue out if we should be off based on the schedule.
    if context.serviceType==ServiceType.SCHEDULED and context.scheduleOff and context.panelState==PanelState.OFF:
        return PanelDecision.DO_NOTHING
    if context.serviceType==ServiceType.SCHEDULED and context.scheduleOff and context.panelState==PanelState.ON:
        return PanelDecision.TURN_OFF

    #figure out if eco mode is enabled, and add an eco factor if so
    if(context.ecoMode == EcoMode.ENABLED):
        ecoFactor=context.ecoReduction
    else:
        ecoFactor=float(0)    

    # be a thermostat
    if context.panelState == PanelState.OFF and context.readingTemp < context.configTemp - context.allowableDrift - ecoFactor  :
        print(f"[{log_time()}] temp {context.readingTemp} in room {context.configTemp} is unacceptably cool given ecoFactor {ecoFactor} and allowable drift {context.allowableDrift}, turning on panel")
        return PanelDecision.TURN_ON
    if context.panelState == PanelState.ON and context.readingTemp > context.configTemp + context.allowableDrift - ecoFactor :
        print(f"[{log_time()}] temp {context.readingTemp} in room set to {context.configTemp} is unacceptably warm given ecoFactor {ecoFactor} and allowable drift {context.allowableDrift}, turning off panel")
        return PanelDecision.TURN_OFF

    return PanelDecision.DO_NOTHING

def get_moer() -> int:
    moer=moerStore.select_latest_moer_reading(moerStore.get_local_ba_id())
    return int(moer.percent)

### BOTH ###
def log_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

### MAIN ###
def too_soon() -> bool:
    global last_reading_time ## perhaps we ought to be a class so that we dont need globals.
    this_reading_time = int(time.time())
    elapsed = this_reading_time - last_reading_time
    last_reading_time=this_reading_time
    return elapsed < CHECK_INTERVAL

def on_advertisement(advertisement):
    GOVEE_BT_MAC_OUI_PREFIX = "A4:C1:38"
    H5075_UPDATE_UUID16 = UUID16(0xEC88)

    if advertisement.address.address.startswith(GOVEE_BT_MAC_OUI_PREFIX):
        if H5075_UPDATE_UUID16 in advertisement.uuid16s:
            reading = GoveeSensorsDiscovery.reading_from_advertisement(advertisement)
            if not too_soon():
                print(f"[{log_time()}] sensor_id: {reading.sensor_id} temp: {reading.temp} humidity: {reading.humidity} battery: {reading.battery}")
                (id,config)=configStore.get_sensor_config(reading.sensor_id)
                tempStore.save_if_newer(reading,TEMPERATURE_RECORD_STEP)
                if not config:
                    return
                asyncio.run(handle_reading(reading,config))

def main() -> int:
    print("Starting thermo process.")
    try:
        adapter = get_provider().get_adapter()
        observer = Observer(adapter)
        observer.on_advertising_data = on_advertisement
    except Exception as e:
        print(f"Error getting ble adaptor {e}")
        raise

    try:
        while True:
            observer.start()
            time.sleep(1)  # I don't yet understand why this start/sleep/stop loop is necessary.
            observer.stop() # When I skip the sleep and stop, it forks to the background but doesn't work
    except KeyboardInterrupt:
        try:
            print(f"[{log_time()}] Received keyboard interrupt, stopping.")
            observer.stop()
            sys.exit(0)
        except SystemExit:
            observer.stop()
            os._exit(0)

if __name__ == '__main__':
    sys.exit(main())
