#!/usr/bin/env python
import time
import os
import sys
import asyncio
import json
import datetime

from bleson import get_provider, Observer, UUID16
from bleson.logger import log, set_level, ERROR, DEBUG, INFO

# Disable warnings
set_level(ERROR)

class GoveeSensorsDiscovery:
        
    # https://macaddresschanger.com/bluetooth-mac-lookup/A4%3AC1%3A38
    # OUI Prefix	Company
    # A4:C1:38	Telink Semiconductor (Taipei) Co. Ltd.
    GOVEE_BT_mac_OUI_PREFIX = "A4:C1:38"
    H5075_UPDATE_UUID16 = UUID16(0xEC88)

    sensors=[]
    found_sensor_names=[]
    
    @staticmethod
    def reading_from_advertisement(advertisement):
        mfg_data='{:>7}'.format(int(advertisement.mfg_data.hex()[6:12],16))
        temperature=float(mfg_data[0:4])/10
        humidity=float(mfg_data[4:7])/10
        battery = int(advertisement.mfg_data.hex()[12:14], 16)
        return {'sensor_id': str(advertisement._name), 'temp': float(temperature), 'battery': int(battery), 'humidity': float(humidity)}

    def on_advertisement(self,advertisement):
        log.debug(advertisement)
        if advertisement.address.address.startswith(GoveeSensorsDiscovery.GOVEE_BT_mac_OUI_PREFIX):
            if GoveeSensorsDiscovery.H5075_UPDATE_UUID16 in advertisement.uuid16s:
                reading = GoveeSensorsDiscovery.reading_from_advertisement(advertisement)
                if(reading['sensor_id'] not in self.found_sensor_names):
                    self.found_sensor_names.append(reading['sensor_id'])
                    self.sensors.append(reading)


    def scan(self):
        adapter = get_provider().get_adapter()
        observer = Observer(adapter)
        observer.on_advertising_data = self.on_advertisement
        for x in range(0,6):
            observer.start()
            time.sleep(5)
            observer.stop()
        return self.sensors

def discover():
    d = GoveeSensorsDiscovery()
    return d.scan()

def main() -> int:
    for sensor in discover():
        print(f"name: {sensor['name']}")
        for property in sensor:
            print(f"\t{property}:\t{sensor[property]}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
