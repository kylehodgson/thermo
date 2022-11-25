#!/usr/bin/env python
import time
import os
import sys
import asyncio
import datetime
from bleson import get_provider, Observer
from plugins.goveesensors import GoveeSensor
from zonemgr.thermostat import Thermostat


def log_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def on_advertisement(advertisement):

    if GoveeSensor.recognizes(advertisement):
        reading = GoveeSensor.reading_from_advertisement(advertisement)
        thermo = Thermostat()
        asyncio.run(thermo.handle_reading(reading))


def main() -> int:
    print("Starting thermo process.")
    try:
        adapter = get_provider().get_adapter()
        observer = Observer(adapter)
        observer.on_advertising_data = on_advertisement
    except Exception as exception:
        print(f"Error getting ble adaptor {exception}")
        raise

    try:
        while True:
            observer.start()
            # I don't yet understand why this start/sleep/stop loop is necessary.
            time.sleep(1)
            # When I skip the sleep and stop, it forks to the background but doesn't work
            observer.stop()
    except KeyboardInterrupt:
        try:
            print(f"[{log_time()}] Received keyboard interrupt, stopping.")
            observer.stop()
            sys.exit(0)
        except SystemExit:
            print(f"[{log_time()}] Received system shutdown, stopping.")
            observer.stop()
            os._exit(0)


if __name__ == '__main__':
    sys.exit(main())
