from zonemgr.db import ZoneManagerDB
from zonemgr.models import MoerReading

class MoerReadingStore:
    zmdb: ZoneManagerDB

    def get_local_ba_id(self)->str:
        return "IESO_NORTH" ## replace me with something that uses the WattTime API to get the local ba

    def __init__(self, zmdb: ZoneManagerDB) -> None:
        self.zmdb=zmdb

    def save_if_newer(self, reading: MoerReading, seconds_elapsed: int) -> None:
        with self.zmdb as conn: 
            with conn.cursor() as cursor:
                cursor.execute( ("INSERT INTO public.moer_readings (reading) "
                                 "SELECT (%s) WHERE NOT EXISTS "
                                 "  (SELECT id FROM public.moer_readings "
                                 "   WHERE extract(epoch from (CURRENT_TIMESTAMP::timestamp - reading_time::timestamp)) < %s "
                                 "   AND reading ->> 'sensor_id' = %s );"), 
                                 (reading.json(), seconds_elapsed, reading.ba_id))
                conn.commit()

    def select_latest_moer_reading(self,ba_id: str):
        criteria="""{"ba_id": "%s"}""" % ba_id
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("""select reading, reading_time from public.moer_readings where reading @> %s ORDER BY reading_time desc LIMIT 1;""" , (criteria, ))
                if cursor.rowcount>0:
                    record=cursor.fetchone()
                    (reading,timestamp)=record
                    mr = MoerReading.parse_obj(reading)
                    return mr
                else:
                    return (False, False)

