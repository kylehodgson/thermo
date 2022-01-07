#!/usr/bin/env python
import time
import os
import sys
import asyncio
import json
import datetime

from bleson import get_provider, Observer, UUID16
from bleson.logger import log, set_level, ERROR, DEBUG
from kasa import SmartPlug

# Disable warnings
set_level(ERROR)

# # Uncomment for debug log level
#set_level(DEBUG)

# https://macaddresschanger.com/bluetooth-mac-lookup/A4%3AC1%3A38
# OUI Prefix	Company
# A4:C1:38	Telink Semiconductor (Taipei) Co. Ltd.
GOVEE_BT_mac_OUI_PREFIX = "A4:C1:38"
H5075_UPDATE_UUID16 = UUID16(0xEC88)

# ###########################################################################
CHECK_INTERVAL = int(5)
DEFAULT_TEMP = float(20)
ACCEPTABLE_DRIFT = float(1)

def load_config():
    try:
        f = open('config.json')
        config=json.load(f)
        f.close()
    except OSError:
        print("Could not read from config.json in load_config")
        return
    return config

def schedule_off():
    now = datetime.datetime.now()
    if now.hour > 8 and now.hour < 22:
        return True
    return False

def update_room_state(reading):
    return update_room_state_file(reading)

def update_room_state_file(reading):
    import os.path
    from pathlib import Path
    DIR="data/"
    filename=DIR + "thermo-state-" + reading['name'] + ".json"

    if os.path.isfile(filename)==False:
        Path(filename).touch()
        with open(filename, 'w') as f:
            json.dump(reading, f)

    try:
        f = open(filename) 
        last=json.load(f)
        f.close()
    except OSError:
        print(f"Error opening existing file {filename} ..")
        return
    
    if reading['temp']!=last['temp']:
        with open(filename, 'w') as f:
            json.dump(reading, f)
    return

last_reading=int(time.time()) - (CHECK_INTERVAL * 2)
async def process_thermo(reading):
    #update room state with this reading
    update_room_state(reading)
    
    # see if enough time has elapsed since last reading so that we dont just run all the time 
    global last_reading
    this_reading=int(time.time())
    elapsed=this_reading - last_reading
    if elapsed < CHECK_INTERVAL:
        return

    logtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #print(f"[{logtime}] Location: {reading['name']} temp: {reading['temp']} humidity: {reading['humidity']} battery: {reading['battery']}")
    
    SENSORS=load_config()
    if reading['name'] in SENSORS:
        config=SENSORS[reading['name']]
    else:
        return

    try:
        p=SmartPlug(config['plug'])
        await p.update()
    except:
        print(f"[{logtime}] trouble connecting to plug {config['plug']} in {config['location']}")
        return False

    # if the sensor is configured to be turned off, make sure it is off
    if str(config['service'])==str("off") and p.is_on:
        return
    if str(config['service'])==str("off") and p.is_off:
        print(f"[{logtime}] panel in room {config['location']} on and should be off, turning it off")
        await p.turn_off()
        return

    # if the sensors schedule indicates the panel should be turned off, make sure it is off
    if str(config['service'])==str("scheduled") and schedule_off() and p.is_off:
        return
    if str(config['service'])==str("scheduled") and schedule_off() and p.is_on:
        print(f"[{logtime}] panel in room {config['location']} on off schedule; turning it off")
        await p.turn_off()
        return

    # sensor enabled, check if temperature is in range
    if p.is_off and float(reading['temp']) < float(config['temp']) - float(ACCEPTABLE_DRIFT) :
        print(f"[{logtime}] temp {reading['temp']} in room {config['location']} is unacceptably cool, turning on panel")
        await p.turn_on()
    if p.is_on and float(reading['temp']) > float(config['temp']) + float(ACCEPTABLE_DRIFT) :
        print(f"[{logtime}] temp {reading['temp']} in room {config['location']} is unacceptably warm, turning off panel")
        await p.turn_off()
   
    # update reading time
    last_reading=this_reading

def reading_from_advertisement(advertisement):
    mfg_data='{:>7}'.format(int(advertisement.mfg_data.hex()[6:12],16))
    temperature=float(mfg_data[0:4])/10
    humidity=float(mfg_data[4:7])/10
    battery = int(advertisement.mfg_data.hex()[12:14], 16)
    return {'name': str(advertisement._name), 'temp': float(temperature), 'battery': int(battery), 'humidity': float(humidity)}

# On BLE advertisement callback
def on_advertisement(advertisement):
    log.debug(advertisement)

    if advertisement.address.address.startswith(GOVEE_BT_mac_OUI_PREFIX):
        if H5075_UPDATE_UUID16 in advertisement.uuid16s:
            reading = reading_from_advertisement(advertisement)
            asyncio.run(process_thermo(reading))


adapter = get_provider().get_adapter()
observer = Observer(adapter)
observer.on_advertising_data = on_advertisement

try:
    while True:
        observer.start()
        time.sleep(2)
        observer.stop()
except KeyboardInterrupt:
    try:
        observer.stop()
        sys.exit(0)
    except SystemExit:
        observer.stop()
        os._exit(0)
