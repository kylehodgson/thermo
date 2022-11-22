import schedule
import time
from zonemgr.services.moer_reading_db_service import MoerReadingStore
from zonemgr.db import ZoneManagerDB
from zonemgr.models import MoerReadingFrom
from simplemoer.client import WattTime

def update_moer():
    print("updating moer...")
    moersvc=MoerReadingStore(ZoneManagerDB())
    wt = WattTime()
    reading = wt.get_index()
    print(f"reading: {reading}")
    moer_reading = MoerReadingFrom(reading)
    print(f"reading parsed: {moer_reading}")
    moersvc.save_if_newer(moer_reading)

schedule.every(5).minutes.do(update_moer)
while True:
    schedule.run_pending()
    time.sleep(1)

