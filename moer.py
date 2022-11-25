import time
import schedule
from simplemoer.client import WattTime
from zonemgr.services.moer_reading_db_service import MoerReadingStore
from zonemgr.db import ZoneManagerDB
from zonemgr.models import MoerReadingFrom


def update_moer():
    print("updating moer...")
    moersvc = MoerReadingStore(ZoneManagerDB())
    watt_time = WattTime()
    reading = watt_time.get_index()
    print(f"reading: {reading}")
    moer_reading = MoerReadingFrom(reading)
    print(f"reading parsed: {moer_reading}")
    moersvc.save_if_newer(moer_reading)


schedule.every(5).minutes.do(update_moer)
while True:
    schedule.run_pending()
    time.sleep(1)
