#!/usr/bin/env python
import time
import os
import sys
import asyncio
import datetime
from zonemgr.services.config_db_service import ConfigStore
from zonemgr.services.temp_reading_db_service import TempReadingStore
from zonemgr.db import ZoneManagerDB
from zonemgr.models import SensorConfiguration, TemperatureReading, ServiceTypes
from thermostat.smartplug import SmartPlug

import bleson
from bleson import get_provider, Observer, UUID16
from bleson.logger import log, ERROR, DEBUG, INFO
from discover.goveesensors import GoveeSensorsDiscovery

## if ble advertisements with temperature readings are appearing faster than this rate, ignore them 
## until this many seconds have passed so that the script isnt running constantly
CHECK_INTERVAL = int(5)
## the amount, in celcius, that the temperature may differ from the specified 
## temperature before starting/stopping the heater
ACCEPTABLE_DRIFT = float(1)
## integer of the hour to stop the system when its set to "schedule"
SCHEDULE_STOP = 8
## integer of the hour to start the system when its set to "schedule"
SCHEDULE_START = 22
## integer - the number of seconds that should pass before we write another record to the db
## for a given sensor
TEMPERATURE_RECORD_STEP = 60 * 10

## set the "last reading time" in the past so that the system will start immediately
last_reading_time=int(time.time()) - (CHECK_INTERVAL * 2)

zmdb=ZoneManagerDB()
tempStore=TempReadingStore(zmdb)
configStore=ConfigStore(zmdb)

def schedule_off():
    now = datetime.datetime.now()
    if now.hour > SCHEDULE_STOP and now.hour < SCHEDULE_START:
        return True
    return False

def update_room_state(reading):
    (id,currentConfig)=configStore.get_sensor_config(reading.sensor_id)
    if not currentConfig:
        print(f"Found a new sensor in reading {reading}")
        configStore.create_default_for(reading)

    tr = TemperatureReading(battery=reading.battery, temp=reading.temp, humidity=reading.humidity, sensor_id=reading.sensor_id)
    tempStore.save_if_newer(tr,TEMPERATURE_RECORD_STEP)
    return

def too_soon() -> bool:
    global last_reading_time ## perhaps we ought to be a class so that we dont need globals.
    this_reading_time = int(time.time())
    elapsed = this_reading_time - last_reading_time
    last_reading_time=this_reading_time
    return elapsed < CHECK_INTERVAL

def logtime() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def handle_reading(reading: TemperatureReading, config: SensorConfiguration):
    try:
        plugSvc=SmartPlug(config.plug)
        await plugSvc.update()
    except:
        print(f"[{logtime()}] trouble connecting to plug {config.plug} in location {config.location}")
        return
    
    # if the sensor is configured to be turned off, make sure it is off
    if config.service_type == ServiceTypes.Off and plugSvc.is_off:
        return
    if config.service_type == ServiceTypes.Off  and plugSvc.is_on:
        print(f"[{logtime}] panel in room {config.location} on and should be off, turning it off")
        await plugSvc.turn_off()
        return

    # if the sensors schedule indicates the panel should be turned off, make sure it is off
    if config.service_type == ServiceTypes.Scheduled  and schedule_off() and plugSvc.is_off:
        return
    if config.service_type== ServiceTypes.Scheduled and schedule_off() and plugSvc.is_on:
        print(f"[{logtime}] panel in room {config.location} on off schedule; turning it off")
        await plugSvc.turn_off()
        return

    # sensor enabled, check if temperature is in range
    if plugSvc.is_off and float(reading.temp) < config.temp - float(ACCEPTABLE_DRIFT) :
        print(f"[{logtime}] temp {reading.temp} in room {config.location} is unacceptably cool, turning on panel")
        await plugSvc.turn_on()
    if plugSvc.is_on and float(reading.temp) > config.temp + float(ACCEPTABLE_DRIFT) :
        print(f"[{logtime}] temp {reading.temp} in room {config.location} is unacceptably warm, turning off panel")
        await plugSvc.turn_off()


def on_advertisement(advertisement):

    GOVEE_BT_MAC_OUI_PREFIX = "A4:C1:38"
    H5075_UPDATE_UUID16 = UUID16(0xEC88)

    if advertisement.address.address.startswith(GOVEE_BT_MAC_OUI_PREFIX):
        if H5075_UPDATE_UUID16 in advertisement.uuid16s:
            reading = GoveeSensorsDiscovery.reading_from_advertisement(advertisement)
            if not too_soon():
                print(f"[{logtime()}] sensor_id: {reading.sensor_id} temp: {reading.temp} humidity: {reading.humidity} battery: {reading.battery}")
                update_room_state(reading)
                (id,config)=configStore.get_sensor_config(reading.sensor_id)
                if not config:
                    print(f"[{logtime()}] could not find config for sensor {reading.sensor_id}")
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
            time.sleep(10)  # I don't yet understand why this start/sleep/stop loop is necessary.
            observer.stop() # When I skip the sleep and stop, it forks to the background but doesn't work
    except KeyboardInterrupt:
        try:
            observer.stop()
            sys.exit(0)
        except SystemExit:
            observer.stop()
            os._exit(0)
    return 0


if __name__ == '__main__':
    sys.exit(main())
