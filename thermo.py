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

govee_devices = {}

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
    
    last_reading=this_reading
    print(f"Location: {location} temp: {reading['temp']} humidity: {reading['humidity']} battery: {reading['battery']}")

    if location=="garage":
        return
    
    desired=float(20)
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

# Decode H5075 Temperature into degrees Celcius
def decode_temp_in_c(encoded_data):
    return format((encoded_data / 10000), FORMAT_PRECISION)


# Decode H5075 Temperature into degrees Fahrenheit
def decode_temp_in_f(encoded_data):
    return format((((encoded_data / 10000) * 1.8) + 32), FORMAT_PRECISION)


# Decode H5075 percent humidity
def decode_humidity(encoded_data):
    return format(((encoded_data % 1000) / 10), FORMAT_PRECISION)


def print_values(mac):
    govee_device = govee_devices[mac]
    print(
        f"{govee_device['name']} ({govee_device['address']}) - \
Temperature {govee_device['tempInC']}C / {govee_device['tempInF']}F  - \
Humidity: {govee_device['humidity']}% - \
Battery:  {govee_device['battery']}%"
    )


def print_rssi(mac):
    govee_device = govee_devices[mac]
    outstr=""
    if "rssi" in govee_device.keys():
        outstr+=" RSSI: " + str(govee_device['rssi'])
    if "address" in govee_device.keys():
        outstr+=" Address: " + str(govee_device['address'])
    print(outstr)


# On BLE advertisement callback
def on_advertisement(advertisement):
    log.debug(advertisement)

    if advertisement.address.address.startswith(GOVEE_BT_mac_OUI_PREFIX):
        mac = advertisement.address.address

        if mac not in govee_devices:
            govee_devices[mac] = {}
        if H5075_UPDATE_UUID16 in advertisement.uuid16s:
            name = advertisement._name
            encoded_data = int(advertisement.mfg_data.hex()[6:12], 16)
            battery = int(advertisement.mfg_data.hex()[12:14], 16)
            # govee_devices[mac]["address"] = mac
            # govee_devices[mac]["name"] = name
            # govee_devices[mac]["mfg_data"] = advertisement.mfg_data
            # govee_devices[mac]["data"] = encoded_data

            # govee_devices[mac]["tempInC"] = decode_temp_in_c(encoded_data)
            # govee_devices[mac]["tempInF"] = decode_temp_in_f(encoded_data)
            # govee_devices[mac]["humidity"] = decode_humidity(encoded_data)

            # govee_devices[mac]["battery"] = battery
            #print_values(mac)
            reading={'name': str(name), 'temp': float(decode_temp_in_c(encoded_data)), 'battery': float(battery), 'humidity': float(decode_humidity(encoded_data))}
            asyncio.run(process_thermo(reading))

        if advertisement.rssi is not None and advertisement.rssi != 0:
            govee_devices[mac]["rssi"] = advertisement.rssi
            #print_rssi(mac)

        log.debug(govee_devices[mac])


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
