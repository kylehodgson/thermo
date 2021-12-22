#!/usr/bin/env python

import time
import os
import sys
import asyncio

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
FORMAT_PRECISION = ".2f"

check_interval=int(5)
last_reading=int(time.time()) - (check_interval * 2)
async def process_thermo(reading):
    global last_reading, check_interval

    this_reading=int(time.time())
    elapsed=this_reading - last_reading

    if elapsed < check_interval:
        return
    
    if reading['name']=="GVH5075_E666":
        location="office"
    else:
        location="garage"

    if location=="garage":
        return

    print(f"Location: {location} temp: {reading['temp']} humidity: {reading['humidity']} battery: {reading['battery']}")
    
    desired=float(21)
    acceptable_drift=float(1)
    heater_ip="192.168.2.46"
    
    p=SmartPlug(heater_ip)
    await p.update()
    
    if reading['name']=='GVH5075_E666' and p.is_off and float(reading['temp']) < desired-acceptable_drift :
        print(f"temp {reading['temp']} is unacceptably cool, turning on panel")
        await p.turn_on()

    if reading['name']=='GVH5075_E666' and p.is_on and float(reading['temp']) > desired+acceptable_drift :
        print(f"temp {reading['temp']} is unacceptably warm, turning off panel")
        await p.turn_off()
    
    last_reading=this_reading

# Decode H5075 Temperature into degrees Celcius
def decode_temp_in_c(encoded_data):
    return format((encoded_data / 10000), FORMAT_PRECISION)


# Decode H5075 Temperature into degrees Fahrenheit
def decode_temp_in_f(encoded_data):
    return format((((encoded_data / 10000) * 1.8) + 32), FORMAT_PRECISION)


# Decode H5075 percent humidity
def decode_humidity(encoded_data):
    return format(((encoded_data % 1000) / 10), FORMAT_PRECISION)

# On BLE advertisement callback
def on_advertisement(advertisement):
    log.debug(advertisement)

    if advertisement.address.address.startswith(GOVEE_BT_mac_OUI_PREFIX):
        mac = advertisement.address.address
        if H5075_UPDATE_UUID16 in advertisement.uuid16s:
            encoded_data = int(advertisement.mfg_data.hex()[6:12], 16)
            battery = int(advertisement.mfg_data.hex()[12:14], 16)
            
            reading={'name': str(advertisement._name), 'temp': float(decode_temp_in_c(encoded_data)), 'battery': float(battery), 'humidity': float(decode_humidity(encoded_data))}
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
