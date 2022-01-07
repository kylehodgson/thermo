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
    return config

def is_daytime():
    now = datetime.datetime.now()
    if now.hour > 8 and now.hour < 22:
        return True
    return False

last_reading=int(time.time()) - (CHECK_INTERVAL * 2)
async def process_thermo(reading):
    global last_reading

    this_reading=int(time.time())
    elapsed=this_reading - last_reading

    #print(f"Location: {reading['name']} temp: {reading['temp']} humidity: {reading['humidity']} battery: {reading['battery']}")

    if elapsed < CHECK_INTERVAL:
        return

    SENSORS=load_config()

    if reading['name'] in SENSORS:
        config=SENSORS[reading['name']]
    else:
        return

    p=SmartPlug(config['plug'])
    await p.update()
    logtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if str(config['service'])==str("off") and p.is_on:
        print(f"[{logtime}] panel in room {config['location']} on and should be off, turning it off")
        await p.turn_off()
        return

    if str(config['service'])==str("overnight") and is_daytime() and p.is_off:
        return

    if str(config['service'])==str("overnight") and is_daytime() and p.is_on:
        print(f"[{logtime}] panel in room {config['location']} on during the day; turning it off")
        await p.turn_off()
        return

    if p.is_off and float(reading['temp']) < float(config['temp']) - float(ACCEPTABLE_DRIFT) :
        print(f"[{logtime}] temp {reading['temp']} in room {config['location']} is unacceptably cool, turning on panel")
        await p.turn_on()

    if p.is_on and float(reading['temp']) > float(config['temp']) + float(ACCEPTABLE_DRIFT) :
        print(f"[{logtime}] temp {reading['temp']} in room {config['location']} is unacceptably warm, turning off panel")
        await p.turn_off()
    
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


# ###########################################################################


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
