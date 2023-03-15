import sys
if __name__ == "__main__" and __package__ is None:
    from os.path import dirname 
    sys.path.append(dirname(sys.path[0]))
import time
from bleson import get_provider, Observer, UUID16
#from bleson.logger import log, set_level, ERROR
from zonemgr.models import TemperatureReading

# Disable warnings
#set_level(ERROR)

import logging
log = logging.getLogger(__name__)

class GoveeSensor:

    GOVEE_BT_MAC_OUI_PREFIX = "A4:C1:38"
    H5075_UPDATE_UUID16 = UUID16(0xEC88)

    sensors = []
    found_sensor_names = []

    @staticmethod
    def recognizes(advertisement):
        if advertisement.address.address.startswith(GoveeSensor.GOVEE_BT_MAC_OUI_PREFIX):
            if GoveeSensor.H5075_UPDATE_UUID16 in advertisement.uuid16s:
                return True
        return False

    @staticmethod
    def reading_from_advertisement(advertisement) -> TemperatureReading:
        mfg_data = '{:>7}'.format(int(advertisement.mfg_data.hex()[6:12], 16))
        temperature=float(0.0)
        try:
            orig_val=mfg_data[0:4]
            temperature = float(orig_val)/10
        except ValueError as e:
            log.info(f"Could not convert '{orig_val}' to float. mfg_data: {mfg_data} Exception: {e}")

        humidity = float(mfg_data[4:7])/10
        battery = int(advertisement.mfg_data.hex()[12:14], 16)
        return TemperatureReading(
            sensor_id=str(advertisement._name),
            temp=float(temperature),
            battery=int(battery),
            humidity=float(humidity))

    def on_advertisement(self, advertisement):
        log.debug(advertisement)
        if advertisement.address.address.startswith(GoveeSensor.GOVEE_BT_MAC_OUI_PREFIX):
            if GoveeSensor.H5075_UPDATE_UUID16 in advertisement.uuid16s:
                reading = GoveeSensor.reading_from_advertisement(advertisement)
                if reading.sensor_id not in self.found_sensor_names:
                    self.found_sensor_names.append(reading.sensor_id)
                    self.sensors.append(reading)

    def scan(self):
        adapter = get_provider().get_adapter()
        observer = Observer(adapter)
        observer.on_advertising_data = self.on_advertisement
        for x in range(0, 6):
            observer.start()
            time.sleep(5)
            observer.stop()
        return self.sensors


def discover():
    d = GoveeSensor()
    return d.scan()


def main() -> int:
    for sensor in discover():
        log.info(f"sensor: {sensor}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
