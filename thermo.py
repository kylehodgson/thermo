#!/usr/bin/env python
import time
import os
import logging
import sys
import asyncio
import datetime

from bleson import get_provider, Observer

from plugins.goveesensors import GoveeSensor
#from plugins.ui import Display
from zonemgr.panel_plug import PanelPlugFactory
from zonemgr.thermostat import Thermostat
from zonemgr.db import ZoneManagerDB
from zonemgr.services.config_db_service import ConfigStore
from zonemgr.services.temp_reading_db_service import TempReadingStore
from zonemgr.services.moer_reading_db_service import MoerReadingStore
from zonemgr.services.presence_db_service import ZonePresenceStore

class OneLineExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)
 
    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "") + '|'
        return result

handler = logging.StreamHandler()
#formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
formatter = OneLineExceptionFormatter('%(asctime)s|%(name)s|%(levelname)s|%(message)s|','%Y/%m/%d %H:%M:%S')
handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
root.addHandler(handler)
logging.getLogger("bleson").setLevel(logging.ERROR)

zmdb=ZoneManagerDB()
config_store=ConfigStore(zmdb)
temp_store=TempReadingStore(zmdb)
moer_store=MoerReadingStore(zmdb)
plug_service=PanelPlugFactory()
presence_store=ZonePresenceStore(zmdb)

#display_service=Display()
thermostat = Thermostat(temp_store, config_store, moer_store, plug_service, presence_store)
#thermostat = Thermostat(temp_store, config_store, moer_store, plug_service, display_service)

def on_advertisement(advertisement):
        if GoveeSensor.recognizes(advertisement):
            reading = GoveeSensor.reading_from_advertisement(advertisement)
            asyncio.run(thermostat.handle_reading(reading))

def main() -> int:
    logging.info("Starting thermo process.")
    try:
        adapter = get_provider().get_adapter()
        observer = Observer(adapter)
        observer.on_advertising_data = on_advertisement
    except Exception as exception:
        logging.info(f"Error getting ble adaptor {exception}")
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
            logging.info(f"Received keyboard interrupt, stopping.")
            observer.stop()
            sys.exit(0)
        except SystemExit:
            logging.info(f"Received system shutdown, stopping.")
            observer.stop()
            os._exit(0)



if __name__ == '__main__':
    try:
        exit(main())
    except Exception:
        logging.exception("Exception in main(): ")
        exit(1)
