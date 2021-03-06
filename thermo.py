#!/usr/bin/env python
import time
import os
import sys
import asyncio
import datetime
from zonemgr.services.config_db_service import ConfigService
from zonemgr.services.temp_reading_db_service import TempReadingService
from zonemgr.db import ZoneManagerDB
from zonemgr.models import SensorConfiguration, TemperatureReading
import bleson
from bleson import get_provider, Observer, UUID16
from bleson.logger import log, ERROR, DEBUG, INFO
from kasa import SmartPlug
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
bleson.logger.set_level(ERROR)
# https://macaddresschanger.com/bluetooth-mac-lookup/A4%3AC1%3A38
# OUI Prefix	Company
# A4:C1:38	Telink Semiconductor (Taipei) Co. Ltd.
GOVEE_BT_mac_OUI_PREFIX = "A4:C1:38"
H5075_UPDATE_UUID16 = UUID16(0xEC88)

## set the "last reading time" in the past so that the system will start immediately
last_reading_time=int(time.time()) - (CHECK_INTERVAL * 2)

zmdb=ZoneManagerDB()
tempsvc=TempReadingService(zmdb)
configsvc=ConfigService(zmdb)

def schedule_off():
    now = datetime.datetime.now()
    if now.hour > SCHEDULE_STOP and now.hour < SCHEDULE_START:
        return True
    return False

def update_room_state(reading):
    (id,currentConfig)=configsvc.get_sensor_config(reading.sensor_id)
    if not currentConfig:
        print(f"Found a new sensor in reading {reading}")
        configsvc.create_default_for(reading)

    tr = TemperatureReading(battery=reading.battery, temp=reading.temp, humidity=reading.humidity, sensor_id=reading.sensor_id)
    tempsvc.save_if_newer(tr,TEMPERATURE_RECORD_STEP)
    return

def too_soon() -> bool:
    global last_reading_time ## perhaps we ought to be a class so that we dont need globals.
    this_reading_time = int(time.time())
    elapsed = this_reading_time - last_reading_time
    last_reading_time=this_reading_time
    return elapsed < CHECK_INTERVAL

def logtime() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def get_plug_for_config(config: SensorConfiguration) -> SmartPlug:
    pass

async def handle_reading(reading: TemperatureReading, config: SensorConfiguration):
    try:
        plug=SmartPlug(config.plug)
        await plug.update()
    except:
        print(f"[{logtime()}] trouble connecting to plug {config.plug} in location {config.location}")
        return
    
    # if the sensor is configured to be turned off, make sure it is off
    if config.service_type.lower()=="off" and plug.is_off:
        return
    if config.service_type.lower()=="off" and plug.is_on:
        print(f"[{logtime}] panel in room {config.location} on and should be off, turning it off")
        await plug.turn_off()
        return

    # if the sensors schedule indicates the panel should be turned off, make sure it is off
    if config.service_type.lower()=="scheduled" and schedule_off() and plug.is_off:
        return
    if config.service_type.lower()=="scheduled" and schedule_off() and plug.is_on:
        print(f"[{logtime}] panel in room {config.location} on off schedule; turning it off")
        await plug.turn_off()
        return

    # sensor enabled, check if temperature is in range
    if plug.is_off and float(reading.temp) < config.temp - float(ACCEPTABLE_DRIFT) :
        print(f"[{logtime}] temp {reading.temp} in room {config.location} is unacceptably cool, turning on panel")
        await plug.turn_on()
    if plug.is_on and float(reading.temp) > config.temp + float(ACCEPTABLE_DRIFT) :
        print(f"[{logtime}] temp {reading.temp} in room {config.location} is unacceptably warm, turning off panel")
        await plug.turn_off()


def on_advertisement(advertisement):
    log.debug(advertisement)
    if advertisement.address.address.startswith(GOVEE_BT_mac_OUI_PREFIX):
        if H5075_UPDATE_UUID16 in advertisement.uuid16s:
            reading = GoveeSensorsDiscovery.reading_from_advertisement(advertisement)
            if not too_soon():
                print(f"[{logtime()}] sensor_id: {reading.sensor_id} temp: {reading.temp} humidity: {reading.humidity} battery: {reading.battery}")
                update_room_state(reading)
                (id,config)=configsvc.get_sensor_config(reading.sensor_id)
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
