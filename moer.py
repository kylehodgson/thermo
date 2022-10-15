import schedule
import time
from thirdparty.watttime.WattTimeAPI import WattTime
from zonemgr.services.moer_reading_db_service import MoerReadingStore
from zonemgr.db import ZoneManagerDB
from zonemgr.models import MoerReading, MoerReadingFrom

WATTTIMEUSERNAME="longbranchflyer"
WATTTIMEPASSWORD="AJqPC4aXQLo*gm8mQEoWHcWK"

def update_moer():
    print("updating moer...")
    moersvc=MoerReadingStore(ZoneManagerDB())
    ba_id=moersvc.get_local_ba_id()
    wt=WattTime(WATTTIMEUSERNAME, WATTTIMEPASSWORD)
    reading_json=wt.get_index_json(ba_id)
    #moer_reading=MoerReading.parse_obj(reading_json)
    moer_reading=MoerReadingFrom(reading_json)
    moersvc.save_if_newer(moer_reading)

schedule.every(5).minutes.do(update_moer)
while True:
    schedule.run_pending()
    time.sleep(1)

